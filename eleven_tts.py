# eleven_tts.py

import json
import winsound
import wave
import tempfile
import os
import threading
import time
import msvcrt
import subprocess
import sys
from elevenlabs.client import ElevenLabs

# Load your ElevenLabs API key
cfg = json.load(open("config.json"))
client = ElevenLabs(api_key=cfg["elevenlabs_api_key"])

# Replace with the voice ID you like or your custom Jarvis clone
JARVIS_VOICE_ID = "0ftRGguxoxqhsFVf0V6K"

# Global flag for interrupt control
_interrupt_requested = threading.Event()
_current_audio_process = None

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

def speak(text: str):
    """
    Generate PCM audio via ElevenLabs, save as WAV, play it with interrupt capability.
    Press 'j' to interrupt speech.
    """
    print(f"🔊 [ElevenLabs→WAV] {text}")
    
    # Clear any previous interrupt flag
    _interrupt_requested.clear()
    global _current_audio_process
    
    try:
        # Request PCM output from ElevenLabs
        audio_stream = client.text_to_speech.convert(
            voice_id=JARVIS_VOICE_ID,
            text=text,
            model_id="eleven_multilingual_v1",
            optimize_streaming_latency="0",
            output_format="pcm_22050"  # raw PCM
        )
        # Collect all audio bytes
        audio_bytes = b"".join(audio_stream)

        # Write to a temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_filename = tmp.name
        with wave.open(temp_filename, 'wb') as wav_file:
            wav_file.setnchannels(1)          # Mono
            wav_file.setsampwidth(2)          # 16-bit samples
            wav_file.setframerate(22050)      # 22.05 kHz
            wav_file.writeframes(audio_bytes)

        # Use Windows Media Player for more controllable playback
        def play_with_process():
            global _current_audio_process
            try:
                # Use powershell to play audio with better control
                cmd = [
                    'powershell', '-Command',
                    f'(New-Object Media.SoundPlayer "{temp_filename}").PlaySync()'
                ]
                _current_audio_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                _current_audio_process.wait()
            except Exception as e:
                # Fallback to winsound if powershell fails
                try:
                    winsound.PlaySound(temp_filename, winsound.SND_FILENAME)
                except:
                    pass
            finally:
                _current_audio_process = None
        
        playback_thread = threading.Thread(target=play_with_process)
        playback_thread.daemon = True
        playback_thread.start()
        
        # Monitor for interrupt while audio plays
        while playback_thread.is_alive():
            if check_for_interrupt():
                # Kill the audio process immediately
                if _current_audio_process:
                    try:
                        _current_audio_process.terminate()
                        _current_audio_process.kill()
                    except:
                        pass
                
                # Also try to stop any winsound playback
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except:
                    pass
                
                break
            time.sleep(0.05)  # Check every 50ms for faster response
        
        # Wait for thread to finish if not interrupted
        playback_thread.join(timeout=0.1)

        # Cleanup temp file
        try:
            os.remove(temp_filename)
        except:
            pass  # Ignore cleanup errors

    except Exception as e:
        print(f"❌ ElevenLabs WAV playback failed: {e}")
        # Fallback to local TTS
        from tts import speak as fallback_speak
        fallback_speak(text)
