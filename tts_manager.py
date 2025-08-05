import pyttsx3
from threading import Thread

class TTSManager:
    def __init__(self, voice_name=None, rate=150, volume=1.0):
        self.engine = pyttsx3.init()
        # Configure the engine
        if voice_name:
            for v in self.engine.getProperty("voices"):
                if voice_name.lower() in v.name.lower():
                    self.engine.setProperty("voice", v.id)
                    break
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)

    def speak_async(self, text: str):
        """Start speaking in a background thread."""
        def _run():
            self.engine.say(text)
            self.engine.runAndWait()
        self.thread = Thread(target=_run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop speaking immediately."""
        self.engine.stop()

    def is_busy(self) -> bool:
        """Return True if still speaking."""
        return self.engine.isBusy()
