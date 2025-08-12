#!/usr/bin/env python3
"""
Robust music command parser and router
Catches music commands early before GPT can respond
"""
import re
from typing import Optional, Dict, Any

# Robust regex that catches various music command patterns
MUSIC_RE = re.compile(
    r"""^\s*
        (?:(?:hey|ok)\s+)?(?:jarvis[,!\s]+)?    # optional wake words
        (?:(?:please|can\s+you|could\s+you|would\s+you)\s+)?  # polite prelude
        (?:play|put\s+on|start|queue(?:\s+up)?)\s+
        (?P<query>.+?)                           # artist/song/genre
        (?:\s+on\s+(?P<service>spotify|youtube|yt|apple\s+music|google\s+music))?
        [\.\!\s]*$                               # trailing punctuation
    """,
    re.IGNORECASE | re.VERBOSE
)

def normalize_text(text: str) -> str:
    """Normalize whitespace & punctuation before intent detection"""
    if not text:
        return ""
    
    # Trim and collapse spaces
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common emoji and extra punctuation
    text = re.sub(r'[🎶🎵🎤🎧🔊🔉🔈🎼♪♫]', '', text)
    text = re.sub(r'[""''`]', '', text)
    
    return text

def parse_music_command(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse music commands with robust pattern matching
    Returns None if not a music command, otherwise returns parsed command dict
    """
    if not text:
        return None
    
    # Normalize the text first
    normalized = normalize_text(text)
    
    # Try the main music regex
    m = MUSIC_RE.match(normalized)
    if not m:
        return None
    
    # Extract service and normalize it
    service = (m.group("service") or "spotify").lower().replace(" ", "")
    if service == "yt":
        service = "youtube"
    elif service == "googlem usic":
        service = "youtube"  # Fallback for Google Music
    
    query = m.group("query").strip()
    
    # Additional validation - make sure query isn't empty or too generic
    if not query or len(query.strip()) < 2:
        return None
    
    # Exclude non-music queries that might match accidentally
    # Be more specific about exclusions to avoid false negatives
    non_music_words = ["video game", "movie file", "app store", "program files", "document folder"]
    query_lower = query.lower()
    if any(phrase in query_lower for phrase in non_music_words):
        return None
    
    # Additional check: if it's a very generic query that's clearly not music
    generic_non_music = ["the game", "a game", "some video", "a video", "my files", "the app"]
    if query_lower in generic_non_music:
        return None
    
    return {
        "query": query,
        "service": service,
        "original_command": text,
        "normalized_command": normalized
    }

def is_music_command(text: str) -> bool:
    """
    Quick check if text is a music command
    Use this for guardrails before calling GPT
    """
    if not text:
        return False
    
    # Belt-and-suspenders check
    if re.search(r"\b(play|put\s+on|queue(?:\s+up)?|start)\b", text, re.I):
        # Double-check it's actually a music command
        parsed = parse_music_command(text)
        return parsed is not None
    
    return False

def route_music_command(text: str) -> Optional[Dict[str, Any]]:
    """
    Route music command to the appropriate handler
    Returns result dict if handled, None if not a music command
    """
    parsed = parse_music_command(text)
    if not parsed:
        return None
    
    print(f"🎵 MUSIC ROUTER: Caught command '{text}'")
    print(f"🎵 MUSIC ROUTER: Parsed - Query: '{parsed['query']}', Service: '{parsed['service']}'")
    
    try:
        # Import here to avoid circular imports
        from google_home_direct import send_music_command
        
        # Route to the appropriate service
        if parsed["service"] == "spotify":
            result = send_music_command(parsed["query"], "spotify")
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": f"🎵 {result.get('message')}",
                    "routed": True,
                    "router": "music_spotify"
                }
            else:
                # Even if Google Home fails, try Spotify Web API
                try:
                    from spotify_client import search_and_play_spotify
                    spotify_result = search_and_play_spotify(parsed["query"])
                    return {
                        "success": True,
                        "message": f"🎵 Spotify: {spotify_result}",
                        "routed": True,
                        "router": "music_spotify_web"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"❌ Music playback failed: {str(e)}",
                        "routed": True,
                        "router": "music_failed"
                    }
        
        elif parsed["service"] == "youtube":
            # For YouTube, provide instruction since we don't have direct YT Music control
            return {
                "success": True,
                "message": f"🎵 For YouTube Music, please say 'Hey Google, play {parsed['query']} on YouTube Music' to your Google Home speaker.",
                "routed": True,
                "router": "music_youtube_instruction"
            }
        
        else:
            # Default to Spotify for unknown services
            result = send_music_command(parsed["query"], "spotify")
            return {
                "success": True,
                "message": f"🎵 {result.get('message')} (defaulted to Spotify)",
                "routed": True,
                "router": "music_default_spotify"
            }
    
    except Exception as e:
        print(f"❌ MUSIC ROUTER: Error routing command: {e}")
        return {
            "success": False,
            "message": f"❌ Music router error: {str(e)}",
            "routed": True,
            "router": "music_error"
        }

if __name__ == "__main__":
    # Quick smoke tests
    test_commands = [
        "play the beatles",
        "put on AC/DC on spotify", 
        "queue up some jazz",
        "start Hotel California on youtube",
        "please play nirvana",
        "play bob dylan on spotify",
        "not a music command",
        "play video game"  # should be excluded
    ]
    
    print("🧪 Testing Music Router")
    print("=" * 40)
    
    for cmd in test_commands:
        parsed = parse_music_command(cmd)
        is_music = is_music_command(cmd)
        print(f"\nCommand: '{cmd}'")
        print(f"Is Music: {is_music}")
        print(f"Parsed: {parsed}")
