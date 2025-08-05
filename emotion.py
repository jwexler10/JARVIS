# emotion.py - Simplified emotion detection using speech features

import soundfile as sf
import numpy as np
import os

def detect_emotion(wav_path: str) -> str:
    """
    Analyze the given WAV file and return a basic emotion estimate.
    This is a simplified version that analyzes basic audio features.
    """
    try:
        # 1) Read audio as a NumPy array
        wav, sr = sf.read(wav_path)
        
        # Handle stereo files
        if wav.ndim > 1:
            wav = wav[:, 0]  # Take first channel
        
        # Basic audio feature analysis
        # Calculate energy (RMS)
        energy = np.sqrt(np.mean(wav**2))
        
        # Calculate zero crossing rate (indicates speech characteristics)
        zero_crossings = np.sum(np.diff(np.sign(wav)) != 0)
        zcr = zero_crossings / len(wav)
        
        # Calculate spectral features (simplified)
        fft = np.fft.fft(wav)
        magnitude = np.abs(fft)
        spectral_centroid = np.sum(magnitude * np.arange(len(magnitude))) / np.sum(magnitude)
        
        # Simple heuristic emotion classification based on audio features
        if energy > 0.05:  # High energy
            if zcr > 0.1:  # High variability
                return "excited"
            else:
                return "happy"
        elif energy < 0.01:  # Low energy
            if spectral_centroid < len(wav) * 0.3:  # Lower frequencies
                return "sad"
            else:
                return "calm"
        else:  # Medium energy
            if zcr > 0.08:
                return "neutral"
            else:
                return "content"
                
    except Exception as e:
        print(f"Error analyzing emotion: {e}")
        return "neutral"

# For more advanced emotion recognition, you would need:
# 1. A properly trained model (like the SpeechBrain one we tried)
# 2. More sophisticated feature extraction
# 3. Better compatibility between dependencies

def detect_emotion_advanced(wav_path: str) -> str:
    """
    Placeholder for advanced emotion detection.
    This would use a trained model when dependencies are resolved.
    """
    # For now, fall back to basic detection
    return detect_emotion(wav_path)
