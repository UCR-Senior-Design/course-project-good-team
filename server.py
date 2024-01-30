import os
import base64
import requests
import pymongo
import spotipy
import certifi
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, send_from_directory, session, url_for, render_template
from datetime import timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from random import choice


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv()

# Read environment variables from .env
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')


app = Flask(__name__)
app.secret_key = 'goodgroup'
app.permanent_session_lifetime = timedelta(minutes=30)  # Basically saves your login for 30 minutes

@app.route('/')
def index():
    username = session.get('username', 'Guest')  # Default to 'Guest' if not logged in
    is_logged_in = session.get('is_logged_in', False)  # Default to False if not set
    print("Username in session:", username) 

    random_statistic = None
    if is_logged_in:
        access_token = session.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}

        # Fetch top tracks or artists
        top_tracks_response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers)
        top_artists_response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers)
        
        if top_tracks_response.status_code == 200 and top_artists_response.status_code == 200:
            top_tracks = top_tracks_response.json().get('items', [])
            top_artists = top_artists_response.json().get('items', [])

            # Select a random statistic
            if top_tracks and top_artists:
                random_statistic = choice([
                    f"Your most played artist of all time is {top_artists[0]['name']}",
                    f"Your most played track of all time is {top_tracks[0]['name']}"
                    # Add more options, this all i got for now
                ])

    return render_template('index.html', username=username, is_logged_in=is_logged_in, random_statistic=random_statistic)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/db')
def database():
    return render_template('database.html')

@app.route('/friends')
def friends():
    if 'access_token' not in session:
        return redirect('/login')  #Redirect to login page
    
    ca = certifi.where()

    #Establish connection to the database
    try:
        client = pymongo.MongoClient('mongodb+srv://test:b11094@friendify.plioijt.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
    
    #URI error is thrown 
    except pymongo.errors.ConfigurationError:
        print("An Invalid URI host error was received.")
        #Idk if this line should be in here specifically
        sys.exit(1)

    #Setup access within database
    mydb = client.Friendify
    users = mydb["Users"]

    #Base64 Encode Client ID and Client Secret
    client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()


    #Headers for POST request
    headers = {
        'Authorization': f"Basic {client_credentials_b64}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    access_token = session.get('access_token', 'ERROR')

    if(access_token != 'ERROR'):
        headers = {'Authorization': f'Bearer {access_token}'}
        user_profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)

        if user_profile_response.status_code == 200:
            user_data = user_profile_response.json()
            userid = user_data.get('id')
            username = user_data.get('display_name')

            if users.find_one({'id': userid}) is not None:
                print(f"'{userid}' is already registered.")
            else:
                #TODO: This does not update the user profile with new playlists, it currently only takes a snapshot of the user profile data
                #at the time of initially adding them to the database, I need to make it so that each time it connects it re checks the playlist
                #data and adds if new playlists exist, cause right now the query here is useless, since it isn't checking against any existing data
                
                #Fetch user's playlists
                playlists_response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
                if playlists_response.status_code == 200:
                    playlists_data = playlists_response.json()

                    playlistsnameid = []
                    #Process playlists data here
                    for playlist in playlists_data['items']:
                        plist = (playlist['name'], playlist['id'])
                        #Query to check if the tuple exists in the data field for a specific document
                        query = {
                            "id": userid,
                            "playlists": {
                                "$elemMatch": {
                                    "$eq": plist
                                }
                            }
                        }
                        existing_document = users.find_one(query)
                        playlistsnameid.append(plist)
                
                #Create a new user document

                new_user = {
                    'id': userid,
                    'username': username,
                    'friends': [],
                    'playlists': playlistsnameid
                }

                #Insert the new user document into the collection
                users.insert_one(new_user)
                print(f"User '{username}' added successfully.")
    else:
        print("error")
    return redirect('/db')


@app.route('/addfriend', methods=['POST'])
def addfriend():
    if 'access_token' not in session:
        return redirect('/login')  #Redirect to login page

    data = request.json
    friend_name = data.get('friendName')

    ca = certifi.where()

    print(f"Received friend's name: {friend_name}")
    
    try:
        client = pymongo.MongoClient('mongodb+srv://test:b11094@friendify.plioijt.mongodb.net/?retryWrites=true&w=majority', tlsCAFile=ca)
    
    #URI error is thrown 
    except pymongo.errors.ConfigurationError:
        print("An Invalid URI host error was received.")
        #Idk if this line should be in here specifically
        sys.exit(1)
    
    mydb = client.Friendify
    users = mydb["Users"]

    #Is your friend real
    if(users.find_one({'username': friend_name}) is not None):
        #Setup access within database
        username = session.get('username')
        
        update_query = {'username': username}
        update_operation = {'$addToSet': {'friends': friend_name}}

        users.update_one(update_query, update_operation)
    
    return redirect('/db')

@app.route('/callback')
def callback():
    code = request.args.get('code')

    # Base64 Encode Client ID and Client Secret
    client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_credentials_b64 = base64.b64encode(client_credentials.encode()).decode()


    # Headers for POST request
    headers = {
        'Authorization': f"Basic {client_credentials_b64}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Body data for the POST request
    body = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }

    response = requests.post('https://accounts.spotify.com/api/token', data=body, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        print("Token request successful.")
        access_token = response.json().get('access_token')
        
        # Fetch user's profile data
        headers = {'Authorization': f'Bearer {access_token}'}
        user_profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        
        if user_profile_response.status_code == 200:
            user_data = user_profile_response.json()
            username = user_data.get('display_name')
            print("Recieved data from ", username)

            # For right now just using flask session to store username, if theres a better way to do this i'll change it later
            session['username'] = username
            session['access_token'] = access_token
            session['is_logged_in'] = True
        return redirect(url_for('index', username=username))

    else:
        print("Failed to retrieve access token. Status code:", response.status_code)
        print("Response:", response.json())
        return redirect('/error')  # Redirect to an error page that we haven't implemented yet

if __name__ == '__main__':
    app.run(port=8080)