from app.models import Quiz, QuizResult, User, Folder, QuizAnswer, QuizSummary
from app import db
from datetime import datetime
from flask import Blueprint, session, request, jsonify, render_template, redirect, url_for
from flask import render_template, session, request

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
        time_remaining=session.get("time_remaining", 0),
        quiz_id=session.get("quiz_id"),
        attempt_id=session.get("attempt_id")
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
        session['quiz_session_id'] = f"{quiz.id}_{datetime.utcnow().timestamp()}"
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
    session['quiz_session_id'] = f"{quiz.id}_{datetime.utcnow().timestamp()}"
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

    # Inject a cookie to signal the frontend to clear relevant localStorage for this quiz
    response = redirect(url_for('stats_bp.dashboard'))
    response.set_cookie(f"clearLocalStorage_quiz_{quiz_id}", "true", max_age=10)
    return response

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

            time_data = session.get('time_per_question', {})
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
            import traceback
            traceback.print_exc()
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

# @quiz_routes.route('/delete_quiz_attempt/<int:attempt_id>', methods=['POST'])
# def delete_quiz_attempt(attempt_id):
#     attempt = QuizResult.query.get_or_404(attempt_id)
#     if attempt.user_id != session.get('user_id'):
#         return "Unauthorized", 403

#     db.session.delete(attempt)
#     db.session.commit()
#     return redirect(url_for('stats_bp.dashboard'))

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
        user_answers=user_answers
    )

# Endpoint to get the full quiz from the session for review
@quiz_routes.route('/get_full_quiz')
def get_full_quiz():
    quiz = session.get('quiz', [])
    return jsonify(quiz)