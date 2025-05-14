import json

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from flask_login import current_user
from app.models import User, Quiz, Folder, db, QuizShare
from app.utils.email_utils import send_email

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard_view():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    user_quizzes = Quiz.query.filter_by(user_id=user.id, completed=True).order_by(Quiz.created_at.desc()).all()
    recent_quizzes = user_quizzes[:3]
    past_quizzes = user_quizzes[3:]
    user_folders = Folder.query.filter_by(user_id=user.id).all()

    return render_template("dashboard.html", recent_quizzes=recent_quizzes, past_quizzes=past_quizzes, folders=user_folders, all_quizzes=user_quizzes)

@dashboard_bp.route('/redo_quiz/<int:quiz_id>')
def redo_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    session['quiz'] = json.loads(quiz.questions_json)
    session['score'] = 0
    session['current_question'] = 0
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

@dashboard_bp.route('/share_quiz', methods=['POST'])
def share_quiz():
    if 'user_email' not in session:
        return jsonify({'error': 'You must be logged in to share quizzes.'}), 401

    user = User.query.filter_by(email=session['user_email']).first()
    if not user:
        return jsonify({'error': 'User not found. Please log in again.'}), 401

    quiz_id = request.form.get('quiz_id')
    recipient_email = request.form.get('recipient_email')

    if not quiz_id or not recipient_email:
        return jsonify({'error': 'Quiz ID and recipient email are required.'}), 400

    quiz = Quiz.query.filter_by(id=quiz_id, user_id=user.id).first()
    if not quiz:
        return jsonify({'error': 'Quiz not found or you do not have permission to share it.'}), 404

    recipient = User.query.filter_by(email=recipient_email).first()
    if not recipient:
        return jsonify({'error': 'This email address has not been authorized yet. Please ask them to sign in or choose another recipient.'}), 400

    # Check if the quiz is already shared with the recipient
    if recipient in quiz.shared_with_users:
        return jsonify({'error': 'This quiz is already shared with the specified user.'}), 400

    # Append the recipient to the shared_with_users relationship
    quiz.shared_with_users.append(recipient)
    db.session.commit()

    return jsonify({'success': 'Quiz successfully shared with the user.'}), 200

@dashboard_bp.route('/unshare_quiz/<int:share_id>', methods=['POST'])
def unshare_quiz(share_id):
    share = QuizShare.query.get(share_id)
    if not share or share.shared_by_user_id != current_user.id:
        flash('Invalid share or permission denied.', 'error')
        return redirect(url_for('dashboard.dashboard_view'))

    db.session.delete(share)
    db.session.commit()

    flash('Quiz unshared successfully.', 'success')
    return redirect(url_for('dashboard.dashboard_view'))

@dashboard_bp.route('/shared_quizzes', methods=['GET'])
def shared_quizzes():
    received_quizzes = QuizShare.query.filter_by(shared_with_user_id=current_user.id).all()
    return render_template('shared_quizzes.html', received_quizzes=received_quizzes)

@dashboard_bp.route('/search_users')
def search_users():
    query = request.args.get('query', '')
    if not query:
        return jsonify(users=[])

    users = User.query.filter(User.email.ilike(f"%{query}%")).all()
    user_data = [{'id': user.id, 'email': user.email} for user in users]

    return jsonify(users=user_data)