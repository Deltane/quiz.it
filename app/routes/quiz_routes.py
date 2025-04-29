from flask import Blueprint, session, request, jsonify, render_template

quiz_routes = Blueprint('quiz_routes', __name__)

@quiz_routes.route('/take_quiz')
def take_quiz():
    return render_template('take_quiz.html')

@quiz_routes.route('/store_quiz', methods=['POST'])
def store_quiz():
    session['quiz'] = request.json['quiz']
    session['current_question'] = 0
    return '', 204

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

    # Store the user's answer (you can save it in the session or database)
    if 'answers' not in session:
        session['answers'] = {}
    session['answers'][question_index] = answer

    return '', 204