import unittest
import subprocess
import time
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse, parse_qs

#http://127.0.0.1:8080

class PageTitleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Start the server in the background
        cls.server_process = subprocess.Popen(['python', 'server.py'])

        # Allow some time for the server to start
        time.sleep(1)

        # Currently comment / uncomment out the appropriate webdriver before compilation

        # FOR RUNNING ON CHROME:
        #cls.driver = webdriver.Chrome()

        # FOR RUNNING ON FIREFOX:
        cls.driver = webdriver.Firefox()

    def setUp(self):
        # Open the website in the browser
        self.driver.get('http://127.0.0.1:8080') 

    def test_home(self):
        self.assertEqual('Friendify', self.driver.title)

    def test_about(self):
        self.driver.get("http://127.0.0.1:8080/about")
        self.assertEqual('About Page', self.driver.title)

    def test_login(self):
        login_url = "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Faccounts.spotify.com%2Fauthorize%3Fshow_dialogue%3Dtrue%26scope%3Duser-read-private%2Buser-top-read%2Bplaylist-read-private%2Bplaylist-read-collaborative%2Buser-follow-read%26response_type%3Dcode%26redirect_uri%3Dhttp%253A%252F%252F127.0.0.1%253A8080%252Fcallback%26client_id%3D4f8a0448747a497e99591f5c8983f2d7"

        self.driver.get(login_url) 

        loginUsername = self.driver.find_element(By.ID, "login-username")
        loginPassword = self.driver.find_element(By.ID, "login-password")
        loginButton = self.driver.find_element(By.ID, "login-button")

        #INSERT USERNAME HERE WHEN TESTING
        username = ''
        #INSERT PASSWORD HERE WHEN TESTING
        password = ''

        loginUsername.send_keys(username)
        loginPassword.send_keys(password)
        loginButton.click()

        #Give login time to process, may fail the assertion if the login doesn't go through, so time.sleep(x) should be changed to match that
        time.sleep(10)
        parsed_url = urlparse(self.driver.current_url)
        # Extract the scheme, netloc, and path
        scheme = parsed_url.scheme
        netloc = parsed_url.netloc
        path = parsed_url.path

        # Create the expected URL up to 'username='
        curr_parsed_url = f"{scheme}://{netloc}{path}?username="

        # Without connecting to the database, we cannot check the exact username
        self.assertEqual('http://127.0.0.1:8080/?username=', curr_parsed_url)

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        cls.server_process.terminate()

        # Quit the WebDriver
        cls.driver.quit()

if __name__ == '__main__':
    unittest.main()