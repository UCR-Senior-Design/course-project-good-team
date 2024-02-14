import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from io import BytesIO
import base64
import requests
from random import choice

def fetch_user_top_artists_genres(access_token, time_range='medium_term'):
    sp = spotipy.Spotify(auth=access_token)
    top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
    genre_count = defaultdict(int)

    for index, artist in enumerate(top_artists['items'], start=1):
        weight = 51 - index  # weights more listened to artists heavier in pie chart calculation
        for genre in artist['genres']:
            genre_count[genre] += weight

    return genre_count


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

    random_friend_username = choice(friends_list)  # Choose a random friend
    friend_data = users.find_one({'username': random_friend_username})

    if not friend_data:
        return None, None, None

    stat_type = choice(['tracks', 'artists'])
    time_range = choice(['short_term', 'medium_term', 'long_term'])
    time_range_text = {
        'short_term': 'in the last 4 weeks',
        'medium_term': 'in the last 6 months',
        'long_term': 'of all time'
    }[time_range]

    if not friend_data.get(f'{time_range}_{stat_type}'):
        return None, None, None

    random_stat = choice(friend_data[f'{time_range}_{stat_type}'])
    random_statistic = f"Your friend {random_friend_username}'s favorite {stat_type[:-1]} {time_range_text} is "
    special_name = random_stat['name']
    image_url = random_stat['image_url']

    return random_statistic, special_name, image_url