import json
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.models import User, Quiz, Folder, QuizResult, db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard_view():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    attempts = QuizResult.query.filter_by(user_id=user.id, completed=True).order_by(QuizResult.timestamp.desc()).all()
    quiz_attempts_map = {}
    scores = []
    quiz_type_count = {}
    for attempt in attempts:
        quiz_id = attempt.quiz_id
        if quiz_id not in quiz_attempts_map:
            quiz_attempts_map[quiz_id] = {
                "quiz": attempt.quiz,
                "attempts": []
            }
        quiz_attempts_map[quiz_id]["attempts"].append(attempt)

        if attempt.completed:
            scores.append(attempt.score / attempt.total_questions if attempt.total_questions else 0)
            quiz_type = attempt.quiz_type
            quiz_type_count[quiz_type] = quiz_type_count.get(quiz_type, 0) + 1

    quizzes_completed = len({attempt.quiz_id for attempts in quiz_attempts_map.values() for attempt in attempts["attempts"] if attempt.completed})
    quizzes_above_80 = sum(1 for s in scores if s >= 0.8)
    most_frequent_quiz_type = max(quiz_type_count, key=quiz_type_count.get) if quiz_type_count else None
    recent_topics = [quiz_data['quiz'].title for quiz_data in quiz_attempts_map.values() if quiz_data['attempts']]

    # Ensure recent_quizzes and past_quizzes are constructed from unique quizzes with their attempts, sorted by most recent attempt
    recent_quizzes = sorted(
        quiz_attempts_map.values(),
        key=lambda x: x["attempts"][-1].timestamp if x["attempts"] else datetime.min,
        reverse=True
    )
    past_quizzes = recent_quizzes[3:]
    recent_quizzes = recent_quizzes[:3]

    user_folders = Folder.query.filter_by(user_id=user.id).all()

    return render_template(
        "dashboard.html",
        recent_quizzes=recent_quizzes,
        past_quizzes=past_quizzes,
        folders=user_folders,
        quizzes_completed=quizzes_completed,
        quizzes_above_80=quizzes_above_80,
        most_frequent_quiz_type=most_frequent_quiz_type,
        recent_topics=recent_topics
    )

@dashboard_bp.route('/redo_quiz/<int:quiz_id>')
def redo_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    user_id = session.get("user_id")

    # Create a new attempt
    new_attempt = QuizResult(
        user_id=user_id,
        quiz_id=quiz.id,
        title=quiz.title,
        total_questions=len(json.loads(quiz.questions_json)),
        quiz_type=quiz.title,
        completed=False,
        current_index=0,
        score=0,
        start_time=datetime.utcnow()
    )
    db.session.add(new_attempt)
    db.session.commit()

    # Initialize session for the new attempt
    session['quiz'] = json.loads(quiz.questions_json)
    session['score'] = 0
    session['current_question'] = 0
    session['attempt_id'] = new_attempt.id
    session['quiz_id'] = quiz.id
    session['topic'] = quiz.title
    session['time_remaining'] = session.get("quiz_duration", 5) * 60

    return redirect(url_for('quiz_routes.take_quiz'))

@dashboard_bp.route('/create_folder', methods=['GET','POST'])
def create_folder():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    folder_name = request.form.get('folder_name')
    print("Folder name submitted:", folder_name)
    selected_quiz_ids = request.form.getlist('quiz_ids') or request.form.getlist('quiz_ids[]')
    print("Selected quiz IDs:", selected_quiz_ids)

    if not folder_name:
        flash("Folder name cannot be empty.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    new_folder = Folder(name=folder_name, user_id=user.id)
    db.session.add(new_folder)
    db.session.flush()  # to get the new_folder.id

    for quiz_id in selected_quiz_ids:
        quiz = Quiz.query.get(int(quiz_id))
        if quiz and quiz.user_id == user.id:
            if new_folder not in quiz.folders:
                quiz.folders.append(new_folder)
            db.session.add(quiz)

    db.session.commit()
    flash(f"Folder '{folder_name}' created successfully.", "success")
    return redirect(url_for('dashboard.dashboard_view'))


# Route to handle deleting a folder
@dashboard_bp.route('/delete_folder/<int:folder_id>', methods=['POST'])
def delete_folder(folder_id):
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != user.id:
        flash("You are not authorized to delete this folder.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    # Unassign the folder from its quizzes before deleting
    for quiz in folder.quizzes:
        if folder in quiz.folders:
            quiz.folders.remove(folder)
        db.session.add(quiz)

    db.session.delete(folder)
    db.session.commit()
    flash("Folder deleted successfully.", "success")
    return redirect(url_for('dashboard.dashboard_view'))

@dashboard_bp.route('/rename_folder/<int:folder_id>', methods=['POST'])
def rename_folder(folder_id):
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != user.id:
        flash("You are not authorized to rename this folder.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    new_name = request.form.get('new_name')
    if new_name:
        folder.name = new_name
        db.session.commit()
        flash("Folder renamed successfully.", "success")
    else:
        flash("New folder name cannot be empty.", "error")

    return redirect(url_for('dashboard.dashboard_view'))

@dashboard_bp.route('/create_quiz_in_folder/<int:folder_id>', methods=['GET'])
def create_quiz_in_folder(folder_id):
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != user.id:
        flash("You are not authorized to create a quiz in this folder.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    # Store folder_id in session to use when saving the quiz later
    session['selected_folder_id'] = folder_id
    return redirect(url_for('quiz_routes.create_quiz'))

from flask import jsonify

@dashboard_bp.route('/assign_quiz_to_folder', methods=['POST'])
def assign_quiz_to_folder():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    folder_id = request.form.get('folder_id')
    quiz_id = request.form.get('quiz_id')

    if not folder_id or not quiz_id:
        return jsonify({'error': 'Missing folder or quiz ID.'}), 400

    folder = Folder.query.get_or_404(folder_id)
    if folder.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    quiz = Quiz.query.get(int(quiz_id))
    if quiz and quiz.user_id == user.id:
        if folder not in quiz.folders:
            quiz.folders.append(folder)
        db.session.add(quiz)
        db.session.commit()

        quiz_html = render_template("components/_quiz_item.html", quiz=quiz, folder=folder)
        return jsonify({"quiz_html": quiz_html, "folder_id": folder.id})
    else:
        return jsonify({"error": "Invalid quiz selected."}), 400

@dashboard_bp.route('/unassign_quiz_from_folder', methods=['POST'])
def unassign_quiz_from_folder():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    folder_id = request.form.get('folder_id')
    quiz_id = request.form.get('quiz_id')

    if not folder_id or not quiz_id:
        flash("Missing folder or quiz ID.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    folder = Folder.query.get_or_404(folder_id)
    quiz = Quiz.query.get_or_404(quiz_id)

    if folder.user_id != user.id or quiz.user_id != user.id:
        flash("You are not authorized to unassign this quiz.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    if folder in quiz.folders:
        quiz.folders.remove(folder)
        db.session.commit()
        flash("Quiz unassigned from folder.", "success")
    else:
        flash("Quiz was not assigned to this folder.", "error")

    return redirect(url_for('dashboard.dashboard_view'))