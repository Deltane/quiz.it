import os
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import json
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image
from flask import render_template, session, request
from app.forms import QuizSetupForm
from flask_wtf.csrf import validate_csrf, CSRFError

# Define the blueprint
ai_routes = Blueprint('ai_routes', __name__)

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
        topic = session.pop('quiz_title_from_form', data.get('quiz_title', data.get('title', 'Untitled')))
        is_public = session.pop('is_public_from_form', data.get('is_public', True))
        questions = data['quiz']
        folder_id = session.pop("folder_id", None) 
        
        quiz = Quiz(
            title=topic, 
            questions_json=json.dumps(questions), 
            user_id=user.id,
            is_public=is_public # Save visibility status
        )
        if folder_id:
            folder = Folder.query.get(folder_id)
            if folder:
                quiz.folders.append(folder)
        db.session.add(quiz)

# Define the blueprint
ai_routes = Blueprint('ai_routes', __name__)

# Load environment variables from .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Route to render the create_quiz.html page
@ai_routes.route('/create_quiz')
def create_quiz():
    form = QuizSetupForm()
    return render_template('create_quiz.html', form=form)

# Route to handle quiz generation
@ai_routes.route('/generate_quiz', methods=['GET', 'POST'])
def generate_quiz():
    form = QuizSetupForm()
    if request.method == 'GET':
        return render_template('create_quiz.html', form=form)
    

     # Use WTForms validation
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
        
    else:
        return render_template('create_quiz.html', form=form)

    text = text_input

    # Handle PDF upload
    if uploaded_file and uploaded_file.filename.endswith('.pdf'):
        try:
            # Create absolute path for uploads directory
            base_dir = os.path.abspath(os.path.dirname(__file__))
            upload_dir = os.path.join(base_dir, '..', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            # Secure the filename and create full path
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(upload_dir, filename)

            # Save the uploaded file
            uploaded_file.save(filepath)

            # Verify file exists and is not empty
            if not os.path.exists(filepath):
                return jsonify({"error": f"Failed to save file at {filepath}"})
            
            if os.path.getsize(filepath) == 0:
                return jsonify({"error": "Uploaded file is empty"})

            # Extract text from PDF using PyMuPDF
            try:
                with fitz.open(filepath) as doc:
                    pdf_text = "\n".join(page.get_text() for page in doc)
                    if pdf_text.strip():
                        text = pdf_text              
                    else:
                        # Fallback to OCR for image-based PDFs
                        text = ""
                        for page_num in range(len(doc)):
                            pix = doc[page_num].get_pixmap()
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            text += pytesseract.image_to_string(img)
                        
                        if not text.strip():
                            return jsonify({"error": "The PDF does not contain extractable text, even with OCR."})
                       
            except Exception as e:
                return jsonify({"error": f"Failed to process PDF: {str(e)}"})
            finally:
                # Clean up the uploaded file
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Warning: Failed to remove temporary file {filepath}: {e}")

        except Exception as e:
            return jsonify({"error": f"Failed to process PDF: {str(e)}"})

    # Ensure we have text to process
    if not text or not text.strip():
        return jsonify({"error": "No valid text provided. Please enter text or upload a valid PDF."})

    print(f"Processing text with OpenAI (length: {len(text)})")
    
    # Use OpenAI to generate quiz
    try:
        if quiz_type == "Fill in the Blank":
            system_prompt = (
                f"You are a quiz maker AI. Generate a fill-in-the-blank quiz based on the following content. "
                f"Return exactly {question_count} questions in JSON format. "
                "For each question, create a sentence with '_____' where the blank should be, "
                "and provide the correct answer. "
                "Do not provide explanations. "
                "Return only a JSON array in this format: "
                "[{\"question\": \"The process of _____ is used to convert analog signals to digital.\", "
                "\"answer\": \"digitization\"}, ...]"
            )
        elif quiz_type == "Short Answer":
            system_prompt = (
                f"You are a quiz maker AI. Generate short answer questions based on the following content. "
                f"Return exactly {question_count} questions in JSON format. "
                "Each question should require a brief, specific answer. "
                "Do not provide explanations. "
                "Return only a JSON array in this format: "
                "[{\"question\": \"What protocol is used for secure web browsing?\", "
                "\"answer\": \"HTTPS\"}, ...]"
            )
        elif quiz_type == "Multiple Choice":
            system_prompt = (
                f"You are a quiz maker AI. Generate a multiple-choice quiz based on the following content. "
                f"Return exactly {question_count} questions in JSON format. "
                "Each question should have 4 options, and one correct answer. "
                "Do not provide any explanations or preambles. "
                "Only return a JSON array in the following format: "
                "[{\"question\": \"...\", \"options\": [\"...\", \"...\", \"...\", \"...\"], \"answer\": \"...\"}, ...]"
            )

        print("Sending request to OpenAI API...")
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
            # Clean up the response content
            content = response.choices[0].message.content
            cleaned_content = content.replace('```json', '').replace('```', '').strip()
            
            # Parse the cleaned content
            quiz_data = json.loads(cleaned_content)  # Use cleaned_content instead of original
            
            if isinstance(quiz_data, list):
                session['quiz'] = quiz_data
                return jsonify({"quiz": quiz_data})
            else:
                return jsonify({"error": "Unexpected response format from OpenAI."})

        except json.JSONDecodeError as je:
            return jsonify({"error": f"Failed to parse OpenAI response: {str(je)}"})

    except Exception as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"})
    
# Route to handle quiz submission
@ai_routes.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        # Parse the JSON data from the request
        data = request.get_json()
        user_answers = {answer['name']: answer['value'] for answer in data['answers']}
        quiz = data['quiz']

        score = 0
        for index, question in enumerate(quiz):
            correct_answer = question['answer']
            user_answer = user_answers.get(f'q{index}')
            if user_answer == correct_answer:
                score += 1

        # Return the score as JSON
        return jsonify({"score": score})
    except Exception as e:
        # Return an error message if something goes wrong
        return jsonify({"error": str(e)})
