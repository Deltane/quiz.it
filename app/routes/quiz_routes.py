from app.models import QuizResult
from app import db
from datetime import datetime
from flask import Blueprint, session, request, jsonify, render_template, redirect, url_for, flash
from flask import render_template, session, request
from app.models import QuizShare, User, Quiz, PendingQuizShare  # Add PendingQuizShare to imports
from flask_login import current_user, login_required

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/')
def home():
    return render_template('landing_page.html')

# Direct quiz link handler - new route
@quiz_routes.route('/<int:quiz_id>')
def direct_quiz_link(quiz_id):
    """
    Handle direct quiz links (e.g., /123) for shared quizzes
    If user is not logged in, show auth loading animation and redirect to login
    If user is logged in, check if quiz is shared with them and show confirmation
    """
    # Store the quiz_id for after login
    session['shared_quiz_id'] = quiz_id
    
    # If user is not logged in, show auth loading animation and redirect to Google OAuth
    if not current_user.is_authenticated:
        # Generate the Google auth URL but don't redirect yet - we'll show the animation first
        auth_url = url_for('auth.login')
        return render_template('auth_loading.html', auth_url=auth_url)
    
    # User is logged in, now check if quiz is shared with them
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user is the quiz owner
    if quiz.user_id == current_user.id:
        # Redirect to standard quiz taking flow
        return redirect(url_for('quiz_routes.redo_quiz', quiz_id=quiz_id))
        
    # Check if quiz is shared with this user
    quiz_share = QuizShare.query.filter_by(
        quiz_id=quiz_id,
        shared_with_user_id=current_user.id
    ).first()
    
    # Check for pending share
    pending_share = None
    if not quiz_share:
        pending_share = PendingQuizShare.query.filter_by(
            quiz_id=quiz_id,
            recipient_email=current_user.email
        ).first()
        
        if pending_share:
            # Convert pending share to actual share
            quiz_share = QuizShare(
                quiz_id=quiz_id,
                shared_with_user_id=current_user.id,
                shared_by_user_id=pending_share.shared_by_user_id
            )
            db.session.add(quiz_share)
            db.session.delete(pending_share)
            db.session.commit()
    
    if quiz_share:
        # Add a flag to session to show modal on dashboard redirect
        session['show_shared_quiz_modal'] = True
        session['shared_quiz_id'] = quiz_id
        session['shared_quiz_sender_id'] = quiz_share.shared_by_user_id
        
        # Redirect to dashboard with a flash message
        flash(f"Quiz '{quiz.title}' has been shared with you.", "info")
        return redirect(url_for('dashboard.dashboard_view'))
    
    # Quiz isn't shared with this user
    flash("This quiz hasn't been shared with you or doesn't exist.", "error")
    return redirect(url_for('dashboard.dashboard_view'))

