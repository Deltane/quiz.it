from flask import Blueprint, render_template, abort, flash, redirect, url_for
from flask_login import current_user, login_required
from app.models import User, Quiz, QuizResult # Assuming QuizResult might be used for stats
from app import db

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<username>')
@login_required # Ensure user is logged in to view any profile
def view_profile(username):
    profile_user = User.query.filter_by(username=username).first()
    if not profile_user:
        abort(404) # User not found

    query = Quiz.query.filter_by(user_id=profile_user.id)

    if current_user.id == profile_user.id:
        # Owner sees all their quizzes
        quizzes_to_display = query.order_by(Quiz.created_at.desc()).all()
    else:
        # Others see only public quizzes
        quizzes_to_display = query.filter_by(is_public=True).order_by(Quiz.created_at.desc()).all()
    
    # Basic stats (can be expanded)
    total_quizzes_created = Quiz.query.filter_by(user_id=profile_user.id).count()
    public_quizzes_count = Quiz.query.filter_by(user_id=profile_user.id, is_public=True).count()
    # More complex stats like completion rates would require joining with QuizResult

    profile_stats = {
        'total_quizzes_created': total_quizzes_created,
        'public_quizzes_count': public_quizzes_count,
        # Add more stats as needed, e.g., from QuizResult
    }

    return render_template(
        'profile/view.html', 
        profile_user=profile_user, 
        quizzes=quizzes_to_display,
        profile_stats=profile_stats,
        is_own_profile=(current_user.id == profile_user.id)
    )
