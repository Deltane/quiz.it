from flask import Blueprint, session, request, jsonify, render_template, redirect, url_for

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/')
def home():
    return render_template('landing_page.html')

@quiz_routes.route('/take_quiz')
def take_quiz():
    return render_template('take_quiz.html')

@quiz_routes.route('/store_quiz', methods=['POST'])
def store_quiz():
    session['quiz'] = request.json['quiz']
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
        quiz = Quiz(title=topic, questions_json=json.dumps(questions), author=user, folder=folder)
        db.session.add(quiz)
        db.session.commit()
        
    return '', 204

# Redo quiz route
@quiz_routes.route('/redo_quiz/<int:quiz_id>', methods=['POST'])
def redo_quiz(quiz_id):
    from app.models import Quiz
    import json
    quiz = Quiz.query.get_or_404(quiz_id)
    session['quiz'] = json.loads(quiz.questions_json)
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}
    return redirect(url_for('quiz_routes.take_quiz'))

@quiz_routes.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
def delete_quiz(quiz_id):
    from app.models import Quiz, db
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for('dashboard.dashboard_view'))

@quiz_routes.route('/create_quiz_for_folder/<int:folder_id>', methods=['GET'])
def create_quiz_for_folder(folder_id):
    from app.models import Folder, User
    user_email = session.get("user_email")
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return redirect(url_for('quiz_routes.home'))

    folder = Folder.query.get(folder_id)
    if not folder or folder.user_id != user.id:
        return "Unauthorized access or folder not found", 403

    # Store folder ID in session and redirect to create_quiz page
    session['folder_id'] = folder.id
    return redirect(url_for('ai_routes.generate_quiz'))  # Ensure this route exists

@quiz_routes.route('/get_question/<int:question_index>', methods=['GET'])
def get_question(question_index):
    quiz = session.get('quiz', [])
    if question_index < len(quiz):
        question = quiz[question_index]
        return jsonify({
            'question': question['question'],
            'options': question['options']
        })
    return jsonify({}), 404

@quiz_routes.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    question_index = data['questionIndex']
    answer = data['answer']

    # Store the user's answer 
    if 'answers' not in session:
        session['answers'] = {}
    session['answers'][question_index] = answer

    # Check if the quiz is completed
    quiz = session.get('quiz', [])
    if len(session['answers']) == len(quiz):
        # Calculate the score
        score = 0
        for index, question in enumerate(quiz):
            # Ensure both values are strings for comparison
            if str(session['answers'].get(index)) == str(question['answer']):
                score += 1
        session['score'] = score
        session.pop('quiz', None)
        session.pop('answers', None)
        session.pop('current_question', None)
        print(f"Quiz completed. Score: {score}/{len(quiz)}")
        return jsonify({'completed': True, 'score': score})

    return jsonify({'completed': False})

    return '', 204
