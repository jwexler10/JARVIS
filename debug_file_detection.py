#!/usr/bin/env python3
"""
Debug script to test file operation detection logic
"""

def test_file_operation_logic():
    """Test the same logic that jarvis.py uses for file operation detection"""
    
    test_commands = [
        "play beatles on spotify",
        "play rolling stones", 
        "play the beatles",
        "play some music",
        "list files",
        "show me python files",
        "open file.txt"
    ]
    
    # Copy the exact logic from jarvis.py
    file_keywords = [
        "list files", "list all", "show files", "find files", "files in", "what files",
        "read file", "read the file", "open file", "show me the contents",
        "create file", "write file", "save file", "make a file",
        "delete file", "remove file", "move file", "rename file",
        "copy file", "directory", "folder", "recent files", "newest files", 
        "latest files", "most recent", "recent thing", "newest thing", "latest thing",
        "what's in", "whats in", "show me", "contents of", "files on", "what's on",
        # Add semantic search keywords
        "search files", "search for files", "find documents", "look for files",
        "show me pdfs", "find pdfs", "python files", "audio files", "image files",
        "configuration files", "config files", "class files", "homework files"
    ]
    
    file_extensions = [
        ".txt", ".py", ".json", ".csv", ".md", ".png", ".jpg", ".jpeg", 
        ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
        ".zip", ".rar", ".mp3", ".mp4", ".avi", ".mov", ".exe", ".bat"
    ]
    
    file_action_words = ["delete", "remove", "erase", "trash", "open", "move", "copy", "rename", "edit", "read"]
    file_reference_words = ["file", "folder", "directory", "document", "image", "picture", "photo", "video"]
    web_keywords = ["research", "website", "page", "fandom", "wiki", "url", "link", "web", "site", "online", "internet", "browser", "visit", "go to", "navigate", "browse"]
    
    # Add music exclusion keywords
    music_keywords = ["play", "pause", "stop", "resume", "skip", "next", "previous", "music", "song", "artist", "album", "playlist", "spotify", "youtube", "beatles", "rolling stones"]
    
    for command in test_commands:
        print(f"\n🔍 Testing: '{command}'")
        cmd_lower = command.lower()
        
        # Test primary file operation detection
        condition1 = any(keyword in cmd_lower for keyword in file_keywords)
        condition2 = any(ext in cmd_lower for ext in file_extensions)
        condition3 = ("open" in cmd_lower and any(ext in cmd_lower for ext in file_extensions))
        
        primary_detection = condition1 or condition2 or condition3
        
        print(f"   File keywords match: {condition1}")
        if condition1:
            matching_keywords = [kw for kw in file_keywords if kw in cmd_lower]
            print(f"   → Matching keywords: {matching_keywords}")
        
        print(f"   File extensions match: {condition2}")
        if condition2:
            matching_extensions = [ext for ext in file_extensions if ext in cmd_lower]
            print(f"   → Matching extensions: {matching_extensions}")
        
        print(f"   Open + extension match: {condition3}")
        print(f"   Primary detection result: {primary_detection}")
        
        if primary_detection:
            # Test web exclusion
            has_web_keyword = any(web_keyword in cmd_lower for web_keyword in web_keywords)
            is_web_request = (
                has_web_keyword or
                "http" in cmd_lower or
                "www." in cmd_lower or
                ".com" in cmd_lower or
                ".org" in cmd_lower or
                "search for" in cmd_lower or
                "look up" in cmd_lower or
                "find me" in cmd_lower or
                ("open" in cmd_lower and ("page" in cmd_lower or "site" in cmd_lower))
            )
            
            if is_web_request:
                print(f"   ❌ EXCLUDED as web request")
                final_result = False
            else:
                # Check for music exclusion
                has_music_keyword = any(music_keyword in cmd_lower for music_keyword in music_keywords)
                is_music_request = (
                    has_music_keyword or
                    cmd_lower.startswith("play ") or
                    any(phrase in cmd_lower for phrase in [
                        "on spotify", "on youtube", "stop music", "pause music", "resume music", 
                        "next song", "previous song", "skip song", "volume"
                    ])
                )
                
                if is_music_request:
                    print(f"   ❌ EXCLUDED as music request")
                    final_result = False
                else:
                    print(f"   ✅ FINAL RESULT: FILE OPERATION")
                    final_result = True
        else:
            # Test secondary detection (action + file reference)
            is_question = cmd_lower.startswith(("what", "where", "which", "how", "why", "when", "who", "do you see", "can you see", "tell me about"))
            
            if not is_question:
                has_action = any(action in cmd_lower for action in file_action_words)
                has_file_ref = any(ref in cmd_lower for ref in file_reference_words)
                
                secondary_detection = has_action and has_file_ref
                
                print(f"   Secondary detection - Action words: {has_action}")
                if has_action:
                    matching_actions = [action for action in file_action_words if action in cmd_lower]
                    print(f"   → Matching actions: {matching_actions}")
                
                print(f"   Secondary detection - File references: {has_file_ref}")
                if has_file_ref:
                    matching_refs = [ref for ref in file_reference_words if ref in cmd_lower]
                    print(f"   → Matching references: {matching_refs}")
                
                print(f"   Secondary detection result: {secondary_detection}")
                final_result = secondary_detection
            else:
                print(f"   Excluded as question")
                final_result = False
        
        print(f"   🎯 FINAL: {'FILE OPERATION' if final_result else 'NOT FILE OPERATION'}")

if __name__ == "__main__":
    test_file_operation_logic()
