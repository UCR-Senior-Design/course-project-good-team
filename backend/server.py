import os
from flask import Flask, request, redirect, send_from_directory
import requests

app = Flask(__name__)

@app.route('/')
def index():
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



@app.route('/callback')
def callback():
    code = request.args.get('code')
    response = requests.post('https://accounts.spotify.com/api/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': 'http://127.0.0.1:8080/callback',
        'client_id': '4f8a0448747a497e99591f5c8983f2d7',
        'client_secret': 'b7ba599280d64d2ab32cf9cc9cbec47a'
    })
    access_token = response.json().get('access_token')
    return redirect('/?login=success')  # Redirect to a different page after login

if __name__ == '__main__':
    app.run(port=8080)
