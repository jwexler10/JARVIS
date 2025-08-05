# test_speaker_id.py
import os
from audio_input import record_audio_with_vad
from speaker_id import identify_speaker, enroll

def test_identification():
    """Test speaker identification with a new recording."""
    print("=== Testing Speaker Identification ===")
    
    # Record a test sample
    test_file = "test_voice.wav"
    print("Record a test sample...")
    if not record_audio_with_vad(filename=test_file, timeout=15, phrase_timeout=1.5):
        print("Failed to record audio")
        return
    
    # Identify the speaker
    result = identify_speaker(test_file)
    print(f"\n🔊 Identified speaker: {result}")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)

def enroll_speaker():
    """Enroll a new speaker."""
    print("=== Enrolling New Speaker ===")
    name = input("Enter speaker name: ").strip()
    if not name:
        print("Invalid name")
        return
    
    # Record enrollment sample
    enroll_file = f"enroll_{name}.wav"
    print(f"Recording enrollment sample for {name}...")
    if not record_audio_with_vad(filename=enroll_file, timeout=15, phrase_timeout=1.5):
        print("Failed to record audio")
        return
    
    # Enroll the speaker
    try:
        enroll(name, enroll_file)
        print(f"✅ Successfully enrolled {name}")
    except Exception as e:
        print(f"❌ Enrollment failed: {e}")

def main():
    while True:
        print("\n=== Speaker ID Test Tool ===")
        print("1. Enroll a new speaker")
        print("2. Test identification")
        print("3. Exit")
        
        choice = input("Choose an option (1-3): ").strip()
        
        if choice == "1":
            enroll_speaker()
        elif choice == "2":
            test_identification()
        elif choice == "3":
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
