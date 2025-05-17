from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import unittest
import time

class QuizTimerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.base_url = "http://localhost:5000" 

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_quiz_timer(self):
        driver = self.driver
        driver.get(self.base_url + "/take_quiz")  

        # Wait for the countdown timer to appear
        timer = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, "countdown-timer"))
        )
        self.assertTrue(timer.is_displayed(), "Timer not visible")

        # Optionally, check that timer text is updating or not "Loading..."
        timer_text = timer.text.strip()
        self.assertNotEqual(timer_text, "Loading...", "Timer did not initialize")

    def test_pause_resume_timer(self):
        driver = self.driver
        driver.get(self.base_url + "/take_quiz")

        # Wait for the pause/resume button to appear
        pause_btn = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, "pause-resume-btn"))
        )
        self.assertTrue(pause_btn.is_displayed(), "Pause/Resume button not visible")

        # Get timer value before pause
        timer = driver.find_element(By.ID, "countdown-timer")
        time_before = timer.text.strip()

        # Click pause
        pause_btn.click()
        time.sleep(2)  # Wait to ensure timer is paused

        # Get timer value after pause
        time_after = timer.text.strip()
        self.assertEqual(time_before, time_after, "Timer should not change while paused")

        # Click resume
        pause_btn.click()
        time.sleep(2)  # Wait to ensure timer resumes

        # Get timer value after resume
        time_resumed = timer.text.strip()
        self.assertNotEqual(time_after, time_resumed, "Timer should resume after clicking resume")

    def test_navigation_buttons_present(self):
        driver = self.driver
        driver.get(self.base_url + "/take_quiz")

        # Check that navigation buttons exist in the DOM
        prev_btn = driver.find_element(By.ID, "prev-question")
        next_btn = driver.find_element(By.ID, "next-question")
        self.assertIsNotNone(prev_btn, "Previous question button not found in DOM")
        self.assertIsNotNone(next_btn, "Next question button not found in DOM")

    def test_exit_quiz_button(self):
        driver = self.driver
        driver.get(self.base_url + "/take_quiz")

        # Check for exit quiz button
        exit_btn = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, "exit-quiz-btn"))
        )
        self.assertTrue(exit_btn.is_displayed(), "Exit quiz button not visible")

if __name__ == "__main__":
    unittest.main()