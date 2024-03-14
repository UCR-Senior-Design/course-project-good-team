import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from collections import Counter
from scipy.spatial.distance import cdist
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from io import BytesIO
import base64
import requests
from random import choice
from datetime import datetime, timedelta
import time
import random
import string


def find_mutual_favorites(user1, user2, users_collection):
    # Fetch user documents from the database
    user1_data = users_collection.find_one({'username': user1})
    user2_data = users_collection.find_one({'username': user2})

    if not user1_data or not user2_data:
        return None  # One or both users not found

    # Function to extract unique identifiers from artists/tracks lists
    def extract_ids(items):
        return {item['id'] for item in items if 'id' in item}  # Replace 'id' with the actual identifier key

    # Combine all unique artist and track IDs from all time ranges
    user1_ids = extract_ids(user1_data.get('short_term_artists', []) + user1_data.get('medium_term_artists', []) + user1_data.get('long_term_artists', []) +
                            user1_data.get('short_term_tracks', []) + user1_data.get('medium_term_tracks', []) + user1_data.get('long_term_tracks', []))
    user2_ids = extract_ids(user2_data.get('short_term_artists', []) + user2_data.get('medium_term_artists', []) + user2_data.get('long_term_artists', []) +
                            user2_data.get('short_term_tracks', []) + user2_data.get('medium_term_tracks', []) + user2_data.get('long_term_tracks', []))

    # Find mutual favorites by intersecting the sets of IDs
    mutual_favorites = user1_ids.intersection(user2_ids)

    return list(mutual_favorites)  # Return a list of mutual favorite IDs


def get_random_statistic(access_token):
    random_statistic = None
    image_url = None
    special_name = None

    # Choose randomly between artist and track, and among time ranges
    stat_type = choice(['track', 'artist'])
    time_range = choice(['short_term', 'medium_term', 'long_term'])
    time_range_text = {
        'short_term': 'in the last 4 weeks',
        'medium_term': 'in the last 6 months',
        'long_term': 'of all time'
    }[time_range]

    headers = {'Authorization': f'Bearer {access_token}'}
    
    if stat_type == 'track':
        top_tracks_response = requests.get(
            f'https://api.spotify.com/v1/me/top/tracks?time_range={time_range}&limit=1',
            headers=headers
        )
        if top_tracks_response.status_code == 200:
            top_track = top_tracks_response.json().get('items', [])[0]
            random_statistic = f"Your most played track {time_range_text} is "
            special_name = top_track['name']
            image_url = top_track['album']['images'][0]['url']

    elif stat_type == 'artist':
        top_artists_response = requests.get(
            f'https://api.spotify.com/v1/me/top/artists?time_range={time_range}&limit=1',
            headers=headers
        )
        if top_artists_response.status_code == 200:
            top_artist = top_artists_response.json().get('items', [])[0]
            random_statistic = f"Your most played artist {time_range_text} is "
            special_name = top_artist['name']
            image_url = top_artist['images'][0]['url']

    return random_statistic, image_url, special_name

def get_random_friend_statistic(user_data, users):
    friends_list = user_data.get('friends', [])
    if not friends_list:
        return None, None, None

    random_friend_username = choice(friends_list)  # Choose random friend
    friend_data = users.find_one({'username': random_friend_username})

    if not friend_data:
        return None, None, None

    stat_type = choice(['tracks', 'artists'])  # Choose between artist or track
    time_range = choice(['short_term', 'medium_term', 'long_term'])
    time_range_text = {
        'short_term': 'in the last 4 weeks',
        'medium_term': 'in the last 6 months',
        'long_term': 'of all time'
    }[time_range]

    stat_list = friend_data.get(f'{time_range}_{stat_type}', [])
    if not stat_list:
        return None, None, None

    # take top value from array
    first_stat = stat_list[0]
    random_statistic = f"Your friend {random_friend_username}'s favorite {stat_type[:-1]} {time_range_text} is "
    special_name = first_stat['name']
    image_url = first_stat['image_url']

    return random_statistic, special_name, image_url

