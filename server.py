import os
import base64
import requests
import pymongo
import spotipy
import certifi
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, send_from_directory, session, url_for, render_template, flash
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

try:
    client = pymongo.MongoClient('mongodb+srv://test:b11094@friendify.plioijt.mongodb.net/?retryWrites=true&w=majority', tlsAllowInvalidCertificates=True) # This is not a permanent solution, and is just for development. We should not allow invalid certificates during deployment.
    
#URI error is thrown 
except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received.")
    #Idk if this line should be in here specifically
    sys.exit(1)

mydb = client.Friendify
users = mydb["Users"]

@app.route('/')
def index():
    username = session.get('username', 'Guest')
    is_logged_in = session.get('is_logged_in', False)
    random_statistic = None
    image_url = None  # URL for the image

    if is_logged_in:
        access_token = session.get('access_token')
        headers = {'Authorization': f'Bearer {access_token}'}

        # Choose randomly between artist and track, and among time ranges
        stat_type = choice(['track', 'artist'])
        time_range = choice(['short_term', 'medium_term', 'long_term'])
        time_range_text = {
            'short_term': 'in the last 4 weeks',
            'medium_term': 'in the last 6 months',
            'long_term': 'of all time'
        }[time_range]

        if stat_type == 'track':
            top_tracks_response = requests.get(
                f'https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=1',
                headers=headers
            )
            if top_tracks_response.status_code == 200:
                top_track = top_tracks_response.json().get('items', [])[0]
                random_statistic = f"Your most played track {time_range_text} is {top_track['name']}"
                image_url = top_track['album']['images'][0]['url']

        elif stat_type == 'artist':
            top_artists_response = requests.get(
                f'https://api.spotify.com/v1/me/top/artists?time_range={time_range}&limit=1',
                headers=headers
            )
            if top_artists_response.status_code == 200:
                top_artist = top_artists_response.json().get('items', [])[0]
                random_statistic = f"Your most played artist {time_range_text} is {top_artist['name']}"
                image_url = top_artist['images'][0]['url']

    return render_template('index.html', username=username, is_logged_in=is_logged_in, random_statistic=random_statistic, image_url=image_url)

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
    if 'access_token' in session:
        username = session.get('username')
        user_data = users.find_one({'username': username})
        if user_data:
            friends_list = user_data.get('friends', [])
            return render_template('friends.html', friends=friends_list)
        else:
            flash("User data not found.")
            return redirect(url_for('index'))
    else:
        flash("Please log in to view your friends.")
        return redirect(url_for('login'))


@app.route('/addfriend', methods=['POST'])
def addfriend():
    if 'access_token' not in session:
        # Gotta log in to add friends lol
        return {'message': 'Please log in to add friends.'}, 401

    data = request.json
    friend_name = data.get('friendName')
    username = session.get('username')

    # Checking if friend is in our database
    if not users.find_one({'username': friend_name}):
        return {'message': 'User is not in Friendify database.'}, 404

    # Check if friend is already added
    user = users.find_one({'username': username})
    if friend_name in user.get('friends', []):
        return {'message': 'User is already your friend.'}, 409

    # Successfully adding friend to list
    users.update_one({'username': username}, {'$addToSet': {'friends': friend_name}})
    return {'message': 'Friend successfully added.'}, 200


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
            userid = user_data.get('id')
            print("Recieved data from ", username)

            # For right now just using flask session to store username, if theres a better way to do this i'll change it later
            session['username'] = username
            session['access_token'] = access_token
            session['is_logged_in'] = True
            
            #Storing the logged in user to the database if they are not already in it
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
        return redirect(url_for('index', username=username))

    else:
        print("Failed to retrieve access token. Status code:", response.status_code)
        print("Response:", response.json())
        return redirect('/error')  # Redirect to an error page that we haven't implemented yet

if __name__ == '__main__':
    app.run(port=8080)
