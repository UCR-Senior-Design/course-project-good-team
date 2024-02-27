import unittest
import subprocess
import time
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pymongo
from pymongo import MongoClient
from bson import ObjectId

#http://127.0.0.1:8080

class DataBaseTests(unittest.TestCase):

    mongo_client = pymongo.MongoClient('mongodb+srv://test:b11094@friendify.plioijt.mongodb.net/?retryWrites=true&w=majority', tlsAllowInvalidCertificates=True) # This is not a permanent solution, and is just for development. We should not allow invalid certificates during deployment.

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
        # Set up connection to MongoDB
        self.db = self.mongo_client['Friendify']  
        self.collection = self.db['Users']  
        # Set up Selenium WebDriver

        # Open the website in the browser
        self.driver = webdriver.Chrome()
        
        self.driver.get('http://127.0.0.1:8080') 
        

    def test_user_inserted_on_login(self):
        #Note: the object id is dependent on an entry we plan to delete in advance, since it also depends on login
        #Currently there is no safeguard against accidentally deleting user data with same username, so don't test
        # with a username that has a duplicate in the database
        
        #INSERT USERNAME HERE WHEN TESTING
        username = ''
        #INSERT PASSWORD HERE WHEN TESTING
        password = ''

        #In the event we test with a user that is not already in the database set this to False (we do not need to backup the data)
        userExists = True
        if(userExists):
            query = {'id': username}

            document_to_store = self.collection.find_one(query)

            # Check if the document exists
            if document_to_store:
                # Store the document's data with the original _id
                stored_data = document_to_store.copy()
                
                # Explicitly copy the _id field to the stored data
                stored_data['_id'] = document_to_store['_id']
                print(stored_data)

                # Delete the document from the collection
                result = self.collection.delete_one(query)
                if result.deleted_count == 1:
                    print(f"Document with ID {stored_data['_id']} deleted successfully.") 

        login_url = "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Faccounts.spotify.com%2Fauthorize%3Fshow_dialogue%3Dtrue%26scope%3Duser-read-private%2Buser-top-read%2Bplaylist-read-private%2Bplaylist-read-collaborative%2Buser-follow-read%26response_type%3Dcode%26redirect_uri%3Dhttp%253A%252F%252F127.0.0.1%253A8080%252Fcallback%26client_id%3D4f8a0448747a497e99591f5c8983f2d7"

        self.driver.get(login_url) 

        loginUsername = self.driver.find_element(By.ID, "login-username")
        loginPassword = self.driver.find_element(By.ID, "login-password")
        loginButton = self.driver.find_element(By.ID, "login-button")

        loginUsername.send_keys(username)
        loginPassword.send_keys(password)
        loginButton.click()

        time.sleep(10)

        # Find the newly created document (Note: This doesn't guarantee uniqueness in username
        # so if there are two users with the same username, data may be deleted that shouldn't be)
        document = self.collection.find_one({'id': username})

        # Assert that the user record exists in MongoDB
        self.assertIsNotNone(document)
        self.assertEqual(document['id'], username)

        # Delete this newly created document and backup the old version
        if(userExists):
            self.collection.delete_one({'id': username})

            new_document_id = self.collection.insert_one(stored_data).inserted_id
            print(f"Stored data re-uploaded as a new document with ID {new_document_id}")
        
    def test_update_friend_list(self):
        #INSERT USERNAME HERE WHEN TESTING
        username = ''
        #INSERT PASSWORD HERE WHEN TESTING
        password = ''

        login_url = "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Faccounts.spotify.com%2Fauthorize%3Fshow_dialogue%3Dtrue%26scope%3Duser-read-private%2Buser-top-read%2Bplaylist-read-private%2Bplaylist-read-collaborative%2Buser-follow-read%26response_type%3Dcode%26redirect_uri%3Dhttp%253A%252F%252F127.0.0.1%253A8080%252Fcallback%26client_id%3D4f8a0448747a497e99591f5c8983f2d7"

        self.driver.get(login_url) 

        loginUsername = self.driver.find_element(By.ID, "login-username")
        loginPassword = self.driver.find_element(By.ID, "login-password")
        loginButton = self.driver.find_element(By.ID, "login-button")

        loginUsername.send_keys(username)
        loginPassword.send_keys(password)
        loginButton.click()

        time.sleep(10)

        #Find the existing list of friends
        existing_friends = self.collection.find_one({'id': username})['friends']

        # Append a new username to the list
        new_username = 'Totally_Real_Person'
        updated_friends = existing_friends + [new_username]

        update_query = {'id': username}
        update_operation = {'$set': {'friends': updated_friends}}
        self.collection.update_one(update_query, update_operation)

        updated_document = self.collection.find_one({'id': username})      

        # Assert that the user record exists in MongoDB and the friend was added
        self.assertIsNotNone(updated_document)
        self.assertEqual(updated_friends, updated_document['friends'])

        

        # Remove new friend and backup the old version
        update_operation = {'$pull': {'friends': new_username}}
        self.collection.update_one(updated_document, update_operation)

    @classmethod
    def tearDownClass(cls):
        # Close connection to db
        cls.mongo_client.close()

        # Stop the server
        cls.server_process.terminate()

        # Quit the WebDriver
        cls.driver.quit()

if __name__ == '__main__':
    unittest.main()