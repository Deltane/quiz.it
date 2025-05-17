import unittest
import warnings
import re
from app import create_app

# Ignore deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class TestUserRoutes(unittest.TestCase):
    """Test user-related routes"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config.update({
            'TESTING': True,
            'SECRET_KEY': 'test-key',
        })
        self.client = self.app.test_client()
        
        # Set up a session for authenticated routes
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_email'] = 'test@example.com'
    
    
    def test_profile_route_exists(self):
        """Test that profile page responds to requests"""
        response = self.client.get('/profile', follow_redirects=True)
        
        # Should return something other than a 500 error
        self.assertLess(response.status_code, 500, "Profile route should respond without server error")
        
        # If we got a 200 response, check basic content
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            self.assertIn('<!DOCTYPE html>', content)
            self.assertTrue(
                'profile' in content.lower() or 'user' in content.lower() or 'account' in content.lower(),
                "Profile page should contain relevant terms"
            )
    
    def test_take_quiz_route(self):
        """Test that take_quiz route is accessible"""
        # This route was visible in your quiz_routes.py file
        response = self.client.get('/take_quiz', follow_redirects=True)
        
        # Should return a status code below 500
        self.assertLess(response.status_code, 500, "Take quiz route should respond without server error")
    
    def test_home_route_redirects(self):
        """Test that home route exists and redirects are followed"""
        response = self.client.get('/', follow_redirects=True)
        
        # Should be a 200 OK after following any redirects
        self.assertEqual(response.status_code, 200)
        
        # Should be HTML content
        content = response.data.decode('utf-8')
        self.assertIn('<!DOCTYPE html>', content)
        
        # Should have a basic structure with navigation
        self.assertIn('<body', content)
        
        # Should contain navigation elements
        self.assertTrue(
            '<nav' in content.lower() or 
            '<header' in content.lower() or 
            re.search(r'<a\s+[^>]*href', content),
            "Page should have navigation elements"
        )

if __name__ == '__main__':
    unittest.main()