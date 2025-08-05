# enroll.py
import argparse
from audio_input import record_audio           # your existing recorder
from speaker_id import enroll

def main():
    parser = argparse.ArgumentParser(
        description="Record a sample and enroll a new speaker"
    )
    parser.add_argument("name", help="Speaker name (e.g. 'Jason')")
    parser.add_argument(
        "--duration", type=int, default=10,
        help="How many seconds to record (default 10)"
    )
    args = parser.parse_args()

    wav_file = f"enroll_{args.name}.wav"
    print(f"[enroll] Recording {args.duration}s for speaker '{args.name}'…")
    record_audio(filename=wav_file, duration=args.duration)
    print(f"[enroll] Saved sample to {wav_file}. Computing embedding…")

    enroll(args.name, wav_file)
    print("[enroll] Done. You can now identify this speaker in your main loop.")

if __name__ == "__main__":
    main()
