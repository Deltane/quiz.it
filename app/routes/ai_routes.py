import os
from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import json
import pytesseract
from openai import OpenAI
from dotenv import load_dotenv
from PIL import Image

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
    return render_template('create_quiz.html')

# Route to handle quiz generation
@ai_routes.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    text_input = request.form.get('ai-prompt', '')
    question_count = int(request.form.get('question-count', 5))
    uploaded_file = request.files.get('upload-file')

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
        system_prompt = (
            f"You are a quiz maker AI. Generate a multiple-choice quiz based on the following content. "
            f"Return exactly {question_count} questions in JSON format. "
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
            # Parse the response content
            quiz_data = json.loads(response.choices[0].message.content)
            
            if isinstance(quiz_data, list):
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

        # Clear any existing session or cached quiz data here if applicable
        # (Since no session or cache is shown, this is a placeholder comment)

        print("User Answers:", user_answers)
        print("Quiz Data:", quiz)

        score = 0
        for index, question in enumerate(quiz):
            correct_answer = question['answer']
            user_answer = user_answers.get(f'q{index}')
            print(f"Q{index} - Correct: {correct_answer}, User: {user_answer}")
            if user_answer == correct_answer:
                score += 1

        # Return the score as JSON
        return jsonify({"score": score})
    except Exception as e:
        # Return an error message if something goes wrong
        return jsonify({"error": str(e)})
