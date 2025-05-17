# quiz.it 🧠📚

A web-based AI-assisted quiz creation and practice platform built with Flask and SQLite. Users can generate quizzes from
custom input or files, complete and review their results, and share quizzes with friends or groups.

## 🌟 Features

- User registration and login
- Manual and AI-generated quiz creation
- Import and upload documents for quiz generation via PDF
- Support for MCQ, short answer, and fill-in-the-blank types
- Real-time scoring and quiz attempt history
- Visual statistics with charts (time spent, scores, question review)
- Quiz sharing with individuals or groups.

## 🚀 Technologies

- **Frontend**: HTML, CSS, JavaScript, jQuery, Bootstrap/Tailwind 
- **Backend**: Flask (Python), SQLAlchemy (with SQLite)
- **Other**: AJAX for dynamic interactivity, Chart.js for data visualisation, OpenAI API for AI quiz generation

## 👥 Team Members

| UWA ID   | Name                      | GitHub Username |
|----------|---------------------------|-----------------|
| 23991179 | Amanda Putri Devi Siagian | mandasgn        |
| 23487417 | Rayhan Rayhan             | rayhannm        |
| 23918912 | Gaby Tedjosurjono         | gabrielajt10    |
| 24211939 | Serena McPherson          | Deltane         |

---

## 🧠 How to Run the App

### Prerequisites

- Python 3.8+ installed
- Git installed

### 1. Clone the repository

```bash
git clone https://github.com/Deltane/quiz.it
cd quiz.it
```

### 2. Create a Virtual Environment

#### macOS/Linux
```bash
python3 -m venv venv  
source venv/bin/activate  
pip install --upgrade pip  
pip install -r requirements.txt

# If you make any changes to requirements.txt, run this command to update the file
pip freeze > requirements.txt
```

#### Windows
```bash
python3 -m venv venv  
venv\Scripts\activate  
pip install --upgrade pip  
pip install -r requirements.txt
pip freeze > requirements.txt

# If you make any changes to requirements.txt, run this command to update the file
pip freeze > requirements.txt
```

### 3. Set Up Environment Variables and Initialise Database

Create a `.env` file in the root directory of the project and add the following:

```dotenv
SECRET_KEY=your_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
OAUTHLIB_INSECURE_TRANSPORT=1
```

Replace `your_secret_key_here`, `your_google_client_id_here`, and `your_google_client_secret_here` with your actual values

Before running the app for the first time, set up the database with Flask-Migrate:
```bash
flask db init         # Only needed the first time to initialize migrations
flask db migrate -m "Initial migration"
flask db upgrade

If you make changes to your models in the future, run:
flask db migrate -m "Describe your change"
flask db upgrade
```

### 4. Run the App

#### Using `flask run`

Set the `FLASK_APP` environment variable and run the app:

```bash
export FLASK_APP=run.py  # For macOS/Linux
set FLASK_APP=run.py     # For Windows
flask run
```

#### Using `python run.py`

Alternatively, you can run the app directly:

```bash
python run.py
```

The app will be available at `http://127.0.0.1:5000`.

---