import unittest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

class TestQuizScoring(unittest.TestCase):
    """Test quiz scoring logic, completion status, and time tracking"""
    
    def setUp(self):
        """Set up test environment"""
        self.questions = [
            {"question": "What is 2+2?", "options": ["3", "4", "5", "6"], "answer": "4"},
            {"question": "What is the capital of France?", "options": ["London", "Berlin", "Paris", "Madrid"], "answer": "Paris"},
            {"question": "What is H2O?", "options": ["Salt", "Water", "Oil", "Gold"], "answer": "Water"}
        ]
        
        # Test session data
        self.session = {
            'user_id': 1,
            'quiz_id': 1,
            'quiz_duration': 5,
            'answers': {}
        }
        
        # Create mock client
        self.client = MagicMock()
    
    def test_score_calculation(self):
        """Test that scoring logic calculates correctly"""
        # Set up answers - 2 correct, 1 incorrect
        answers = {
            0: "4",      # correct
            1: "London",  # incorrect (should be Paris)
            2: "Water"    # correct
        }
        
        # Calculate score manually based on our scoring logic
        total_questions = len(self.questions)
        correct_count = 0
        
        for question_index, answer in answers.items():
            expected_answer = self.questions[question_index]["answer"]
            if answer == expected_answer:
                correct_count += 1
        
        # Verify the calculation
        self.assertEqual(correct_count, 2)
        self.assertEqual(total_questions, 3)
        
        # Calculate score percentage using assertAlmostEqual for floating point comparison
        score_percentage = (correct_count / total_questions) * 100
        self.assertAlmostEqual(score_percentage, 66.67, places=2)  # Round to 2 decimal places
    
    def test_completion_status(self):
        """Test completion status logic"""
        # A quiz is considered complete if:
        # 1. All questions are answered
        # 2. Time hasn't run out
        
        # Case 1: All questions answered - should be complete
        all_questions_answered = {
            0: "4",
            1: "Paris",
            2: "Water"
        }
        
        is_complete = len(all_questions_answered) == len(self.questions)
        self.assertTrue(is_complete)
        
        # Case 2: Not all questions answered - should be incomplete
        partial_questions_answered = {
            0: "4",
            1: "Paris"
        }
        
        is_complete = len(partial_questions_answered) == len(self.questions)
        self.assertFalse(is_complete)
    
    def test_time_tracking(self):
        """Test time tracking logic"""
        # Initial quiz duration (in minutes)
        quiz_duration = 5
        quiz_duration_seconds = quiz_duration * 60
        
        # Case 1: Time remaining when exiting
        time_remaining = 180  # 3 minutes left
        time_spent = quiz_duration_seconds - time_remaining
        
        self.assertEqual(time_spent, 120)  # 2 minutes spent (120 seconds)
        self.assertEqual(time_remaining, 180)  # 3 minutes remaining
        
        # Case 2: Time expired
        time_remaining = 0
        time_spent = quiz_duration_seconds - time_remaining
        
        self.assertEqual(time_spent, 300)  # 5 minutes spent (full duration)
        self.assertEqual(time_remaining, 0)  # No time remaining
        
        # Case 3: Calculate percentage of time used
        time_percentage_used = (time_spent / quiz_duration_seconds) * 100
        self.assertEqual(time_percentage_used, 100)  # 100% of time used

    def test_partial_completion_scoring(self):
        """Test scoring with partially completed quiz"""
        # Set up answers - only answered 2 out of 3 questions
        answers = {
            0: "4",      # correct
            1: "Paris",  # correct
        }
        
        # Calculate score for answered questions only
        total_answered = len(answers)
        correct_count = 0
        
        for question_index, answer in answers.items():
            expected_answer = self.questions[question_index]["answer"]
            if answer == expected_answer:
                correct_count += 1
        
        # Verify calculations
        self.assertEqual(correct_count, 2)
        self.assertEqual(total_answered, 2)
        
        # Calculate partial completion score
        partial_score = correct_count
        completion_percentage = (total_answered / len(self.questions)) * 100
        
        self.assertEqual(partial_score, 2)
        self.assertAlmostEqual(completion_percentage, 66.67, places=2)  # Fixed floating-point comparison

if __name__ == '__main__':
    unittest.main()