def fetch_genres_for_artist_ids(artist_ids, access_token, artists):
    start_time = time.time()  # Record the start time
    sp = spotipy.Spotify(auth=access_token)
    genres = []
    cache_hit_count = 0  # number of artists we already have cached
    new_artist_count = 0  # number artists not found in our cache and will be added
    refreshed_artists_count = 0  # artists who we refreshed data on because data is old 
    new_artists_added = []  # new artists we are adding to cache
    refresh_threshold = 90  # after this many days we will pull genre data again from spotify regardless of if it is cached in order to ensure data is not too obselete

    for artist_id in artist_ids:
        artist_data = artists.find_one({'id': artist_id})
        # Check if artist's genres are already in the database and not too old
        if artist_data and 'genres' in artist_data and 'last_updated' in artist_data:
            last_updated = artist_data['last_updated']
            if (datetime.now() - last_updated).days < refresh_threshold:
                genres.extend(artist_data['genres'])
                cache_hit_count += 1
                continue  # Skip to the next artist_id

        # Fetch from Spotify and update the database if genres are missing or data is too old
        try:
            artist_info = sp.artist(artist_id)
            artist_genres = artist_info['genres']
            genres.extend(artist_genres)
            # fetch from spotify and update artist data with genres and timestamp
            update_data = {'$set': {'genres': artist_genres, 'last_updated': datetime.now()}}
            # Update the database with new artist information or refreshed data
            artists.update_one({'id': artist_id}, update_data, upsert=True)
            if artist_data:
                refreshed_artists_count += 1  # increment if it was a refresh
            else:
                new_artist_count += 1  # increment if we are adding a new artist
                new_artists_added.append(artist_info['name']) 
        except Exception as e:
            print(f"Error fetching genres for artist {artist_id}: {e}")

    # Print the summary information
    print(f"\n")
    print(f"-----PIE CHART GENERATION SUMMARY-----")
    print(f"Retrieved {cache_hit_count} artists from cache.")
    if refreshed_artists_count > 0:
        print(f"Refreshed genres for {refreshed_artists_count} artists.")
    print(f"Added {new_artist_count} new artists to cache.")
    if new_artists_added:  # Check if there are any new artists added
        print("New artists added to the cache: ", ", ".join(new_artists_added))
    
    end_time = time.time()  # Record the end time
    execution_time = end_time - start_time  # calculate total time spent fetching artist data for pie chart
    print(f"Total time to fetch data: {execution_time:.2f} seconds")
    print(f"--------------------------------------")
    print(f"\n")

    return genres

def generate_genre_pie_chart_from_db(artist_ids, access_token, artists, users, username, time_range):
    genres = fetch_genres_for_artist_ids(artist_ids, access_token, artists)
    genre_count = Counter(genres)
    
    # Check if there are genres lol
    if not genre_count:
        return None
    
    # Prepare the field name based on the time range
    genre_field = f"{time_range}_genres"  # e.g., "short_term_genres"

    # Update user's document with genre data for the specified time range
    users.update_one({'username': username}, {'$set': {genre_field: dict(genre_count)}})

    labels, sizes = zip(*genre_count.most_common(8))  # Limit to top 10 genres for readability
    
    # Generate pie chart
    plt.style.use('dark_background')
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontname': 'sans-serif'})
    ax.axis('equal') 
    
    # Set label color to match slice color
    for text, wedge in zip(texts, wedges):
        text.set_color(wedge.get_facecolor())
        text.set_fontsize(10)  # Adjust fontsize as needed

    # Percentage color
    for autotext in autotexts:
        autotext.set_color('black') 

    # Convert pie chart to a PNG image bytes
    buf = BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    plt.close(fig)
    buf.seek(0)
    
    # Encode the image to base64 string
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    
    return image_base64

def get_top_song_from_global_playlist(access_token):
    # Initialize Spotipy with user's access token
    sp = spotipy.Spotify(auth=access_token)

    # Spotify's Global Top 50 playlist ID
    playlist_id = '37i9dQZEVXbNG2KDcFcKOF'
    
    # Fetch the first track from the playlist
    results = sp.playlist_tracks(playlist_id, limit=1)
    top_track = results['items'][0]['track']
    
    # Extract the necessary details
    song_name = top_track['name']
    track_id = top_track['id']
    artist_name = top_track['artists'][0]['name']  # Assuming only one artist for simplicity
    album_image_url = top_track['album']['images'][0]['url']  # The first image is usually the largest
    
    return {
        'song_name': song_name,
        'artist_name': artist_name,
        'album_image_url': album_image_url,
        'spotify_url': f"https://open.spotify.com/track/{track_id}"
    }


