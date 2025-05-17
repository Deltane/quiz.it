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

    def test_time_chart_displayed(self):
        """Test that the time spent per question chart section is displayed"""
        self.driver.get(self.base_url + "/quiz_summary")
        
        # Find all chart sections
        chart_sections = self.driver.find_elements("tag name", "section")
        
        # Look for the time chart section
        time_chart_found = False
        for section in chart_sections:
            if "Time Spent Per Question" in section.text:
                time_chart_found = True
                # Check if canvas element exists
                canvas = section.find_element("id", "timeChart")
                self.assertTrue(canvas.is_displayed(), "Time chart canvas should be visible")
                break
                
        self.assertTrue(time_chart_found, "Time Spent Per Question section should be present")

        def test_navigation_bar_elements(self):
            """Test that the navigation bar contains expected elements"""
            self.driver.get(self.base_url + "/quiz_summary")
            
            # Check if navigation exists
            nav = self.driver.find_element("tag name", "nav")
            self.assertTrue(nav.is_displayed(), "Navigation bar should be visible")
            
            # Check for title in navigation
            nav_title = nav.find_element("class name", "dashboard-title")
            self.assertEqual(nav_title.text, "Quiz Summary", "Navigation should have correct title")
            
            # Check for navigation buttons
            nav_links = nav.find_elements("tag name", "a")
            link_texts = [link.text for link in nav_links if link.text]
            
            # Verify essential navigation links exist
            self.assertIn("Home", link_texts, "Navigation should contain Home link")
            self.assertIn("Create Quiz", link_texts, "Navigation should contain Create Quiz link")

if __name__ == "__main__":
    unittest.main()