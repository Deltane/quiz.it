import unittest
from flask import Flask
from flask_testing import TestCase
from app import create_app, db
from app.models import User, QuizResult
from flask_login import login_user

class TestCreateQuiz(TestCase):

    def create_app(self):
        app = create_app()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app

    def setUp(self):
        db.create_all()
        self.client = self.app.test_client()
        self.user = User(username='testuser', email='testuser@example.com', password_hash='testpassword')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_quiz(self):
        with self.client:
            with self.client.session_transaction() as session:
                login_user(self.user)

            response = self.client.post('/store_quiz', json={
                'quiz': [
                    {'question': 'What is 2+2?', 'answer': '4'},
                    {'question': 'What is the capital of France?', 'answer': 'Paris'}
                ],
                'quizType': 'multiple-choice'
            })

            self.assertEqual(response.status_code, 204)

            response = self.client.post('/submit_answer', json={
                'questionIndex': 0,
                'answer': '4'
            })
            self.assertEqual(response.status_code, 200)

            response = self.client.post('/submit_answer', json={
                'questionIndex': 1,
                'answer': 'Paris'
            })
            self.assertEqual(response.status_code, 200)

            quiz_results = QuizResult.query.filter_by(user_id=self.user.id).all()
            self.assertEqual(len(quiz_results), 1)
            self.assertEqual(quiz_results[0].score, 2)
            self.assertEqual(quiz_results[0].total_questions, 2)

    def test_quiz_id_not_null(self):
        with self.client:
            with self.client.session_transaction() as session:
                login_user(self.user)

            response = self.client.post('/store_quiz', json={
                'quiz': [
                    {'question': 'What is 2+2?', 'answer': '4'},
                    {'question': 'What is the capital of France?', 'answer': 'Paris'}
                ],
                'quizType': 'multiple-choice'
            })

            self.assertEqual(response.status_code, 204)

            response = self.client.post('/submit_answer', json={
                'questionIndex': 0,
                'answer': '4'
            })
            self.assertEqual(response.status_code, 200)

            response = self.client.post('/submit_answer', json={
                'questionIndex': 1,
                'answer': 'Paris'
            })
            self.assertEqual(response.status_code, 200)

            quiz_results = QuizResult.query.filter_by(user_id=self.user.id).all()
            self.assertEqual(len(quiz_results), 1)
            self.assertIsNotNone(quiz_results[0].quiz_id)

if __name__ == '__main__':
    unittest.main()