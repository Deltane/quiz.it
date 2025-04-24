quiz.it 🧠📚

A web-based AI-assisted quiz creation and practice platform built with Flask and SQLite. Users can generate quizzes from custom input or files, complete and review their results, and share quizzes with friends or groups.

🌟 Features
	•	User registration and login
	•	Manual and AI-generated quiz creation
	•	Import and upload documents for quiz generation (compatible types TBA)
	•	Support for MCQ, short answer, and fill-in-the-blank types
	•	Real-time scoring and quiz attempt history
	•	Visual statistics with charts (time spent, scores, question review)
	•	Quiz sharing with individuals or groups

🚀 Technologies
	•	Frontend: HTML, CSS, JavaScript, jQuery, Bootstrap/Tailwind (choose one)
	•	Backend: Flask (Python), SQLAlchemy (with SQLite)
	•	Other: AJAX for dynamic interactivity, Chart.js for data visualisation, OpenAI API for AI quiz generation

👥 Team Members

UWA ID	Name	GitHub Username
23991179	Amanda Putri Devi Siagian	mandasgn
23456789	Rayhan Rayhan	rayhannm
34567890	Gaby Tedjosurjono	gabrielajt10
24211939	Serena McPherson	Deltane

🧠 How to Run the App

Follow the instructions for your operating system:

macOS / Linux
	1.	Clone the repository:

git clone https://github.com/Deltane/CITS3403-Group-Project.git
cd CITS3403-Group-Project


	2.	Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate


	3.	Install dependencies:

pip install -r requirements.txt


	4.	Configure environment variables:
	•	Create a file named .env in the project root (or edit instance/config.py) and add:

FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_key  # if using AI features


	5.	Run the application:

flask run


	6.	Open your browser and go to http://127.0.0.1:5000.

Windows (PowerShell)
	1.	Clone the repository:

git clone https://github.com/Deltane/CITS3403-Group-Project.git
cd CITS3403-Group-Project


	2.	Create and activate a virtual environment:

python -m venv venv
venv\Scripts\Activate.ps1


	3.	Install dependencies:

pip install -r requirements.txt


	4.	Configure environment variables:
	•	Create a file named .env in the project root (or edit instance/config.py) and add:

FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_key  # if using AI features

a
	5.	Run the application:

flask run


	6.	Open your browser and go to http://127.0.0.1:5000.

✅ How to Run Tests

From the project root (ensure the virtual environment is active):

python -m unittest discover tests