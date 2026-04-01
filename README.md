# VoxSentiment - Intelligent Text-to-Speech Engine

An advanced emotion-aware Text-to-Speech (TTS) service that detects **12 distinct emotional states** from text and dynamically modulates synthesized speech with custom voice parameters.

Built as a unique alternative to traditional TTS systems, VoxSentiment bridges **NLP emotion classification** into **expressive, SSML-enhanced audio output**.

---

## Features

- **12 Extended Emotions** — happy, melancholy, furious, shocked, calm, anxious, disgusted, curious, empathetic, excited, bored, confident
- **Dynamic Intensity Scaling** — enhanced heuristic scoring that differentiates mild expressions from intense ones
- **Dual TTS Engines** — `gTTS` (Google) for most emotions; `pyttsx3` with native female voice for stronger emotions
- **5 Vocal Parameters** — rate, pitch, volume, sentence pauses, word emphasis — all emotion-driven
- **SSML Integration** — post-processing layer with `<break>`, `<emphasis>`, and `<prosody>` effects
- **FastAPI Backend** — high-performance API with async support
- **Modern Purple Gradient UI** — Tailwind CSS, glass-morphism design, animated emotion badges

---

## Project Structure

```
Darwix/
├── app.py                  # FastAPI app, routing, TTS generation
├── sentiment_engine.py     # Emotion detection, intensity scaling, voice mapping
├── audio_processor.py      # SSML post-processing (pauses, emphasis, markup)
├── voice_worker.py         # pyttsx3 subprocess worker
├── requirements.txt        # Python dependencies
├── README.md
├── templates/
│   └── index.html          # Web interface (Tailwind CSS)
├── static/                 # Static assets (auto-created)
└── generated_audio/        # Generated MP3 files (auto-created)
```

---

## Local Setup

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Install FFmpeg (required by pydub)

On Windows:
- Download from https://ffmpeg.org/download.html
- Add to PATH

On macOS:
```bash
brew install ffmpeg
```

On Ubuntu/Debian:
```bash
sudo apt install ffmpeg
```

### 4) Run the server

```bash
uvicorn app:app --reload
```

Open: http://127.0.0.1:8000

---

## API

### `POST /api/synthesize`

**Request:**

```json
{ "text": "I am absolutely THRILLED about this news!!!" }
```

**Response:**

```json
{
  "emotion": "excited",
  "intensity": 0.856,
  "raw_label": "joy",
  "raw_score": 0.921,
  "all_scores": {
    "joy": 0.921, "surprise": 0.045, "neutral": 0.018, ...
  },
  "tts": {
    "rate": 1.214, "pitch": 2.140, "volume_db": 2.568,
    "pause_ms": 50, "emphasis": 1.257
  },
  "ssml": "<speak version=\"1.0\">\n  <prosody rate=\"+21%\" ...>...</prosody>\n</speak>",
  "audio_url": "/audio/abc123.mp3"
}
```

---

## Differences from Original Project

| Aspect | Original (Empathy Engine) | VoxSentiment |
|--------|---------------------------|--------------|
| **Brand** | Empathy Engine | VoxSentiment |
| **Emotions** | 9 emotions (joy, sadness, anger, etc.) | 12 emotions (happy, furious, excited, confident, etc.) |
| **UI Theme** | Light/clean | Purple gradient, glass-morphism |
| **Voice** | Male (Daniel) for anger/disgust | Female (Zira) for strong emotions |
| **Detection** | Concerned, Inquisitive derived | Curious, Excited, Confident, Bored, Empathetic |
| **API Endpoint** | `/api/generate` | `/api/synthesize` |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Uvicorn |
| Emotion NLP | HuggingFace Transformers (`distilroberta`) |
| TTS (online) | gTTS (Google Text-to-Speech) |
| TTS (offline) | pyttsx3 |
| Audio processing | pydub + FFmpeg |
| Frontend | HTML + Tailwind CSS + vanilla JS |
| SSML | Custom post-processing layer |

---

## Notes

- **First request is slow** — the Transformers model (~300 MB) downloads on first use
- **FFmpeg required** — essential for pydub MP3 encoding
- **Windows voice** — uses Zira female voice via pyttsx3
- **`audioop-lts`** — required on Python 3.13+ since `audioop` was removed from stdlib

---


