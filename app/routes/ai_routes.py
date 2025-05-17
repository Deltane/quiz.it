import os
import logging
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import json
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
from flask_wtf.csrf import validate_csrf, CSRFError
from word2number import w2n
from rapidfuzz import fuzz
from app.forms import QuizSetupForm

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for troubleshooting
logger = logging.getLogger(__name__)

# Define the blueprint
ai_routes = Blueprint('ai_routes', __name__)

# Load environment variables from .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

@ai_routes.route('/store_quiz', methods=['POST'])
def store_quiz():
    data = request.get_json()
    csrf_token = data.get('csrf_token') or request.headers.get('X-CSRFToken')
    try:
        validate_csrf(csrf_token)
    except CSRFError:
        return jsonify({'error': 'Invalid CSRF token'}), 400
    # Check if the user session is valid
    if not session.get('user_id'):
        return jsonify({'error': 'Session expired. Please log in again.'}), 401

    data = request.json
    session['quiz'] = data['quiz']
    session['quiz_duration'] = data.get('quiz_duration', 5)  # in minutes
    session['time_remaining'] = session['quiz_duration'] * 60        # in seconds
    session['score'] = 0
    session['current_question'] = 0
    session['answers'] = {}

    # Save to DB
    from app.models import Quiz, db, User, Folder # Make sure Folder is imported if used
    import json
    user_email = session.get("user_email")
    user = User.query.filter_by(email=user_email).first()
    if user:
        # Use quiz_title and is_public from session if available (set during form submission)
        topic_title = session.pop('quiz_title_from_form', data.get('quiz_title', data.get('title', 'Untitled')))
        is_public = session.pop('is_public_from_form', data.get('is_public', True))
        questions = data['quiz']
        folder_id = session.pop("folder_id", None) 
        
        quiz = Quiz(
            title=topic_title, 
            questions_json=json.dumps(questions), 
            user_id=user.id,
            is_public=is_public # Save visibility status
        )
        if folder_id:
            folder = Folder.query.get(folder_id)
            if folder:
                quiz.folders.append(folder)
        db.session.add(quiz)
        db.session.commit()
        return jsonify({'message': 'Quiz data stored in session and saved to database.'}), 200
    else:
        return jsonify({'error': 'User not found for saving the quiz.'}), 404

@ai_routes.route('/create_quiz')
def create_quiz():
    form = QuizSetupForm()
    return render_template('create_quiz.html', form=form)

@ai_routes.route('/generate_quiz', methods=['GET', 'POST'])
def generate_quiz():
    form = QuizSetupForm()
    if request.method == 'GET':
        return render_template('create_quiz.html', form=form)

    if form.validate_on_submit():
        text_input = form.ai_prompt.data or ''
        question_count = form.question_count.data
        timer_minutes = form.timer.data
        session['quiz_duration'] = timer_minutes
        quiz_type = form.quiz_type.data
        uploaded_file = form.upload_file.data
        # Capture quiz name and visibility from the form
        session['quiz_title_from_form'] = form.quiz_name.data
        session['is_public_from_form'] = form.visibility.data == 'public'
        
        # For 'topic' / 'most_frequent_quiz_type' from origin/main, using quiz_name as per user's preference
        # This local variable will be used later to set session['most_frequent_quiz_type']
        current_quiz_topic_for_session = form.quiz_name.data
        # If origin/main's logic relied on session['topic'] directly, set it here:
        session['topic'] = current_quiz_topic_for_session
        
    else:
        return render_template('create_quiz.html', form=form)

    text = text_input

    if uploaded_file and uploaded_file.filename.endswith('.pdf'):
        try:
            max_file_size = 10 * 1024 * 1024
            if uploaded_file.content_length > max_file_size:
                return jsonify({"error": "File size exceeds 10MB limit"}), 400

            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_dir = os.path.join(base_dir, '..', 'Uploads')
            os.makedirs(upload_dir, exist_ok=True)

            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(upload_dir, filename)

            uploaded_file.save(filepath)

            if not os.path.exists(filepath):
                return jsonify({"error": f"Failed to save file at {filepath}"}), 500
            
            if os.path.getsize(filepath) == 0:
                return jsonify({"error": "Uploaded file is empty"}), 400

            try:
                with fitz.open(filepath) as doc:
                    pdf_text = "\n".join(page.get_text() for page in doc)
                    if pdf_text.strip():
                        text = pdf_text              
                    else:
                        text = ""
                        max_pages = 10
                        for page_num in range(min(len(doc), max_pages)):
                            pix = doc[page_num].get_pixmap()
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            text += pytesseract.image_to_string(img)
                        
                        if not text.strip():
                            return jsonify({"error": "The PDF does not contain extractable text, even with OCR."}), 400
                       
            except Exception as e:
                return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500
            finally:
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {filepath}: {e}")

        except Exception as e:
            return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

    if not text or not text.strip():
        return jsonify({"error": "No valid text provided. Please enter text or upload a valid PDF."}), 400

    try:
        if quiz_type == "Fill in the Blank":
            system_prompt = (
                f"You are a quiz maker AI. Generate a fill-in-the-blank quiz based on the following content. "
                f"Return exactly {question_count} questions in JSON format. "
                "Each question must be complete, clear, and at least 15 characters long. "
                "For numeric answers, use digits (e.g., '6' instead of 'six'). "
                "Do not provide explanations. "
                "Return only a JSON array in this format: "
                "[{\"question\": \"The process of _____ is used to convert analog signals to digital.\", "
                "\"answer\": \"digitization\"}, ...]"
                "DO NOT INCLUDE THE ABOVE QUESTION IN THE QUIZ"
            )
        elif quiz_type == "Short Answer":
            system_prompt = (
                f"You are a quiz maker AI. Generate short answer questions based on the following content. "
                f"Return exactly {question_count} questions in JSON format. "
                "Each question must be complete, clear, and at least 15 characters long. "
                "For numeric answers, use digits (e.g., '6' instead of 'six'). "
                "Do not provide explanations. "
                "Return only a JSON array in this format: "
                "[{\"question\": \"What protocol is used for secure web browsing?\", "
                "\"answer\": \"HTTPS\"}, ...]"
            )
        elif quiz_type == "Multiple Choice":
            system_prompt = (
                f"You are a quiz maker AI. Generate a multiple-choice quiz based on the following content. "
                f"Return exactly {question_count} questions in JSON format. "
                "Each question must be complete, clear, and at least 15 characters long. "
                "For numeric answers, use digits (e.g., '6' instead of 'six'). "
                "Each question should have 4 options, and one correct answer. "
                "Do not provide any explanations or preambles. "
                "Only return a JSON array in the following format: "
                "[{\"question\": \"...\", \"options\": [\"...\", \"...\", \"...\", \"...\"], \"answer\": \"...\"}, ...]"
            )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        try:
            logger.debug(f"Raw OpenAI response: {response.choices[0].message.content}")
            content = response.choices[0].message.content
            cleaned_content = content.replace('```json', '').replace('```', '').strip()
            quiz_data = json.loads(cleaned_content)
            
            if not isinstance(quiz_data, list):
                return jsonify({"error": "Unexpected response format from OpenAI."}), 500
            
            for idx, question in enumerate(quiz_data):
                if not question.get('question') or not question.get('answer') or len(question['question'].strip()) < 15:
                    logger.warning(f"Invalid question at index {idx}: {question}")
                    return jsonify({"error": "Generated quiz contains incomplete or invalid questions."}), 500
                
                answer = question['answer']
                if normalise_answer(answer).isdigit() and answer != normalise_answer(answer):
                    logger.warning(f"Answer '{answer}' at index {idx} is not in digit format")
                    question['answer'] = normalise_answer(answer)

            session['quiz'] = quiz_data
            session['most_frequent_quiz_type'] = current_quiz_topic_for_session
            return jsonify({"quiz": quiz_data})

        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse OpenAI response: {str(je)}")
            return jsonify({"error": f"Failed to parse OpenAI response: {str(je)}"}), 500

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

