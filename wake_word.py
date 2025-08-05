import speech_recognition as sr

WAKE_WORD = "jarvis"

def detect_wake_word(timeout=3):
    """
    Listen for up to `timeout` seconds and return True
    if the wake word is detected in the audio.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"Listening for wake word (‘{WAKE_WORD}’) for {timeout}s…")
        audio = r.listen(source, phrase_time_limit=timeout)
    try:
        text = r.recognize_sphinx(audio).lower()
        print(f"Heard (Sphinx): {text}")
        if WAKE_WORD in text:
            return True
    except sr.UnknownValueError:
        # No intelligible speech detected
        pass
    except sr.RequestError as e:
        print(f"Sphinx error: {e}")
    return False

if __name__ == "__main__":
    if detect_wake_word():
        print("✅ Wake-word detected!")
    else:
        print("— Wake-word NOT detected.")
