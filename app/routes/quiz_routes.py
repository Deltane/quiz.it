from app.models import Quiz, QuizResult, User, Folder, QuizAnswer, QuizSummary, QuizShare, PendingQuizShare
from app import db
from datetime import datetime
from flask import Blueprint, session, request, jsonify, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
import json
from pytz import timezone

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/')
def home():
    return render_template('landing_page.html')

# Direct quiz link handler - new route
@quiz_routes.route('/<int:quiz_id>')
def direct_quiz_link(quiz_id):
    if not current_user.is_authenticated:
        session.permanent = True
        session['shared_quiz_id'] = quiz_id
        session.modified = True
        auth_url = url_for('auth.login', next=f'/{quiz_id}')
        return render_template('auth_loading.html', auth_url=auth_url)

    quiz = Quiz.query.get_or_404(quiz_id)

    if quiz.user_id == current_user.id:
        return redirect(url_for('quiz_routes.redo_quiz', quiz_id=quiz_id))

    quiz_share = QuizShare.query.filter_by(
        quiz_id=quiz_id,
        shared_with_user_id=current_user.id
    ).first()

    pending_share = None
    if not quiz_share:
        pending_share = PendingQuizShare.query.filter_by(
            quiz_id=quiz_id,
            recipient_email=current_user.email
        ).first()

        if pending_share:
            quiz_share = QuizShare(
                quiz_id=quiz_id,
                shared_with_user_id=current_user.id,
                shared_by_user_id=pending_share.shared_by_user_id
            )
            db.session.add(quiz_share)
            db.session.delete(pending_share)
            db.session.commit()

    if quiz_share:
        sender = User.query.get(quiz_share.shared_by_user_id)
        return render_template(
            'dashboard.html',
            show_shared_quiz_modal=True,
            shared_quiz=quiz,
            sender=sender,
            recent_quizzes=Quiz.query.filter_by(user_id=current_user.id).order_by(Quiz.created_at.desc()).limit(3).all(),
            shared_quizzes=[{'quiz': quiz, 'sender': sender}],
            stats={
                'quizzes_completed': 0,
                'quizzes_above_80': 0,
                'most_frequent_quiz_type': 'None'
            }
        )

    flash("This quiz hasn't been shared with you or doesn't exist.", "error")
    return redirect(url_for('dashboard.dashboard_view'))

