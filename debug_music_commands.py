#!/usr/bin/env python3
"""
Debug script to test music command processing logic
"""

def test_music_command_logic():
    """Test the same logic that jarvis.py uses for music commands"""
    
    test_commands = [
        "play beatles on spotify",
        "play rolling stones", 
        "play the beatles",
        "play some music",
        "pause music",
        "stop music"
    ]
    
    for command in test_commands:
        print(f"\n🎵 Testing: '{command}'")
        cmd_lower = command.lower()
        
        # Test the exact condition from jarvis.py line 751-755
        condition1 = any(phrase in cmd_lower for phrase in [
            "play ", "stop music", "pause music", "resume music", "next song", "previous song", "skip"
        ])
        
        condition2 = not any(question_word in cmd_lower for question_word in [
            "what about", "what is", "tell me about", "do you know", "have you heard"
        ])
        
        full_condition = condition1 and condition2
        
        print(f"   Contains music phrases: {condition1}")
        print(f"   No question words: {condition2}")
        print(f"   Should match music handler: {full_condition}")
        
        if full_condition:
            # Test the specific play command logic
            if cmd_lower.startswith("play "):
                query = command[5:].strip()
                print(f"   ✅ Would extract query: '{query}'")
                
                # Test for platform indicators
                spotify_indicators = ["on spotify", "from spotify", "via spotify", "using spotify"]
                clean_query = query
                for indicator in spotify_indicators:
                    if indicator in query.lower():
                        clean_query = query.lower().replace(indicator, "").strip()
                        break
                
                print(f"   ✅ Clean query: '{clean_query}'")
                
                # Test for skip words
                skip_words = ["video", "movie", "game", "app", "program"]
                should_skip = any(skip_word in clean_query.lower() for skip_word in skip_words)
                print(f"   Should skip: {should_skip}")
                
                if not should_skip:
                    print(f"   ✅ WOULD CALL: search_and_play_spotify('{clean_query}')")
                else:
                    print(f"   ❌ Would skip - contains skip words")
            else:
                print(f"   ✅ WOULD CALL: control_spotify_playback('{command}')")
        else:
            print(f"   ❌ Would not match music handler")

if __name__ == "__main__":
    test_music_command_logic()
