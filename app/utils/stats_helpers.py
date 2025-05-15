# app/utils/stat_helpers.py
from app.models import QuizResult
from app import db

def get_user_stats(user_id):
    from app.models import QuizResult
    quizzes_completed = QuizResult.query.filter_by(user_id=user_id).count()
    recent_topics = QuizResult.query.filter_by(user_id=user_id)\
        .order_by(QuizResult.timestamp.desc()).limit(5).all()
    with db.session.no_autoflush:
        most_frequent_quiz_type = db.session.query(
            QuizResult.quiz_type,
            db.func.count(QuizResult.quiz_type)
        ).filter_by(user_id=user_id, completed=True)\
         .group_by(QuizResult.quiz_type)\
         .order_by(db.func.count(QuizResult.quiz_type).desc())\
         .first()

    highest = get_highest_scoring_quiz(user_id)

    return {
        'quizzes_completed': quizzes_completed,
        'recent_topics': [r.quiz_type for r in recent_topics],
        'most_frequent_quiz_type': most_frequent_quiz_type[0] if most_frequent_quiz_type else None,
        'best_score': {
            'score': highest.score,
            'total': highest.total_questions,
            'type': highest.quiz_type
        } if highest else None
    }

def get_highest_scoring_quiz(user_id):
    from app.models import QuizResult
    return QuizResult.query.filter_by(user_id=user_id)\
        .order_by((QuizResult.score / QuizResult.total_questions).desc())\
        .first()