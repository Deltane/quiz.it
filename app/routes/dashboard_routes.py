from flask import Blueprint, render_template, session, redirect, url_for
from app.models import User, Quiz

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard_view():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    user_quizzes = Quiz.query.filter_by(user_id=user.id).order_by(Quiz.created_at.desc()).all()
    recent_quizzes = user_quizzes[:3]
    past_quizzes = user_quizzes[3:]
    folders = []  # Replace with actual folder logic if available

    return render_template("dashboard.html", recent_quizzes=recent_quizzes, past_quizzes=past_quizzes, folders=folders)

@dashboard_bp.route('/redo_quiz/<int:quiz_id>')
def redo_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    session['quiz'] = json.loads(quiz.questions_json)
    session['score'] = 0
    session['current_question'] = 0
    return redirect(url_for('quiz_routes.take_quiz'))