from flask import Blueprint, render_template

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/')
def index():
    return render_template('base.html')  # Render the landing page

@quiz_bp.route('/create-quiz')
def create_quiz():
    return render_template('create_quiz.html')
