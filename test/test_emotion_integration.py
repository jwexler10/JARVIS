#!/usr/bin/env python3
"""
Test script for emotion detection integration
"""

from emotion import detect_emotion
import os

def test_emotion_detection():
    """Test the emotion detection on an existing audio file."""
    
    # Check if we have an audio file to test with
    test_files = ["command.wav", "input.wav", "enroll_Jason.wav"]
    
    test_file = None
    for file in test_files:
        if os.path.exists(file):
            test_file = file
            break
    
    if not test_file:
        print("❌ No audio files found for testing")
        return
    
    print(f"🧪 Testing emotion detection with file: {test_file}")
    
    try:
        emotion = detect_emotion(test_file)
        print(f"✅ Detected emotion: {emotion}")
        
        # Test the empathic response logic (now only for sad emotions)
        if emotion == "sad":
            response = "I sense you may be upset. Is there anything I can do to help?"
        else:
            response = f"No empathic response - emotion detected: {emotion} (only responds to 'sad')"
        
        print(f"🤖 JARVIS would respond: '{response}'")
        
    except Exception as e:
        print(f"❌ Error during emotion detection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_emotion_detection()
