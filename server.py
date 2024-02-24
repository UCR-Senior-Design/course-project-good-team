import os
import io
import base64
import requests
import pymongo
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import certifi
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, redirect, send_from_directory, session, url_for, render_template, flash
from datetime import timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from random import choice
from PIL import Image
import requests
from collections import Counter

from spotify_utils import generate_genre_pie_chart, get_random_statistic, get_random_friend_statistic, generate_genre_pie_chart_from_db
from image_utils import get_dominant_color, get_contrasting_text_color
from db_utils import update_user_document


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
#PATCH FIX


@app.route('/')
def index():
    background_color = '#defaultBackgroundColor'  # Set a default background color
    text_color = '#defaultTextColor'  # Set a default text color
    username = session.get('username', 'Guest')
    is_logged_in = session.get('is_logged_in', False)
    random_statistic = None
    image_url = None  # URL for the image
    icon1_link = url_for('static', filename='images/favicon.ico')
    icon2_link = url_for('static', filename='images/favicon2.ico')
    special_name = None
    playlistsnameid = []

    icon_link = choice([icon1_link, icon2_link])

    if is_logged_in:
        access_token = session.get('access_token')
        user_data = users.find_one({'username': username})
        display_friend_stat = choice([True, False])  # Decide if we want to show a friend's stat
        
        if display_friend_stat:
            random_statistic, special_name, image_url = get_random_friend_statistic(user_data, users)
        
        if not random_statistic:
            # If no friend statistic was found or not displaying friend's stat, get the user's own statistic
            random_statistic, image_url, special_name = get_random_statistic(access_token)

        # Determine the background and text color based on the image
        if image_url:
            background_color = get_dominant_color(image_url)
            text_color = get_contrasting_text_color(background_color)
        else:
            background_color = '#defaultColor'
            text_color = '#defaultColor'
        

    return render_template('index.html', username=username, is_logged_in=is_logged_in,
                           random_statistic=random_statistic, image_url=image_url,
                           icon_link=icon_link, special_name=special_name,
                           background_color=background_color, text_color=text_color)

@app.route('/logout')
def logout():
    session.clear()  # Clears the user's session
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

@app.route('/about')
def about():
    is_logged_in = 'username' in session
    username = session.get('username', 'Guest')

    icon1_link = url_for('static', filename='images/favicon.ico')
    icon2_link = url_for('static', filename='images/favicon2.ico')

    icon_link = choice([icon1_link, icon2_link])
    return render_template('about.html', icon_link=icon_link, username=username, is_logged_in=is_logged_in)

@app.route('/stats')
def stats():
    is_logged_in = 'username' in session
    if 'access_token' not in session:
        flash("Please log in to view your stats.")
        return redirect('https://accounts.spotify.com/authorize?client_id=4f8a0448747a497e99591f5c8983f2d7&response_type=code&redirect_uri=http://127.0.0.1:8080/callback&show_dialogue=true&scope=user-read-private user-top-read playlist-read-private playlist-read-collaborative user-follow-read')

    icon1_link = url_for('static', filename='images/favicon.ico')
    icon2_link = url_for('static', filename='images/favicon2.ico')
    icon_link = choice([icon1_link, icon2_link])

    username = session.get('username', 'Guest')
    access_token = session['access_token']
    # Retrieve the selected time range from the request, default to 'medium_term'
    selected_time_range = request.args.get('time_range', 'short_term')
    genres = fetch_user_top_artists_genres(access_token, selected_time_range)
    image_data = generate_genre_pie_chart(genres)

    return render_template('stats.html', image_data=image_data, username=username, icon_link=icon_link, is_logged_in=is_logged_in)

@app.route('/friends')
def friends():
    is_logged_in = 'username' in session

    icon1_link = url_for('static', filename='images/favicon.ico')
    icon2_link = url_for('static', filename='images/favicon2.ico')
    icon_link = choice([icon1_link, icon2_link])

    friend_requests = [] 

    if 'access_token' in session:
        username = session.get('username')
        user_data = users.find_one({'username': username})
        if user_data:
            friends_list = user_data.get('friends', [])
            friend_requests = user_data.get('friendRequests', [])  # Get the list of friend requests

            profile_pics = {}
            for friend in friends_list:
                friend_data = users.find_one({'username': friend})
                if friend_data and 'profile_pic_url' in friend_data:
                    profile_pics[friend] = friend_data['profile_pic_url']
                else:
                    # Default or placeholder profile pic if not found
                    profile_pics[friend] = url_for('static', filename='images/favicon.ico') #need to get a default pfp, for now just using our logo

            return render_template('friends.html', friends=friends_list, profile_pics=profile_pics, icon_link=icon_link, username=username, is_logged_in=is_logged_in, friend_requests=friend_requests)
        else:
            flash("User data not found.")
            return redirect(url_for('index'))
    else:
        flash("Please log in to view your friends.")
        return redirect('https://accounts.spotify.com/authorize?client_id=4f8a0448747a497e99591f5c8983f2d7&response_type=code&redirect_uri=http://127.0.0.1:8080/callback&show_dialogue=true&scope=user-read-private user-top-read playlist-read-private playlist-read-collaborative user-follow-read')


