from flask import Blueprint, jsonify, session, request, render_template
from app.models import QuizResult, Quiz
from app import db
from flask_login import login_required, current_user
from app.utils.stats_helpers import get_user_stats

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():

    user_id = current_user.id

    quizzes_completed = QuizResult.query.filter_by(user_id=user_id, completed=True).count()
    quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id, completed=True).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
    recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
    most_frequent_quiz_type = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id, completed=True).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc()).first()

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
    user_id = current_user.id

    quizzes_completed = QuizResult.query.filter_by(user_id=user_id, completed=True).count()
    quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id, completed=True).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
    recent_quiz_results = QuizResult.query.filter_by(user_id=user_id, completed=True).order_by(QuizResult.timestamp.desc()).limit(5).all()
    recent_quizzes = [result.quiz for result in recent_quiz_results if result.quiz is not None]
    most_frequent_quiz_type = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id, completed=True).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc()).first()

    from app.models import Folder
    folders = Folder.query.filter_by(user_id=user_id).all()
    unfinished_attempts = QuizResult.query.filter_by(user_id=user_id, completed=False).order_by(QuizResult.timestamp.desc()).all()

    stats = {
        'quizzes_completed': quizzes_completed,
        'quizzes_above_80': quizzes_above_80,
        'recent_quizzes': [{'id': quiz.id, 'title': quiz.title} for quiz in recent_quizzes],
        'most_frequent_quiz_type': most_frequent_quiz_type[0] if most_frequent_quiz_type else None
    }

    return render_template('dashboard.html', stats=stats, recent_quizzes=recent_quizzes, folders=folders, unfinished_attempts=unfinished_attempts)

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