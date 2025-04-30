from flask import Blueprint, session, request, jsonify, render_template

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/')
def index():
    return render_template('base.html')  # Render the landing page

@quiz_routes.route('/take_quiz')
def take_quiz():
    return render_template('take_quiz.html')

@quiz_routes.route('/store_quiz', methods=['POST'])
def store_quiz():
    session['quiz'] = request.json['quiz']
    session['current_question'] = 0
    session['answers'] = {}  # Ensure clean slate on new quiz
    return '', 204

@quiz_routes.route('/get_question/<int:question_index>', methods=['GET'])
def get_question(question_index):
    quiz = session.get('quiz', [])
    if question_index < len(quiz):
        question = quiz[question_index]
        return jsonify({
            'question': question.get('question'),
            'options': question.get('options', []),
            'answer': question.get('answer')  # Include answer for validation/testing purposes
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
            if str(session['answers'].get(index)) == str(question.get('answer')):
                score += 1
        session['score'] = score
        return jsonify({'completed': True, 'score': score})

    return jsonify({'completed': False})