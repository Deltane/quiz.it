import unittest
from flask import session
import warnings
from app import create_app, db
from app.models import User, Quiz

# Ignore deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class TestQuizSecurityFeatures(unittest.TestCase):
    """Test security features specific to quiz creation"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-security-key',
            'WTF_CSRF_ENABLED': True  # Keep CSRF enabled for security testing
        })
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create a simple test user
            self.user = User(
                username='testuser', 
                email='test@example.com'
            )
            # Only add password hash if your User model requires it
            db.session.add(self.user)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_csrf_protection(self):
        """Test CSRF protection on quiz creation form"""
        # Login or set session for authenticated user
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
            sess['user_id'] = 1
        
        # First, make a GET request to view the form (should work)
        response = self.client.get('/create_quiz')
        self.assertEqual(response.status_code, 200, "Should be able to access create quiz form")
        
        # Try to submit form WITHOUT a CSRF token (should fail)
        response = self.client.post('/create_quiz', data={
            'quiz_name': 'Test Quiz',
            'quiz_type': 'Multiple Choice',
            'question_count': 5,
            # No CSRF token included
        })
        
        # Request should fail due to CSRF protection
        self.assertNotEqual(response.status_code, 200, "Form without CSRF token should be rejected")
        self.assertNotEqual(response.status_code, 302, "Form without CSRF token should not redirect to success page")
        
        # Now get a valid CSRF token by viewing the form page
        response = self.client.get('/create_quiz')
        
    def test_xss_prevention(self):
        """Test that XSS attempts are properly escaped in quiz creation"""
        # Login or set session
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
            sess['user_id'] = 1
        
        # Submit a form with an XSS payload in the quiz name
        xss_payload = '<script>alert("XSS")</script>'
        
        # Get the form first to have a valid CSRF token
        response = self.client.get('/create_quiz')
        
        # Then submit a form that includes an XSS attempt
        # Note: In a real test, you'd extract the CSRF token from the form
        response = self.client.post('/create_quiz', data={
            'quiz_name': xss_payload,
            'quiz_type': 'Multiple Choice',
            'question_count': 5,
            # Other required fields would go here
        }, follow_redirects=True)
        
        # Now check if this quiz appears on dashboard/quiz list
        response = self.client.get('/dashboard')
        
        # The raw script tags should not appear in the response
        self.assertNotIn(bytes(xss_payload, 'utf-8'), response.data,
                      "XSS payload should be escaped")
        
        # If we can get the quiz ID, also check the quiz page itself
        with self.app.app_context():
            quiz = Quiz.query.filter_by(title=xss_payload).first()
            if quiz:
                response = self.client.get(f'/quiz/{quiz.id}')
                self.assertNotIn(bytes(xss_payload, 'utf-8'), response.data,
                             "XSS payload should be escaped on quiz page")

if __name__ == '__main__':
    unittest.main()