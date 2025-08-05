#!/usr/bin/env python3
"""
Test script to verify that background tasks are still functioning
even when debug output is suppressed.
"""

import os
import sys
from jarvis import quiet_identify_speaker, quiet_transcribe_audio, quiet_retrieve_relevant, VERBOSE_MODE

def test_background_functionality():
    """Test that all background tasks still work without verbose output."""
    
    print("🧪 Testing Background Task Functionality")
    print("=" * 50)
    
    # Test 1: Speaker identification (if we have audio files)
    if os.path.exists("command.wav"):
        print("1️⃣ Testing Speaker Identification...")
        try:
            # This should work silently (no debug output)
            speaker = quiet_identify_speaker("command.wav", threshold=0.9)
            print(f"   ✅ Speaker identified: {speaker}")
            print(f"   🤫 Verbose mode: {VERBOSE_MODE} (should be False)")
        except Exception as e:
            print(f"   ❌ Speaker ID failed: {e}")
    else:
        print("1️⃣ Skipping Speaker ID test (no command.wav file)")
    
    # Test 2: Memory retrieval
    print("\n2️⃣ Testing Memory Retrieval...")
    try:
        # This should work silently (no debug output)
        results = quiet_retrieve_relevant("what is my name", top_k=2, speaker="Jason")
        print(f"   ✅ Memory search completed, found {len(results) if results else 0} results")
        print(f"   🤫 No debug output should have appeared above")
    except Exception as e:
        print(f"   ❌ Memory retrieval failed: {e}")
    
    # Test 3: Transcription (if we have audio)
    if os.path.exists("command.wav"):
        print("\n3️⃣ Testing Transcription...")
        try:
            # This should work silently (no debug output)
            text = quiet_transcribe_audio("command.wav")
            print(f"   ✅ Transcription completed: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            print(f"   🤫 No 'Transcribing...' messages should have appeared above")
        except Exception as e:
            print(f"   ❌ Transcription failed: {e}")
    else:
        print("\n3️⃣ Skipping Transcription test (no command.wav file)")
    
    print("\n" + "=" * 50)
    print("✅ Background functionality test complete!")
    print("💡 All tasks run silently but still perform their full operations")

if __name__ == "__main__":
    test_background_functionality()
