import speech_recognition as sr
import time

def record_audio_with_vad(filename="input.wav", timeout=15, phrase_timeout=1.5):
    """
    Record audio using voice activity detection.
    Listens until you stop talking, with intelligent silence detection.
    
    Args:
        filename: Output file name
        timeout: Maximum total recording time (safety limit)
        phrase_timeout: Seconds of silence before stopping recording
    """
    r = sr.Recognizer()
    
    # Optimize recognizer settings for better voice detection
    r.energy_threshold = 300  # Minimum audio energy to consider for recording
    r.dynamic_energy_threshold = True  # Automatically adjust to ambient noise
    r.pause_threshold = phrase_timeout  # Seconds of non-speaking audio before phrase ends
    
    # Quick ambient noise adjustment
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
    
    with sr.Microphone() as source:
        print("🎤 Speak naturally... I'll wait for you to finish.")
        
        try:
            # Listen with intelligent stopping - use timeout and phrase_time_limit
            audio = r.listen(
                source, 
                timeout=timeout,              # Max time to wait for speech to start
                phrase_time_limit=None       # No hard limit - let them speak!
            )
            
            print("🎤 Got it! Processing...")
            
        except sr.WaitTimeoutError:
            print("⏰ Silence detected - no input received")
            return False
    
    # Save to WAV
    try:
        with open(filename, "wb") as f:
            f.write(audio.get_wav_data())
        return True
    except Exception as e:
        print(f"❌ Failed to save audio: {e}")
        return False

def record_audio(filename="input.wav", duration=5):
    """
    Legacy function for backwards compatibility.
    Now uses voice activity detection instead of fixed duration.
    """
    return record_audio_with_vad(filename, timeout=15, phrase_timeout=1.5)

if __name__ == "__main__":
    record_audio_with_vad()
