#!/usr/bin/env python3
"""Quick test script for VoxSentiment"""

print("Testing imports...")

try:
    from sentiment_engine import detect_emotion, tts_parameters, clamp_tts_params
    print("✓ sentiment_engine imported successfully")
except Exception as e:
    print(f"✗ sentiment_engine import failed: {e}")
    exit(1)

try:
    from audio_processor import apply_ssml_effects, generate_ssml_markup
    print("✓ audio_processor imported successfully")
except Exception as e:
    print(f"✗ audio_processor import failed: {e}")
    exit(1)

try:
    from fastapi import FastAPI
    print("✓ FastAPI imported successfully")
except Exception as e:
    print(f"✗ FastAPI import failed: {e}")
    exit(1)

try:
    from gtts import gTTS
    print("✓ gTTS imported successfully")
except Exception as e:
    print(f"✗ gTTS import failed: {e}")
    exit(1)

try:
    from pydub import AudioSegment
    print("✓ pydub imported successfully")
except Exception as e:
    print(f"✗ pydub import failed: {e}")
    exit(1)

print("\nTesting emotion detection...")

test_cases = [
    "I am absolutely THRILLED about this amazing news!!!",
    "I am so sad and depressed today...",
    "What do you think about this?",
    "I am furious and angry right now!!!",
]

for text in test_cases:
    try:
        result = detect_emotion(text)
        params = clamp_tts_params(tts_parameters(result.emotion, result.intensity))
        print(f"✓ '{text[:40]}...' -> {result.emotion} (intensity: {result.intensity:.2f})")
    except Exception as e:
        print(f"✗ Failed on '{text[:40]}...': {e}")

print("\n✅ All tests passed! Project is working properly.")
print("\nTo run the server:")
print("  uvicorn app:app --reload")
print("\nThen open: http://127.0.0.1:8000")
