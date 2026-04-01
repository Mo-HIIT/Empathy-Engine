"""Standalone pyttsx3 worker for VoxSentiment.

Usage:
    python voice_worker.py <output_path> <voice_id> <rate_wpm> <volume> <text>

Generates an AIFF file at <output_path> using the specified voice settings.
"""
from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) < 6:
        print("Usage: voice_worker.py <output> <voice_id> <rate> <volume> <text...>", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    voice_id = sys.argv[2]
    rate_wpm = int(sys.argv[3])
    volume = float(sys.argv[4])
    text = " ".join(sys.argv[5:])

    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("voice", voice_id)
    engine.setProperty("rate", rate_wpm)
    engine.setProperty("volume", max(0.0, min(1.0, volume)))
    engine.save_to_file(text, output_path)
    engine.runAndWait()
    engine.stop()


if __name__ == "__main__":
    main()
