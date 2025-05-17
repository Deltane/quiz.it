import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

class QuizFormAttributesTest(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = "http://127.0.0.1:5000"

    def tearDown(self):
        self.driver.quit()

    def test_basic_form_elements(self):
        """Test that all basic form elements are present"""
        self.driver.get(self.base_url + "/create_quiz")
        
        # Verify all required form elements exist
        elements = [
            "quiz-name", 
            "upload-file",
            "ai-prompt",
            "timer",
            "quiz-type",
            "question-count",
            "public",
            "private"
        ]
        
        for element_id in elements:
            self.assertIsNotNone(
                self.driver.find_element(By.ID, element_id),
                f"Element with id '{element_id}' should exist"
            )
    
    def test_timer_attribute(self):
        """Test that timer has the minimum value attribute set"""
        self.driver.get(self.base_url + "/create_quiz")
        timer_input = self.driver.find_element(By.ID, "timer")
        # Just check the attribute exists, don't test enforcement
        self.assertEqual(timer_input.get_attribute("min"), "0")
        
    def test_question_count_attributes(self):
        """Test that question count has min and max attributes set"""
        self.driver.get(self.base_url + "/create_quiz")
        count_input = self.driver.find_element(By.ID, "question-count")
        # Just check the attributes exist, don't test enforcement
        self.assertEqual(count_input.get_attribute("min"), "1")
        self.assertEqual(count_input.get_attribute("max"), "50")
        
    def test_privacy_default_selection(self):
        """Test that public privacy is selected by default"""
        self.driver.get(self.base_url + "/create_quiz")
        public_radio = self.driver.find_element(By.ID, "public")
        self.assertTrue(public_radio.is_selected())

    def test_form_submit_button(self):
        """Test that the submit button exists with correct value"""
        self.driver.get(self.base_url + "/create_quiz")
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn.btn-primary")
        self.assertTrue(submit_btn.is_displayed())
        # Value attribute should match the form definition
        self.assertTrue(submit_btn.get_attribute("value") in ["Generate Quiz", "Submit"])

if __name__ == "__main__":
    unittest.main()