@ai_routes.route('/verify_quiz', methods=['POST'])
def verify_quiz():
    try:
        data = request.get_json()
        quiz_data = data.get('quiz')
        original_text = data.get('original_text')
        
        if not quiz_data or not original_text:
            return jsonify({"error": "Missing quiz data or original text"}), 400
        
        formatted_quiz = json.dumps(quiz_data, indent=2)
        
        verification_prompt = (
            "You are a quiz verification assistant. Review the following quiz questions and answers "
            "that were generated based on the provided content. For each question-answer pair:\n"
            "1. Verify the answer is correct based on the content\n"
            "2. Check for ambiguity or unclear wording\n"
            "3. Confirm the difficulty is appropriate\n\n"
            "Return your verification in JSON format as follows:\n"
            "[{\"question_index\": 0, \"is_correct\": true/false, \"issue\": \"description if any\", \"suggested_correction\": \"correction if needed\"}, ...]\n\n"
            f"Quiz to verify: {formatted_quiz}\n\n"
            f"Original content: {original_text}"
        )
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a quiz verification assistant that checks answers for accuracy."},
                {"role": "user", "content": verification_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        verification_result = json.loads(response.choices[0].message.content.strip())
        
        return jsonify({"verification": verification_result})
    
    except json.JSONDecodeError as je:
        return jsonify({"error": f"Failed to parse verification result: {str(je)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Verification error: {str(e)}"}), 500

@ai_routes.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        data = request.get_json()
        user_answers = {answer['name']: answer['value'] for answer in data['answers']}
        quiz = data['quiz']

        score = 0
        for index, question in enumerate(quiz):
            correct_answer = question['answer']
            user_answer = user_answers.get(f'q{index}')
            
            norm_user = normalise_answer(user_answer)
            norm_correct = normalise_answer(correct_answer)
            is_correct = compare_answers(user_answer, correct_answer)
            logger.debug(f"Q{index}: User answer: '{user_answer}' -> '{norm_user}', "
                        f"Correct answer: '{correct_answer}' -> '{norm_correct}', "
                        f"Match: {is_correct}")

            if is_correct:
                score += 1

        return jsonify({"score": score})
    except Exception as e:
        logger.error(f"Submit quiz error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def normalise_answer(answer):
    """Normalize an answer for comparison, converting numbers to digits."""
    if answer is None:
        return ""
    
    answer = str(answer).lower().strip()
    
    answer = answer.replace("th", "").replace("rd", "").replace("nd", "").replace("st", "")
    answer = answer.split(".")[0]
    
    try:
        num = w2n.word_to_num(answer)
        logger.debug(f"Normalized '{answer}' to '{num}'")
        return str(num)
    except ValueError:
        pass
    
    if answer.isdigit():
        logger.debug(f"Answer '{answer}' is already a digit")
        return answer
    
    logger.debug(f"Answer '{answer}' is non-numeric")
    return answer

def compare_answers(user_answer, correct_answer, similarity_threshold=85):
    """Compare user and correct answers with normalization and fuzzy matching."""
    norm_user = normalise_answer(user_answer)
    norm_correct = normalise_answer(correct_answer)
    
    if norm_user == norm_correct:
        return True
    
    if not norm_user.isdigit() and not norm_correct.isdigit():
        return fuzz.ratio(norm_user, norm_correct) >= similarity_threshold
    
    return False
