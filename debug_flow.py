#!/usr/bin/env python3
"""
Debug script to trace exactly what happens with music commands in jarvis.py
"""

def test_music_command_flow():
    command = "play some bob dylan on spotify"
    cmd_lower = command.lower()
    
    print(f"🎵 Testing command: '{command}'")
    print(f"🎵 Lowercase: '{cmd_lower}'")
    print()
    
    # Test each section of jarvis.py process_command in order
    
    # Section 1: Exit keywords
    print("=== Section 1: Exit Keywords ===")
    exit_keywords = ["exit", "quit", "stop", "goodbye", "thanks", "thank you"]
    if cmd_lower in exit_keywords:
        print("✅ MATCHES exit keywords - would return early")
        return
    else:
        print("❌ No match - continues")
    print()
    
    # Section 2: File operations (simplified check)
    print("=== Section 2: File Operations ===")
    file_keywords = ["list files", "read file", "delete file", "move file"]
    music_keywords = ["play", "pause", "stop", "resume", "skip", "next", "previous", "music", "song", "artist", "album", "playlist", "spotify", "youtube", "beatles", "rolling stones"]
    
    # Check if it would be detected as file operation
    has_music_keyword = any(music_keyword in cmd_lower for music_keyword in music_keywords)
    cmd_starts_with_play = cmd_lower.startswith("play ")
    has_spotify = "on spotify" in cmd_lower
    
    print(f"Has music keyword: {has_music_keyword}")
    print(f"Starts with 'play ': {cmd_starts_with_play}")
    print(f"Has 'on spotify': {has_spotify}")
    
    # The music exclusion logic should prevent file operation classification
    is_music_request = (
        has_music_keyword or
        cmd_starts_with_play or
        has_spotify
    )
    
    print(f"Should be excluded from file operations: {is_music_request}")
    
    if is_music_request:
        print("❌ Should NOT be detected as file operation - continues")
    else:
        print("✅ Could be detected as file operation - would return early")
        return
    print()
    
    # Section 3: System commands
    print("=== Section 3: System Commands ===")
    if cmd_lower.startswith(("open ", "launch ", "start ")):
        print("✅ MATCHES system commands - would return early")
        return
    else:
        print("❌ No match - continues")
    print()
    
    # Section 4: Weather
    print("=== Section 4: Weather ===")
    if "weather" in cmd_lower:
        print("✅ MATCHES weather - would return early")
        return
    else:
        print("❌ No match - continues")
    print()
    
    # Section 5: Web search
    print("=== Section 5: Web Search ===")
    if cmd_lower.startswith(("search for ", "look up ", "google ")):
        print("✅ MATCHES web search - would return early")
        return
    else:
        print("❌ No match - continues")
    print()
    
    # Section 6: Google Services
    print("=== Section 6: Google Services ===")
    google_keywords = ["email", "gmail", "mail", "message", "drive", "files", "documents"]
    calendar_starters = ["list", "show", "check"]
    calendar_keywords = ["calendar", "events", "appointments"]
    
    has_google_keyword = any(keyword in cmd_lower for keyword in google_keywords)
    has_calendar_pattern = (cmd_lower.startswith(tuple(calendar_starters)) and 
                           any(keyword in cmd_lower for keyword in calendar_keywords))
    
    print(f"Has Google keyword: {has_google_keyword}")
    print(f"Has calendar pattern: {has_calendar_pattern}")
    
    if has_google_keyword or has_calendar_pattern:
        print("✅ MATCHES Google services - would call handle_google_command()")
        print("⚠️ If handle_google_command() returns None/False, execution continues")
        print("⚠️ If handle_google_command() returns a result, would return early")
    else:
        print("❌ No match - continues")
    print()
    
    # Section 7: Music (the one we want to hit!)
    print("=== Section 7: Direct Spotify Music Control ===")
    music_phrases = ["play ", "stop music", "pause music", "resume music", "next song", "previous song", "skip"]
    question_words = ["what about", "what is", "tell me about", "do you know", "have you heard"]
    
    has_music_phrase = any(phrase in cmd_lower for phrase in music_phrases)
    has_question_word = any(question_word in cmd_lower for question_word in question_words)
    
    print(f"Has music phrase: {has_music_phrase}")
    print(f"Has question word: {has_question_word}")
    print(f"Overall condition: {has_music_phrase and not has_question_word}")
    
    if has_music_phrase and not has_question_word:
        print("✅ SHOULD MATCH music section!")
        
        # Check specific play command logic
        if cmd_lower.startswith("play "):
            query = command[5:].strip()
            print(f"Would extract query: '{query}'")
            
            # Clean up query
            spotify_indicators = ["on spotify", "from spotify", "via spotify", "using spotify"]
            for indicator in spotify_indicators:
                if indicator in query.lower():
                    query = query.lower().replace(indicator, "").strip()
                    break
            
            print(f"Clean query: '{query}'")
            
            # Check skip conditions
            skip_words = ["video", "movie", "game", "app", "program"]
            should_skip = any(skip_word in query.lower() for skip_word in skip_words)
            print(f"Should skip: {should_skip}")
            
            if not should_skip:
                print("✅ WOULD CALL Google Home integration!")
                print("🎵 send_music_command(query, 'spotify')")
            else:
                print("⚠️ Would skip due to skip words")
        else:
            print("ℹ️ Not a 'play' command, would handle as control command")
    else:
        print("❌ No match - continues to fallback GPT")
    print()

if __name__ == "__main__":
    test_music_command_flow()
