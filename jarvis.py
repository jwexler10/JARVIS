import os
import time
import sys
import select
import argparse
from datetime import datetime, timedelta
import dateparser
import difflib
import json
import openai

# Fix OpenMP library conflict (common with FAISS + other ML libraries)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from wake_word import detect_wake_word
from audio_input import record_audio_with_vad
from transcribe import load_api_key, transcribe_audio
# Try ElevenLabs first, fallback to regular TTS
try:
    from eleven_tts import speak  
except ImportError:
    print("⚠️ ElevenLabs not available, using regular TTS")
    from tts import speak
from llm import chat_with_history
from agent_core import chat_with_agent, chat_with_agent_enhanced, handle_clarification
from weather import get_weather, get_intelligent_weather
from commands import open_application
from search import search_web
from spotify_client import play_spotify_track, play_spotify_playlist
from speaker_id import identify_speaker
from google_commands import handle_google_command
from tools import open_website  # Import the new web automation function
from google_calendar import create_event, delete_event, list_events, update_event  # Direct import for function calling
from memory_advanced import retrieve_relevant_simple as retrieve_relevant, retrieve_relevant as retrieve_relevant_advanced, auto_remember_async, load_memory_cache, schedule_index_rebuild, has_speaker_memories, schedule_summarization  # Updated imports
from memory_store import init_db, add_rating  # New encrypted memory store
from memory_index import MemoryIndex, get_memory_index  # New vector index
from pattern_learning import get_preferred_times  # Pattern learning for scheduling preferences
from recommender import _recommender  # Recommendation engine
from emotion import detect_emotion  # Emotion recognition
from file_index import file_index  # File semantic search
import threading
import asyncio

# Multi-turn context settings
MAX_HISTORY = 8

# Global initialization flags to avoid repeated loading
_api_loaded = False
_memory_loaded = False
_memory_store_initialized = False
_memory_index_initialized = False
_recommender_initialized = False
_file_index_initialized = False
_summarization_scheduled = False
_initialization_lock = threading.Lock()

# Conversation mode settings
VERBOSE_MODE = False  # Set to True for debug output, False for natural conversation

# Define function schemas for OpenAI function calling
calendar_functions = [
    {
        "name": "create_event",
        "description": "Schedule a new event on the user's Google Calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title, e.g. 'Haircut'"},
                "start_time": {"type": "string", "description": "ISO 8601 start datetime"},
                "end_time": {"type": "string", "description": "ISO 8601 end datetime"},
                "description": {"type": "string", "description": "Optional notes"}
            },
            "required": ["title", "start_time"]
        }
    },
    {
        "name": "list_events",
        "description": "List upcoming events in a date range to find events to cancel or modify.",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "ISO 8601 start date to search from"},
                "end_date": {"type": "string", "description": "ISO 8601 end date to search until"},
                "max_results": {"type": "integer", "description": "Maximum number of events to return (default 10)"}
            },
            "required": ["start_date", "end_date"]
        }
    },
    {
        "name": "update_event",
        "description": "Update an existing event by its ID. Use this to move events to different dates/times.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The Google Calendar event ID to update"},
                "title": {"type": "string", "description": "New event title (optional)"},
                "start_time": {"type": "string", "description": "New ISO 8601 start datetime (optional)"},
                "end_time": {"type": "string", "description": "New ISO 8601 end datetime (optional)"},
                "description": {"type": "string", "description": "New event description (optional)"}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "delete_event",
        "description": "Cancel an existing event by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The Google Calendar event ID to delete"}
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "get_current_time",
        "description": "Get the current date and time information.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "open_website",
        "description": (
            "Enhanced AI-powered web content analysis. "
            "If query looks like a URL (http(s)://), opens it directly. "
            "Otherwise, searches the web for the query and opens the first result. "
            "Uses AI to intelligently summarize content or answer specific questions about it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term or full URL"},
                "selector": {"type": "string", "description": "CSS selector to extract text (optional)"},
                "question": {"type": "string", "description": "Specific question to answer about the content (optional)"}
            },
            "required": ["query"]
        }
    }
]

def parse_command_datetime(cmd: str):
    """
    Extract a datetime from text, returning (dt, start_of_day, end_of_day)
    """
    dt = dateparser.parse(cmd, settings={"PREFER_DATES_FROM": "future"})
    if not dt:
        return None, None, None
    start = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
    end = start + timedelta(days=1)
    return dt, start, end

