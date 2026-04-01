# VoxSentiment

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> **Text-to-Speech that actually understands how you feel.**

VoxSentiment is an intelligent TTS (Text-to-Speech) engine that goes beyond robotic voice synthesis. It detects emotions in your text and automatically adjusts the speech output—modulating pitch, speed, volume, and pauses to match the emotional tone.

Traditional TTS systems speak in a flat, monotone voice. VoxSentiment reads between the lines, recognizing whether you're happy, sad, excited, or curious, and then adapts the voice accordingly. The result? Speech that sounds genuinely human.

---

## What Makes It Special

### 12 Emotion States

Unlike typical TTS systems, VoxSentiment recognizes and vocalizes **12 distinct emotional states**:

| Emotion | How It Sounds |
|:--------|:--------------|
| **Happy** | Upbeat, faster tempo, higher pitch |
| **Melancholy** | Slow, soft, gentle pauses |
| **Furious** | Fast, loud, sharp emphasis |
| **Shocked** | Quick, raised pitch, energetic |
| **Anxious** | Hurried, tense, quieter |
| **Disgusted** | Slow, lower tone, assertive |
| **Curious** | Rising intonation, questioning |
| **Empathetic** | Warm, measured, comforting |
| **Excited** | Very fast, high pitch, loud |
| **Bored** | Slow, soft, drawn-out pauses |
| **Confident** | Steady, clear, authoritative |
| **Calm** | Neutral, balanced, relaxed |

### Smart Intensity Detection

The system doesn't just detect emotions—it measures **how intense they are**:

- "I'm happy" produces calm, moderate joy
- "I am SOOO HAPPY!!!" triggers maximum excitement with raised pitch and faster speech

The algorithm analyzes punctuation, capitalization, word choice, and sentence structure to get the intensity just right. It picks up on exclamation marks, ALL CAPS words, intensifiers like "very" and "extremely," and elongated words like "sooo."

### Dynamic Voice Modulation

Every emotion maps to 5 vocal parameters:
- **Rate** — how fast or slow the speech is
- **Pitch** — the tone of voice (higher or lower)
- **Volume** — loudness or softness
- **Pauses** — duration of breaks between sentences
- **Emphasis** — stress on particular words

---

## Getting Started

### Prerequisites
- Python 3.8 or higher
- FFmpeg installed on your system

### Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Mo-HIIT/Empathy-Engine.git
cd Empathy-Engine
```

**2. Create a virtual environment:**
```bash
python -m venv .venv
```

Activate it:
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

**3. Install Python packages:**
```bash
pip install -r requirements.txt
```

**4. Install FFmpeg:**

| OS | Command |
|:---|:--------|
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH |
| macOS | `brew install ffmpeg` |
| Ubuntu/Debian | `sudo apt install ffmpeg` |

**5. Launch the server:**
```bash
uvicorn app:app --reload
```

**6. Open in your browser:**
```
http://127.0.0.1:8000
```

---

## How to Use

### Web Interface

1. Type or paste any text into the input box
2. Click **"Synthesize Speech"**
3. Watch as the system detects the emotion and displays the intensity
4. Listen to your text spoken with the appropriate emotional tone

**Try these examples:**
- "I can't believe we won!!! This is absolutely incredible!!!"
- "I'm worried about how things will turn out..."
- "What do you think about this proposal?"
- "I'm totally confident this will work."

### API Usage

Send a POST request to `/api/synthesize`:

```bash
curl -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "I am absolutely THRILLED about this news!!!"}'
```

**Response:**
```json
{
  "emotion": "excited",
  "intensity": 0.856,
  "tts": {
    "rate": 1.214,
    "pitch": 2.140,
    "volume_db": 2.568,
    "pause_ms": 50,
    "emphasis": 1.257
  },
  "audio_url": "/audio/abc123.mp3"
}
```

---

## Project Structure

```
Empathy-Engine/
├── app.py                 # Main FastAPI application
├── sentiment_engine.py    # Core emotion detection logic
├── audio_processor.py     # SSML & audio post-processing
├── voice_worker.py        # TTS subprocess handler
├── test_project.py        # Test suite
├── templates/
│   └── index.html         # Purple gradient web interface
├── requirements.txt       # Dependencies
└── README.md
```

---

## Under the Hood

### Emotion Detection

We use the [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base) model, a fine-tuned RoBERTa from HuggingFace that recognizes 7 base emotions. We extend this to 12 emotions through contextual analysis of text patterns—looking for question marks to detect curiosity, combining fear and sadness signals for empathy, and spotting excitement keywords.

### Intensity Scoring

Our custom algorithm blends:
- **30%** Model confidence (which emotion is detected)
- **70%** Textual signals (how intense the expression is)

The textual analysis looks for:
- Punctuation (exclamation marks and question marks)
- Capitalization (ALL CAPS words)
- Intensifiers ("very," "extremely," "sooo")
- Diminishers ("slightly," "somewhat")

### Audio Processing

- **gTTS** (Google Text-to-Speech) generates the base audio with natural-sounding voice
- **pydub** handles pitch shifting, speed adjustment, and volume control
- **pyttsx3** serves as a backup offline TTS engine for specific emotions

---

## Quick Test

Want to verify everything works without starting the server?

```bash
python test_project.py
```

This tests all imports and runs a few emotion detection examples.

---

## Tech Stack

- **Backend:** FastAPI + Uvicorn
- **ML/NLP:** HuggingFace Transformers, PyTorch
- **TTS:** gTTS, pyttsx3
- **Audio:** pydub + FFmpeg
- **Frontend:** Tailwind CSS, vanilla JavaScript

---

## Important Notes

- **First launch takes time** — The emotion model (~300MB) downloads automatically on first use from HuggingFace
- **FFmpeg is essential** — Without it, audio file generation will fail
- **Python 3.13+ users** — `audioop-lts` is included in requirements for compatibility since the `audioop` stdlib module was removed

---

## Contributing

Found a bug or have an idea for improvement? Contributions are welcome.

1. Fork the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

MIT License — use it freely for personal or commercial projects.

---

<div align="center">

**Made by [Mo-HIIT](https://github.com/Mo-HIIT)**

If you find this useful, consider giving it a star on GitHub.

</div>

---


