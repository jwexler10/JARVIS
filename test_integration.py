#!/usr/bin/env python3
"""
Test individual Jarvis music command handling
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_client import search_and_play_spotify, control_spotify_playback

def test_music_commands():
    print("🧪 Testing Jarvis Music Command Integration")
    print("=" * 60)
    
    # Test the commands that Jarvis will recognize
    test_commands = [
        ("play the beatles", "Music search and play"),
        ("play some jazz", "General music search"),
        ("play a chill playlist", "Playlist search (fixed)"),
        ("pause music", "Playback control"),
        ("skip this song", "Track control"),
        ("resume music", "Resume playback")
    ]
    
    for command, description in test_commands:
        print(f"\n🎵 Testing: '{command}' ({description})")
        
        try:
            if any(word in command.lower() for word in ["pause", "skip", "stop", "resume", "next", "previous"]):
                result = control_spotify_playback(command)
            else:
                # Extract query from play command
                if command.startswith("play "):
                    query = command[5:].strip()
                    result = search_and_play_spotify(query)
                else:
                    result = search_and_play_spotify(command)
            
            print(f"   ✅ Result: {result}")
            
            # Only pause for successful music plays
            if "✅ Playing" in result:
                input("   Press Enter to continue...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎉 All tests completed!")
    print("\n💡 These are the exact commands Jarvis will now handle:")
    print("   • 'play [any song/artist]' → Direct Spotify search and play")
    print("   • 'play [playlist name] playlist' → Playlist search and play") 
    print("   • 'pause music' → Pause current playback")
    print("   • 'skip this song' → Skip to next track")
    print("   • 'resume music' → Resume playback")
    print("   • And more!")

if __name__ == "__main__":
    test_music_commands()