@quiz_routes.route('/start_shared_quiz/<int:quiz_id>', methods=['GET'])
@login_required
def start_shared_quiz(quiz_id):
    """Start a quiz that was shared with the current user"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify the quiz is shared with this user
    quiz_share = QuizShare.query.filter_by(
        quiz_id=quiz_id,
        shared_with_user_id=current_user.id
    ).first()
    
    if not quiz_share and quiz.user_id != current_user.id:
        flash("This quiz hasn't been shared with you.", "error")
        return redirect(url_for('dashboard.dashboard_view'))
    
    # Set up the quiz session
    import json
    session['quiz'] = json.loads(quiz.questions_json)
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}
    session['quiz_id'] = quiz.id
    session['topic'] = quiz.title
    session['quiz_duration'] = 5  # Default duration in minutes
    session['time_remaining'] = 5 * 60  # Default time in seconds
    
    return redirect(url_for('quiz_routes.take_quiz'))

@quiz_routes.route('/take_quiz')
def take_quiz():
    return render_template(
        'take_quiz.html',
        quiz_duration=session.get("quiz_duration", 5),
        current_question=session.get("current_question", 0),
        time_remaining=session.get("time_remaining", 0)
    )

@quiz_routes.route('/store_quiz', methods=['POST'])
def store_quiz():
    # Check if the user session is valid
    if not session.get('user_id'):
        return jsonify({'error': 'Session expired. Please log in again.'}), 401

    session['quiz'] = request.json['quiz']
    session['quiz_duration'] = request.json.get('quiz_duration', 5)  # in minutes
    session['time_remaining'] = session['quiz_duration'] * 60        # in seconds
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}

    # Save to DB
    from app.models import Quiz, db, User, Folder
    import json
    user_email = session.get("user_email")
    user = User.query.filter_by(email=user_email).first()
    if user:
        topic = request.json.get('quiz_title') or request.json.get('title') or 'Untitled'
        questions = request.json['quiz']
        folder_id = session.pop("folder_id", None)
        folder = Folder.query.get(folder_id) if folder_id else None
        quiz = Quiz(title=topic, questions_json=json.dumps(questions), user_id=user.id)
        if folder:
            quiz.folders.append(folder)
        db.session.add(quiz)
        db.session.commit()
        
        session['quiz_id'] = quiz.id
        session['topic'] = topic  # Or whatever type you use

    return '', 204

# Redo quiz route
@quiz_routes.route('/redo_quiz/<int:quiz_id>', methods=['POST'])
def redo_quiz(quiz_id):
    from app.models import Quiz
    import json
    quiz = Quiz.query.get_or_404(quiz_id)

    # Authorization check
    if quiz.user_id != session.get("user_id"):
        return "Unauthorized", 403

    session['quiz'] = json.loads(quiz.questions_json)
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}
    session['quiz_id'] = quiz.id
    session['quiz_type'] = quiz.title

    return redirect(url_for('quiz_routes.take_quiz'))

@quiz_routes.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    from app.models import Quiz, QuizResult, db
    quiz = Quiz.query.get_or_404(quiz_id)

    # Authorization check
    if quiz.user_id != session.get("user_id"):
        return "Unauthorized", 403

    # Delete related results
    QuizResult.query.filter_by(quiz_id=quiz.id).delete()
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for('stats_bp.dashboard'))

@quiz_routes.route('/rename_quiz/<int:quiz_id>', methods=['POST'])
def rename_quiz(quiz_id):
    from app.models import Quiz
    new_title = request.form.get('new_title')
    quiz = Quiz.query.get_or_404(quiz_id)

    # Authorization check
    if quiz.user_id != session.get('user_id'):
        return "Unauthorized", 403

    if new_title:
        quiz.title = new_title
        db.session.commit()

    return redirect(url_for('stats_bp.dashboard'))

@quiz_routes.route('/get_question/<int:question_index>', methods=['GET'])
def get_question(question_index):
    quiz = session.get('quiz', [])
    print(f"Fetching question {question_index}, quiz length = {len(quiz)}")
    if question_index < len(quiz):
        question = quiz[question_index]
        response = {
            'question': question['question'],
            'type': 'multiple-choice' if 'options' in question else 'fill-in-blank',
            'time_limit': session.get('quiz_duration', 5)
        }
        
        # Only include options for multiple choice questions
        if 'options' in question:
            response['options'] = question['options']
            
        return jsonify(response)
    return jsonify({}), 404

@quiz_routes.route('/submit_answer', methods=['POST'])
def submit_answer():
    if not session.get('user_id'):
        return jsonify({'error': 'Session expired. Please log in again.'}), 401
    data = request.json
    question_index = data['questionIndex']
    user_answer = data['answer']

    # Store the user's answer
    if 'answers' not in session:
        session['answers'] = {}
    session['answers'][question_index] = user_answer

    # Check if the quiz is completed
    quiz = session.get('quiz', [])
    if question_index + 1 >= len(quiz):
        # Calculate score
        score = 0
        for i, question in enumerate(quiz):
            user_ans = str(session['answers'].get(i, '')).lower().strip()
            correct_ans = str(question['answer']).lower().strip()
            if user_ans == correct_ans:
                score += 1
        
        session['score'] = score

        # Store quiz result in the database
        user_id = session.get('user_id')
        quiz_id = session.get('quiz_id')
        quiz_title = session.get('topic') or 'Untitled'
        total_questions = len(quiz)
        timestamp = datetime.utcnow()

        print("Session contents before saving QuizResult:", dict(session))

        QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz_id, completed=False).delete()
        # Also remove any previously completed attempts for this quiz to prevent duplicates
        existing_completed = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz_id, completed=True).first()
        if existing_completed:
            db.session.delete(existing_completed)

        quiz_result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions,
            timestamp=timestamp,
            quiz_type=quiz_title,
            title=quiz_title,
            completed=True
        )
        score = 0
        correctness_list = []

        for i, question in enumerate(quiz):
            user_ans = str(session['answers'].get(i, '')).lower().strip()
            correct_ans = str(question['answer']).lower().strip()
            is_correct = user_ans == correct_ans
            correctness_list.append(is_correct)
            if is_correct:
                score += 1

        db.session.add(quiz_result)
        db.session.commit()

        # Calculate and store quiz statistics
        quizzes_completed = QuizResult.query.filter_by(user_id=user_id).count()
        quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
        recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
        most_frequent_quiz_type = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc()).first()

        session['quizzes_completed'] = quizzes_completed
        session['quizzes_above_80'] = quizzes_above_80
        session['recent_topics'] = [result.title for result in recent_topics]
        session['most_frequent_quiz_type'] = most_frequent_quiz_type[0] if most_frequent_quiz_type else None

        # Clean up session
        session.pop('quiz', None)
        session.pop('answers', None)
        session.pop('current_question', None)
        
        return jsonify({
            'completed': True,
            'score': score,
            'total': len(quiz),
            'results': correctness_list
        })

    return jsonify({'completed': False})

# Route to handle quiz exit and save incomplete quiz result
@quiz_routes.route('/exit_quiz', methods=['POST'])
def exit_quiz():
    from app.models import QuizResult
    import json

    user_id = session.get("user_id")
    quiz_id = session.get("quiz_id")
    topic = session.get("topic", "Untitled")
    answers = session.get("answers", {})
    time_remaining = request.form.get("time_left") or (request.json.get("time_left", 0) if request.json else 0)
    quiz_duration = session.get("quiz_duration", 5)  # keep in minutes

    if not user_id or not quiz_id:
        return jsonify(success=False, message="Missing session info"), 400

    quiz_result = QuizResult(
        user_id=user_id,
        quiz_id=quiz_id,
        score=0,  # Will be calculated on resume
        total_questions=len(session.get("quiz", [])),
        timestamp=datetime.utcnow(),
        quiz_type=topic,
        completed=False,
        answers=json.dumps(answers),
        title=topic,
        time_remaining=int(time_remaining),
        quiz_duration=int(quiz_duration)
    )

    db.session.add(quiz_result)
    db.session.commit()

    # Clear session state
    session.pop("quiz", None)
    session.pop("answers", None)
    session.pop("current_question", None)
    session.pop("quiz_id", None)
    session.pop("quiz_duration", None)
    session.pop("topic", None)

    return redirect(url_for('stats_bp.dashboard'))


# Route to resume an unfinished quiz attempt
@quiz_routes.route('/resume_quiz/<int:attempt_id>', methods=['GET'])
def resume_quiz(attempt_id):
    attempt = QuizResult.query.get_or_404(attempt_id)
    if attempt.user_id != session.get('user_id'):
        return "Unauthorized", 403

    from app.models import Quiz
    import json

    quiz = Quiz.query.get(attempt.quiz_id)
    if not quiz:
        return "Quiz not found", 404

    questions = json.loads(quiz.questions_json)
    answers = json.loads(attempt.answers or '{}')
    first_unanswered = 0
    for i in range(len(questions)):
        if str(i) not in answers:
            first_unanswered = i
            break

    session['quiz'] = questions
    session['answers'] = answers
    session['score'] = 0
    session['current_question'] = first_unanswered
    session['quiz_id'] = quiz.id
    session['topic'] = attempt.title
    session['quiz_duration'] = attempt.quiz_duration
    session['time_remaining'] = attempt.time_remaining

    return redirect(url_for('quiz_routes.take_quiz'))

@quiz_routes.route('/delete_quiz_attempt/<int:attempt_id>', methods=['POST'])
def delete_quiz_attempt(attempt_id):
    attempt = QuizResult.query.get_or_404(attempt_id)
    if attempt.user_id != session.get('user_id'):
        return "Unauthorized", 403

    db.session.delete(attempt)
    db.session.commit()
    return redirect(url_for('stats_bp.dashboard'))

@quiz_routes.route('/share_quiz/<int:quiz_id>', methods=['POST'])
def share_quiz(quiz_id):
    """Share a quiz with a recipient email."""
    from flask import current_app
    from app.utils.email_utils import send_email
    import os
    import traceback
    
    if not current_user.is_authenticated:
        return jsonify({'error': 'You must be logged in to share a quiz.'}), 401

    recipient_email = request.json.get('email')
    if not recipient_email:
        return jsonify({'error': 'Recipient email is required.'}), 400

    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        return jsonify({'error': 'You can only share your own quizzes.'}), 403

    # Check if the user is trying to share with themselves
    if recipient_email == current_user.email:
        return jsonify({'error': 'You cannot share a quiz with yourself.'}), 400

    # Check if recipient exists in the system
    recipient = User.query.filter_by(email=recipient_email).first()
    
    # Variable to track if this is a new share (for sending email)
    is_new_share = False
    
    if recipient:
        # If recipient exists, check if quiz is already shared
        existing_share = QuizShare.query.filter_by(
            quiz_id=quiz.id,
            shared_with_user_id=recipient.id
        ).first()
        
        if existing_share:
            return jsonify({'message': 'This quiz is already shared with the specified user.'}), 200
        
        # Share with existing user
        quiz_share = QuizShare(
            quiz_id=quiz.id,
            shared_with_user_id=recipient.id,
            shared_by_user_id=current_user.id
        )
        db.session.add(quiz_share)
        is_new_share = True
    else:
        # If recipient doesn't exist, check for pending share
        from app.models import PendingQuizShare
        
        existing_pending = PendingQuizShare.query.filter_by(
            quiz_id=quiz.id,
            recipient_email=recipient_email
        ).first()
        
        if existing_pending:
            return jsonify({'message': 'This quiz is already shared with the specified email.'}), 200
        
        # Create a pending share for non-existent user
        pending_share = PendingQuizShare(
            quiz_id=quiz.id,
            recipient_email=recipient_email,
            shared_by_user_id=current_user.id
        )
        db.session.add(pending_share)
        is_new_share = True
    
    db.session.commit()
    
    # Send email notification for new shares
    if is_new_share:
        try:
            # Generate absolute URLs
            base_url = request.host_url.rstrip('/')
            login_url = f"{base_url}{url_for('auth.login')}"
            quiz_url = f"{base_url}/{quiz.id}"  # Direct link to the quiz
            
            current_app.logger.info(f"Attempting to send email to {recipient_email} via SendGrid")
            
            # Send email with HTML template
            send_email(
                subject=f"{current_user.username} shared a quiz with you on quiz.it",
                recipients=[recipient_email],
                body=f"Hi there! {current_user.username} has shared a quiz titled '{quiz.title}' with you on quiz.it. Sign in with Google using this email to access it.",
                template='emails/quiz_share.html',
                sender_name=current_user.username,
                quiz_title=quiz.title,
                login_url=login_url,
                quiz_url=quiz_url
            )
            current_app.logger.info(f"✅ Quiz share email sent to {recipient_email}")
        except Exception as e:
            import traceback
            current_app.logger.error(f"❌ Failed to send quiz share email: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            # Note: We don't return an error to the user if email fails
            # The quiz is still shared, even if notification fails

    return jsonify({
        'success': True,
        'message': 'Quiz shared successfully. An invitation email has been sent.'
    }), 200

@quiz_routes.route('/view_quiz/<int:quiz_id>', methods=['GET'])
def view_quiz(quiz_id):
    """View a quiz if access conditions are met."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if the user is the creator of the quiz
    if quiz.user_id == current_user.id:
        return render_template('take_quiz.html', quiz=quiz)
    
    # Check if the quiz is shared with this user through QuizShare
    quiz_share = QuizShare.query.filter_by(
        quiz_id=quiz.id,
        shared_with_user_id=current_user.id
    ).first()

    if quiz_share:
        return render_template('take_quiz.html', quiz=quiz)
        
    # Check if there's a pending share for this user's email
    from app.models import PendingQuizShare
    pending_share = PendingQuizShare.query.filter_by(
        quiz_id=quiz.id,
        recipient_email=current_user.email
    ).first()
    
    if pending_share:
        # Convert the pending share to a regular share now that the user has registered
        new_share = QuizShare(
            quiz_id=quiz.id,
            shared_with_user_id=current_user.id,
            shared_by_user_id=pending_share.shared_by_user_id
        )
        db.session.add(new_share)
        db.session.delete(pending_share)  # Remove the pending share
        db.session.commit()
        return render_template('take_quiz.html', quiz=quiz)
    
    return jsonify({'error': 'You do not have access to this quiz.'}), 403

