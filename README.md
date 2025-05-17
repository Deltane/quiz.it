# quiz.it 🧠📚

A web-based, AI-assisted quiz creation and practice platform built with Flask and SQLite. quiz.it empowers users to generate quizzes from custom input or uploaded files, complete and review their results, and share quizzes with friends or groups.

## 🌟 Features

- User registration and login (including Google OAuth)
- Manual and AI-generated quiz creation (OpenAI integration)
- Import and upload documents for quiz generation via PDF
- Support for multiple question types: MCQ, short answer, fill-in-the-blank
- Real-time scoring, quiz attempt history, and review
- Visual statistics and analytics with interactive charts (time spent, scores, question review)
- Quiz sharing with individuals or groups (invite via email)
- Personal dashboard and user profile pages
- Responsive design for desktop and mobile

## 🚀 Technologies

- **Frontend**: HTML, CSS, JavaScript, jQuery, Bootstrap (and/or Tailwind)
- **Backend**: Flask (Python), SQLAlchemy (with SQLite)
- **Other**: Flask-Login, Flask-Mail, Flask-Migrate, Flask-Session, WTForms, Chart.js (for statistics), OpenAI API (for AI quiz generation), PyPDF2, PyMuPDF, pytesseract (for document import), OAuth (Google)
- **Testing**: pytest, Selenium (optional, for browser automation)

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
```

#### Windows
```bash
python3 -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

> If you add or update dependencies, run `pip freeze > requirements.txt` to update the requirements file.

### 3. Set Up Environment Variables and Initialise Database

Create a `.env` file in the root directory of the project with the following:

```dotenv
SECRET_KEY=your_secret_key_here
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
OAUTHLIB_INSECURE_TRANSPORT=1
```

Replace the placeholder values with your actual credentials.

Before running the app for the first time, set up the database with Flask-Migrate:

```bash
flask db init         # Only needed once to initialize migrations
flask db migrate -m "Initial migration"
flask db upgrade
```

If you make changes to your models in the future, run:
```bash
flask db migrate -m "Describe your change"
flask db upgrade
```

### 4. Run the App

#### Using `flask run`

Set the `FLASK_APP` environment variable and run:

```bash
export FLASK_APP=run.py  # For macOS/Linux
set FLASK_APP=run.py     # For Windows
flask run
```

#### Or, using `python run.py`

```bash
python run.py
```

The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

---
