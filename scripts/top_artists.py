import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Initialize Spotify API
SPOTIPY_CLIENT_ID = '4f8a0448747a497e99591f5c8983f2d7'
SPOTIPY_CLIENT_SECRET = 'b7ba599280d64d2ab32cf9cc9cbec47a'
SPOTIPY_REDIRECT_URI = 'http://localhost:8080/callback'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="user-top-read"))

top_artists = sp.current_user_top_artists(limit=50, time_range='long_term')

for artist in top_artists['items']:
    print(artist['name'])