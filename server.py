import base64
import io
import os
from collections import Counter, defaultdict
from datetime import timedelta, datetime
from random import choice

import random
import certifi
import pymongo
import requests
import spotipy
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from PIL import Image
from pymongo import MongoClient
from spotipy.oauth2 import SpotifyOAuth

from db_utils import update_user_document
from image_utils import get_contrasting_text_color, get_dominant_color
from spotify_utils import (generate_genre_pie_chart_from_db, get_random_friend_statistic, 
                            get_random_statistic, get_user_friends, get_top_song_from_global_playlist, update_match_score,
                            get_random_song, find_mutual_favorites, calculate_match_score, retrieve_or_update_match_score,
                            analyze_playlist)

load_dotenv()

# Read environment variables from .env
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URL = os.environ.get('SPOTIFY_REDIRECT_URL_RENDER') #CHANGE BETWEEN LOCAL AND RENDER FOR DEPLOYMENT AND DEVELOPMENT
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
MONGO_URL = os.environ.get('MONGO_URL')

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.permanent_session_lifetime = timedelta(minutes=30)  # Basically saves your login for 30 minutes

try:
    client = pymongo.MongoClient(MONGO_URL, tlsAllowInvalidCertificates=True) # This is not a permanent solution, and is just for development. We should not allow invalid certificates during deployment.
    
#URI error is thrown 
except pymongo.errors.ConfigurationError:
    print("An Invalid URI host error was received.")
    #Idk if this line should be in here specifically
    sys.exit(1)

mydb = client.Friendify
users = mydb["Users"]
artists = mydb["Artists"]
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
                           background_color=background_color, text_color=text_color, REDIRECT_URL=REDIRECT_URL)


@app.route('/logout')
def logout():
    session.clear()  # Clears the user's session
    return redirect(url_for('index'))


@app.route('/about')
def about():
    is_logged_in = 'username' in session
    username = session.get('username', 'Guest')

    icon1_link = url_for('static', filename='images/favicon.ico')
    icon2_link = url_for('static', filename='images/favicon2.ico')

    icon_link = choice([icon1_link, icon2_link])
    return render_template('about.html', icon_link=icon_link, username=username, is_logged_in=is_logged_in, REDIRECT_URL=REDIRECT_URL)


@app.route('/friends')
def friends():
    is_logged_in = 'username' in session
    icon_link = choice([url_for('static', filename='images/favicon.ico'),
                        url_for('static', filename='images/favicon2.ico')])

    if 'access_token' in session:
        username = session.get('username')
        user_data = users.find_one({'username': username})
        if user_data:
            friends_list = user_data.get('friends', [])
            friend_requests = user_data.get('friendRequests', [])
            friends_details = []

            for friend in friends_list:
                friend_data = users.find_one({'username': friend})
                match_score = user_data.get('match_scores', {}).get(friend, {}).get('score')

                # If match_score is None, calculate and update it
                if match_score is None:
                    print(f"Calculating match score for {username} and {friend}")
                    match_score = calculate_match_score(user_data, friend_data)
                    # Update match score in database for both users
                    update_match_score(users, username, friend, match_score)

                profile_pic_url = friend_data.get('profile_pic_url', url_for('static', filename='images/default_profile_pic.png'))
                friends_details.append({
                    'username': friend,
                    'match_score': match_score if match_score is not None else 'N/A',  # Fallback to 'N/A' if needed
                    'profile_pic_url': profile_pic_url
                })

            return render_template('friends.html', friends_details=friends_details, is_logged_in=is_logged_in, 
                                   friend_requests=friend_requests, icon_link=icon_link, username=username, REDIRECT_URL=REDIRECT_URL)
        else:
            return redirect(url_for('index'))
    else:
        return redirect('https://accounts.spotify.com/authorize?client_id=4f8a0448747a497e99591f5c8983f2d7&response_type=code&redirect_uri=' + REDIRECT_URL + '&show_dialogue=true&scope=user-read-private user-top-read')


@app.route('/profile/<username>')
def profile(username):
    # Fetch user data from db for the profile being visited
    profile_data = users.find_one({'username': username})
    if not profile_data:
        return "User not found", 404

    access_token = session.get('access_token')
    if not access_token:
        # If no access token, prompt a login
        return redirect(url_for('login'))

    # Setup UI
    icon_link = choice([
        url_for('static', filename='images/favicon.ico'),
        url_for('static', filename='images/favicon2.ico')
    ])

    selected_time_range = request.args.get('time_range', 'long_term')
    time_range_display = {'short_term': 'Last Month', 'medium_term': 'Last 6 Months', 'long_term': 'All Time'}.get(selected_time_range, 'All Time')

    # Fetch top artists, tracks for the visited profile
    top_artists = profile_data.get(f'{selected_time_range}_artists', [])[:3]
    top_tracks = profile_data.get(f'{selected_time_range}_tracks', [])[:3]

    sp = spotipy.Spotify(auth=access_token)
    playlists = sp.user_playlists(profile_data['id'], limit=50)
    playlists_data = [{'name': playlist['name'], 'image_url': playlist['images'][0]['url'] if playlist['images'] else None, 'id': playlist['id']} for playlist in playlists['items']]

    date_joined = profile_data.get('date_joined', '')
    session_username = session.get('username')

    # Generate the genre breakdown pie chart
    artist_ids = [artist['id'] for artist in profile_data.get(f'{selected_time_range}_artists', [])[:25]]
    genre_pie_chart_base64 = generate_genre_pie_chart_from_db(artist_ids, access_token, artists, users, username, selected_time_range)

    # Compute mutual favorites between the logged-in user and the visited profile
    logged_in_user_data = users.find_one({'username': session['username']})
    mutual_favorites = find_mutual_favorites(logged_in_user_data, profile_data)


    #MATCH SCORE GENERATION
    print("----MATCH SCORE GENERATION SUMMARY----")
    start_time = datetime.now()
    if session.get('username') == username:
        # dont need to calculate match score for own profile
        match_score = None
    else:
        # Retrieve or calculate match score
        match_score = retrieve_or_update_match_score(users, logged_in_user_data, profile_data)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"Friendify Match Score: {match_score}")
    print(f"Match score calculation took {duration.total_seconds()} seconds.")
    print("--------------------------------------")
    print(f"\n")

    return render_template('profile.html', user=profile_data, top_artists=top_artists, top_tracks=top_tracks,
                           selected_time_range=selected_time_range, time_range_display=time_range_display,
                           date_joined=date_joined, is_logged_in='username' in session, genre_pie_chart=genre_pie_chart_base64,
                           icon_link=icon_link, playlists_data=playlists_data, mutual_favorites=mutual_favorites,
                           profile_username=username, session_username=session_username, match_score=match_score,
                           logged_in_user_profile_pic_url=logged_in_user_data['profile_pic_url'], REDIRECT_URL=REDIRECT_URL)
 


