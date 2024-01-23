import os
import base64
import requests
from flask import Flask, request, redirect, send_from_directory, session, url_for
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv()

# Read environment variables from .env
CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('SPOTIFY_REDIRECT_URI')


app = Flask(__name__)
app.secret_key = 'goodgroup'

@app.route('/')
def index():
    username = session.get('username', 'Guest')  # Default to 'Guest' if not logged in
    html_boilerplate_dir = os.path.abspath('../html-boilerplate/pages')
    return send_from_directory(html_boilerplate_dir, 'index.html')

@app.route('/login')
def login():
    html_boilerplate_pages_dir = os.path.abspath('../html-boilerplate/pages')
    return send_from_directory(html_boilerplate_pages_dir, 'login.html')

@app.route('/about')
def about():
    html_boilerplate_pages_dir = os.path.abspath('../html-boilerplate/pages')
    return send_from_directory(html_boilerplate_pages_dir, 'about.html')


@app.route('/images/<filename>')
def images(filename):
    images_dir = os.path.abspath('../html-boilerplate/images')
    return send_from_directory(images_dir, filename)

@app.route('/stylesheets/<filename>')
def stylesheet(filename):
    stylesheets_dir = os.path.abspath('../html-boilerplate/stylesheets')
    return send_from_directory(stylesheets_dir, filename)

@app.route('/fonts/<filename>')
def fonts(filename):
    fonts_dir = os.path.abspath('../html-boilerplate/fonts')
    return send_from_directory(fonts_dir, filename)


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

        return redirect(url_for('index', username=username))

    else:
        print("Failed to retrieve access token. Status code:", response.status_code)
        print("Response:", response.json())
        return redirect('/error')  # Redirect to an error page that we haven't implemented yet

if __name__ == '__main__':
    app.run(port=8080)
