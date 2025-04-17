# quiz.it 🧠📚

A web-based AI-assisted quiz creation and practice platform built with Flask and SQLite. Users can generate quizzes from custom input or files, complete and review their results, and share quizzes with friends or groups.

## 🌟 Features

- User registration and login
- Manual and AI-generated quiz creation
- Import and upload documents for quiz generation (compatible types TBA)
- Support for MCQ, short answer, and fill-in-the-blank types
- Real-time scoring and quiz attempt history
- Visual statistics with charts (time spent, scores, question review)
- Quiz sharing with individuals or groups

## 🚀 Technologies

- **Frontend**: HTML, CSS, JavaScript, jQuery, Bootstrap/Tailwind (choose one)
- **Backend**: Flask (Python), SQLAlchemy (with SQLite)
- **Other**: AJAX for dynamic interactivity, Chart.js for data visualisation, OpenAI API for AI quiz generation

## 👥 Team Members

| UWA ID   | Name                      | GitHub Username |
|----------|---------------------------|-----------------|
| 23991179 | Amanda Putri Devi Siagian | mandasgn        |
| 23456789 | Rayhan Rayhan             | rayhannm        |
| 34567890 | Gaby Tedjosurjono         | gabrielajt10    |
| 24211939 | Serena McPherson          | Deltane         |

## 🧠 How to Run the App

1. Clone this repository:
    ```bash
    git clone https://github.com/Deltane/CITS3403-Group-Project
    cd TBA
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Set up the environment:
    - Create a `.env` file or modify `config.py` with:
      - FLASK_APP=run.py
      - SECRET_KEY=your_secret
      - OPENAI_API_KEY=your_key_here (if using AI)

5. Run the Flask app:
    ```bash
    flask run
    ```

6. Visit `http://127.0.0.1:5000` in your browser.

## ✅ How to Run Tests

```bash
python -m unittest discover tests