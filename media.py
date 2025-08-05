import os
import random

# Folder where you store your tracks
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "music")

def list_tracks():
    """Return all audio files in the music folder."""
    if not os.path.isdir(MUSIC_DIR):
        return []
    return [
        f for f in os.listdir(MUSIC_DIR)
        if f.lower().endswith((".mp3", ".wav", ".ogg", ".m4a", ".flac"))
    ]

def play_track(track_name: str) -> str:
    """
    If track_name matches a file, open it with the default app.
    Otherwise pick a random file.
    """
    tracks = list_tracks()
    if not tracks:
        return "❌ No music files found in the music folder."

    # Try to match by substring
    for t in tracks:
        if track_name.lower() in t.lower():
            path = os.path.join(MUSIC_DIR, t)
            try:
                os.startfile(path)
                return f"✅ Playing {t}"
            except Exception as e:
                return f"❌ Error playing {t}: {e}"

    # No match → random
    choice = random.choice(tracks)
    path = os.path.join(MUSIC_DIR, choice)
    try:
        os.startfile(path)
        return f"🔀 Playing random track: {choice}"
    except Exception as e:
        return f"❌ Error playing {choice}: {e}"
