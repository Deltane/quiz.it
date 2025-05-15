import unittest
from flask import Flask
from app.forms import QuizSetupForm

class TestQuizSetupForm(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        self.app_context.pop()
        
    def test_valid_form(self):
        """Test that a form with all required fields validates successfully"""
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=10,
            privacy="public",
            timer=5
        )
        self.assertTrue(form.validate())
        
    def test_required_fields(self):
        """Test that required fields are enforced"""
        form = QuizSetupForm()
        self.assertFalse(form.validate())
        self.assertIn('quiz_name', form.errors)
        self.assertIn('quiz_type', form.errors)
        self.assertIn('question_count', form.errors)
        
    def test_question_count_range(self):
        """Test question_count range validation"""
        # Test below minimum
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=0,
            privacy="public"
        )
        self.assertFalse(form.validate())
        self.assertIn('question_count', form.errors)
        
        # Test above maximum
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=51,
            privacy="public"
        )
        self.assertFalse(form.validate())
        self.assertIn('question_count', form.errors)
        
        # Test valid boundaries
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=1,
            privacy="public"
        )
        self.assertTrue(form.validate())
        
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=50,
            privacy="public"
        )
        self.assertTrue(form.validate())
        
    def test_timer_range(self):
        """Test timer range validation"""
        # Test negative value
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=10,
            privacy="public",
            timer=-1
        )
        self.assertFalse(form.validate())
        self.assertIn('timer', form.errors)
        
        # Test valid value
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Multiple Choice",
            question_count=10,
            privacy="public",
            timer=0
        )
        self.assertTrue(form.validate())
        
    def test_default_values(self):
        """Test default values are set correctly"""
        form = QuizSetupForm()
        self.assertEqual(form.timer.default, 0)
        self.assertEqual(form.privacy.default, 'public')
        
    def test_quiz_type_choices(self):
        """Test quiz type choices validation"""
        form = QuizSetupForm(
            quiz_name="Test Quiz",
            quiz_type="Invalid Type",  # This is not in the choices
            question_count=10
        )
        self.assertFalse(form.validate())
        self.assertIn('quiz_type', form.errors)

if __name__ == '__main__':
    unittest.main()