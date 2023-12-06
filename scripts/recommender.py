import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from collections import defaultdict

def extract_playlist_id(playlist_link):
    """Extract playlist ID from the Spotify link"""
    return playlist_link.split('/')[-1].split('?')[0]

def get_recommendations(playlist_id):
    # Fetch the user-specified playlist
    playlist_tracks = sp.playlist_tracks(playlist_id)
    playlist_track_ids = [track['track']['id'] for track in playlist_tracks['items']]
    playlist_features = sp.audio_features(playlist_track_ids)
    df_playlist = pd.DataFrame(playlist_features)

    # Merge user's top tracks and the playlist tracks
    combined_df = pd.concat([df_top_tracks, df_playlist], ignore_index=True)

    # Extract and standardize the features
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(combined_df[features])

    # Train k-NN
    model = NearestNeighbors(metric='cosine', algorithm='brute')
    model.fit(scaled_data)

    # Dictionary to tally the counts of recommended tracks
    recommendation_tally = defaultdict(int)

    # Get recommendations for all top 50 songs
    for idx in range(50):  # loop over top 50 tracks
        _, indices = model.kneighbors([scaled_data[idx]], n_neighbors=6)
        
        for i in range(1, len(indices[0])):
            if indices[0][i] < len(df_top_tracks):
                continue
            recommended_song = playlist_tracks['items'][indices[0][i] - len(df_top_tracks)]['track']['name']
            recommendation_tally[recommended_song] += 1

    # Sort the recommended songs by tally and return the top 5
    sorted_recommendations = sorted(recommendation_tally.items(), key=lambda x: x[1], reverse=True)[:5]

    return sorted_recommendations

# Initialize Spotify API
SPOTIPY_CLIENT_ID = '4f8a0448747a497e99591f5c8983f2d7'
SPOTIPY_CLIENT_SECRET = 'b7ba599280d64d2ab32cf9cc9cbec47a'
SPOTIPY_REDIRECT_URI = 'http://localhost:8080/callback'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="user-top-read"))

# Get top tracks for the user
top_tracks = sp.current_user_top_tracks(limit=50)
track_ids = [track['id'] for track in top_tracks['items']]
track_features = sp.audio_features(track_ids)
df_top_tracks = pd.DataFrame(track_features)
features = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'tempo', 'valence']

while True:
    playlist_link = input("Enter the Spotify playlist link to get recommendations from: ")
    playlist_id = extract_playlist_id(playlist_link)

    recommendations = get_recommendations(playlist_id)
    
    print("\nTop 5 most recommended songs:")
    for idx, (song, count) in enumerate(recommendations, 1):
        # print(f"{idx}. {song} (Recommended {count} times)")
        print(f"{idx}. {song}")

    choice = input("\nEnter 'new' to enter a new playlist or 'exit' to quit: ")

    if choice == 'new':
        continue
    elif choice == 'exit':
        break
    else:
        print("Invalid input. Try again.")
