from flask import Blueprint, jsonify, session, request
from app.models import QuizResult
from app import db
from flask_login import login_required, current_user

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    user_id = current_user.id

    quizzes_completed = QuizResult.query.filter_by(user_id=user_id).count()
    quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
    recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
    most_frequent_quiz_type = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc()).first()

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

    quizzes_completed = QuizResult.query.filter_by(user_id=user_id).count()
    quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
    recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
    most_frequent_quiz_type = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc()).first()

    stats = {
        'quizzes_completed': quizzes_completed,
        'quizzes_above_80': quizzes_above_80,
        'recent_topics': [result.quiz_type for result in recent_topics],
        'most_frequent_quiz_type': most_frequent_quiz_type[0] if most_frequent_quiz_type else None
    }

    return render_template('dashboard.html', stats=stats)

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
        query = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc())

    if sort_order == 'asc':
        query = query.order_by(QuizResult.timestamp.asc())
    else:
        query = query.order_by(QuizResult.timestamp.desc())

    filtered_stats = query.all()

    return jsonify([result.to_dict() for result in filtered_stats])