@app.route('/profile/<username>')
def profile(username):
    # Fetch user data from db
    user_data = users.find_one({'username': username})
    if not user_data:
        return "User not found", 404
    
    access_token = session.get('access_token')
    # Check if the access token exists
    if not access_token:
        # If no access token, prompt a login
        flash("Please log in to view this page.", "warning")
        return redirect(url_for('login'))

    # Setup UI
    icon_link = choice([
        url_for('static', filename='images/favicon.ico'),
        url_for('static', filename='images/favicon2.ico')
    ])

    # Determine selected time range, default is all time
    selected_time_range = request.args.get('time_range', 'long_term')
    time_range_display = {'short_term': 'Last Month', 'medium_term': 'Last 6 Months', 'long_term': 'All Time'}.get(selected_time_range, 'All Time')

    # Fetch top artists and tracks for display
    top_artists = user_data.get(f'{selected_time_range}_artists', [])[:3]
    top_tracks = user_data.get(f'{selected_time_range}_tracks', [])[:3]

    # Other variables that need to be passed to profile page
    date_joined = user_data.get('date_joined', '')
    session_username = session.get('username')

    
    
    # Generate the genre breakdown pie chart
    
    artist_ids = [artist['id'] for artist in user_data.get(f'{selected_time_range}_artists', [])[:15]] # Limiting to 15 artists because doing all takes way too long
    #artist_ids = [artist['id'] for artist in user_data.get(f'{selected_time_range}_artists', [])] #This doesn't limit to 10 artists but makes load time long
    genre_pie_chart_base64 = generate_genre_pie_chart_from_db(artist_ids, access_token)

    # Render the profile template with all data
    return render_template('profile.html', user=user_data, top_artists=top_artists, top_tracks=top_tracks,
                           selected_time_range=selected_time_range, time_range_display=time_range_display,
                           date_joined=date_joined, is_logged_in='username' in session, genre_pie_chart=genre_pie_chart_base64,
                           icon_link=icon_link, 
                           username=session_username, #This should be profile you're viewing
                           session_username=session_username) # This should be the logged-in user's username 

@app.route('/discover')
def discover():
    if 'access_token' not in session:
        # User is not logged in, redirect to Spotify login
        return redirect('https://accounts.spotify.com/authorize?client_id={}&response_type=code&redirect_uri={}&scope={}'.format(
            CLIENT_ID, REDIRECT_URI, "user-read-private user-top-read playlist-read-private playlist-read-collaborative"
        ))

    # User is logged in
    username = session.get('username', 'Guest')
    access_token = session['access_token']


    # Render the Discover page template with fetched data
    return render_template('discover.html', username=username, is_logged_in=True)



@app.route('/addfriend', methods=['POST'])
def addfriend():
    if 'access_token' not in session:
        return {'message': 'Please log in to add friends.'}, 401

    data = request.json
    recipient_username = data.get('friendName')  # Username of the user to whom the request is being sent
    requester_username = session.get('username')  # Username of the user sending the request

    if recipient_username == requester_username:
        return {'message': 'You cannot add yourself as a friend.'}, 400

    recipient = users.find_one({'username': recipient_username})
    if not recipient:
        return {'message': 'Recipient user does not exist.'}, 404

    # Check if friend request is already sent, or already friends
    if requester_username in recipient.get('friendRequests', []) or requester_username in recipient.get('friends', []):
        return {'message': 'Friend request already sent or you are already friends.'}, 409

    # Add a friend request to the recipient
    result = users.update_one(
        {'username': recipient_username},
        {'$addToSet': {'friendRequests': requester_username}}
    )

    if result.modified_count == 1:
        return {'message': 'Friend request sent successfully.'}, 200
    else:
        return {'message': 'Failed to send friend request.'}, 500


