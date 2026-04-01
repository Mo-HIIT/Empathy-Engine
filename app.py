from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from gtts import gTTS
from pydub import AudioSegment

from sentiment_engine import clamp_tts_params, detect_emotion, pitch_semitones_to_rate, tts_parameters
from audio_processor import apply_ssml_effects, generate_ssml_markup

# Female voice ID for Windows
FEMALE_VOICE_ID = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"

_WORKER = str(Path(__file__).resolve().parent / "voice_worker.py")
_PYTHON = sys.executable


async def _generate_pyttsx3(text: str, rate_wpm: int, volume: float,
                            voice_id: str, output_path: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        _PYTHON, _WORKER, output_path, voice_id,
        str(rate_wpm), str(volume), text,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"pyttsx3 worker failed: {stderr.decode(errors='replace')}")


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = BASE_DIR / "generated_audio"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="VoxSentiment", version="2.0.0")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/synthesize")
async def synthesize(payload: Dict[str, Any]):
    text = str(payload.get("text", ""))
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        emo = detect_emotion(text)
        params = clamp_tts_params(tts_parameters(emo.emotion, emo.intensity))

        file_id = uuid.uuid4().hex
        base_raw = AUDIO_DIR / f"{file_id}_base"
        final_mp3 = AUDIO_DIR / f"{file_id}.mp3"

        use_pyttsx3 = emo.emotion in {"furious", "disgusted", "confident"}

        if use_pyttsx3:
            base_wav = base_raw.with_suffix(".wav")
            base_wpm = 180
            rate_wpm = int(base_wpm * float(params["rate"]))
            vol_scalar = min(1.0, max(0.3, 0.6 + float(params["volume_db"]) / 12.0))

            await _generate_pyttsx3(
                text, rate_wpm, vol_scalar,
                FEMALE_VOICE_ID, str(base_wav),
            )

            audio = AudioSegment.from_file(str(base_wav))
            original_frame_rate = audio.frame_rate

            semitones = float(params["pitch"])
            if abs(semitones) > 0.01:
                pf = pitch_semitones_to_rate(semitones)
                audio = audio._spawn(audio.raw_data, overrides={
                    "frame_rate": int(original_frame_rate * pf)
                })
                audio = audio.set_frame_rate(original_frame_rate)

            volume_db = float(params["volume_db"])
            if volume_db > 0.01:
                audio = audio + volume_db

            audio = apply_ssml_effects(audio, text, params)

            audio.export(str(final_mp3), format="mp3")
            base_wav.unlink(missing_ok=True)

        else:
            base_mp3 = base_raw.with_suffix(".mp3")
            tts = gTTS(text=text, lang="en")
            tts.save(str(base_mp3))

            audio = AudioSegment.from_file(str(base_mp3), format="mp3")
            original_frame_rate = audio.frame_rate

            rate = float(params["rate"])
            semitones = float(params["pitch"])
            volume_db = float(params["volume_db"])

            if abs(rate - 1.0) > 0.01:
                new_fr = int(original_frame_rate * rate)
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_fr})
                audio = audio.set_frame_rate(original_frame_rate)

            if abs(semitones) > 0.01:
                pf = pitch_semitones_to_rate(semitones)
                cur_fr = audio.frame_rate
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(cur_fr * pf)})
                audio = audio.set_frame_rate(original_frame_rate)

            if abs(volume_db) > 0.01:
                audio = audio + volume_db

            audio = apply_ssml_effects(audio, text, params)

            audio.export(str(final_mp3), format="mp3")
            base_mp3.unlink(missing_ok=True)

        ssml_markup = generate_ssml_markup(text, emo.emotion, emo.intensity, params)

        return JSONResponse(
            {
                "emotion": emo.emotion,
                "intensity": round(float(emo.intensity), 3),
                "raw_label": emo.raw_label,
                "raw_score": round(float(emo.raw_score), 3),
                "all_scores": emo.all_scores,
                "tts": params,
                "ssml": ssml_markup,
                "audio_url": f"/audio/{final_mp3.name}",
            }
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Audio generation failed (missing system dependency). "
                "Make sure ffmpeg is installed and available in PATH. "
                f"Original error: {str(e)}"
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
