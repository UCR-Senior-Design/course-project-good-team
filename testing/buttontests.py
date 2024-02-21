import unittest
import subprocess
import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By

#http://127.0.0.1:8080

class ButtonTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Start the server in the background
        cls.server_process = subprocess.Popen(['python', 'server.py'])

        # Allow some time for the server to start
        time.sleep(2)

        # Currently the webdriver is commented / uncommented out before compilation

        # IF RUNNING ON CHROME:
        #cls.driver = webdriver.Chrome()

        # IF RUNNING ON FIREFOX:
        cls.driver = webdriver.Firefox()

    def setUp(self):
        # Open the website in the browser
        self.driver.get('http://127.0.0.1:8080') 

    def test_about_button_navigation(self):
        # Locate the about button
        button = self.driver.find_element(By.XPATH, "//a[@href='/about']")

        # Click the button
        button.click()

        new_page_url = self.driver.title
        self.assertEqual(new_page_url, 'About Page')

    def test_home_from_about_navigation(self):
        # Locate the about button
        button = self.driver.find_element(By.XPATH, "//a[@href='/about']")

        # Click the button
        button.click()

        # Locate the home button
        button = self.driver.find_element(By.XPATH, "//a[@href='/']")

        # Click the button
        button.click()

        new_page_url = self.driver.title
        self.assertEqual(new_page_url, 'Friendify')

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        cls.server_process.terminate()

        # Quit the WebDriver
        cls.driver.quit()

if __name__ == '__main__':
    unittest.main()