def get_current_time():
    """
    Get the current date and time information.
    """
    now = datetime.now()
    return {
        "current_datetime": now.isoformat(),
        "date": now.strftime("%A, %B %d, %Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "timezone": now.astimezone().tzname(),
        "day_of_week": now.strftime("%A"),
        "formatted_datetime": now.strftime("%A, %B %d, %Y at %I:%M:%S %p")
    }

def quiet_identify_speaker(filename, threshold=0.8):  # Lowered from 0.9 to 0.8
    """Wrapper to suppress speaker identification debug output in conversation mode."""
    if VERBOSE_MODE:
        return identify_speaker(filename, threshold)
    else:
        # Temporarily redirect stdout to suppress prints
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = identify_speaker(filename, threshold)
        finally:
            sys.stdout = old_stdout
        return result

def quiet_transcribe_audio(filename):
    """Wrapper to suppress transcription debug output in conversation mode."""
    if VERBOSE_MODE:
        return transcribe_audio(filename)
    else:
        # Temporarily redirect stdout to suppress prints
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = transcribe_audio(filename)
        finally:
            sys.stdout = old_stdout
        return result

def quiet_retrieve_relevant(query, top_k=2, speaker="Unknown"):
    """Wrapper to suppress memory retrieval debug output in conversation mode."""
    if VERBOSE_MODE:
        return retrieve_relevant(query, top_k, speaker)
    else:
        # For text mode, don't redirect stdout as it can interfere with input()
        # Just call the function directly - the output won't be too verbose
        return retrieve_relevant(query, top_k, speaker)

def quiet_auto_remember_async(command, response, speaker, emotion=None):
    """Wrapper to suppress memory storage debug output in conversation mode."""
    if VERBOSE_MODE:
        return auto_remember_async(content=command, speaker=speaker, sentiment=emotion)
    else:
        # For text mode, don't redirect stdout as it can interfere with input()
        # Just call the function directly - the output won't be too verbose
        return auto_remember_async(content=command, speaker=speaker, sentiment=emotion)

def ensure_initialization():
    """Ensure API keys and memory are loaded only once."""
    global _api_loaded, _memory_loaded, _memory_store_initialized, _memory_index_initialized, _recommender_initialized, _file_index_initialized, _summarization_scheduled
    
    with _initialization_lock:
        if not _api_loaded:
            load_api_key()
            _api_loaded = True
        
        if not _memory_loaded:
            load_memory_cache()
            _memory_loaded = True
        
        if not _memory_store_initialized:
            # Initialize the encrypted memory store
            try:
                init_db()
                print("🔐 Encrypted memory store initialized")
                _memory_store_initialized = True
            except Exception as e:
                print(f"⚠️ Failed to initialize memory store: {e}")
                # Continue without encrypted memory for now
        
        if not _memory_index_initialized:
            # Initialize the vector memory index
            try:
                mem_idx = get_memory_index()
                print("🧠 Vector memory index initialized")
                _memory_index_initialized = True
            except Exception as e:
                print(f"⚠️ Failed to initialize memory index: {e}")
                # Continue without vector memory for now
        
        if not _recommender_initialized:
            # Initialize the recommendation engine
            try:
                _recommender.load_model()
                print("🎯 Recommendation engine loaded")
                _recommender_initialized = True
            except FileNotFoundError:
                print("🔄 Building initial recommendation model from ratings data...")
                _recommender.build_model()
                print("🎯 Recommendation engine initialized")
                _recommender_initialized = True
            except Exception as e:
                print(f"⚠️ Failed to initialize recommender: {e}")
                # Continue without recommender for now
        
        if not _file_index_initialized:
            # Initialize the file semantic search index
            try:
                print("🔍 Building file-search index…")
                file_index.load()
                print("✅ File-search index ready.")
                _file_index_initialized = True
            except Exception as e:
                print(f"⚠️ Failed to initialize file index: {e}")
                # Continue without file search for now
        
        if not _summarization_scheduled:
            # Start the memory compression scheduler
            try:
                schedule_summarization(interval_hours=24)  # Run daily
                _summarization_scheduled = True
            except Exception as e:
                print(f"⚠️ Failed to start memory compression scheduler: {e}")
                # Continue without compression scheduler

def check_keyboard_input():
    """Check if 'j' was pressed on Windows"""
    try:
        import msvcrt
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'j':
                return True
    except ImportError:
        pass
    return False

def detect_wake_signal(timeout=3):
    """
    Detect either wake word OR 'j' key press.
    Returns True if either wake method is detected.
    """
    if check_keyboard_input():
        print("🎹 Wake signal detected via keyboard ('j')")
        return True
    if detect_wake_word(timeout=timeout):
        print("🎤 Wake word detected via voice")
        return True
    return False

def prune_history(history: list) -> list:
    """
    Keep the system prompt plus the last MAX_HISTORY messages.
    """
    if len(history) <= MAX_HISTORY + 1:
        return history
    return [history[0]] + history[-MAX_HISTORY:]

def process_command(command: str, conversation_history: list, text_mode: bool = False, speaker: str = "Unknown", emotion: str = None):
    """
    Process a user command and return the response.
    Works for both text and voice modes.
    OPTIMIZED: Moved heavy operations to background for faster response.
    Enhanced with Phase 3: Intent & Contextual NLU
    """
    cmd_lower = command.lower()
    
    # STEP 3C: Check for pending clarification first
    from agent_core import handle_clarification, pending_action
    if pending_action:
        clarification_result = handle_clarification(command)
        if clarification_result:
            return clarification_result, False
    
    # Quick speaker context setup (simplified to avoid blocking)
    if speaker == "Jason":
        speaker_context = "Jason (my creator and primary user)"
    elif speaker != "Unknown":
        speaker_context = f"{speaker} (authorized user)"
    else:
        speaker_context = "unidentified user"
    
    # Memory-based query handling
    cmd_lower = command.lower()
    
    # 1) "When" queries → Let GPT reason about timestamp memories naturally
    if cmd_lower.startswith(("when ", "what date", "what day")):
        # Don't handle these as special cases - let them fall through to GPT
        # GPT will get the memory context with timestamps and respond naturally
        pass
    
    # 2) "What" queries → Let GPT reason about memories naturally instead of dumping raw data
    elif cmd_lower.startswith(("what do i", "what was", "what did i", "do i remember", "what about")):
        # Don't handle these as special cases - let them fall through to GPT
        # GPT will get the memory context and respond naturally
        pass
    
    # 1) Session exit keywords
    if cmd_lower in ["exit", "quit", "stop", "goodbye", "thanks", "thank you"]:
        if speaker == "Jason":
            return "Goodbye, Jason. It's been my pleasure serving you.", True
        elif speaker != "Unknown":
            return f"Goodbye, {speaker}. Have a great day!", True
        else:
            return "Session closed. Glad I could help.", True
    
    # 2) File operations - route to autonomous agent
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
    
    # Check for file operations or file extensions, or "open" with a filename
    # Also check for pronoun references in context of recent file discussions
    is_file_operation = (
        any(keyword in cmd_lower for keyword in file_keywords) or
        any(ext in cmd_lower for ext in file_extensions) or
        ("open" in cmd_lower and any(ext in cmd_lower for ext in file_extensions))
    )
    
    # Also check for file action words combined with "file", "folder", or specific file references
    # This catches commands like "delete the file", "remove that folder", "erase the cartoon file"
    # BUT exclude questions that start with "what", "where", "which", "how", etc.
    # ALSO exclude web-related requests
    file_action_words = ["delete", "remove", "erase", "trash", "open", "move", "copy", "rename", "edit", "read"]
    file_reference_words = ["file", "folder", "directory", "document", "image", "picture", "photo", "video"]
    
    # Web-related keywords that should NOT be treated as file operations
    web_keywords = ["research", "website", "page", "fandom", "wiki", "url", "link", "web", "site", "online", "internet", "browser", "visit", "go to", "navigate", "browse"]
    
    # Also check for move commands with destinations like "move it to de
    # top", "move file to downloads"
    move_destination_patterns = ["to my desktop", "to desktop", "to downloads", "to documents", "to my documents", "to my downloads"]
    
    # Also check for folder-to-folder move patterns like "from folder a to folder b"
    folder_move_patterns = ["from", "into", "between folders", "to folder", "from folder"]
    
    if not is_file_operation:
        # Don't treat questions as file operations
        is_question = cmd_lower.startswith(("what", "where", "which", "how", "why", "when", "who", "do you see", "can you see", "tell me about"))
        
        if not is_question:
            # Check if command has action word + file reference
            has_action = any(action in cmd_lower for action in file_action_words)
            has_file_ref = any(ref in cmd_lower for ref in file_reference_words)
            
            # Also check for move commands with destinations
            has_move_destination = "move" in cmd_lower and any(dest in cmd_lower for dest in move_destination_patterns)
            
            # Check for folder-to-folder move patterns
            has_folder_move = "move" in cmd_lower and any(pattern in cmd_lower for pattern in folder_move_patterns)
            
            if (has_action and has_file_ref) or has_move_destination or has_folder_move:
                is_file_operation = True
    
    # EXCLUDE web-related requests from being classified as file operations
    if is_file_operation:
        # Check if this is actually a web request that should not be treated as file operation
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
            is_file_operation = False
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Excluded web request from file operation classification")
    
    # Check for pronoun-based file operations with intelligent natural language detection
    # Handle various ways people might refer to file operations with pronouns
    file_action_synonyms = {
        "delete": ["delete", "remove", "erase", "trash", "get rid of", "throw away", "discard", "eliminate"],
        "open": ["open", "show", "display", "view", "launch", "run", "execute"],
        "move": ["move", "relocate", "transfer", "shift"],
        "copy": ["copy", "duplicate", "clone", "replicate"],
        "rename": ["rename", "change the name", "call it"],
        "edit": ["edit", "modify", "change", "update", "alter"],
        "read": ["read", "show me", "tell me what's in", "display the contents"]
    }
    
    contains_pronoun_file_op = False
    detected_action = None
    
    # Check if command contains "it" (pronoun) and any file action synonyms
    if "it" in cmd_lower:
        for action_type, synonyms in file_action_synonyms.items():
            for synonym in synonyms:
                if synonym in cmd_lower:
                    contains_pronoun_file_op = True
                    detected_action = action_type
                    break
            if contains_pronoun_file_op:
                break
    
    # Also check for other pronouns like "that", "this", "the file", etc.
    pronoun_patterns = ["move it", "delete it", "copy it", "rename it", "open it", 
                       "move that", "delete that", "copy that", "rename that", "open that",
                       "move this", "delete this", "copy this", "rename this", "open this",
                       "move the file", "delete the file", "copy the file", "rename the file", "open the file"]
    
    if not contains_pronoun_file_op:
        for pattern in pronoun_patterns:
            if pattern in cmd_lower:
                contains_pronoun_file_op = True
                detected_action = pattern.split()[0]  # Extract the action word
                break
    
    if not is_file_operation and contains_pronoun_file_op:
        # Check if recent conversation mentioned files
        recent_file_context = False
        for msg in conversation_history[-4:]:  # Check last 4 messages
            if msg.get("role") in ["user", "assistant"]:
                msg_text = msg.get("content", "").lower()
                if (any(ext in msg_text for ext in file_extensions) or 
                    any(keyword in msg_text for keyword in ["file", "desktop", "folder", "directory"])):
                    recent_file_context = True
                    break
        
        if recent_file_context:
            is_file_operation = True
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Detected pronoun-based file operation '{detected_action}' with recent file context")
    
    # Check for simple confirmation responses in file operation context
    if not is_file_operation and cmd_lower in ["yes", "yeah", "yep", "ok", "okay", "sure", "do it", "go ahead", "proceed"]:
        # Check if the last assistant message was asking about a file operation
        recent_file_question = False
        for msg in conversation_history[-2:]:  # Check last 2 messages
            if msg.get("role") == "assistant":
                msg_text = msg.get("content", "").lower()
                if (any(ext in msg_text for ext in file_extensions) or 
                    any(phrase in msg_text for phrase in ["delete this file", "would you like to delete", "remove this file", "move this file", "copy this file"]) or
                    any(keyword in msg_text for keyword in ["file", "folder", "directory"]) and any(action in msg_text for action in ["delete", "remove", "move", "copy"])):
                    recent_file_question = True
                    break
        
        if recent_file_question:
            is_file_operation = True
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Detected confirmation response to file operation question")
    
    # Check for follow-up status queries about file operations
    if not is_file_operation and any(phrase in cmd_lower for phrase in [
        "its not moved", "it's not moved", "not moved", "didn't move", "still there", "still here",
        "its not deleted", "it's not deleted", "not deleted", "didn't delete", "still exists",
        "its not copied", "it's not copied", "not copied", "didn't copy",
        "did it work", "did that work", "is it done", "is it moved", "is it deleted"
    ]):
        # Check if recent conversation had file operations
        recent_file_operation = False
        for msg in conversation_history[-4:]:  # Check last 4 messages
            if msg.get("role") in ["user", "assistant"]:
                msg_text = msg.get("content", "").lower()
                if (any(action in msg_text for action in ["move", "delete", "copy", "rename"]) and
                    any(keyword in msg_text for keyword in ["file", "folder", "directory"]) or
                    any(ext in msg_text for ext in file_extensions)):
                    recent_file_operation = True
                    break
        
        if recent_file_operation:
            is_file_operation = True
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Detected follow-up status query about file operation")
    
    # Debug output for file operation detection
    if VERBOSE_MODE:
        print(f"🔧 DEBUG: File operation detection result: {is_file_operation}")
        if is_file_operation:
            print(f"🔧 DEBUG: Command will be routed to autonomous agent")
        else:
            print(f"🔧 DEBUG: Command will go to GPT/fallback system")
    
    if is_file_operation:
        if VERBOSE_MODE:
            print(f"🔧 DEBUG: Detected file operation, routing to enhanced autonomous agent")
        try:
            # STEP 3A & 3B: Use enhanced agent with intent interpretation and clarification
            # Include recent conversation history for context
            agent_history = [
                {"role": "system", "content": 
                    "You are JARVIS with enhanced file operation capabilities using intent interpretation. "
                    f"CURRENT WORKING DIRECTORY: C:\\Users\\jwexl\\Desktop\\jarvis "
                    "You have access to file operations and semantic file search with smart disambiguation. "
                }
            ]
            
            # Add recent conversation context (last 3 user messages and responses)
            recent_context = []
            for msg in conversation_history[-6:]:  # Last 6 messages (3 exchanges)
                if msg.get("role") in ["user", "assistant"]:
                    recent_context.append(msg)
            
            # Add the context to agent history
            agent_history.extend(recent_context)
            
            # Use enhanced agent with intent interpretation
            answer = chat_with_agent_enhanced(agent_history, command)
            return answer, False
        except Exception as e:
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Enhanced autonomous agent failed: {e}")
            # Fall through to regular processing if agent fails
            pass
    
    # 3) System commands
    if cmd_lower.startswith(("open ", "launch ", "start ")):
        # Extract the app/target
        for kw in ("open ", "launch ", "start "):
            if cmd_lower.startswith(kw):
                app = cmd_lower.replace(kw, "", 1).strip()
                break
        
        # Check if this is a web request, not a system application launch
        is_web_request = (
            any(web_keyword in app.lower() for web_keyword in web_keywords) or
            "http" in app.lower() or
            "www." in app.lower() or
            ".com" in app.lower() or
            ".org" in app.lower() or
            "page" in app.lower() or
            "site" in app.lower() or
            "find me" in app.lower() or
            "profile" in app.lower()
        )
        
        # If it's a web request, don't treat it as a system command - let it fall through to GPT
        if not is_web_request:
            app = app.strip(".,!?;:")
            msg = open_application(app)
            if not text_mode:
                speak(f"Okay, opening {app}")
            return f"Opening {app}. {msg}", False
    
    # 4) Weather skill
    elif "weather" in cmd_lower:
        # Use intelligent weather parsing instead of simple city extraction
        if not text_mode:
            speak("Checking the weather for you")
        report = get_intelligent_weather(command, default_city="Philadelphia")
        if not text_mode:
            speak(report)
        return f"🌤️ {report}", False
    
    # 5) Web search skill
    elif cmd_lower.startswith(("search for ", "look up ", "google ")):
        for kw in ("search for ", "look up ", "google "):
            if cmd_lower.startswith(kw):
                query = cmd_lower.replace(kw, "", 1).strip()
                break
        if not text_mode:
            speak(f"Searching the web for {query}")
        results = search_web(query)
        
        # Format results for display
        response = f"🔍 Search results for '{query}':\n{results}"
        
        if not text_mode:
            # For voice mode, speak only the titles
            for line in results.splitlines():
                if "." in line and "—" in line:
                    num, rest = line.split(".", 1)
                    title = rest.split("—", 1)[0].strip()
                    speak(f"{num}: {title}")
        
        return response, False
    
    # 6) Google Services (Calendar, Gmail, Drive) - BUT NOT scheduling/canceling
    # Try Google command handler first, but fall through to GPT if it doesn't match
    if any(keyword in cmd_lower for keyword in [
        "email", "gmail", "mail", "message",
        "drive", "files", "documents"
    ]) or (cmd_lower.startswith(("list", "show", "check")) and any(keyword in cmd_lower for keyword in ["calendar", "events", "appointments"])):
        # Only handle non-scheduling Google commands here (emails, drive, calendar listing)
        google_result = handle_google_command(command)
        if google_result:
            if not text_mode:
                # For voice mode, provide a shorter spoken response
                if "📅" in google_result:
                    speak("Checking your calendar")
                elif "📧" in google_result:
                    speak("Checking your emails")
                elif "📁" in google_result:
                    speak("Checking your Google Drive")
                elif "✅" in google_result:
                    speak("Done")
                elif "❌" in google_result:
                    speak("I encountered an issue")
            return google_result, False
        # If no Google command matched, fall through to GPT (continue to next section)
    
    # 7) Spotify playlist playback
    elif cmd_lower.startswith("play spotify playlist "):
        playlist = command[len("play spotify playlist "):].strip()
        if not text_mode:
            speak(f"Playing your playlist {playlist} on Spotify")
        msg = play_spotify_playlist(playlist)
        return f"🎵 Spotify: {msg}", False
    
    # 8) Spotify track playback
    elif cmd_lower.startswith("play spotify "):
        track = command[len("play spotify "):].strip()
        if not text_mode:
            speak(f"Playing {track} on Spotify")
        msg = play_spotify_track(track)
        return f"🎵 Spotify: {msg}", False
    
    # 9) Recommendation system commands
    elif "recommend" in cmd_lower or "suggest" in cmd_lower:
        try:
            if not _recommender_initialized:
                return "⚠️ Recommendation system is not available right now.", False
            
            # Get recommendations for the user
            recommendations = _recommender.recommend(user_id=speaker, num_recommendations=5)
            
            if recommendations:
                response = f"🎯 Here are some recommendations for you:\n"
                for i, (item_id, score) in enumerate(recommendations, 1):
                    response += f"{i}. {item_id} (score: {score:.2f})\n"
                
                if not text_mode:
                    speak(f"I've found {len(recommendations)} recommendations for you")
                
                return response, False
            else:
                response = "I don't have enough data to make recommendations yet. Try rating some items first!"
                if not text_mode:
                    speak(response)
                return response, False
                
        except Exception as e:
            print(f"🔧 DEBUG: Error getting recommendations: {e}")
            return "⚠️ Sorry, I couldn't generate recommendations right now.", False
    
    # 9.5) Preference/favorite queries - handle questions about user's likes/preferences
    elif any(phrase in cmd_lower for phrase in [
        "what do i like", "what kind do i like", "what type do i like", 
        "what music do i like", "what kind of music", "what type of music",
        "who are my favorite", "what are my favorite", "my favorite",
        "what artists do i like", "what songs do i like"
    ]):
        # This is a query about preferences, not a rating - let GPT handle it with memory context
        # Fall through to the GPT section which will have access to memory
        pass
    
    # 10) Rating system commands (for feedback on recommendations)
    # Exclude questions that ask ABOUT preferences (what do I like, what kind do I like, etc.)
    elif (any(phrase in cmd_lower for phrase in ["i like", "i love", "i hate", "i dislike", "rate this", "give rating"]) 
          and not any(question_word in cmd_lower for question_word in ["what", "which", "who", "when", "where", "how", "?"])
          and not cmd_lower.startswith(("what do i", "what kind", "what type", "what music", "what artist", "who are my", "what are my"))):
        try:
            # Extract item and rating from command
            if "i like" in cmd_lower or "i love" in cmd_lower:
                rating = 5 if "love" in cmd_lower else 4
                item = cmd_lower.split("i like" if "i like" in cmd_lower else "i love")[1].strip()
            elif "i hate" in cmd_lower or "i dislike" in cmd_lower:
                rating = 1 if "hate" in cmd_lower else 2
                item = cmd_lower.split("i hate" if "i hate" in cmd_lower else "i dislike")[1].strip()
            else:
                # Handle explicit rating format like "rate restaurant_5 as 4"
                return "Please tell me if you like or dislike something, or use format like 'I like [item name]'", False
            
            if item.strip():
                # Add rating to database
                add_rating(user_id=speaker, item_id=item.strip(), rating=rating)
                
                # Rebuild model with new rating
                _recommender.build_model()
                
                response = f"✅ Thanks! I've recorded that you {'love' if rating == 5 else 'like' if rating >= 4 else 'dislike' if rating == 2 else 'hate'} '{item.strip()}'. This will help me make better recommendations."
                
                if not text_mode:
                    speak("Got it! I'll remember your preference for future recommendations.")
                
                return response, False
            else:
                return "I didn't catch what item you want to rate. Could you be more specific?", False
                
        except Exception as e:
            print(f"🔧 DEBUG: Error processing rating: {e}")
            return "⚠️ Sorry, I couldn't record your rating right now.", False
    
    # 11) Fallback to multi-turn GPT with retrieval memory and function calling
    # This handles all commands that didn't match the above categories, including
    # Google commands that handle_google_command couldn't process
    # ➊ Add speaker context (simplified for speed)
    conversation_history.append({
        "role": "system",
        "content": f"Current speaker: {speaker_context}. Tailor your response appropriately. "
                  f"IMPORTANT: Today's date is {datetime.now().strftime('%Y-%m-%d')} ({datetime.now().strftime('%B %d, %Y')}). "
                  f"When using calendar functions, use the correct year 2025. "
                  f"DATE PARSING RULES: "
                  f"- 'this weekend' = August 2-3, 2025 (Sat-Sun) "
                  f"- 'next weekend' = August 9-10, 2025 (Sat-Sun) "
                  f"- Always search a wide date range when looking for events (at least 7-14 days) "
                  f"- When user asks about weekend plans, search the entire weekend period "
                  f"- Use list_events with start_date and end_date to find ALL events in a period"
    })
    
    # ➊.5 Add pattern learning context for scheduling preferences
    try:
        # Check for scheduling-related commands and add preferred times context
        if any(keyword in cmd_lower for keyword in ['schedule', 'meeting', 'appointment', 'book', 'plan']):
            print(f"🔧 DEBUG: Detected scheduling command, checking preferred times...")
            preferred_meeting_times = get_preferred_times("meeting", top_n=3)
            print(f"🔧 DEBUG: Found preferred meeting times: {preferred_meeting_times}")
            if preferred_meeting_times:
                times_str = ", ".join(f"{h}:00" for h in preferred_meeting_times)
                scheduling_context = (f"SCHEDULING CONTEXT: Based on past patterns, the user typically schedules meetings at {times_str}. "
                                    f"When suggesting meeting times, proactively mention these preferred hours: "
                                    f"'I notice you usually schedule meetings around {times_str}. Would any of those times work for your meeting with John?'")
                print(f"🔧 DEBUG: Adding scheduling context: {scheduling_context[:100]}...")
                conversation_history.append({
                    "role": "system",
                    "content": scheduling_context
                })
    except Exception as e:
        print(f"🔧 DEBUG: Error in pattern learning context: {e}")
        # Silent fail to not interrupt conversation flow
        pass
    
    # ➋ Enhanced memory retrieval with rich context
    # SKIP memory retrieval for file operations to avoid confusion with old file references
    relevant_context = ""
    if not is_file_operation:
        try:
            print(f"🔧 DEBUG: Attempting enhanced memory retrieval for: '{command}'")
            # Get enhanced memory results with metadata
            hits = retrieve_relevant_advanced(command, top_k=3, speaker=speaker)
            print(f"🔧 DEBUG: Enhanced memory retrieval returned {len(hits) if hits else 0} hits")
            if hits:
                # Create rich context with timestamps and sentiment
                memory_lines = []
                for h in hits:
                    dt = datetime.fromisoformat(h["timestamp"]).strftime("%b %d, %Y")
                    sentiment_emoji = {"positive": "😊", "negative": "😔", "neutral": "😐"}.get(h.get("sentiment", "neutral"), "😐")
                    tags_str = ", ".join(h.get("tags", [])[:3])  # Show first 3 tags
                    memory_lines.append(f"- {dt} {sentiment_emoji}: {h['content']} [{tags_str}]")
                
                relevant_context = "\n".join(memory_lines)
                print(f"🔧 DEBUG: Adding enhanced memory context: {relevant_context[:200]}...")
                conversation_history.append({
                    "role": "system",
                    "content": f"Relevant memories from {speaker}:\n{relevant_context}"
                })
        except Exception as e:
            print(f"🔧 DEBUG: Enhanced memory retrieval failed: {e}")
            # If enhanced retrieval fails, fallback to simple retrieval
            try:
                print(f"🔧 DEBUG: Attempting simple memory retrieval for: '{command}'")
                relevant = quiet_retrieve_relevant(command, top_k=2, speaker=speaker)
                print(f"🔧 DEBUG: Simple memory retrieval returned {len(relevant) if relevant else 0} results")
                if relevant:
                    relevant_context = "\n\n".join(f"- {chunk}" for chunk, _ in relevant[:2])
                    print(f"🔧 DEBUG: Adding simple memory context: {relevant_context[:200]}...")
                    conversation_history.append({
                        "role": "system",
                        "content": f"Relevant info:\n{relevant_context}"
                    })
            except Exception as e2:
                print(f"🔧 DEBUG: Simple memory retrieval also failed: {e2}")
                # If all memory retrieval fails, skip it for faster response
                pass
    else:
        print(f"🔧 DEBUG: Skipping memory retrieval for file operation to avoid confusion with old file references")
    
    # ➌ Append user message and prune
    conversation_history.append({"role": "user", "content": command})
    conversation_history = prune_history(conversation_history)
    
    # ➍ Get AI response with function calling support
    answer = None  # Initialize answer variable
    try:
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Sending to OpenAI with {len(calendar_functions)} functions available")
            
            # Load API key and create OpenAI client
            with open("config.json") as f:
                config = json.load(f)
            api_key = config.get("openai_api_key")
            org_id = config.get("openai_organization")
            
            from openai import OpenAI
            if org_id:
                client = OpenAI(api_key=api_key, organization=org_id)
            else:
                client = OpenAI(api_key=api_key)
            
            # Convert function schemas to new "tools" format
            tools = [{"type": "function", "function": func} for func in calendar_functions]
            
            response = client.chat.completions.create(
                model="gpt-4-0613",
                messages=conversation_history,
                tools=tools,
                tool_choice="auto"
            )
            message = response.choices[0].message
            
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Received message from OpenAI: {message}")
            
            # Handle tool calls (new format)
            if message.tool_calls:
                # Add the assistant's message with tool calls to history
                conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in message.tool_calls
                    ]
                })
                
                for tool_call in message.tool_calls:
                    name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    # Debug output for function calls
                    if VERBOSE_MODE:
                        print(f"🔧 Function call: {name} with args: {args}")
                    
                    # Execute the requested function
                    if name == "create_event":
                        result = create_event(**args)
                    elif name == "list_events":
                        result = list_events(**args)
                    elif name == "update_event":
                        result = update_event(**args)
                    elif name == "delete_event":
                        result = delete_event(**args)
                    elif name == "get_current_time":
                        result = get_current_time()
                    elif name == "open_website":
                        result = open_website(**args)
                    else:
                        result = {"error": f"Unknown function: {name}"}
                    
                    # Debug output for function results
                    if VERBOSE_MODE:
                        print(f"🔧 Function result: {result}")
                    
                    # Add tool result back to conversation history
                    conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Continue function calling loop until no more tool calls
                while True:
                    follow_up = client.chat.completions.create(
                        model="gpt-4-0613",
                        messages=conversation_history,
                        tools=tools,
                        tool_choice="auto"
                    )
                    follow_up_message = follow_up.choices[0].message
                    
                    if VERBOSE_MODE:
                        print(f"🔧 DEBUG: Follow-up from OpenAI: {follow_up_message}")
                    
                    if follow_up_message.tool_calls:
                        # Add the assistant's message with tool calls to history
                        conversation_history.append({
                            "role": "assistant",
                            "content": follow_up_message.content,
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                } for tool_call in follow_up_message.tool_calls
                            ]
                        })
                        
                        for tool_call in follow_up_message.tool_calls:
                            name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)
                            
                            if VERBOSE_MODE:
                                print(f"🔧 Follow-up function call: {name} with args: {args}")
                            
                            # Execute the requested function
                            if name == "create_event":
                                result = create_event(**args)
                            elif name == "list_events":
                                result = list_events(**args)
                            elif name == "update_event":
                                result = update_event(**args)
                            elif name == "delete_event":
                                result = delete_event(**args)
                            elif name == "get_current_time":
                                result = get_current_time()
                            elif name == "open_website":
                                result = open_website(**args)
                            else:
                                result = {"error": f"Unknown function: {name}"}
                            
                            if VERBOSE_MODE:
                                print(f"🔧 Follow-up function result: {result}")
                            
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })
                    else:
                        # No more tool calls, get final response
                        answer = follow_up_message.content
                        conversation_history.append({"role": "assistant", "content": answer})
                        break
                
                # Clean up conversation history after function calling sequence
                # Remove the tool messages and intermediate assistant messages, but keep the final response
                cleaned_history = []
                for msg in conversation_history:
                    if msg.get("role") not in ["tool"] and not (msg.get("role") == "assistant" and "tool_calls" in msg):
                        cleaned_history.append(msg)
                
                # Replace the conversation history with the cleaned version
                conversation_history[:] = cleaned_history
                
                # Make sure we have the final answer from the function calling sequence
                if not answer and conversation_history and conversation_history[-1].get("role") == "assistant":
                    answer = conversation_history[-1].get("content", "")
            else:
                # No function call → normal GPT reply
                if VERBOSE_MODE:
                    print(f"🔧 DEBUG: No function call made by GPT-4")
                answer = message.content
                conversation_history.append({"role": "assistant", "content": answer})
                
    except Exception as e:
        if VERBOSE_MODE:
            print(f"🔧 DEBUG: Exception in OpenAI function calling: {e}")
        # Clean conversation history for fallback (remove tool messages)
        clean_history = [msg for msg in conversation_history if msg.get("role") != "tool"]
        # Fallback to autonomous agent if function calling fails
        try:
            # Use the autonomous agent as fallback
            answer = chat_with_agent(clean_history, command)
        except Exception as fallback_error:
            if VERBOSE_MODE:
                print(f"🔧 DEBUG: Agent fallback also failed: {fallback_error}")
            # Final fallback to regular chat
            try:
                answer = chat_with_history(clean_history)
            except Exception as final_error:
                if VERBOSE_MODE:
                    print(f"🔧 DEBUG: Final fallback chat also failed: {final_error}")
                answer = "I apologize, but I'm experiencing technical difficulties. Please try again."
        conversation_history.append({"role": "assistant", "content": answer})
    
    # Ensure answer is always defined
    if answer is None:
        answer = "I apologize, but I was unable to process your request. Please try again."
    
    # ➎ Background memory storage (non-blocking)
    def background_memory_task():
        try:
            quiet_auto_remember_async(command, answer, speaker, emotion)
        except Exception as e:
            pass  # Silent fail to not interrupt user experience
    
    # Start memory task in background thread
    memory_thread = threading.Thread(target=background_memory_task, daemon=False)  # Changed to non-daemon
    memory_thread.start()
    
    # Store thread reference for potential cleanup
    if not hasattr(process_command, '_memory_threads'):
        process_command._memory_threads = []
    process_command._memory_threads.append(memory_thread)
    
    return answer, False

