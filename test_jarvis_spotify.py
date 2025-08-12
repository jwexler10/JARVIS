#!/usr/bin/env python3
"""
Test Jarvis Spotify integration
"""

import sys
import os

# Add current directory to path so we can import jarvis modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spotify_client import search_and_play_spotify, control_spotify_playback, list_spotify_devices

def test_spotify_integration():
    print("🧪 Testing Jarvis Spotify Integration")
    print("=" * 50)
    
    # Test 1: Device discovery
    print("1️⃣ Testing device discovery...")
    devices = list_spotify_devices()
    print(devices)
    print()
    
    if "Google Home" in devices or "🏠" in devices:
        print("✅ Google Home found! Testing commands...")
        
        # Test 2: Music search and play
        print("\n2️⃣ Testing music command recognition...")
        test_commands = [
            "play the beatles",
            "play some jazz music", 
            "play a chill playlist",
            "pause music",
            "skip this song"
        ]
        
        for cmd in test_commands:
            print(f"\n🎵 Testing: '{cmd}'")
            
            if any(word in cmd.lower() for word in ["pause", "skip", "stop", "next", "previous"]):
                result = control_spotify_playback(cmd)
            else:
                # Extract query from play command
                if cmd.startswith("play "):
                    query = cmd[5:].strip()
                    result = search_and_play_spotify(query)
                else:
                    result = search_and_play_spotify(cmd)
            
            print(f"   Result: {result}")
            
            # Ask user if they want to continue
            if "✅" in result:
                choice = input("   Continue testing? (y/n): ").strip().lower()
                if choice != 'y':
                    break
    else:
        print("⚠️ Google Home not found. Make sure it's connected to Spotify first.")
        print("💡 Run: python test_devices.py to connect Google Home")

if __name__ == "__main__":
    test_spotify_integration()
