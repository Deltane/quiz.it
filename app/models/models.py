from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    quizzes = db.relationship('Quiz', backref='author', lazy=True)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    questions_json = db.Column(db.Text)  # Store quiz data as JSON
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)