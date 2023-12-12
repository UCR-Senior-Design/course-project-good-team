import pymongo
import sys
from pymongo import MongoClient
from bson.objectid import ObjectId

#Establish connection to the database
try:
  client = pymongo.MongoClient('mongodb+srv://test:b11094@friendify.plioijt.mongodb.net/?retryWrites=true&w=majority')
  
#URI error is thrown 
except pymongo.errors.ConfigurationError:
  print("An Invalid URI host error was received.")
  sys.exit(1)

#Setup access within database
mydb = client.Friendify
users = mydb["Users"]

def returnUser():
    #Search for a user, id strings can be variable length
    username_to_search = input("Enter username string to lookup: ")
    query = {'username': username_to_search}
    projection = {'_id': 0}

    #This should only return one document
    result = users.find(query, projection)

    #This prints the user found, result is a cursor object pointing to the document(s)
    for user in result:
        print(user)

def addFriend():
    #Adds a new user to the initial user's friends array
    username_to_add = input("Enter username string of friend to add: ")
    update_query = {'username': username_to_search}
    update_operation = {'$addToSet': {'friends': username_to_add}}

    users.update_one(update_query, update_operation)

username_to_search = input("Enter your username string: ")

while True:
    
    choice = input("\nEnter 'add' to add a friend, 'find' to return a friends account id, or 'exit' to quit: ")

    if choice == 'add':
        addFriend()
        continue
    elif choice == 'find':
        returnUser()
        continue
    elif choice == 'exit':
        break
    else:
        print("Invalid input. Try again.")

client.close()
