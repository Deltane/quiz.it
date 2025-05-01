from flask import Blueprint, session, request, jsonify, render_template

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
    print(f"Stored quiz with {len(session['quiz'])} questions.")
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}
    return '', 204

@quiz_routes.route('/get_question/<int:question_index>', methods=['GET'])
def get_question(question_index):
    quiz = session.get('quiz', [])
    print(f"Fetching question {question_index}, quiz length = {len(quiz)}")
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