@quiz_routes.route('/share_quiz', methods=['POST'])
def share_quiz_root():
    """
    Root-level endpoint for sharing quizzes with any email address.
    The quiz will be accessible only if the recipient logs in with the shared email.
    """
    from flask import current_app
    from app.utils.email_utils import send_email
    import os
    
    if not current_user.is_authenticated:
        return jsonify({'error': 'You must be logged in to share quizzes.'}), 401

    if not request.is_json:
        return jsonify({'error': 'Request must be JSON.'}), 415

    data = request.get_json()
    quiz_id = data.get('quiz_id')
    recipient_email = data.get('recipient_email')

    if not quiz_id or not recipient_email:
        return jsonify({'error': 'Quiz ID and recipient email are required.'}), 400

    try:
        quiz_id = int(quiz_id)
    except ValueError:
        return jsonify({'error': 'Invalid Quiz ID format.'}), 400

    # Get the quiz
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({'error': 'Quiz not found.'}), 404

    # Authorization check
    if quiz.user_id != current_user.id:
        return jsonify({'error': 'You can only share your own quizzes.'}), 403

    # Check if the user is trying to share with themselves
    if recipient_email == current_user.email:
        return jsonify({'error': 'You cannot share a quiz with yourself.'}), 400

    # Variable to track if this is a new share (for sending email)
    is_new_share = False
    
    # Check if recipient exists in the system
    recipient = User.query.filter_by(email=recipient_email).first()
    
    if recipient:
        # If recipient exists, check if quiz is already shared
        existing_share = QuizShare.query.filter_by(
            quiz_id=quiz.id,
            shared_with_user_id=recipient.id
        ).first()
        
        if existing_share:
            return jsonify({'message': 'This quiz is already shared with the specified user.'}), 200
        
        # Share with existing user
        quiz_share = QuizShare(
            quiz_id=quiz.id,
            shared_with_user_id=recipient.id,
            shared_by_user_id=current_user.id
        )
        db.session.add(quiz_share)
        is_new_share = True
    else:
        # If recipient doesn't exist, check for pending share
        from app.models import PendingQuizShare
        
        existing_pending = PendingQuizShare.query.filter_by(
            quiz_id=quiz.id,
            recipient_email=recipient_email
        ).first()
        
        if existing_pending:
            return jsonify({'message': 'This quiz is already shared with the specified email.'}), 200
        
        # Create a pending share for non-existent user
        pending_share = PendingQuizShare(
            quiz_id=quiz.id,
            recipient_email=recipient_email,
            shared_by_user_id=current_user.id
        )
        db.session.add(pending_share)
        is_new_share = True
    
    db.session.commit()
    
    # Send email notification for new shares
    if is_new_share:
        try:
            # Generate absolute URLs
            base_url = request.host_url.rstrip('/')
            login_url = f"{base_url}{url_for('auth.login')}"
            quiz_url = f"{base_url}/{quiz.id}"  # Direct link to the quiz
            
            # Send email with HTML template
            send_email(
                subject=f"{current_user.username} shared a quiz with you on quiz.it",
                recipients=[recipient_email],
                body=f"Hi there! {current_user.username} has shared a quiz titled '{quiz.title}' with you on quiz.it. Sign in with Google using this email to access it.",
                template='emails/quiz_share.html',
                sender_name=current_user.username,
                quiz_title=quiz.title,
                login_url=login_url,
                quiz_url=quiz_url
            )
            current_app.logger.info(f"Sent quiz share email to {recipient_email}")
        except Exception as e:
            current_app.logger.error(f"Failed to send quiz share email: {str(e)}")
            # Note: We don't return an error to the user if email fails
            # The quiz is still shared, even if notification fails
    
    return jsonify({'success': True, 'message': f'Quiz successfully shared with {recipient_email}.'}), 200

@quiz_routes.route('/check_login')
def check_login():
    """
    Root-level endpoint to check login status for frontend requests.
    Returns whether the user is currently authenticated.
    """
    return jsonify({
        'logged_in': current_user.is_authenticated,
        'user_info': {
            'id': current_user.id,
            'name': session.get('user_name'),
            'email': current_user.email if current_user.is_authenticated else None,
            'picture': session.get('user_pic')
        } if current_user.is_authenticated else None
    })
