from app.models import QuizResult
from app import db
from datetime import datetime
from flask import Blueprint, session, request, jsonify, render_template, redirect, url_for

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/')
def home():
    return render_template('landing_page.html')

@quiz_routes.route('/take_quiz')
def take_quiz():
    return render_template('take_quiz.html', quiz_duration=session.get("quiz_duration", 5))

@quiz_routes.route('/store_quiz', methods=['POST'])
def store_quiz():
    # Check if the user session is valid
    if not session.get('user_id'):
        return jsonify({'error': 'Session expired. Please log in again.'}), 401

    session['quiz'] = request.json['quiz']
    session['quiz_duration'] = request.json.get('quiz_duration', 5)
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
    if quiz.user_id != session.get("user_id"):
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
            'type': 'multiple-choice' if 'options' in question else 'fill-in-blank'
        }
        
        # Only include options for multiple choice questions
        if 'options' in question:
            response['options'] = question['options']
            
        return jsonify(response)
    return jsonify({}), 404

@quiz_routes.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    question_index = data['questionIndex']
    user_answer = data['answer']
    print("submit_answer session user_id:", session.get("user_id"))
    print("submit_answer session quiz_id:", session.get("quiz_id"))
    print("submit_answer session quiz_type:", session.get("quiz_type"))

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
        quiz_type = session.get('quiz_type')
        total_questions = len(quiz)
        timestamp = datetime.utcnow()

        print("Session contents before saving QuizResult:", dict(session))

        quiz_result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions,
            timestamp=timestamp,
            quiz_type=quiz_type
        )
        db.session.add(quiz_result)
        db.session.commit()

        # Calculate and store quiz statistics
        quizzes_completed = QuizResult.query.filter_by(user_id=user_id).count()
        quizzes_above_80 = QuizResult.query.filter_by(user_id=user_id).filter(QuizResult.score / QuizResult.total_questions >= 0.8).count()
        recent_topics = QuizResult.query.filter_by(user_id=user_id).order_by(QuizResult.timestamp.desc()).limit(5).all()
        most_frequent_quiz_type = db.session.query(QuizResult.quiz_type, db.func.count(QuizResult.quiz_type)).filter_by(user_id=user_id).group_by(QuizResult.quiz_type).order_by(db.func.count(QuizResult.quiz_type).desc()).first()

        session['quizzes_completed'] = quizzes_completed
        session['quizzes_above_80'] = quizzes_above_80
        session['recent_topics'] = [result.quiz_type for result in recent_topics]
        session['most_frequent_quiz_type'] = most_frequent_quiz_type[0] if most_frequent_quiz_type else None

        # Clean up session
        session.pop('quiz', None)
        session.pop('answers', None)
        session.pop('current_question', None)
        
        return jsonify({
            'completed': True,
            'score': score,
            'total': len(quiz)
        })

    return jsonify({'completed': False})

    return '', 204
