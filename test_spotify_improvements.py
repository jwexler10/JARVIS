#!/usr/bin/env python3
"""
Test script for Spotify improvements:
1. Question commands should not trigger music search
2. Album search should work properly
3. Personal playlist search should work
"""

from spotify_client import search_and_play_spotify, play_spotify_album, play_spotify_playlist

def test_improvements():
    print("🎵 Testing Spotify Improvements")
    print("=" * 50)
    
    # Test 1: Album search
    print("\n1. Testing album search:")
    print("   Command: 'abbey road album'")
    result = search_and_play_spotify("abbey road album")
    print(f"   Result: {result}")
    
    # Test 2: Personal playlist search
    print("\n2. Testing personal playlist search:")
    print("   Command: 'buckets of rain playlist'")
    result = search_and_play_spotify("buckets of rain playlist")
    print(f"   Result: {result}")
    
    # Test 3: Direct album function
    print("\n3. Testing direct album function:")
    print("   Command: 'abbey road'")
    result = play_spotify_album("abbey road")
    print(f"   Result: {result}")
    
    # Test 4: Direct personal playlist function
    print("\n4. Testing direct personal playlist function:")
    print("   Command: 'buckets of rain'")
    result = play_spotify_playlist("buckets of rain")
    print(f"   Result: {result}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed! Check results above.")
    print("\nNote: These tests will attempt to play music if devices are active.")
    print("Make sure your Google Home is connected to Spotify before running.")

if __name__ == "__main__":
    test_improvements()