@quiz_routes.route('/start_shared_quiz/<int:quiz_id>', methods=['GET'])
@login_required
def start_shared_quiz(quiz_id):
    """Start a quiz that was shared with the current user"""
    from flask import current_app
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Verify the quiz is shared with this user
    quiz_share = QuizShare.query.filter_by(
        quiz_id=quiz_id,
        shared_with_user_id=current_user.id
    ).first()
    
    if not quiz_share and quiz.user_id != current_user.id:
        flash("This quiz hasn't been shared with you.", "error")
        return redirect(url_for('dashboard.dashboard_view'))
    
    # Log access for debugging
    current_app.logger.info(f"User {current_user.email} ({current_user.id}) accessing shared quiz {quiz_id}")
    
    try:
        # Set up the quiz session
        import json
        quiz_data = json.loads(quiz.questions_json)
        current_app.logger.info(f"Quiz {quiz_id} loaded with {len(quiz_data)} questions")
        
        # Store all necessary quiz data in session
        session['quiz'] = quiz_data
        session['score'] = 0
        session['current_question'] = 0
        session['answers'] = {}
        session['quiz_id'] = quiz.id
        session['topic'] = quiz.title
        
        # Ensure we have sensible defaults for quiz configuration
        if 'quiz_duration' not in session or not session['quiz_duration']:
            session['quiz_duration'] = 5  # Default duration in minutes
            
        if 'time_remaining' not in session or not session['time_remaining']:
            session['time_remaining'] = session['quiz_duration'] * 60  # Time in seconds
            
        # Make sure session is saved
        session.modified = True
        
        return redirect(url_for('quiz_routes.take_quiz'))
    except Exception as e:
        current_app.logger.error(f"Error starting shared quiz: {e}")
        flash("There was a problem loading the quiz. Please try again.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

@quiz_routes.route('/take_quiz')
def take_quiz():
    return render_template(
        'take_quiz.html',
        quiz_duration=session.get("quiz_duration", 5),
        current_question=session.get("current_question", 0),
        time_remaining=session.get("time_remaining", 0),
        quiz_id=session.get("quiz_id"),
        attempt_id=session.get("attempt_id"),
        total_questions=len(session.get("quiz", []))
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
    quiz = Quiz.query.get_or_404(quiz_id)

    # Authorization check
    if quiz.user_id != session.get("user_id"):
        return "Unauthorized", 403

    questions = json.loads(quiz.questions_json)

    # Reset session state
    session['quiz'] = questions
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}
    session['quiz_id'] = quiz.id
    session['quiz_type'] = quiz.title
    session['topic'] = quiz.title
    session.pop('attempt_id', None)  # Clear existing attempt_id

    return redirect(url_for('quiz_routes.take_quiz'))

@quiz_routes.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    # Authorization check
    if quiz.user_id != session.get("user_id"):
        return "Unauthorized", 403

    # Delete related results
    QuizResult.query.filter_by(quiz_id=quiz.id).delete()
    QuizAnswer.query.filter(
        QuizAnswer.attempt_id.in_(
            db.session.query(QuizResult.id).filter_by(quiz_id=quiz.id)
        )
    ).delete(synchronize_session=False)
    QuizSummary.query.filter(
        QuizSummary.result_id.in_(
            db.session.query(QuizResult.id).filter_by(quiz_id=quiz.id)
        )
    ).delete(synchronize_session=False)
    db.session.delete(quiz)
    db.session.commit()

    return redirect(url_for('stats_bp.dashboard'))

@quiz_routes.route('/rename_quiz/<int:quiz_id>', methods=['POST'])
def rename_quiz(quiz_id):
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
    if question_index < len(quiz):
        question = quiz[question_index]
        response = {
            'question': question['question'],
            'answer': question.get('answer', ''),
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
        try:
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
            from datetime import timezone
            timestamp = datetime.now(timezone.utc)  # Fixed timestamp creation

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
            
            correctness_list = []

            for i, question in enumerate(quiz):
                user_ans = str(session['answers'].get(i, '')).lower().strip()
                correct_ans = str(question['answer']).lower().strip()
                is_correct = user_ans == correct_ans
                correctness_list.append(is_correct)

            db.session.add(quiz_result)
            db.session.flush()  # Ensure quiz_result.id is available for related inserts
            db.session.commit()
            session['attempt_id'] = quiz_result.id

            # Save individual answers for this attempt
            for i, question in enumerate(quiz):
                user_ans = str(session['answers'].get(i, '')).lower().strip()
                correct_ans = str(question['answer']).lower().strip()
                is_correct = user_ans == correct_ans

                answer_entry = QuizAnswer(
                    attempt_id=quiz_result.id,
                    question_index=i,
                    answer=session['answers'].get(i),
                    is_correct=is_correct
                )
                db.session.add(answer_entry)

            db.session.commit()

            time_data = request.json.get("time_per_question", {})
            if not isinstance(time_data, dict):
                time_data = {}
            existing_summary = QuizSummary.query.filter_by(result_id=quiz_result.id).first()
            if not existing_summary:
                summary = QuizSummary(
                    quiz_id=quiz_result.quiz_id,
                    result_id=quiz_result.id,
                    user_email=session.get('user_email'),
                    correct_answers=quiz_result.score,
                    total_questions=quiz_result.total_questions,
                    time_per_question=json.dumps(time_data),
                )
                db.session.add(summary)
                db.session.commit()

            quizzes_completed = QuizResult.query.filter_by(user_id=user_id).count()
            quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
            recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
            with db.session.no_autoflush:
                most_frequent_quiz_type = db.session.query(
                    QuizResult.quiz_type,
                    db.func.count(QuizResult.quiz_type)
                ).filter_by(user_id=user_id, completed=True)\
                 .group_by(QuizResult.quiz_type)\
                 .order_by(db.func.count(QuizResult.quiz_type).desc())\
                 .first()

            session['quizzes_completed'] = quizzes_completed
            session['quizzes_above_80'] = quizzes_above_80
            session['recent_topics'] = [result.title for result in recent_topics]
            session['most_frequent_quiz_type'] = most_frequent_quiz_type[0] if most_frequent_quiz_type else None

            session.pop('quiz', None)
            session.pop('answers', None)
            session.pop('current_question', None)
            session['quiz_total'] = len(quiz)

            return jsonify({
                'completed': True,
                'score': score,
                'total': len(quiz),
                'results': correctness_list,
                'redirect_url': url_for('quiz_routes.quiz_summary', attempt_id=quiz_result.id)
            })
        except Exception as e:
            print(f"Error in submit_answer: {e}") # Replaced traceback with a simple print
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'completed': False})

# Route to handle quiz exit and save incomplete quiz result
@quiz_routes.route('/exit_quiz', methods=['POST'])
def exit_quiz():
    user_id = session.get("user_id")
    quiz_id = session.get("quiz_id")
    topic = session.get("topic", "Untitled")
    time_remaining = request.form.get("time_left") or (request.json.get("time_left", 0) if request.json else 0)
    quiz_duration = session.get("quiz_duration", 5)  # keep in minutes

    if not user_id or not quiz_id:
        return jsonify(success=False, message="Missing session info"), 400

    from datetime import timezone
    quiz_result = QuizResult(
        user_id=user_id,
        quiz_id=quiz_id,
        score=0,  # Will be calculated on resume
        total_questions=len(session.get("quiz", [])),
        timestamp=datetime.now(timezone.utc),  # Fixed timestamp creation
        quiz_type=topic,
        completed=False,
        title=topic,
        time_remaining=int(time_remaining),
        quiz_duration=int(quiz_duration)
    )

    db.session.add(quiz_result)
    db.session.flush()
    db.session.commit()

    # Store each answer in QuizAnswer table
    for index, user_ans in session.get("answers", {}).items():
        answer_entry = QuizAnswer(
            attempt_id=quiz_result.id,
            question_index=int(index),
            answer=user_ans,
            is_correct=False  # Score will be evaluated on resume
        )
        db.session.add(answer_entry)
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

    quiz = Quiz.query.get(attempt.quiz_id)
    if not quiz:
        return "Quiz not found", 404

    questions = json.loads(quiz.questions_json)
    answers_query = QuizAnswer.query.filter_by(attempt_id=attempt.id).all()
    answers = {a.question_index: a.answer for a in answers_query}
    first_unanswered = len(answers) if len(answers) < len(questions) else len(questions) - 1

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
            current_app.logger.error(f"❌ Failed to send quiz share email: {str(e)}")
            print(f"Error in share_quiz sending email: {e}") # Replaced traceback with a simple print
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
            print(f"Error in share_quiz_root sending email: {e}") # Added for logging if traceback is removed
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

