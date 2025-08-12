#!/usr/bin/env python3
"""
Standalone music-first command processor
Bypasses jarvis.py import issues by handling music commands first
"""
import sys
import os

# Add the jarvis directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def process_command_music_first(command: str, conversation_history: list, text_mode: bool = False, speaker: str = "Unknown", emotion: str = None):
    """
    Process command with MUSIC-FIRST routing to avoid GPT fallback
    """
    print(f"🚨 MUSIC_FIRST_PROCESSOR: Called with '{command}'")
    
    # 🎵 FRONT-LOADED MUSIC ROUTER - Catch music commands BEFORE anything else
    try:
        from music_router import route_music_command, is_music_command
        
        if is_music_command(command):
            print(f"🎵 MUSIC_FIRST: Command '{command}' identified as music command")
            
            # Route the music command and return immediately - NO FALLBACK
            music_result = route_music_command(command)
            if music_result and music_result.get("routed"):
                print(f"🎵 MUSIC_FIRST: Successfully routed, router={music_result.get('router')}")
                return music_result["message"], False
            else:
                print(f"🎵 MUSIC_FIRST: Failed to route music command")
                return "❌ Music command detected but routing failed. Please try again.", False
        else:
            print(f"🔧 MUSIC_FIRST: Not a music command, falling back to regular jarvis...")
    
    except Exception as e:
        print(f"❌ MUSIC_FIRST ERROR: {e}")
    
    # Fall back to regular jarvis processing for non-music commands
    try:
        # Try to import and call the regular process_command
        from jarvis import process_command as jarvis_process_command
        return jarvis_process_command(command, conversation_history, text_mode, speaker, emotion)
    except Exception as e:
        print(f"❌ JARVIS FALLBACK ERROR: {e}")
        return f"❌ System error: {str(e)}", False

def test_music_first():
    """Test the music-first processor"""
    print("🧪 Testing Music-First Processor")
    print("=" * 50)
    
    test_commands = [
        "play the beatles",
        "play bob dylan on spotify", 
        "what's the weather like"  # Non-music command
    ]
    
    for cmd in test_commands:
        print(f"\n🎵 Testing: '{cmd}'")
        print("-" * 30)
        
        conversation = [{"role": "system", "content": "You are JARVIS, an AI assistant."}]
        response, should_exit = process_command_music_first(cmd, conversation, text_mode=True, speaker="Jason")
        
        print(f"Response: {response}")
        
        # Check for success indicators
        if "🎵" in response or "spotify" in response.lower():
            print("✅ SUCCESS: Music command routed!")
        elif "i'm an ai" in response.lower() or "as an ai" in response.lower():
            print("❌ FAILED: Fell through to GPT!")
        else:
            print("⚠️ UNCLEAR: Non-music or error response")

if __name__ == "__main__":
    test_music_first()
