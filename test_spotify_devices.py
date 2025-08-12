#!/usr/bin/env python3
"""
Test script to check Spotify devices and attempt direct playback to Google Home
"""

import sys
sys.path.append('.')

from spotify_client import get_spotify_client, list_spotify_devices

def main():
    print("🎵 Testing Spotify device discovery...")
    
    try:
        # List all available devices
        device_list = list_spotify_devices()
        print(device_list)
        
        # Get raw device data
        sp = get_spotify_client()
        devices = sp.devices()["devices"]
        
        print(f"\n🔍 Raw device data:")
        for device in devices:
            print(f"  - Name: {device['name']}")
            print(f"    Type: {device['type']}")
            print(f"    ID: {device['id']}")
            print(f"    Active: {device['is_active']}")
            print(f"    Volume: {device.get('volume_percent', 'N/A')}%")
            print()
        
        # Check if Google Home is in the list
        google_home_devices = []
        for device in devices:
            device_name = device["name"].lower()
            if any(keyword in device_name for keyword in ["google", "home", "speaker", "nest"]):
                google_home_devices.append(device)
        
        if google_home_devices:
            print(f"✅ Found {len(google_home_devices)} Google Home device(s):")
            for device in google_home_devices:
                print(f"  - {device['name']} ({device['type']})")
        else:
            print("❌ No Google Home devices found in Spotify device list")
            print("💡 Make sure Spotify is installed and logged in on your Google Home")
            print("💡 Try saying 'Play music on Spotify' to your Google Home first")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