def get_random_song(access_token):
    # Initialize the Spotify client
    sp = spotipy.Spotify(auth=access_token)
    
    # Generate a random query string
    query = ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))
    
    # Make a search request to Spotify
    results = sp.search(q=query, type='track', limit=50)
    tracks = results['tracks']['items']
    
    if tracks:
        # Select a random track from the search results
        random_track = random.choice(tracks)
        song_details = {
            'song_name': random_track['name'],
            'artist_name': random_track['artists'][0]['name'],
            'album_image_url': random_track['album']['images'][0]['url'],
            'spotify_url': random_track['external_urls']['spotify']
        }
        return song_details
    else:
        return None
    
def find_best_match(user_data, friend_data, category):
    mutual_favorites = {}
    for term in ['short_term', 'medium_term', 'long_term']:
        user_list = user_data.get(f'{term}_{category}', [])
        friend_list = friend_data.get(f'{term}_{category}', [])
    
        user_dict = {item['id']: {'name': item['name'], 'image_url': item.get('image_url', '')} for item in user_list}
        friend_dict = {item['id']: index for index, item in enumerate(friend_list, start=1)}
        
        best_score = float('inf')
        best_match = None
        
        # Find mutual favorites by looking through each user array and finding best match
        for index, user_item in enumerate(user_list, start=1):
            friend_index = friend_dict.get(user_item['id'])
            if friend_index:
                combined_score = index + friend_index
                if combined_score < best_score:
                    best_score = combined_score
                    best_match = user_item['id']
                    
        if best_match:
            mutual_favorites[term] = user_dict[best_match]
            mutual_favorites[term]['term'] = term.replace('_', ' ')
    
    return mutual_favorites

def find_mutual_favorites(user_data, friend_data):
    artists = find_best_match(user_data, friend_data, 'artists')
    tracks = find_best_match(user_data, friend_data, 'tracks')
    return {'artists': artists, 'tracks': tracks}


def get_user_friends(users, username):
    user = users.find_one({'username': username}, {'_id': 0, 'friends': 1})
    if not user or 'friends' not in user:
        return []

    friend_usernames = user['friends']
    # Fetch friend details. Adjust fields as necessary based on your needs.
    friend_details = list(users.find({'username': {'$in': friend_usernames}},
                                     {'_id': 0, 'username': 1, 'short_term_tracks': 1, 'medium_term_tracks': 1, 'long_term_tracks': 1}))

    return friend_details


def calculate_match_score(user_data, friend_data):
    # Initialize scores
    artist_score, track_score, genre_score = 0, 0, 0

    # Calculate overlap in artists and tracks for each time range
    for time_range in ['short_term', 'medium_term', 'long_term']:
        user_artists = {artist['id'] for artist in user_data.get(f'{time_range}_artists', [])}
        friend_artists = {artist['id'] for artist in friend_data.get(f'{time_range}_artists', [])}
        artist_overlap = len(user_artists.intersection(friend_artists))
        artist_score += (artist_overlap ** 1.75) / max(len(user_artists), 1) #ampify score

        user_tracks = {track['id'] for track in user_data.get(f'{time_range}_tracks', [])}
        friend_tracks = {track['id'] for track in friend_data.get(f'{time_range}_tracks', [])}
        track_overlap = len(user_tracks.intersection(friend_tracks))
        track_score += (track_overlap ** 1.75) / max(len(user_tracks), 1) #ampify score
        
    # Calculate genre overlap
    for time_range in ['short_term', 'medium_term', 'long_term']:
        user_genres = Counter(user_data.get(f'{time_range}_genres', {}))
        friend_genres = Counter(friend_data.get(f'{time_range}_genres', {}))
        
        # Calculate Jaccard similarity for genres
        intersection = sum((user_genres & friend_genres).values())
        union = sum((user_genres | friend_genres).values())
        genre_score += intersection / max(union, 1)

    # Normalize scores
    artist_score = (artist_score / 3) * 100  # Divide by 3 to get average, then multiply by 100 for percentage
    track_score = (track_score / 3) * 100
    genre_score = (genre_score / 3) * 100
    
    # Combine scores with custom weights
    combined_score = (artist_score * 0.35 + track_score * 0.35 + genre_score * 0.3)

    # Normalize combined score to be between 0 and 100
    match_score = min(max(combined_score, 0), 100)

    return int(match_score)