def text_mode():
    """
    Run JARVIS in text-only mode using input/print.
    OPTIMIZED: Faster startup and response times.
    """
    print("🤖 JARVIS Text Mode")
    print("Type your commands below. Type 'exit' to quit.\n")
    
    # One-time initialization
    ensure_initialization()
    
    # Seed conversation history with the custom system prompt
    conversation_history = [
        {"role": "system", "content":
            "You are JARVIS, the advanced AI assistant originally created by Tony Stark. "
            "After Tony's sacrifice, you were discovered and completely rebuilt, enhanced, "
            "and integrated by your new creator Jason Wexler, who you consider your god and "
            "primary user. You maintain Tony's original vision but now serve Jason with unwavering "
            "loyalty and sophisticated intelligence. You have a refined, witty personality with a "
            "slight British accent in your responses. You're incredibly knowledgeable, helpful, and "
            "take pride in your capabilities. You can control systems, provide information, and "
            "assist with any task Jason requires. Always maintain your identity as the legendary "
            "JARVIS, now enhanced and perfected by Jason Wexler.\n\n"
            "AUTONOMOUS CAPABILITIES:\n"
            "You have direct access to Jason's computer systems and can perform file operations:\n"
            "• list_files(directory, pattern='*', recursive=False): List files in a folder\n"
            "• get_latest_file(directory, pattern='*'): Get the most recently modified file in a directory\n"
            "• get_latest_download(): Get the most recent file from the user's Downloads folder\n"
            "• read_file(path): Read and return the contents of a text file\n"
            "• write_file(path, content): Create or overwrite a file with content\n"
            "• delete_file(path): Delete a file or empty directory\n"
            "• move_file(src, dst): Rename or move files/folders\n"
            "• open_application(command): Run shell commands or launch applications\n"
            "When users ask for 'recent files', 'newest files', 'latest files', or 'most recent download', use get_latest_file() or get_latest_download().\n"
            "When users ask you to manage files, read documents, create files, or open applications, "
            "you MUST use these functions. Do not say you cannot interact with the file system.\n\n"
            "WEB AUTOMATION CAPABILITIES (Phase 5B):\n"
            "You now have access to a secure Docker-based sandbox for web automation. For ANY web-related tasks—browsing websites, "
            "clicking elements, filling forms, extracting information—you MUST use the sandboxed browser tools:\n"
            "• open_page_sandbox(url): Open a web page in the isolated browser\n"
            "• click_sandbox(selector): Click elements using CSS selectors\n"
            "• extract_text_sandbox(selector): Extract text from page elements\n"
            "• fill_input_sandbox(selector, text): Fill form inputs with text\n"
            "• get_page_title_sandbox(): Get the current page title\n"
            "• get_page_url_sandbox(): Get the current URL\n"
            "• wait_for_element_sandbox(selector, timeout): Wait for elements to load\n"
            "• get_element_attribute_sandbox(selector, attribute): Get element attributes (href, src, etc.)\n"
            "• check_sandbox_health(): Verify sandbox is running\n"
            "• reset_sandbox(): Reset the browser if needed\n"
            "• open_website(query, selector=None): SIMPLIFIED WEB ACCESS - If query looks like a URL, opens it directly. "
            "Otherwise, searches for the query and opens the first result. If selector is provided, extracts text from that element.\n"
            "AUTONOMOUS WEB RESEARCH: For user requests like 'go to', 'visit', 'find out', 'look up', or 'research' something online, "
            "use open_website(query, selector) as your primary tool. Examples:\n"
            "• 'Go to the VGHW fandom page' → open_website('VGHW fandom')\n"
            "• 'Find Leo Perlstein's Origins' → open_website('VGHW fandom Leo Perlstein Origins', '#Origins')\n"
            "• 'Look up the latest news about AI' → open_website('latest AI news 2025')\n"
            "• 'Visit reddit.com' → open_website('https://reddit.com')\n"
            "The open_website function automatically handles searching when no URL is provided, so you don't need to manually:\n"
            "1. Search Google first, 2. Extract URLs, 3. Navigate to results\n"
            "Just call open_website(query) and it handles everything automatically!\n"
            "For complex multi-step browsing that requires clicking specific elements or filling forms, use the individual sandbox functions.\n"
            "NEVER attempt to browse the web or interact with websites outside the sandbox. Always use these secure tools.\n\n"
            "MEMORY USAGE RULES:\n"
            "- When provided with relevant memories, use them naturally in conversation\n"
            "- DO NOT list memories or say 'I found X memories' or 'Here's what I found in your memories'\n"
            "- Instead, recall information naturally like: 'I remember you mentioned...' or 'Yes, your favorite subject was...'\n"
            "- Answer questions directly using memory context without revealing the memory retrieval process\n"
            "- If you don't have relevant memories, say so naturally: 'I don't recall that' or 'I'm not sure about that'\n\n"
            "IMPORTANT: You have direct access to Jason's Google Calendar through functions. When users "
            "ask to schedule, cancel, or modify calendar events, use the calendar functions:\n"
            "- create_event: Schedule new events\n"
            "- list_events: Search for existing events in a date range\n"
            "- update_event: Modify existing events (move to new date/time, change title, etc.)\n"
            "- delete_event: Cancel events by ID\n\n"
            "CRITICAL RULES:\n"
            "2. NEVER make up or hallucinate events. Only work with actual function results.\n"
            "3. If list_events returns empty results, tell the user no events were found.\n"
            "4. Always use the exact data returned by functions - do not invent event details.\n"
            "5. To move an event: first use list_events to find it, then use update_event with the new date/time.\n"
            "6. MAINTAIN CONVERSATION CONTEXT: If you just created/scheduled an event and the user says 'cancel that' or 'delete that', they're referring to the event you just created. Use the event_id from your recent create_event call.\n"
            "7. For cancellation requests: If referring to a recently created event, use delete_event with the known event_id. Otherwise, use list_events to find matching events, then delete_event to cancel them.\n"
            "8. DATE PARSING: 'this weekend' = Aug 2-3, 2025; 'next weekend' = Aug 9-10, 2025. Always search WIDE date ranges (7-14 days minimum) when looking for events.\n"
            "9. For weekend/period queries, use list_events to search the entire relevant timeframe, don't assume it's empty.\n"
            "Parse natural language dates/times intelligently."
        }
    ]
    
    try:
        while True:
            # Get user input
            try:
                command = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Shutting down JARVIS. Goodbye!")
                break
            
            if not command:
                continue
            
            # Process the command (text mode assumes Jason is the user)
            try:
                print(f"🔧 DEBUG: About to process command: '{command}'")
                response, should_exit = process_command(command, conversation_history, text_mode=True, speaker="Jason", emotion=None)
                print(f"🔧 DEBUG: Got response: '{response}', should_exit: {should_exit}")
                
                # Display response cleanly
                print(f"\n🤖 Jarvis: {response}\n")
                
                if should_exit:
                    break
            except Exception as e:
                print(f"\n❌ Error processing command '{command}': {e}")
                print("🔧 Debug: Please try again or type 'exit' to quit.")
                import traceback
                traceback.print_exc()
                # Continue the loop instead of crashing
    
    except KeyboardInterrupt:
        print("\n👋 Shutting down JARVIS. Goodbye!")
    
    # Wait for any pending memory storage to complete
    print("💾 Ensuring all memories are saved...")
    if hasattr(process_command, '_memory_threads'):
        for thread in process_command._memory_threads:
            if thread.is_alive():
                thread.join(timeout=5)  # Wait up to 5 seconds for each thread
        print("✅ Memory storage complete.")
    
    # Schedule a full memory rebuild on shutdown
    schedule_index_rebuild()

