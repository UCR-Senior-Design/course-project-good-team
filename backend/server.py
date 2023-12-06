from flask import Flask, request, redirect
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('html-boilerplate', 'index.html')

@app.route('/login')
def login():
    # This is where you'd serve your login.html
    return send_from_directory('html-boilerplate', 'login.html')

@app.route('/callback')
def callback():
    code = request.args.get('code')
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://localhost:8080/callback',
        'client_id': '4f8a0448747a497e99591f5c8983f2d7',
        'client_secret': 'b7ba599280d64d2ab32cf9cc9cbec47a'
    })
    access_token = response.json().get('access_token')
    # Handle the access token (store it, create session, etc.)
    return redirect('/some_page_after_login')  # Redirect to a different page after login

if __name__ == '__main__':
    app.run()
