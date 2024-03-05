import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
from collections import Counter
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


def generate_genre_pie_chart(genres):
    # Sort genres and select top N
    top_genres = dict(sorted(genres.items(), key=lambda item: item[1], reverse=True)[:10])
    
    # Create figure and axis
    fig, ax = plt.subplots()
    # Set background color of chart
    fig.patch.set_facecolor('#373737')  #just matching the background of the html page for now, probably can do something better
    ax.set_facecolor('#373737')
    
    # Font for chart, can mess around with this
    font_properties = FontProperties()
    font_properties.set_family('sans-serif')
    font_properties.set_weight('bold')
    
    # Generate pie chart with customizations
    wedges, texts, autotexts = ax.pie(top_genres.values(), labels=top_genres.keys(), autopct='%1.1f%%', startangle=90,
                                      textprops=dict(color="w", fontproperties=font_properties))  # Set text color to white
    
    # Make sure the pie chart is a circle
    ax.axis('equal')
    
    # Change the font color of the percentages
    for autotext in autotexts:
        autotext.set_color('black')  # Change as needed
    
    # Save to buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    
    # Base64 encoding
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return image_base64

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

    return genres

def generate_genre_pie_chart_from_db(artist_ids, access_token, artists):
    genres = fetch_genres_for_artist_ids(artist_ids, access_token, artists)
    genre_count = Counter(genres)
    
    # Check if there are genres lol
    if not genre_count:
        return None
    
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