@quiz_routes.route('/quiz_summary/<int:attempt_id>')
def quiz_summary(attempt_id):
    attempt = QuizResult.query.get_or_404(attempt_id)

    # Authorization check
    if attempt.user_id != session.get('user_id'):
        return "Unauthorized", 403

    score = attempt.score
    total = attempt.total_questions
    incorrect = total - score

    # Restore useful session stats
    quizzes_completed = QuizResult.query.filter_by(user_id=attempt.user_id).count()
    quizzes_above_80 = QuizResult.query.filter_by(user_id=attempt.user_id).filter(
        QuizResult.score / QuizResult.total_questions >= 0.8
    ).count()
    recent_topics = QuizResult.query.filter_by(user_id=attempt.user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
    most_frequent_quiz_type = db.session.query(
        QuizResult.quiz_type,
        db.func.count(QuizResult.quiz_type)
    ).filter_by(user_id=attempt.user_id, completed=True) \
     .group_by(QuizResult.quiz_type) \
     .order_by(db.func.count(QuizResult.quiz_type).desc()) \
     .first()

    # Fetch extra context for JS charts
    quiz = Quiz.query.get(attempt.quiz_id)
    quiz_questions = json.loads(quiz.questions_json) if quiz else []

    summary = QuizSummary.query.filter_by(result_id=attempt_id).first()
    time_per_question = json.loads(summary.time_per_question) if summary and summary.time_per_question else {}

    answers = QuizAnswer.query.filter_by(attempt_id=attempt_id).all()
    user_answers = {a.question_index: a.answer for a in answers}

    # Construct quiz review data
    quiz_review_data = []
    for i, q in enumerate(quiz_questions):
        user_ans = str(user_answers.get(i, '')).strip().lower()
        correct_ans = str(q.get('answer', '')).strip().lower()
        quiz_review_data.append({
            "question": q.get("question", ""),
            "userAnswer": user_ans,
            "correctAnswer": correct_ans,
            "isCorrect": user_ans == correct_ans
        })

    # Time per question list
    time_per_question_list = [v for k, v in sorted(time_per_question.items())]

    # Attempt scores for comparison chart
    previous_attempts = QuizResult.query.filter_by(
        user_id=attempt.user_id,
        quiz_id=quiz.id,
        completed=True
    ).order_by(QuizResult.timestamp.asc()).all()
    attempt_scores = [r.score for r in previous_attempts]
    attempt_labels = [f"Attempt {i + 1}" for i in range(len(previous_attempts))]

    return render_template(
        'quiz_summary.html',
        score=score,
        correct=score,
        incorrect=incorrect,
        total=total,
        quizzes_completed=quizzes_completed,
        quizzes_above_80=quizzes_above_80,
        recent_topics=[r.title for r in recent_topics],
        most_frequent_quiz_type=most_frequent_quiz_type[0] if most_frequent_quiz_type else 'N/A',
        quiz_id=quiz.id,
        attempt_id=attempt.id,
        quiz_title=quiz.title if quiz else 'Untitled',
        quiz_questions=quiz_questions,
        time_per_question=time_per_question,
        user_answers=user_answers,
        quiz_review_data=quiz_review_data,
        time_per_question_list=time_per_question_list,
        attempt_scores=attempt_scores,
        attempt_labels=attempt_labels
    )

# Route for viewing "My Quizzes" history page
@quiz_routes.route('/my_quizzes')
def my_quizzes():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for('auth_routes.login'))

    quizzes = Quiz.query.filter_by(user_id=user_id).order_by(Quiz.id.desc()).all()

    from datetime import timezone as dt_timezone

    perth = timezone("Australia/Perth")
    quiz_attempts_map = {}

    for quiz in quizzes:
        attempts = QuizResult.query.filter_by(user_id=user_id, quiz_id=quiz.id).order_by(QuizResult.timestamp.desc()).all()
        for attempt in attempts:
            if attempt.timestamp and attempt.timestamp.tzinfo is None:
                attempt.timestamp = attempt.timestamp.replace(tzinfo=dt_timezone.utc)
            if attempt.timestamp:
                attempt.timestamp = attempt.timestamp.astimezone(perth)
        quiz_attempts_map[quiz.id] = attempts

    return render_template(
        'my_quizzes.html',
        quizzes=quizzes,
        quiz_attempts_map=quiz_attempts_map
    )
