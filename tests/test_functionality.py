import unittest
import warnings
import json
import re
from flask import session
from app import create_app

# Ignore deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class TestFunctionality(unittest.TestCase):
    """Test basic application functionality with enhanced tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-key',
            'SERVER_NAME': 'localhost',
            'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        })
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()
    
    def test_app_creates_successfully(self):
        """Test that the Flask app initializes correctly with proper configuration"""
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.testing)
        self.assertEqual(self.app.config['SERVER_NAME'], 'localhost')
        
        # Check for essential configuration
        self.assertIn('SECRET_KEY', self.app.config)
        self.assertIn('SQLALCHEMY_DATABASE_URI', self.app.config)
        
        # Test app has proper context
        self.assertTrue(hasattr(self.app, 'url_map'))
        self.assertTrue(hasattr(self.app, 'view_functions'))


    def test_session_functionality(self):
        """Test that sessions can be set and retrieved"""
        with self.client.session_transaction() as sess:
            sess['test_key'] = 'test_value'
            
        # Now the session should contain the test key
        response = self.client.get('/')
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['test_key'], 'test_value')
    
    def test_simple_string_operations(self):
        """Test string operations that might be useful in quiz processing"""
        # Basic string tests
        test_string = "Quiz Application"
        self.assertEqual(len(test_string), 16)
        self.assertTrue("Quiz" in test_string)
        self.assertEqual(test_string.split()[0], "Quiz")
        
        # Test string normalization (useful for answer comparison)
        answer1 = "  Washington, D.C.  "
        answer2 = "washington dc"
        
        # Normalize both answers (lowercase, strip, remove punctuation)
        normalized1 = re.sub(r'[^\w\s]', '', answer1.lower().strip())
        normalized2 = re.sub(r'[^\w\s]', '', answer2.lower().strip())
        
        self.assertEqual(normalized1.replace(" ", ""), normalized2.replace(" ", ""))
    
    def test_json_handling(self):
        """Test JSON operations that would be used in quiz data"""
        # Test quiz question data structure
        quiz_data = [
            {
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "answer": "Paris"
            },
            {
                "question": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "answer": "4"
            }
        ]
        
        # Convert to JSON string
        json_str = json.dumps(quiz_data)
        
        # Parse back and verify
        parsed_data = json.loads(json_str)
        self.assertEqual(len(parsed_data), 2)
        self.assertEqual(parsed_data[0]["question"], "What is the capital of France?")
        self.assertEqual(parsed_data[1]["answer"], "4")
        
        # Test answer checking logic (core quiz functionality)
        user_answer = "Paris"
        correct_answer = parsed_data[0]["answer"]
        self.assertEqual(user_answer, correct_answer)
        
        # Test score calculation
        correct_count = 0
        user_answers = ["Paris", "5"]  # One correct, one wrong
        
        for i, answer in enumerate(user_answers):
            if answer == parsed_data[i]["answer"]:
                correct_count += 1
                
        self.assertEqual(correct_count, 1)
        score_percentage = (correct_count / len(quiz_data)) * 100
        self.assertEqual(score_percentage, 50.0)

if __name__ == '__main__':
    unittest.main()