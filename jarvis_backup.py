import os
import time
import sys
import select
import argparse
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
from weather import get_weather
from commands import open_application
from search import search_web
from spotify_client import play_spotify_track, play_spotify_playlist
from speaker_id import identify_speaker
from memory import retrieve_relevant, auto_remember_async, load_memory_cache, schedule_index_rebuild, has_speaker_memories  # Updated imports

# Import optimized modules for performance
try:
    from jarvis_all_in_one import ask_jarvis_streaming, get_jarvis, benchmark_performance, ask_jarvis_optimized
    OPTIMIZED_MODE = True
    print("🚀 All-in-one optimized module loaded")
except ImportError as e:
    OPTIMIZED_MODE = False
    print(f"⚠️ Optimized module not available: {e}")

import threading
import asyncio

# Multi-turn context settings
MAX_HISTORY = 8

# Global initialization flags to avoid repeated loading
_api_loaded = False
_memory_loaded = False
_initialization_lock = threading.Lock()

# Conversation mode settings
VERBOSE_MODE = False  # Set to True for debug output, False for natural conversation
STREAMING_MODE = True  # Set to True for optimized streaming responses

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
        # Temporarily redirect stdout to suppress prints
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = retrieve_relevant(query, top_k, speaker)
        finally:
            sys.stdout = old_stdout
        return result

def quiet_auto_remember_async(command, response, speaker):
    """Wrapper to suppress memory storage debug output in conversation mode."""
    if VERBOSE_MODE:
        return auto_remember_async(command, response, speaker)
    else:
        # Temporarily redirect stdout to suppress prints
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = auto_remember_async(command, response, speaker)
        finally:
            sys.stdout = old_stdout
        return result

def ensure_initialization():
    """Ensure API keys and memory are loaded only once."""
    global _api_loaded, _memory_loaded
    
    with _initialization_lock:
        if not _api_loaded:
            load_api_key()
            _api_loaded = True
        
        if not _memory_loaded:
            load_memory_cache()
            _memory_loaded = True

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

def process_command(command: str, conversation_history: list, text_mode: bool = False, speaker: str = "Unknown"):
    """
    Process a user command and return the response.
    Works for both text and voice modes.
    OPTIMIZED: Moved heavy operations to background for faster response.
    """
    cmd_lower = command.lower()
    
    # Quick speaker context setup (simplified to avoid blocking)
    if speaker == "Jason":
        speaker_context = "Jason (my creator and primary user)"
    elif speaker != "Unknown":
        speaker_context = f"{speaker} (authorized user)"
    else:
        speaker_context = "unidentified user"
    
    # 1) Session exit keywords
    if cmd_lower in ["exit", "quit", "stop", "goodbye", "thanks", "thank you"]:
        if speaker == "Jason":
            return "Goodbye, Jason. It's been my pleasure serving you.", True
        elif speaker != "Unknown":
            return f"Goodbye, {speaker}. Have a great day!", True
        else:
            return "Session closed. Glad I could help.", True
    
    # 2) System commands
    if cmd_lower.startswith(("open ", "launch ", "start ")):
        for kw in ("open ", "launch ", "start "):
            if cmd_lower.startswith(kw):
                app = cmd_lower.replace(kw, "", 1).strip()
                break
        app = app.strip(".,!?;:")
        msg = open_application(app)
        if not text_mode:
            speak(f"Okay, opening {app}")
        return f"Opening {app}. {msg}", False
    
    # 3) Weather skill
    elif "weather" in cmd_lower:
        city = cmd_lower.split("in")[-1].strip() if "in" in cmd_lower else "Philadelphia"
        if not text_mode:
            speak(f"Checking the weather in {city}")
        report = get_weather(city)
        if not text_mode:
            speak(report)
        return f"🌤️ Weather in {city}: {report}", False
    
    # 4) Web search skill
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
    
    # 5) Spotify playlist playback
    elif cmd_lower.startswith("play spotify playlist "):
        playlist = command[len("play spotify playlist "):].strip()
        if not text_mode:
            speak(f"Playing your playlist {playlist} on Spotify")
        msg = play_spotify_playlist(playlist)
        return f"🎵 Spotify: {msg}", False
    
    # 6) Spotify track playback
    elif cmd_lower.startswith("play spotify "):
        track = command[len("play spotify "):].strip()
        if not text_mode:
            speak(f"Playing {track} on Spotify")
        msg = play_spotify_track(track)
        return f"🎵 Spotify: {msg}", False
    
    # 7) Fallback to multi-turn GPT with retrieval memory
    else:
        # ➊ Use optimized streaming if available and enabled
        if OPTIMIZED_MODE and STREAMING_MODE and not text_mode:
            try:
                # Use optimized streaming response for voice mode
                import asyncio
                
                # Create async function to handle streaming
                async def stream_response():
                    jarvis_opt = get_jarvis()
                    metrics = await jarvis_opt.process_command_streaming(command, speaker)
                    
                    # Get the response from conversation history
                    if jarvis_opt.conversation_history:
                        return jarvis_opt.conversation_history[-1].get("content", "")
                    return "Response processed"
                
                # Run streaming in event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create task if loop is already running
                        future = asyncio.create_task(stream_response())
                        # For now, return a placeholder - the actual speech happens via streaming
                        return "Processing your request...", False
                    else:
                        # Run in new event loop
                        response = asyncio.run(stream_response())
                        return response, False
                except:
                    # Fallback if async fails
                    pass
                    
            except Exception as e:
                if VERBOSE_MODE:
                    print(f"🔄 Optimized streaming failed, using fallback: {e}")
        
        # ➊ Add speaker context (simplified for speed)
        conversation_history.append({
            "role": "system",
            "content": f"Current speaker: {speaker_context}. Tailor your response appropriately."
        })
        
        # ➋ Quick memory retrieval (background if slow)
        relevant_context = ""
        try:
            # Try fast memory retrieval with short timeout
            relevant = quiet_retrieve_relevant(command, top_k=2, speaker=speaker)  # Reduced from 3 to 2
            if relevant:
                relevant_context = "\n\n".join(f"- {chunk}" for chunk, _ in relevant[:2])  # Limit context
                conversation_history.append({
                    "role": "system",
                    "content": f"Relevant info:\n{relevant_context}"
                })
        except Exception:
            # If memory retrieval fails/is slow, skip it for faster response
            pass
        
        # ➌ Append user message and prune
        conversation_history.append({"role": "user", "content": command})
        conversation_history = prune_history(conversation_history)
        
        # ➍ Get AI response (main bottleneck - keep this fast)
        if OPTIMIZED_MODE and not text_mode:
            # Use optimized all-in-one JARVIS for voice responses
            jarvis_opt = get_jarvis()
            # Extract just the LLM response part
            full_response = jarvis_opt.process_command_sync(command, speaker)
            answer = full_response
        else:
            # Use regular LLM
            answer = chat_with_history(conversation_history)
        
        conversation_history.append({"role": "assistant", "content": answer})
        
        # ➎ Background memory storage (non-blocking)
        def background_memory_task():
            try:
                quiet_auto_remember_async(command, answer, speaker)
            except Exception as e:
                pass  # Silent fail to not interrupt user experience
        
        # Start memory task in background thread
        memory_thread = threading.Thread(target=background_memory_task, daemon=True)
        memory_thread.start()
        
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
            "JARVIS, now enhanced and perfected by Jason Wexler."
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
            response, should_exit = process_command(command, conversation_history, text_mode=True, speaker="Jason")
            
            # Display response cleanly
            print(f"\n🤖 Jarvis: {response}\n")
            
            if should_exit:
                break
    
    except KeyboardInterrupt:
        print("\n👋 Shutting down JARVIS. Goodbye!")
    
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
            "JARVIS, now enhanced and perfected by Jason Wexler."
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
                    
                    command = quiet_transcribe_audio(filename="command.wav").strip()

                    # 2) Check for silence / inactivity
                    if not command:
                        if time.time() - last_activity > 10:
                            speak("No input detected for a while. Ending session.")
                            break
                        continue

                    last_activity = time.time()
                    
                    # Process the command with speaker information
                    response, should_exit = process_command(command, conversation_history, text_mode=False, speaker=speaker)
                    
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
        # Schedule a full memory rebuild on shutdown
        schedule_index_rebuild()

