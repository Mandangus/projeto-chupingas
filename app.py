from flask import Flask, redirect, request, session, url_for
import requests
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = "http://localhost:5000/callback"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"

# Authorization Scopes
SCOPES = "user-read-private playlist-read-private"
load_dotenv()

@app.route("/")
def home():
    return """
    <h1>Spotify Flask App</h1>
    <a href="/login">Log in with Spotify</a>
    """

@app.route("/login")
def login():
    # Spotify Authorization URL
    auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode({'response_type': 'code', 'client_id': SPOTIFY_CLIENT_ID, 'redirect_uri': SPOTIFY_REDIRECT_URI, 'scope': SCOPES})}"
    return redirect(auth_url)

@app.route("/callback")
def callback():
    # Retrieve authorization code
    code = request.args.get("code")
    if not code:
        return "Authorization failed. Please try again."

    # Exchange code for access token
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(SPOTIFY_TOKEN_URL, data=token_data)
    token_info = response.json()

    # Save access token in session
    session["access_token"] = token_info["access_token"]
    return redirect(url_for("playlists"))

@app.route("/playlists")
def playlists():
    # Access token from session
    token = session.get("access_token")
    if not token:
        return redirect(url_for("login"))

    # Fetch user's playlists
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{SPOTIFY_API_URL}/me/playlists", headers=headers)

    if response.status_code != 200:
        error_message = response.json().get('error', {}).get('message', 'Unknown error')
        return f"Failed to fetch playlists: {error_message}"

    # Ensure 'items' key exists
    response_data = response.json()
    playlists = response_data.get("items", [])

    if not playlists:
        return "<h1>No playlists found</h1><a href='/'>Go Home</a>"

    # Safeguard against None items
    playlists_html = "".join(
        f"<li>{p.get('name', 'Unnamed')} ({p.get('tracks', {}).get('total', 0)} tracks)</li>"
        for p in playlists if p is not None
    )

    return f"""
    <h1>Your Spotify Playlists</h1>
    <ul>{playlists_html}</ul>
    <a href="/">Go Home</a>
    """


if __name__ == "__main__":
    app.run(debug=True)
