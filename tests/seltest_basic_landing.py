from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest

class WebsiteTest(unittest.TestCase):
    def setUp(self):
        # Set up Chrome WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = "http://127.0.0.1:5000"  

    def test_page_title(self):
        # Test if the page title is correct
        driver = self.driver
        driver.get(self.base_url)
        expected_title = "quiz.it"  
        self.assertEqual(driver.title, expected_title, f"Expected title '{expected_title}', but got '{driver.title}'")

    def test_broken_link(self):
        # Test for broken links (404 errors)
        driver = self.driver
        driver.get(self.base_url + "/nonexistent-page")
        error_message = driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Not Found", error_message, "Expected 'Not Found' error, but got different response")

    def tearDown(self):
        # Clean up and close browser
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()