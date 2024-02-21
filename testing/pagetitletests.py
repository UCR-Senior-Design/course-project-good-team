import unittest
import subprocess
import time
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

#http://127.0.0.1:8080

class PageTitleTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Start the server in the background
        cls.server_process = subprocess.Popen(['python', 'server.py'])

        # Allow some time for the server to start
        time.sleep(1)

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

    def test_login(self):
        # This will currently give a 404 error, looking into how to fix
        login_url = "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Faccounts.spotify.com%2Fauthorize%3Fshow_dialogue%3Dtrue%26scope%3Duser-read-private%2Buser-top-read%2Bplaylist-read-private%2Bplaylist-read-collaborative%2Buser-follow-read%26response_type%3Dcode%26redirect_uri%3Dhttp%253A%252F%252F127.0.0.1%253A8080%252Fcallback%26client_id%3D4f8a0448747a497e99591f5c8983f2d7"

        self.driver.get(login_url) 

        loginUsername = self.driver.find_element(By.ID, "login-username")
        loginPassword = self.driver.find_element(By.ID, "login-password")
        loginButton = self.driver.find_element(By.ID, "login-button")

        loginUsername.send_keys('mr.crimsoneagle')
        loginPassword.send_keys('proudswifter')
        loginButton.click()

        #Give login time to process
        time.sleep(4)
        self.assertEqual('http://127.0.0.1:8080/?username=Vincent+Martinez', self.driver.current_url)

    @classmethod
    def tearDownClass(cls):
        # Stop the server
        cls.server_process.terminate()

        # Quit the WebDriver
        cls.driver.quit()

if __name__ == '__main__':
    unittest.main()