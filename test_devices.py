#!/usr/bin/env python3
"""
Test Spotify device discovery and playback
"""

from spotify_client import list_spotify_devices, play_spotify_track

def test_devices():
    print("🎵 Testing Spotify device discovery...")
    print()
    
    result = list_spotify_devices()
    print(result)
    print()
    
    if "Google Home" in result or "🏠" in result:
        print("🎉 Google Home found! Let's test playback...")
        
        # Test playing a song
        test_choice = input("Want to test playing a song on Google Home? (y/n): ").strip().lower()
        if test_choice == 'y':
            song = input("Enter a song to play (or press Enter for 'test'): ").strip()
            if not song:
                song = "test"
            
            print(f"\n🎵 Trying to play '{song}'...")
            play_result = play_spotify_track(song)
            print(play_result)
    else:
        print("💡 Next steps:")
        print("   1. Open Spotify on your phone")
        print("   2. Start playing any song")
        print("   3. Tap the 'Connect to a device' icon (speaker with wifi)")
        print("   4. Select your Google Home from the list")
        print("   5. Run this test again")
        print()
        print("🔄 After connecting, run: python test_devices.py")

if __name__ == "__main__":
    test_devices()
