import unittest
import subprocess
import time
import pytest
from selenium import webdriver

#http://127.0.0.1:8080

class FriendifyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Start the server in the background
        cls.server_process = subprocess.Popen(['python', 'server.py'])

        # Allow some time for the server to start
        time.sleep(2)

        # Currently comment / uncomment out the appropriate webdriver before compilation

        # IF RUNNING ON CHROME:
        #cls.driver = webdriver.Chrome()

        # IF RUNNING ON FIREFOX:
        cls.driver = webdriver.Firefox()

    def setUp(self):
        # Open the website in the browser
        self.driver.get('http://127.0.0.1:8080') 

    def test_home(self):
        self.assertEqual('Friendify', self.driver.title)

    def test_about(self):
        self.driver.get("http://127.0.0.1:8080/about")
        self.assertEqual('About Page', self.driver.title)

    #def test_login(self):
        #This will currently give a 404 error, looking into how to fix
        #self.driver.get("http://127.0.0.1:8080/login")
        #self.assertEqual('Login - Spotify', self.driver.title)

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        cls.server_process.terminate()

        # Quit the WebDriver
        cls.driver.quit()

if __name__ == '__main__':
    unittest.main()