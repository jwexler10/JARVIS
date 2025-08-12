#!/usr/bin/env python3
"""
Minimal test that bypasses dependency issues
"""
import sys
import os

# Add the jarvis directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import only the music router (no jarvis.py dependencies)
from music_router import parse_music_command, is_music_command, route_music_command

def test_minimal():
    """Test music router without jarvis.py dependencies"""
    print("🧪 MINIMAL MUSIC ROUTER TEST")
    print("=" * 40)
    
    cmd = "play the beatles"
    print(f"\n🎵 Testing: '{cmd}'")
    print("-" * 30)
    
    # Test parser
    is_music = is_music_command(cmd)
    parsed = parse_music_command(cmd)
    print(f"Is Music: {is_music}")
    print(f"Parsed: {parsed}")
    
    if is_music:
        # Test router
        result = route_music_command(cmd)
        print(f"Router Result: {result}")
        
        if result and result.get("routed"):
            print("✅ SUCCESS: Music router works!")
            print(f"Message: {result['message']}")
        else:
            print("❌ FAILED: Music router didn't route properly")
    else:
        print("❌ FAILED: Command not detected as music")

if __name__ == "__main__":
    test_minimal()