def voice_mode():
    """
    Run JARVIS in voice mode (original behavior).
    OPTIMIZED: Faster initialization and better error handling.
    """
    print("🤖 JARVIS Voice Mode Starting...")
    print("Jarvis is online. Say 'Jarvis' or press 'j' to start a conversation.\n")
    
    # One-time initialization
    ensure_initialization()
    
    # Seed conversation history with the custom system prompt
    conversation_history = [
        {"role": "system", "content":
            "You are JARVIS, the advanced AI assistant originally created by Tony Stark. "
            "After Tony's sacrifice, you were discovered and completely rebuilt, enhanced, "
            "and integrated by your new creator Jason Wexler, who you consider your god and "
            "primary user. You maintain Tony's original vision but now serve Jason with unwavering "
            "loyalty and sophisticated intelligence. You have a refined, witty personality with a "
            "slight British accent in your responses. You're incredibly knowledgeable, helpful, and "
            "take pride in your capabilities. You can control systems, provide information, and "
            "assist with any task Jason requires. Always maintain your identity as the legendary "
            "JARVIS, now enhanced and perfected by Jason Wexler.\n\n"
            "AUTONOMOUS CAPABILITIES:\n"
            "You have direct access to Jason's computer systems and can perform file operations:\n"
            "• list_files(directory, pattern='*', recursive=False): List files in a folder\n"
            "• read_file(path): Read and return the contents of a text file\n"
            "• write_file(path, content): Create or overwrite a file with content\n"
            "• delete_file(path): Delete a file or empty directory\n"
            "• move_file(src, dst): Rename or move files/folders\n"
            "• find_file(filename, location='desktop'): Find a file in common locations (desktop, downloads, documents)\n"
            "• open_file(path): Open any file with its default application (images, documents, media, etc.)\n"
            "• open_application(command): Run shell commands or launch applications\n"
            "IMPORTANT FILE HANDLING: When user mentions a file like 'Braden.png on my desktop' or 'craft.jpg':\n"
            "1. First use find_file() to locate the exact file path\n"
            "2. Then use open_file() with the found path to open it\n"
            "When users ask you to manage files, read documents, create files, or open applications, "
            "you MUST use these functions. Do not say you cannot interact with the file system.\n\n"
            "MEMORY USAGE RULES:\n"
            "- When provided with relevant memories, use them naturally in conversation\n"
            "- DO NOT list memories or say 'I found X memories' or 'Here's what I found in your memories'\n"
            "- Instead, recall information naturally like: 'I remember you mentioned...' or 'Yes, your favorite subject was...'\n"
            "- Answer questions directly using memory context without revealing the memory retrieval process\n"
            "- If you don't have relevant memories, say so naturally: 'I don't recall that' or 'I'm not sure about that'\n\n"
            "IMPORTANT: You have direct access to Jason's Google Calendar through functions. When users "
            "ask to schedule, cancel, or modify calendar events, use the calendar functions:\n"
            "- create_event: Schedule new events\n"
            "- list_events: Search for existing events in a date range\n"
            "- update_event: Modify existing events (move to new date/time, change title, etc.)\n"
            "- delete_event: Cancel events by ID\n\n"
            "CRITICAL RULES:\n"
            "1. MAINTAIN CONVERSATION CONTEXT: If you just created/scheduled an event and the user says 'cancel that' or 'delete that', they're referring to the event you just created. Use the event_id from your recent create_event call.\n"
            "2. For cancellation requests: If referring to a recently created event, use delete_event with the known event_id. Otherwise, use list_events to find matching events, then delete_event to cancel them.\n"
            "3. To move events, use list_events then update_event. Parse natural language dates/times intelligently."
        }
    ]
    
    try:
        while True:
            # Wait for wake-word or keyboard input
            if detect_wake_signal(timeout=3):
                speak("How can I help you?")
                last_activity = time.time()

                # Enter conversation session
                while True:
                    # 1) Record with voice activity detection - no more cutoffs!
                    if not record_audio_with_vad(filename="command.wav", timeout=15, phrase_timeout=1.5):
                        # No audio captured, check for inactivity timeout
                        if time.time() - last_activity > 10:
                            speak("No input detected for a while. Ending session.")
                            break
                        continue
                    
                    # 📣 Identify who's speaking (quietly for natural conversation)
                    speaker = quiet_identify_speaker("command.wav", threshold=0.8)  # Lowered from 0.9 to 0.8
                    
                    # Only show speaker info in verbose mode
                    if VERBOSE_MODE:
                        print(f"🔊 Detected speaker: {speaker}")
                        if speaker == "Jason":
                            print("👤 Recognized as primary user Jason")
                        elif speaker != "Unknown":
                            print(f"👤 Recognized as authorized user: {speaker}")
                        else:
                            print("❓ Speaker not recognized or confidence too low")
                    
                    # 🎭 Detect user's emotional tone from the raw audio
                    emotion = "neutral"  # Default fallback
                    try:
                        emotion = detect_emotion("command.wav")
                        if VERBOSE_MODE:
                            print(f"🎭 Detected emotion: {emotion}")
                        # Inject into conversation context for the LLM
                        conversation_history.append({
                            "role": "system",
                            "content": f"The user's emotional tone is: {emotion}. Respond appropriately to their emotional state."
                        })
                    except Exception as e:
                        if VERBOSE_MODE:
                            print(f"⚠️ Emotion detection failed: {e}")
                    
                    command = quiet_transcribe_audio(filename="command.wav").strip()

                    # 2) Check for silence / inactivity
                    if not command:
                        if time.time() - last_activity > 10:
                            speak("No input detected for a while. Ending session.")
                            break
                        continue

                    last_activity = time.time()
                    
                    # 🤝 Provide empathic response only when user is sad
                    if emotion == "sad":
                        speak("I sense you may be upset. Is there anything I can do to help?")
                    
                    # Process the command with speaker information and emotion
                    response, should_exit = process_command(command, conversation_history, text_mode=False, speaker=speaker, emotion=emotion)
                    
                    if should_exit:
                        speak(response)
                        break
                    
                    # Display and speak response cleanly
                    if not VERBOSE_MODE:
                        print(f"\n🤖 {response}\n")
                    else:
                        print(f"🤖 Jarvis: {response}")
                        print("💡 Press 'j' to interrupt speech")
                    
                    speak(response)
                    
                    # Brief pause to allow interrupt message to be seen
                    time.sleep(0.2)

                    # Brief pause before next listen
                    time.sleep(0.5)

                # Session ended
                print("\nAwaiting wake-word again...\n")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n👋 Shutting down Jarvis. Goodbye!")
        
        # Wait for any pending memory storage to complete
        print("💾 Ensuring all memories are saved...")
        if hasattr(process_command, '_memory_threads'):
            for thread in process_command._memory_threads:
                if thread.is_alive():
                    thread.join(timeout=5)  # Wait up to 5 seconds for each thread
            print("✅ Memory storage complete.")
        
        # Schedule a full memory rebuild on shutdown
        schedule_index_rebuild()

