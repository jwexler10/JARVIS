from tts import init_tts, speak

if __name__ == "__main__":
    # Initialize engine with a known Windows voice:
    engine = init_tts(voice_name="Zira", rate=150, volume=1.0)
    speak("Hello, I am Jarvis. Testing text to speech.", engine)
