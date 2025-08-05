import json
import openai

def load_api_key(config_path="config.json"):
    with open(config_path) as f:
        config = json.load(f)
    openai.api_key = config.get("openai_api_key")

def transcribe_audio(filename="input.wav"):
    print(f"Transcribing {filename} with Whisper-1…")
    with open(filename, "rb") as audio_file:
        # new interface:
        transcript = openai.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1"
        )
    text = transcript.text
    print("Transcription result:")
    print(text)
    return text

if __name__ == "__main__":
    load_api_key()
    transcribe_audio()
