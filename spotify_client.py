# spotify_client.py
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def get_spotify_client():
    cfg = json.load(open("config.json"))
    sp_cfg = cfg["spotify"]
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=sp_cfg["client_id"],
        client_secret=sp_cfg["client_secret"],
        redirect_uri=sp_cfg["redirect_uri"],
        scope="user-modify-playback-state,user-read-playback-state",
        cache_path=".cache-spotify"
    ))

def play_spotify_track(query: str) -> str:
    sp = get_spotify_client()
    # 1) Search for the track
    results = sp.search(q=f"track:{query}", type="track", limit=1)
    items = results["tracks"]["items"]
    if not items:
        return f"❌ No track found for '{query}'."
    track = items[0]
    uri = track["uri"]
    name = track["name"]
    artists = ", ".join(a["name"] for a in track["artists"])
    # 2) Find an active device
    devices = sp.devices()["devices"]
    if not devices:
        return "❌ No active Spotify device found. Please open Spotify on one of your devices."
    device_id = devices[0]["id"]
    # 3) Start playback
    sp.start_playback(device_id=device_id, uris=[uri])
    return f"✅ Playing '{name}' by {artists}."

def play_spotify_playlist(query: str) -> str:
    sp = get_spotify_client()
    # 1) Search for the playlist
    pl = sp.search(q=f"playlist:{query}", type="playlist", limit=1)
    items = pl["playlists"]["items"]
    if not items:
        return f"❌ No playlist found for '{query}'."
    playlist = items[0]
    uri = playlist["uri"]
    name = playlist["name"]
    # 2) Find an active device
    devices = sp.devices()["devices"]
    if not devices:
        return "❌ No active Spotify device found."
    device_id = devices[0]["id"]
    # 3) Start playback of the playlist
    sp.start_playback(device_id=device_id, context_uri=uri)
    return f"✅ Playing playlist '{name}'."