@app.route('/acceptfriend', methods=['POST'])
def acceptfriend():
    if 'access_token' not in session:
        return {'message': 'Please log in to manage friend requests.'}, 401

    data = request.json
    requester_username = data.get('requesterUsername')  # Username of the user who sent the friend request
    recipient_username = session.get('username')  # Username of the user accepting the request

    # Fetch both the recipient and requester user
    recipient = users.find_one({'username': recipient_username})
    requester = users.find_one({'username': requester_username})

    if not requester or not recipient:
        return {'message': 'User not found.'}, 404

    # Check if the requester is in the recipient's friendRequests array
    if requester_username not in recipient.get('friendRequests', []):
        return {'message': 'Friend request not found.'}, 404

    # Update operations
    # Remove requester from friendrequests and add to friends
    users.update_one(
        {'username': recipient_username},
        {'$pull': {'friendRequests': requester_username},
         '$addToSet': {'friends': requester_username}} 
    )

    # Check if there is a mutual friend request
    if recipient_username in requester.get('friendRequests', []):
        # If mutual, add recipient to requester's friends list and remove the friend request
        users.update_one(
            {'username': requester_username},
            {'$pull': {'friendRequests': recipient_username},
             '$addToSet': {'friends': recipient_username}}  # Add to friends list
        )
    else:
        # If not mutual, add recipient to requester's friends list
        users.update_one(
            {'username': requester_username},
            {'$addToSet': {'friends': recipient_username}}
        )

    return {'message': 'Friend request accepted.'}, 200


@app.route('/declinefriend', methods=['POST'])
def declinefriend():
    if 'access_token' not in session:
        return {'message': 'Please log in to manage friend requests.'}, 401

    data = request.json
    requester_username = data.get('requesterUsername')
    recipient_username = session.get('username')

    # Just remove from requests
    result = users.update_one(
        {'username': recipient_username},
        {'$pull': {'friendRequests': requester_username}}
    )

    if result.modified_count == 1:
        return {'message': 'Friend request declined successfully.'}, 200
    else:
        return {'message': 'Failed to decline friend request.'}, 500


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
        sp = spotipy.Spotify(auth=access_token)


        # Fetch user's profile data
        headers = {'Authorization': f'Bearer {access_token}'}
        user_profile_response = requests.get('https://api.spotify.com/v1/me', headers=headers)
        
        if user_profile_response.status_code == 200:
            user_data = user_profile_response.json()
            username = user_data.get('display_name')
            userid = user_data.get('id')
            profile_pic_url = user_data['images'][0]['url'] if user_data['images'] else None
            
            # Dictionary to store top tracks and artists for each time range
            top_data = {}
            for time_range in ['short_term', 'medium_term', 'long_term']:
                # Fetch top artists and tracks
                top_artists = sp.current_user_top_artists(time_range=time_range, limit=50)
                top_tracks = sp.current_user_top_tracks(time_range=time_range, limit=50)

                # Format and store the data
                top_data[f'{time_range}_artists'] = [{'id': artist['id'], 'name': artist['name'], 'image_url': artist['images'][0]['url'] if artist['images'] else ''} for artist in top_artists['items']]
                top_data[f'{time_range}_tracks'] = [{'id': track['id'], 'name': track['name'], 'image_url': track['album']['images'][0]['url'] if track['album']['images'] else ''} for track in top_tracks['items']]
                    
            print("Recieved data from ", username)

            # For right now just using flask session to store username, if theres a better way to do this i'll change it later
            session['username'] = username
            session['access_token'] = access_token
            session['is_logged_in'] = True
                
                #Fetch user's playlists
            playlists_response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
            if playlists_response.status_code == 200:
                playlists_data = playlists_response.json()

                playlistsnameid = []
                #Process playlists data here
                for playlist in playlists_data['items']:
                    plist = (playlist['name'], playlist['id'])
                    playlistsnameid.append(plist)
            else:
                print("error")

            # Update user document with profile picture URL
            update_user_document(users, user_data['id'], user_data['display_name'], profile_pic_url, top_data, playlistsnameid)
        return redirect(url_for('index', username=username))

    else:
        print("Failed to retrieve access token. Status code:", response.status_code)
        print("Response:", response.json())
        return redirect('/error')  # Redirect to an error page that we haven't implemented yet

if __name__ == '__main__':
    app.run(port=8080)