@app.route('/discover')
def discover():

    icon_link = choice([
        url_for('static', filename='images/favicon.ico'),
        url_for('static', filename='images/favicon2.ico')
    ])
    username = session.get("username")
    session_username = session.get('username')
    user_data = users.find_one({'username': username})
    if not user_data:
        return "User not found", 404
    if 'access_token' not in session:
        # User is not logged in, redirect to Spotify login
        return redirect('https://accounts.spotify.com/authorize?client_id={}&response_type=code&redirect_uri={}&scope={}'.format(
            CLIENT_ID, REDIRECT_URL, "user-read-private user-top-read&show_dialog=true"
        ))

    # User is logged in
    username = session.get('username', 'Guest')
    access_token = session['access_token']
    is_logged_in = 'access_token' in session

    random_song_requested = request.args.get('random_song', 'false') == 'true'
    access_token = session['access_token']
    
    if random_song_requested:
        # Fetch a random song using a function that you will define
        song_details = get_random_song(access_token)
    else:
        # Fetch the top song details as before
        song_details = get_top_song_from_global_playlist(access_token)

    return render_template('discover.html', username = username, song_details=song_details, random_song=random_song_requested, user=user_data, icon_link=icon_link, session_username=session_username, is_logged_in=is_logged_in)

@app.route('/discover/friend-queue')
def get_friend_queue():
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({'error': 'User not authenticated'}), 401

    username = session.get('username')
    user_friends = get_user_friends(users, username)

    track_popularity = {}
    for friend in user_friends:
        for time_range in ['short_term_tracks', 'medium_term_tracks', 'long_term_tracks']:
            friend_tracks = friend.get(time_range, [])
            for track in friend_tracks:
                track_id = track['id']
                if track_id not in track_popularity:
                    track_popularity[track_id] = {
                        'count': 0, 
                        'track_name': track['name'], 
                        'image_url': track['image_url'],
                        'friends': set(),
                        'random_order': random.random()  # Assign a random number
                    }
                track_popularity[track_id]['count'] += 1
                track_popularity[track_id]['friends'].add(friend['username'])

    for track_info in track_popularity.values():
        track_info['friends'] = list(track_info['friends'])
        track_info['unique_friends'] = len(track_info['friends'])

    # Sort by unique friends, then total count, and finally random_order
    sorted_tracks = sorted(track_popularity.values(), key=lambda x: (-x['unique_friends'], -x['count'], x['random_order']))

    return jsonify(sorted_tracks)

@app.route('/analyze_playlist', methods=['GET', 'POST'])
def analyze_playlist_route():
    if 'access_token' not in session:
        # Redirect to login if the user is not logged in
        return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=session['access_token'])
    username = session.get('username')  # Get the username from session
    user_data = users.find_one({'username': username})  # Fetch user data from the database

    if request.method == 'POST':
        playlist_url = request.json.get('playlist_url')  # Access the JSON data sent by the client
        print(f"Received playlist URL for analysis: {playlist_url}")  # Debug print
        
        if playlist_url:
            # Pass the Spotify client, playlist URL, user data, and artists collection to the analyze function
            analysis_result = analyze_playlist(sp, playlist_url, user_data, artists)
            print(f"Analysis result: {analysis_result}")  # Debug print
            return jsonify(analysis_result)
    
    # If GET request or no playlist URL provided, redirect back to the discover page
    return redirect(url_for('discover'))




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
    

@app.route('/removefriend', methods=['POST'])
def removefriend():
    if 'access_token' not in session:
        return {'message': 'Please log in to manage friends.'}, 401

    data = request.json
    friend_username = data.get('friendUsername')
    current_username = session.get('username')

    if friend_username == current_username:
        return {'message': 'You cannot remove yourself.'}, 400

    # Remove each other from friends list
    result1 = users.update_one(
        {'username': current_username},
        {'$pull': {'friends': friend_username}}
    )

    result2 = users.update_one(
        {'username': friend_username},
        {'$pull': {'friends': current_username}}
    )

    if result1.modified_count == 1 and result2.modified_count == 1:
        return {'message': 'Friend removed successfully.'}, 200
    else:
        return {'message': 'Failed to remove friend.'}, 500



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
        'redirect_uri': REDIRECT_URL
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
