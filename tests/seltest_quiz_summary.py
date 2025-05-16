import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class QuizSummaryTest(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = "http://127.0.0.1:5000"

    def tearDown(self):
        self.driver.quit()

    def test_quiz_summary_page_loads(self):
        # Adjust the URL if your route is different
        self.driver.get(self.base_url + "/quiz_summary")
        self.assertEqual(self.driver.title, "Quiz Summary")
        # Check for the "Correct Answers" section
        body_text = self.driver.page_source
        self.assertIn("Correct Answers", body_text)

if __name__ == "__main__":
    unittest.main()