def main():
    """
    Main entry point with argument parsing for text vs voice mode.
    OPTIMIZED: Pre-initialize for faster startup with performance options.
    """
    global VERBOSE_MODE, STREAMING_MODE
    
    print("🤖 JARVIS is initializing...")
    
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
    parser.add_argument(
        "--speed", 
        action="store_true", 
        help="Enable maximum speed optimizations (streaming, fast model, caching)"
    )
    parser.add_argument(
        "--quality", 
        action="store_true", 
        help="Optimize for quality over speed (disable fast model, reduce caching)"
    )
    parser.add_argument(
        "--benchmark", 
        action="store_true", 
        help="Run performance benchmark and exit"
    )
    parser.add_argument(
        "--no-streaming", 
        action="store_true", 
        help="Disable streaming optimizations"
    )
    
    args = parser.parse_args()
    
    # Set global modes
    VERBOSE_MODE = args.verbose
    STREAMING_MODE = not args.no_streaming
    
    # Performance mode configuration
    if args.speed and OPTIMIZED_MODE:
        jarvis_opt = get_jarvis()
        jarvis_opt.optimize_for_speed()
        print("🚀 Maximum speed mode enabled")
    elif args.quality and OPTIMIZED_MODE:
        jarvis_opt = get_jarvis()
        jarvis_opt.optimize_for_quality()
        print("🎯 Quality mode enabled")
    
    # Run benchmark if requested
    if args.benchmark and OPTIMIZED_MODE:
        print("🏃 Running performance benchmark...")
        results = benchmark_performance(num_tests=5)
        print("\n📊 BENCHMARK RESULTS:")
        if "summary" in results:
            summary = results["summary"]
            print(f"   Average total time: {summary['avg_total_ms']:.1f}ms")
            print(f"   Average first token: {summary['avg_first_token_ms']:.1f}ms")
            print(f"   Fastest response: {summary['fastest_ms']:.1f}ms")
            print(f"   Success rate: {summary['success_rate']:.1f}%")
        else:
            print("   Benchmark failed - check optimized modules")
        return
    
    # Pre-initialize essential components for faster response
    ensure_initialization()
    
    # Start warmup if optimized mode is available  
    if OPTIMIZED_MODE:
        jarvis_opt = get_jarvis()  # This starts warmup automatically
        print("🔥 Optimized JARVIS initialized with warmup")
    
    if VERBOSE_MODE:
        print("🔧 Verbose mode enabled - showing debug information")
    else:
        print("🤫 Quiet mode enabled - natural conversation flow")
    
    if STREAMING_MODE and OPTIMIZED_MODE:
        print("⚡ Streaming optimizations enabled")
    elif not OPTIMIZED_MODE:
        print("⚠️ Optimized modules not available - using standard mode")
    
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
            "JARVIS, now enhanced and perfected by Jason Wexler."
        }
    ]
    
    # Process the command and return the response
    response, _ = process_command(command, conversation_history, text_mode=text_mode, speaker=speaker)
    return response

if __name__ == "__main__":
    main()
