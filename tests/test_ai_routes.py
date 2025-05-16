import unittest
from app.routes.ai_routes import normalise_answer, compare_answers

class TestAiRoutes(unittest.TestCase):
    def setUp(self):
        """Set up shared test data or state."""
        self.numeric_inputs = [("six", "6"), ("twenty-one", "21"), ("100", "100")]
        self.non_numeric_inputs = [("hello", "hello"), ("HTTPS", "https")]
        self.empty_inputs = [(None, ""), ("", "")]
        self.fuzzy_inputs = [("htps", "https")]

    def tearDown(self):
        pass

    def test_normalise_answer(self):
        # Test numeric conversions
        for input_value, expected in self.numeric_inputs:
            self.assertEqual(normalise_answer(input_value), expected)
        
        # Test non-numeric inputs
        for input_value, expected in self.non_numeric_inputs:
            self.assertEqual(normalise_answer(input_value), expected)
        
        # Test empty and None inputs
        for input_value, expected in self.empty_inputs:
            self.assertEqual(normalise_answer(input_value), expected)

    def test_compare_answers(self):
        # Test exact matches
        self.assertTrue(compare_answers("six", "6"))
        self.assertTrue(compare_answers("twenty-one", "21"))
        self.assertTrue(compare_answers("HTTPS", "https"))
        
        # Test fuzzy matches
        for user_input, correct_answer in self.fuzzy_inputs:
            self.assertTrue(compare_answers(user_input, correct_answer, similarity_threshold=80))
            self.assertFalse(compare_answers(user_input, correct_answer, similarity_threshold=90))
        
        # Test mismatched answers
        self.assertFalse(compare_answers("six", "seven"))
        self.assertFalse(compare_answers("hello", "world"))

if __name__ == "__main__":
    unittest.main()