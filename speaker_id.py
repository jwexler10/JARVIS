import json
import numpy as np
from numpy.linalg import norm
import soundfile as sf
from resemblyzer import VoiceEncoder

# Path where we persist enrolled embeddings
EMBED_PATH = "speaker_embeddings.json"

# Initialize the Resemblyzer encoder once
encoder = VoiceEncoder()

def embed_file(wav_path: str) -> np.ndarray:
    """
    Load a WAV file and return its speaker embedding (shape ~256,).
    """
    wav, sr = sf.read(wav_path, dtype="float32")
    
    # Let Resemblyzer handle resampling automatically
    return encoder.embed_utterance(wav)

def load_embeddings(path: str = EMBED_PATH) -> dict:
    """Load existing {speaker_name: embedding_list} from JSON (or return empty)."""
    try:
        data = json.load(open(path, encoding="utf-8"))
        # Convert lists back to numpy arrays
        return {name: np.array(vec, dtype=np.float32) for name, vec in data.items()}
    except FileNotFoundError:
        return {}

def save_embeddings(embeds: dict, path: str = EMBED_PATH):
    """Write {speaker_name: embedding_list} to JSON."""
    serial = {name: vec.tolist() for name, vec in embeds.items()}
    json.dump(serial, open(path, "w", encoding="utf-8"), indent=2)

def enroll(speaker_name: str, wav_path: str):
    """
    Compute embedding for wav_path, add it under speaker_name, and save.
    """
    embeds = load_embeddings()
    emb = embed_file(wav_path)
    embeds[speaker_name] = emb
    save_embeddings(embeds)
    print(f"[speaker_id] Enrolled '{speaker_name}' (embedding saved).")


def identify_speaker(wav_path: str,
                     threshold: float = 0.85,  # Increased from 0.75 to 0.85
                     embed_path: str = EMBED_PATH) -> str:
    """
    Given a recorded WAV, compute its embedding and compare
    to all enrolled speaker embeddings. Return the best match
    if similarity ≥ threshold, else return "Unknown".
    """
    # 1) Load all enrolled embeddings
    embeds = load_embeddings(embed_path)  # {name: np.array}
    if not embeds:
        return "Unknown"

    # 2) Embed the incoming audio (let Resemblyzer handle resampling)
    wav, sr = sf.read(wav_path, dtype="float32")
    query_emb = encoder.embed_utterance(wav)

    # 3) Compute cosine similarity to each enrolled speaker
    sims = {name: float(np.dot(query_emb, emb) / (norm(query_emb) * norm(emb) + 1e-8))
            for name, emb in embeds.items()}

    # 4) Debug: Print all similarity scores
    print(f"[speaker_id] Similarity scores:")
    for name, score in sorted(sims.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {score:.3f}")

    # 5) Find best match
    best_name, best_score = max(sims.items(), key=lambda kv: kv[1])
    print(f"[speaker_id] Best match: {best_name} (score: {best_score:.3f}, threshold: {threshold})")
    
    if best_score >= threshold:
        return best_name
    return "Unknown"