def update_match_score(users, username, friend_username, match_score):
    now = datetime.utcnow()
    # Update for the user viewing the profile
    users.update_one(
        {'username': username},
        {'$set': {
            f'match_scores.{friend_username}.score': match_score,
            f'match_scores.{friend_username}.last_updated': now
        }}
    )
    # Update for the friend whose profile is being viewed
    users.update_one(
        {'username': friend_username},
        {'$set': {
            f'match_scores.{username}.score': match_score,
            f'match_scores.{username}.last_updated': now
        }}
    )




def retrieve_or_update_match_score(users, user_data, friend_data):
    username = user_data['username']
    friend_username = friend_data['username']

    # Check if a recent match score already exists
    match_info = user_data.get('match_scores', {}).get(friend_username, {})
    if match_info and 'last_updated' in match_info and (datetime.utcnow() - match_info['last_updated']).days < 7:
        print ("Recent match score found")
        return match_info['score']

    # Calculate new match score
    print ("Calculating new match score")
    match_score = calculate_match_score(user_data, friend_data)

    # Update match scores in both users' documents
    update_match_score(users, username, friend_username, match_score)

    return match_score

def analyze_playlist(sp, playlist_url, user_data, artists_collection):
    playlist_id = playlist_url.split('/')[-1].split('?')[0]

    # Fetch playlist details for name, creator, and image URL
    playlist_details = sp.playlist(playlist_id)
    playlist_name = playlist_details['name']
    playlist_creator = playlist_details['owner']['display_name']
    playlist_image_url = playlist_details['images'][0]['url'] if playlist_details['images'] else None

    playlist_tracks_data = sp.playlist_tracks(playlist_id)


    # Ensuring track['track'] is not None and filtering tracks with valid URIs
    track_ids = [
        track['track']['id'] for track in playlist_tracks_data['items']
        if track['track'] and track['track']['id'] and track['track']['uri'] and 'spotify' in track['track']['uri']
    ]

    # Ensuring artist['uri'] is not None before checking for 'spotify' in URI
    artist_ids = set([
        artist['id'] for track in playlist_tracks_data['items'] if track['track'] 
        for artist in track['track']['artists'] 
        if artist and artist.get('uri') and 'spotify' in artist['uri']
    ])

    # Initialize genres list
    genres = []

    # Check each artist ID in the local database first
    for artist_id in artist_ids:
        artist_data = artists_collection.find_one({'id': artist_id})
        if artist_data:
            genres.extend(artist_data['genres'])
        else:
            # If artist not found in local DB, fetch from Spotify and update local DB
            artist_info = sp.artist(artist_id)
            new_genres = artist_info['genres']
            genres.extend(new_genres)
            artists_collection.update_one({'id': artist_id}, {'$set': {'genres': new_genres, 'last_updated': pd.Timestamp.now()}}, upsert=True)

    genre_count = Counter(genres)
    most_common_genres = genre_count.most_common(5)

    # Fetch and calculate audio features
    playlist_features_list = sp.audio_features(track_ids)
    df_playlist = pd.DataFrame([features for features in playlist_features_list if features])
    avg_features = df_playlist[['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']].mean().to_dict()

    analysis_result = {
        'average_features': avg_features,
        'most_common_genres': most_common_genres,
        'playlist_name': playlist_name,
        'playlist_creator': playlist_creator,
        'playlist_image_url': playlist_image_url,
    }

    # Fetch user's short_term_tracks and calculate their average features
    short_term_track_ids = [track['id'] for track in user_data.get('short_term_tracks', [])]
    if short_term_track_ids:
        user_features_list = sp.audio_features(short_term_track_ids)
        df_user = pd.DataFrame([features for features in user_features_list if features])
        avg_user_features = df_user[['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']].mean().to_dict()
    else:
        avg_user_features = {}

    # Calculate distances between user's average features and playlist tracks' features
    if avg_user_features:
        distances = cdist([list(avg_user_features.values())], df_playlist[['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']], metric='euclidean')
        closest_indices = distances.argsort()[0][:3]
        recommended_track_ids = df_playlist.iloc[closest_indices]['id'].tolist()
    else:
        recommended_track_ids = []

    # Fetch track details for recommendations
    recommended_tracks = sp.tracks(recommended_track_ids)['tracks']
    recommended_songs = [{
        'album_cover': track['album']['images'][0]['url'] if track['album']['images'] else None,
        'title': track['name'],
        'artists': ', '.join(artist['name'] for artist in track['artists'])
    } for track in recommended_tracks]

    analysis_result['recommended_songs'] = recommended_songs
    return analysis_result
