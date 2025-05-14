from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

quiz_folder_association = db.Table('quiz_folder_association',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quiz.id'), primary_key=True),
    db.Column('folder_id', db.Integer, db.ForeignKey('folder.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)
    quiz_results = db.relationship('QuizResult', backref='user', lazy=True)
    quizzes_shared_with_me = db.relationship(
        'QuizShare',
        foreign_keys='QuizShare.shared_with_user_id',
        back_populates='shared_with_user',
        lazy='dynamic'
    )
    quizzes_shared_by_me = db.relationship(
        'QuizShare',
        foreign_keys='QuizShare.shared_by_user_id',
        back_populates='shared_by_user',
        lazy='dynamic'
    )
    shared_quizzes = db.relationship(
        'Quiz',
        secondary='quiz_share',
        primaryjoin='User.id==QuizShare.shared_with_user_id',
        secondaryjoin='Quiz.id==QuizShare.quiz_id',
        viewonly=True,
        lazy='dynamic',
        backref=db.backref('shared_with_users', lazy='dynamic')
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    questions_json = db.Column(db.Text, nullable=False)  # stores quiz questions in JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folders = db.relationship('Folder', secondary=quiz_folder_association, back_populates='quizzes')
    quiz_shares = db.relationship(
        'QuizShare',
        foreign_keys='QuizShare.quiz_id',
        back_populates='quiz',
        lazy='dynamic',
        overlaps="shared_quizzes,shared_with_users"
    )

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    quiz_type = db.Column(db.String(50), nullable=False)
    quiz = db.relationship('Quiz', backref='results')

    completed = db.Column(db.Boolean, default=False)
    answers = db.Column(db.JSON, nullable=True)
    title = db.Column(db.String(255), nullable=True)
    time_remaining = db.Column(db.Integer, nullable=True)
    quiz_duration = db.Column(db.Integer, nullable=True)  # in minutes

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('folders', lazy=True))
    quizzes = db.relationship('Quiz', secondary=quiz_folder_association, back_populates='folders')

class QuizShare(db.Model):
    __tablename__ = 'quiz_share'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)

    quiz = db.relationship('Quiz', foreign_keys=[quiz_id], back_populates='quiz_shares', overlaps="shared_quizzes,shared_with_users")
    shared_with_user = db.relationship('User', foreign_keys=[shared_with_user_id], back_populates='quizzes_shared_with_me', overlaps="shared_quizzes,shared_with_users")
    shared_by_user = db.relationship('User', foreign_keys=[shared_by_user_id], back_populates='quizzes_shared_by_me')