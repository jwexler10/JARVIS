import pyttsx3
import threading
import time
import msvcrt

# Global flag for interrupt control
_interrupt_requested = threading.Event()
_current_engine = None

def check_for_interrupt():
    """
    Check if 'j' key was pressed to interrupt speech.
    """
    if msvcrt.kbhit():
        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
        if key == 'j':
            _interrupt_requested.set()
            print("\n⏹️ Speech interrupted by user")
            return True
    return False

def init_tts(voice_name=None, rate=150, volume=1.0):
    engine = pyttsx3.init()
    # pick a SAPI5 voice by name substring
    if voice_name:
        for v in engine.getProperty("voices"):
            if voice_name.lower() in v.name.lower():
                engine.setProperty("voice", v.id)
                break
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)
    return engine

def speak(text, engine=None):
    """
    Speak text using a fresh engine with interrupt capability.
    Press 'j' to interrupt speech.
    """
    print(f"🔊 [TTS] Speaking: {text}")
    
    # Clear any previous interrupt flag
    _interrupt_requested.clear()
    global _current_engine
    
    # Always create a fresh engine to avoid pyttsx3 reuse issues
    fresh_engine = init_tts(voice_name="Zira", rate=150, volume=1.0)
    _current_engine = fresh_engine
    
    # Start TTS in a separate thread so we can monitor for interrupts
    def speak_audio():
        try:
            fresh_engine.say(text)
            fresh_engine.runAndWait()
        except Exception as e:
            print(f"❌ TTS error: {e}")
        finally:
            try:
                fresh_engine.stop()
            except:
                pass
            _current_engine = None
    
    speech_thread = threading.Thread(target=speak_audio)
    speech_thread.daemon = True
    speech_thread.start()
    
    # Monitor for interrupt while speech plays
    while speech_thread.is_alive():
        if check_for_interrupt():
            # Stop the TTS engine immediately
            if _current_engine:
                try:
                    _current_engine.stop()
                except:
                    pass
            break
        time.sleep(0.05)  # Check every 50ms for faster response
    
    # Wait for thread to finish if not interrupted
    speech_thread.join(timeout=0.1)
    
    # Ensure cleanup
    try:
        if _current_engine:
            _current_engine.stop()
    except:
        pass
