#!/usr/bin/env python3
"""
Quick command to test Spotify integration after device setup
"""

from spotify_client import list_spotify_devices, search_and_play_spotify

def quick_test():
    print("🎵 Quick Spotify Test")
    print("=" * 30)
    
    # Check devices
    print("📱 Checking devices...")
    devices = list_spotify_devices()
    print(devices)
    
    if "Google Home" in devices or "🏠" in devices or "Active" in devices:
        print("\n✅ Active device found! Testing music command...")
        
        # Test the command that failed before
        result = search_and_play_spotify("some beatles")
        print(f"Result: {result}")
        
        if "✅" in result:
            print("\n🎉 SUCCESS! Spotify integration working perfectly!")
        else:
            print(f"\n⚠️ Issue: {result}")
    else:
        print("\n💡 No active devices. Please:")
        print("   1. Open Spotify on your phone")
        print("   2. Start playing music")
        print("   3. Connect to 'Jacy's Room speaker'")
        print("   4. Run this test again")

if __name__ == "__main__":
    quick_test()
