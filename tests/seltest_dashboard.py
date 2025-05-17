import unittest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class DashboardTest(unittest.TestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.base_url = "http://127.0.0.1:5000"

    def tearDown(self):
        self.driver.quit()

    def test_dashboard_redirects_when_not_logged_in(self):
        self.driver.get(self.base_url + "/dashboard")
        time.sleep(2)  # Wait for redirect
        current_url = self.driver.current_url
        self.assertNotEqual(
            current_url,
            self.base_url + "/dashboard",
            "Should redirect away from dashboard if not logged in"
        )

if __name__ == "__main__":
    unittest.main()