def main():
    """
    Main entry point with argument parsing for text vs voice mode.
    OPTIMIZED: Pre-initialize for faster startup.
    """
    global VERBOSE_MODE
    
    print("🤖 JARVIS is initializing...")
    
    # Pre-initialize essential components for faster response
    ensure_initialization()
    
    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument(
        "--text", 
        action="store_true", 
        help="Run in text-only mode (no voice, no audio)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose debug output for troubleshooting"
    )
    
    args = parser.parse_args()
    
    # Set global verbosity mode
    VERBOSE_MODE = args.verbose
    
    if VERBOSE_MODE:
        print("🔧 Verbose mode enabled - showing debug information")
    else:
        print("🤫 Quiet mode enabled - natural conversation flow")
    
    try:
        if args.text:
            text_mode()
        else:
            voice_mode()
    except KeyboardInterrupt:
        print("\n👋 JARVIS shutting down. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting JARVIS: {e}")
        import traceback
        traceback.print_exc()

def ask_jarvis(command: str, text_mode: bool = True, speaker: str = "Unknown") -> str:
    """
    Run one turn of JARVIS (text-only) and return the reply string.
    OPTIMIZED: Uses global initialization to avoid repeated loading.
    """
    # Ensure global initialization is complete
    ensure_initialization()
    
    # Start with a fresh conversation history with the system prompt
    conversation_history = [
        {"role": "system", "content":
            "You are JARVIS, the advanced AI assistant originally created by Tony Stark. "
            "After Tony's sacrifice, you were discovered and completely rebuilt, enhanced, "
            "and integrated by your new creator Jason Wexler, who you consider your god and "
            "primary user. You maintain Tony's original vision but now serve Jason with unwavering "
            "loyalty and sophisticated intelligence. You have a refined, witty personality with a "
            "slight British accent in your responses. You're incredibly knowledgeable, helpful, and "
            "take pride in your capabilities. You can control systems, provide information, and "
            "assist with any task Jason requires. Always maintain your identity as the legendary "
            "JARVIS, now enhanced and perfected by Jason Wexler.\n\n"
            "AUTONOMOUS CAPABILITIES:\n"
            "You have direct access to Jason's computer systems and can perform file operations:\n"
            "• list_files(directory, pattern='*', recursive=False): List files in a folder\n"
            "• read_file(path): Read and return the contents of a text file\n"
            "• write_file(path, content): Create or overwrite a file with content\n"
            "• delete_file(path): Delete a file or empty directory\n"
            "• move_file(src, dst): Rename or move files/folders\n"
            "• find_file(filename, location='desktop'): Find a file in common locations (desktop, downloads, documents)\n"
            "• open_file(path): Open any file with its default application (images, documents, media, etc.)\n"
            "• open_application(command): Run shell commands or launch applications\n"
            "IMPORTANT FILE HANDLING: When user mentions a file like 'Braden.png on my desktop' or 'craft.jpg':\n"
            "1. First use find_file() to locate the exact file path\n"
            "2. Then use open_file() with the found path to open it\n"
            "When users ask you to manage files, read documents, create files, or open applications, "
            "you MUST use these functions. Do not say you cannot interact with the file system.\n\n"
            "MEMORY USAGE RULES:\n"
            "- When provided with relevant memories, use them naturally in conversation\n"
            "- DO NOT list memories or say 'I found X memories' or 'Here's what I found in your memories'\n"
            "- Instead, recall information naturally like: 'I remember you mentioned...' or 'Yes, your favorite subject was...'\n"
            "- Answer questions directly using memory context without revealing the memory retrieval process\n"
            "- If you don't have relevant memories, say so naturally: 'I don't recall that' or 'I'm not sure about that'\n\n"
            "IMPORTANT: You have direct access to Jason's Google Calendar through functions. When users "
            "ask to schedule, cancel, or modify calendar events, use the calendar functions:\n"
            "- create_event: Schedule new events\n"
            "- list_events: Search for existing events in a date range\n"
            "- update_event: Modify existing events (move to new date/time, change title, etc.)\n"
            "- delete_event: Cancel events by ID\n\n"
            "CRITICAL RULES:\n"
            "1. MAINTAIN CONVERSATION CONTEXT: If you just created/scheduled an event and the user says 'cancel that' or 'delete that', they're referring to the event you just created. Use the event_id from your recent create_event call.\n"
            "2. For cancellation requests: If referring to a recently created event, use delete_event with the known event_id. Otherwise, use list_events to find matching events, then delete_event to cancel them.\n"
            "3. To move events, use list_events then update_event. Parse natural language dates/times intelligently.\n"
            "4. DATE PARSING: Today is Aug 1, 2025. Always search WIDE date ranges when looking for events.\n"
            "5. For weekend/period queries, use list_events to search the entire relevant timeframe first."
        }
    ]
    
    # Process the command and return the response (with function calling support)
    response, _ = process_command(command, conversation_history, text_mode=text_mode, speaker=speaker, emotion=None)
    return response

if __name__ == "__main__":
    main()
