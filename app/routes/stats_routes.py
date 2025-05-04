from flask import Blueprint, jsonify, request, render_template
from app.models import QuizResult
from app import db
from flask_login import login_required, current_user
from app.utils.stats_helpers import get_user_stats

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    return jsonify(get_user_stats(current_user.id))

@stats_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html', stats=get_user_stats(current_user.id))

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