#!/usr/bin/env python3
"""
Quick test of Jarvis music command routing
Enhanced to test the front-loaded music router
"""
import sys
import os

# Add the jarvis directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis import process_command
from music_router import parse_music_command, is_music_command

def test_music_commands():
    """Test that Jarvis music commands route to Google Home integration"""
    print("🧪 Testing Jarvis Music Command Routing (Enhanced)")
    print("=" * 60)
    
    # Test the music router directly first
    print("\n🔍 PHASE 1: Testing Music Router Parser")
    print("-" * 40)
    
    test_commands = [
        "play bob dylan on spotify",
        "play the beatles", 
        "play some jazz music",
        "put on AC/DC on spotify",
        "queue up some jazz",
        "start Hotel California on youtube",
        "please play nirvana",
        "not a music command",  # Should NOT be detected
        "play video game"       # Should NOT be detected
    ]
    
    for cmd in test_commands:
        is_music = is_music_command(cmd)
        parsed = parse_music_command(cmd)
        print(f"Command: '{cmd}'")
        print(f"  Is Music: {is_music}")
        print(f"  Parsed: {parsed}")
        print()
    
    # Test full Jarvis integration
    print("\n🔍 PHASE 2: Testing Full Jarvis Integration")
    print("-" * 40)
    
    music_test_commands = [
        "play bob dylan on spotify",
        "play the beatles",
        "play some jazz music"
    ]
    
    for cmd in music_test_commands:
        print(f"\n🎵 Testing: '{cmd}'")
        print("-" * 30)
        
        try:
            # Create a minimal conversation history (just system prompt)
            conversation = [{"role": "system", "content": "You are JARVIS, an AI assistant."}]
            
            # Test the command processing
            response, should_exit = process_command(cmd, conversation, text_mode=True, speaker="Jason")
            
            print(f"Response: {response}")
            
            # Check for deterministic routing indicators (NOT GPT fallback)
            music_indicators = ["🎵", "spotify", "playing", "family room", "google home", "✅"]
            gpt_fallback_indicators = ["i'm an ai", "as an ai", "i cannot", "i'm not able", "text-based", "don't have the ability"]
            
            has_music_indicators = any(indicator.lower() in response.lower() for indicator in music_indicators)
            has_gpt_fallback = any(indicator.lower() in response.lower() for indicator in gpt_fallback_indicators)
            
            if has_gpt_fallback:
                print("❌ FAILED: Command fell through to GPT fallback!")
                print(f"   GPT fallback detected in response: {response}")
            elif has_music_indicators:
                print("✅ SUCCESS: Command routed to music system!")
            else:
                print("⚠️  UNCLEAR: Response doesn't clearly indicate music routing or GPT fallback")
                
        except Exception as e:
            print(f"❌ Error testing command: {e}")
            import traceback
            traceback.print_exc()
    
    # Test non-music commands to ensure they still work
    print("\n🔍 PHASE 3: Testing Non-Music Commands (Should Not Be Intercepted)")
    print("-" * 40)
    
    non_music_commands = [
        "what's the weather like",
        "tell me a joke",
        "what time is it"
    ]
    
    for cmd in non_music_commands:
        print(f"\n🗣️  Testing: '{cmd}'")
        is_music = is_music_command(cmd)
        print(f"Should NOT be music: {not is_music}")
        if is_music:
            print("❌ FAILED: Non-music command incorrectly identified as music!")
        else:
            print("✅ PASSED: Non-music command correctly identified")

if __name__ == "__main__":
    test_music_commands()
