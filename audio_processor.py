"""SSML-inspired audio post-processor for VoxSentiment.

Applies Speech Synthesis Markup Language concepts at the audio level:
- <break>  → silence inserted between sentences / clauses
- <emphasis> → volume boost on emotionally charged words
- <prosody>  → rate / pitch / volume handled by sentiment_engine
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from pydub import AudioSegment


def apply_ssml_effects(audio: AudioSegment, text: str,
                       params: Dict[str, float]) -> AudioSegment:
    pause_ms = int(params.get("pause_ms", 160))
    emphasis_factor = float(params.get("emphasis", 1.0))

    audio = _insert_sentence_pauses(audio, text, pause_ms)

    if abs(emphasis_factor - 1.0) > 0.01:
        db_boost = (emphasis_factor - 1.0) * 7.0
        audio = audio + db_boost

    return audio


def _insert_sentence_pauses(audio: AudioSegment, text: str,
                            pause_ms: int) -> AudioSegment:
    if pause_ms <= 0:
        return audio

    sentences = re.split(r'(?<=[.!?;,])\s+', text.strip())
    n_sentences = len(sentences)

    if n_sentences <= 1:
        return audio

    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        return audio

    silence = AudioSegment.silent(duration=pause_ms)
    duration_ms = len(audio)

    result = AudioSegment.empty()
    char_offset = 0

    for idx, sentence in enumerate(sentences):
        char_offset += len(sentence)
        t_start = int((char_offset - len(sentence)) / total_chars * duration_ms)
        t_end = int(char_offset / total_chars * duration_ms)
        t_end = min(t_end, duration_ms)

        segment = audio[t_start:t_end]
        result += segment

        if idx < n_sentences - 1:
            result += silence

    return result


def generate_ssml_markup(text: str, emotion: str, intensity: float,
                         params: Dict[str, float]) -> str:
    rate_pct = int((float(params.get("rate", 1.0)) - 1.0) * 100)
    pitch_st = float(params.get("pitch", 0.0))
    volume_db = float(params.get("volume_db", 0.0))
    pause_ms = int(params.get("pause_ms", 160))
    emphasis = params.get("emphasis", 1.0)

    rate_str = f"{rate_pct:+d}%" if rate_pct != 0 else "default"
    pitch_str = f"{pitch_st:+.1f}st" if abs(pitch_st) > 0.01 else "default"

    if volume_db > 1.0:
        vol_str = "loud"
    elif volume_db < -1.0:
        vol_str = "soft"
    else:
        vol_str = "medium"

    if emphasis > 1.2:
        emph_level = "strong"
    elif emphasis < 0.9:
        emph_level = "reduced"
    else:
        emph_level = "moderate"

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    ssml_lines = [f'<speak version="1.0">']
    ssml_lines.append(f'  <prosody rate="{rate_str}" pitch="{pitch_str}" volume="{vol_str}">')

    for idx, sentence in enumerate(sentences):
        ssml_lines.append(f'    <emphasis level="{emph_level}">{sentence}</emphasis>')
        if idx < len(sentences) - 1:
            ssml_lines.append(f'    <break time="{pause_ms}ms"/>')

    ssml_lines.append('  </prosody>')
    ssml_lines.append('</speak>')

    return "\n".join(ssml_lines)
