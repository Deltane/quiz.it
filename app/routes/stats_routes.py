from flask import Blueprint, jsonify, session, request, render_template
from app.models import QuizResult, Quiz
from app import db
from flask_login import login_required, current_user
from app.utils.stats_helpers import get_user_stats
from sqlalchemy import desc, func
from datetime import timezone as dt_timezone
from pytz import timezone

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():

    user_id = current_user.id

    quizzes_completed = db.session.query(QuizResult.quiz_id).filter_by(user_id=user_id, completed=True).distinct().count()
    subquery = db.session.query(QuizResult.quiz_id, db.func.max(QuizResult.score / QuizResult.total_questions).label('max_score'))\
        .filter_by(user_id=user_id, completed=True)\
        .group_by(QuizResult.quiz_id)\
        .subquery()
    quizzes_above_80 = db.session.query(subquery).filter(subquery.c.max_score >= 0.8).count()
    recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
    with db.session.no_autoflush:
        most_frequent_quiz_type = db.session.query(
            QuizResult.quiz_type,
            db.func.count(QuizResult.quiz_type)
        ).filter_by(user_id=user_id, completed=True)\
         .group_by(QuizResult.quiz_type)\
         .order_by(db.func.count(QuizResult.quiz_type).desc())\
         .first()

    stats = {
        'quizzes_completed': quizzes_completed,
        'quizzes_above_80': quizzes_above_80,
        'recent_topics': [result.quiz_type for result in recent_topics],
        'most_frequent_quiz_type': most_frequent_quiz_type[0] if most_frequent_quiz_type else None
    }

    return jsonify(stats)

@stats_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    with db.session.no_autoflush:
        user_id = current_user.id

        quizzes_completed = db.session.query(QuizResult.quiz_id).filter_by(user_id=user_id, completed=True).distinct().count()
        subquery = db.session.query(
            QuizResult.quiz_id,
            db.func.max(QuizResult.score / QuizResult.total_questions).label('max_score')
        ).filter_by(user_id=user_id, completed=True).group_by(QuizResult.quiz_id).subquery()

        quizzes_above_80 = db.session.query(subquery).filter(subquery.c.max_score >= 0.8).count()

        latest_attempts_subquery = db.session.query(
            QuizResult.quiz_id,
            func.max(QuizResult.timestamp).label("latest")
        ).filter_by(user_id=user_id, completed=True).group_by(QuizResult.quiz_id).subquery()

        latest_results = db.session.query(QuizResult).join(
            latest_attempts_subquery,
            (QuizResult.quiz_id == latest_attempts_subquery.c.quiz_id) &
            (QuizResult.timestamp == latest_attempts_subquery.c.latest)
        ).order_by(desc(QuizResult.timestamp)).limit(5).all()

        recent_quizzes = []
        seen_quiz_ids = set()
        for result in latest_results:
            quiz = result.quiz
            if quiz and quiz.id not in seen_quiz_ids:
                quiz.attempts = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz.id, completed=True).order_by(QuizResult.timestamp.desc()).all()
                perth = timezone('Australia/Perth')
                for attempt in quiz.attempts:
                    if attempt.timestamp.tzinfo is None:
                        attempt.timestamp = attempt.timestamp.replace(tzinfo=dt_timezone.utc)
                    attempt.timestamp = attempt.timestamp.astimezone(perth)
                recent_quizzes.append(quiz)
                seen_quiz_ids.add(quiz.id)
        most_frequent_quiz_type = db.session.query(
            QuizResult.quiz_type,
            db.func.count(QuizResult.quiz_type)
        ).filter_by(user_id=user_id, completed=True)\
         .group_by(QuizResult.quiz_type)\
         .order_by(db.func.count(QuizResult.quiz_type).desc())\
         .first()
        
        from app.models import Folder
        folders = Folder.query.filter_by(user_id=user_id).all()
        unfinished_attempts = db.session.query(QuizResult).filter(
            QuizResult.user_id == user_id,
            QuizResult.completed == False,
            ~QuizResult.quiz_id.in_(
                db.session.query(QuizResult.quiz_id).filter_by(user_id=user_id, completed=True)
            )
        ).order_by(QuizResult.timestamp.desc()).all()

        stats = {
            'quizzes_completed': quizzes_completed,
            'quizzes_above_80': quizzes_above_80,
            'recent_quizzes': [{'id': quiz.id, 'title': quiz.title} for quiz in recent_quizzes],
            'most_frequent_quiz_type': most_frequent_quiz_type[0] if most_frequent_quiz_type else None
        }

        rendered = render_template('dashboard.html', stats=stats, recent_quizzes=recent_quizzes, folders=folders, unfinished_attempts=unfinished_attempts)
        # Inject the script to clear localStorage for deleted quizzes
        script = '''
<script>
    const cookies = document.cookie.split("; ");
    const clearKey = cookies.find(row => row.startsWith("clearLocalStorage_quiz_"));
    if (clearKey) {
        const quizId = clearKey.split("=")[0].split("_").pop();
        Object.keys(localStorage).forEach(key => {
            if (
                key.startsWith(`quiz_attempts_${quizId}_`) ||
                key.startsWith(`quiz_durations_${quizId}_`) ||
                key.startsWith(`quiz_review_${quizId}_`) ||
                key.startsWith(`current_quiz_${quizId}_`) ||
                key === `quiz_attempt_index_${quizId}`
            ) {
                localStorage.removeItem(key);
            }
        });
        // Clear the cookie so it doesn’t run again
        document.cookie = clearKey.split("=")[0] + "=; Max-Age=0";
    }
</script>
'''
        # Insert the script before closing </body> tag if present
        if '</body>' in rendered:
            rendered = rendered.replace('</body>', script + '</body>')
        else:
            rendered += script

        return rendered

@stats_bp.route('/filter_stats', methods=['POST'])
@login_required
def filter_stats():
    user_id = current_user.id
    filter_type = request.json.get('filter_type')
    sort_order = request.json.get('sort_order', 'desc')

    query = QuizResult.query.filter_by(user_id=user_id)

    if filter_type == 'quizzes_above_80':
        query = query.filter(QuizResult.score / QuizResult.total_questions >= 0.8)
    elif filter_type == 'recent_topics':
        query = query.order_by(QuizResult.timestamp.desc())
    elif filter_type == 'most_frequent_quiz_type':
        query = db.session.query(
            QuizResult.quiz_type,
            db.func.count(QuizResult.quiz_type)
        ).filter_by(user_id=user_id).group_by(
            QuizResult.quiz_type
        ).order_by(
            db.func.count(QuizResult.quiz_type).desc()
        )
        # Skip ordering again
        return jsonify([
            {'quiz_type': row[0], 'count': row[1]}
            for row in query.all()
        ])

    query = query.order_by(QuizResult.timestamp.asc() if sort_order == 'asc' else QuizResult.timestamp.desc())
    return jsonify([result.to_dict() for result in query.all()])