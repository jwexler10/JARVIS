#!/usr/bin/env python3
"""
Direct test of music router integration - bypasses import caching
"""
import sys
import os
import importlib

# Add the jarvis directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force fresh imports
if 'jarvis' in sys.modules:
    importlib.reload(sys.modules['jarvis'])
if 'music_router' in sys.modules:
    importlib.reload(sys.modules['music_router'])

# Import fresh
from jarvis import process_command

def test_direct():
    """Direct test of music router integration"""
    print("🧪 DIRECT MUSIC ROUTER TEST (bypassing caching)")
    print("=" * 50)
    
    cmd = "play the beatles"
    print(f"\n🎵 Testing: '{cmd}'")
    print("-" * 30)
    
    conversation = [{"role": "system", "content": "You are JARVIS, an AI assistant."}]
    
    print(f"🔧 ABOUT TO CALL process_command with: '{cmd}'")
    response, should_exit = process_command(cmd, conversation, text_mode=True, speaker="Jason")
    
    print(f"\n📤 RESPONSE: {response}")
    print(f"📤 SHOULD_EXIT: {should_exit}")
    
    # Check for music router success
    if "🎵" in response or "spotify" in response.lower():
        print("✅ SUCCESS: Music router caught the command!")
    elif "i'm an ai" in response.lower() or "as an ai" in response.lower():
        print("❌ FAILED: Command fell through to GPT!")
    else:
        print("⚠️  UNCLEAR: Response unclear")

if __name__ == "__main__":
    test_direct()
