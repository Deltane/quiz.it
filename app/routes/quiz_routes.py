from app.models import Quiz, QuizResult, User, Folder, QuizAnswer
from app import db
from datetime import datetime
from flask import Blueprint, session, request, jsonify, render_template, redirect, url_for

import json

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/')
def home():
    return render_template('landing_page.html')

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
    db.session.delete(quiz)
    QuizAnswer.query.filter(
        QuizAnswer.attempt_id.in_(
            db.session.query(QuizResult.id).filter_by(quiz_id=quiz.id)
        )
    ).delete(synchronize_session=False)
    db.session.commit()
    return redirect(url_for('stats_bp.dashboard'))

@quiz_routes.route('/rename_quiz/<int:quiz_id>', methods=['POST'])
def rename_quiz(quiz_id):
    new_title = request.form.get('new_title')
    quiz = Quiz.query.get_or_404(quiz_id)

    # Authorization check
    if quiz.user_id != session.get("user_id"):
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
            'type': 'multiple-choice' if 'options' in question else 'fill-in-blank'
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

        # Calculate and store quiz statistics
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
    user_id = session.get("user_id")
    quiz_id = session.get("quiz_id")
    topic = session.get("topic", "Untitled")
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
        title=topic,
        time_remaining=int(time_remaining),
        quiz_duration=int(quiz_duration)
    )

    db.session.add(quiz_result)
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
    first_unanswered = 0
    for i in range(len(questions)):
        if i not in answers:
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
