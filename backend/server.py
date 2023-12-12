import os
from flask import Flask, request, redirect, send_from_directory
import requests

app = Flask(__name__)

@app.route('/')
def index():
    html_boilerplate_dir = os.path.abspath('../html-boilerplate')
    return send_from_directory(html_boilerplate_dir, 'index.html')

@app.route('/login')
def login():
    html_boilerplate_pages_dir = os.path.abspath('../html-boilerplate/pages')
    return send_from_directory(html_boilerplate_pages_dir, 'login.html')

@app.route('/callback')
def callback():
    code = request.args.get('code')
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://127.0.0.1:5000/callback',
        'client_id': '4f8a0448747a497e99591f5c8983f2d7',
        'client_secret': 'b7ba599280d64d2ab32cf9cc9cbec47a'
    })
    access_token = response.json().get('access_token')
    return redirect('/login')  # Redirect to a different page after login

if __name__ == '__main__':
    app.run()