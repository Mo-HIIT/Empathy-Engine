from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, List, Tuple

from transformers import pipeline


# ── Extended emotion set ──────────────────────────────────────────────
SUPPORTED_EMOTIONS = (
    "happy", "melancholy", "furious", "shocked", "calm",
    "anxious", "disgusted", "curious", "empathetic", "excited",
    "bored", "confident"
)


@dataclass(frozen=True)
class EmotionResult:
    emotion: str
    intensity: float
    raw_label: str
    raw_score: float
    all_scores: Dict[str, float] = field(default_factory=dict)


@lru_cache(maxsize=1)
def _emotion_pipeline():
    return pipeline(
        task="text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None,
    )


def detect_emotion(text: str) -> EmotionResult:
    if not text or not text.strip():
        return EmotionResult(
            emotion="calm", intensity=0.0,
            raw_label="neutral", raw_score=1.0,
            all_scores={"neutral": 1.0},
        )

    t = text.strip()
    results = _emotion_pipeline()(t)
    outputs = results[0] if results and isinstance(results[0], list) else results

    all_scores = {str(o["label"]).lower(): round(float(o["score"]), 4) for o in outputs}

    best = max(outputs, key=lambda x: float(x["score"]))
    raw_label = str(best["label"]).lower()
    raw_score = float(best["score"])

    emotion = _classify_extended(t, raw_label, raw_score, all_scores)
    intensity = intensity_scale(t, base_score=raw_score)

    return EmotionResult(
        emotion=emotion, intensity=intensity,
        raw_label=raw_label, raw_score=raw_score,
        all_scores=all_scores,
    )


_CURIOSITY_KEYWORDS = {
    "why", "how", "what if", "wonder", "curious", "interested",
    "tell me", "explain", "learn", "discover", "find out",
    "what is", "who is", "where", "when", "which", "can you"
}

_EXCITEMENT_KEYWORDS = {
    "wow", "awesome", "amazing", "fantastic", "incredible",
    "unbelievable", "wow", "omg", "oh my", "yay", "hooray",
    "can't wait", "looking forward", "excited", "thrilled"
}

_CONFIDENCE_KEYWORDS = {
    "sure", "certain", "definitely", "absolutely", "confident",
    "know", "trust", "believe", "guarantee", "positive",
    "without doubt", "no question", "clearly"
}

_BOREDOM_KEYWORDS = {
    "boring", "tired", "whatever", "meh", "fine",
    "nothing special", "usual", "same old", "dull",
    "uninterested", "dont care", "don't care"
}

_EMPATHY_KEYWORDS = {
    "understand", "feel you", "sorry", "sad to hear",
    "that must be", "poor you", "bless you", "hugging",
    "here for you", "support", "comfort"
}


def _has_keyword_set(text: str, keywords: set) -> bool:
    t = text.lower()
    return any(kw in t for kw in keywords)


def _classify_extended(text: str, raw_label: str, raw_score: float,
                       all_scores: Dict[str, float]) -> str:
    """Map model output + textual cues into the 12-class extended set."""
    label = raw_label.lower()
    t_lower = text.lower()
    has_question = "?" in text
    has_exclaim = "!" in text

    # ── Curious: questions + wonder words ──
    if _has_keyword_set(text, _CURIOSITY_KEYWORDS) or has_question:
        if label in {"neutral", "surprise"} or raw_score < 0.45:
            return "curious"

    # ── Excited: strong positive with emphasis ──
    if _has_keyword_set(text, _EXCITEMENT_KEYWORDS) or has_exclaim:
        if label in {"joy", "surprise"} or raw_score > 0.6:
            return "excited"

    # ── Confident: certainty words ──
    if _has_keyword_set(text, _CONFIDENCE_KEYWORDS):
        if label in {"neutral", "joy"}:
            return "confident"

    # ── Bored: disinterest words ──
    if _has_keyword_set(text, _BOREDOM_KEYWORDS):
        if label in {"neutral", "sadness"}:
            return "bored"

    # ── Empathetic: support words ──
    if _has_keyword_set(text, _EMPATHY_KEYWORDS):
        if label in {"sadness", "fear", "neutral"}:
            return "empathetic"

    # ── Map base emotions ──
    if label in {"joy", "happiness"}:
        return "happy"
    if label == "sadness":
        return "melancholy"
    if label == "anger":
        return "furious"
    if label == "surprise":
        return "shocked"
    if label == "fear":
        return "anxious"
    if label == "disgust":
        return "disgusted"
    if label == "neutral":
        return "calm"

    return "calm"


# ── Intensifier / diminisher word sets ────────────────────────────────
_INTENSIFIERS = {
    "very", "extremely", "so", "really", "incredibly", "absolutely",
    "totally", "completely", "literally", "insanely", "super",
    "best", "worst", "most", "utterly", "deeply", "terribly",
    "enormously", "immensely", "frantically", "desperately",
    "highly", "quite", "remarkably", "exceptionally", "intensely"
}
_DIMINISHERS = {
    "slightly", "somewhat", "a bit", "kind of", "sort of",
    "mildly", "fairly", "rather", "barely", "hardly",
    "scarcely", "only", "just", "little"
}


def intensity_scale(text: str, base_score: float) -> float:
    t = text.strip()

    exclam = min(t.count("!"), 6) / 6.0
    quest = min(t.count("?"), 4) / 4.0

    words = re.findall(r"\b\w+\b", t)
    n_words = max(len(words), 1)

    caps_words = sum(1 for w in words if len(w) >= 2 and w.isupper())
    caps_ratio = caps_words / n_words

    elongated = len(re.findall(r"(\w)\1{2,}", t.lower()))
    elongated_score = min(elongated, 4) / 4.0

    intens = sum(1 for w in words if w.lower() in _INTENSIFIERS)
    intens_score = min(intens, 5) / 5.0
    dimin = sum(1 for w in words if w.lower() in _DIMINISHERS)
    dimin_score = min(dimin, 4) / 4.0

    length_boost = min(n_words / 25.0, 0.25)

    punctuation_emphasis = max(exclam, quest)

    emphasis = (
        0.30 * punctuation_emphasis
        + 0.20 * caps_ratio
        + 0.20 * elongated_score
        + 0.20 * intens_score
        + 0.10 * length_boost
        - 0.25 * dimin_score
    )
    emphasis = max(0.0, min(1.0, emphasis))

    emphasis_boosted = emphasis ** 0.6 if emphasis > 0.0 else 0.0

    blended = 0.25 * float(base_score) + 0.75 * emphasis_boosted

    return float(max(0.0, min(1.0, blended)))


# ── Voice parameter mapping per emotion ───────────────────────────────

def tts_parameters(emotion: str, intensity: float) -> Dict[str, float]:
    e = emotion if emotion in SUPPORTED_EMOTIONS else "calm"
    i = float(max(0.0, min(1.0, intensity)))

    if e == "happy":
        return {
            "rate": 1.0 + 0.18 * i,
            "pitch": 0.0 + 1.5 * i,
            "volume_db": 0.0 + 2.0 * i,
            "pause_ms": 80.0,
            "emphasis": 1.0 + 0.2 * i,
        }

    if e == "melancholy":
        return {
            "rate": 1.0 - 0.08 * i,
            "pitch": 0.0 - 0.8 * i,
            "volume_db": 0.0 - 2.0 * i,
            "pause_ms": 400.0 + 150.0 * i,
            "emphasis": 1.0 - 0.15 * i,
        }

    if e == "furious":
        return {
            "rate": 1.0 + 0.22 * i,
            "pitch": 0.0 + 3.0 * i,
            "volume_db": 0.0 + 6.0 * i,
            "pause_ms": 60.0,
            "emphasis": 1.0 + 0.4 * i,
        }

    if e == "shocked":
        return {
            "rate": 1.0 + 0.15 * i,
            "pitch": 0.0 + 2.0 * i,
            "volume_db": 0.0 + 1.5 * i,
            "pause_ms": 180.0,
            "emphasis": 1.0 + 0.25 * i,
        }

    if e == "anxious":
        return {
            "rate": 1.0 + 0.15 * i,
            "pitch": 0.0 + 1.0 * i,
            "volume_db": 0.0 - 1.5 * i,
            "pause_ms": 280.0 + 120.0 * i,
            "emphasis": 1.0 + 0.1 * i,
        }

    if e == "disgusted":
        return {
            "rate": 1.0 - 0.08 * i,
            "pitch": 0.0 - 0.8 * i,
            "volume_db": 0.0 + 2.0 * i,
            "pause_ms": 220.0,
            "emphasis": 1.0 + 0.2 * i,
        }

    if e == "curious":
        return {
            "rate": 1.0 + 0.08 * i,
            "pitch": 0.0 + 2.0 * i,
            "volume_db": 0.0 + 0.5 * i,
            "pause_ms": 200.0,
            "emphasis": 1.0 + 0.1 * i,
        }

    if e == "empathetic":
        return {
            "rate": 1.0 - 0.05 * i,
            "pitch": 0.0 - 0.2 * i,
            "volume_db": 0.0 - 1.0 * i,
            "pause_ms": 320.0 + 80.0 * i,
            "emphasis": 1.0 - 0.05 * i,
        }

    if e == "excited":
        return {
            "rate": 1.0 + 0.25 * i,
            "pitch": 0.0 + 2.5 * i,
            "volume_db": 0.0 + 3.0 * i,
            "pause_ms": 50.0,
            "emphasis": 1.0 + 0.3 * i,
        }

    if e == "bored":
        return {
            "rate": 1.0 - 0.12 * i,
            "pitch": 0.0 - 0.4 * i,
            "volume_db": 0.0 - 2.5 * i,
            "pause_ms": 500.0 + 100.0 * i,
            "emphasis": 1.0 - 0.2 * i,
        }

    if e == "confident":
        return {
            "rate": 1.0 - 0.02 * i,
            "pitch": 0.0 - 0.3 * i,
            "volume_db": 0.0 + 2.5 * i,
            "pause_ms": 120.0,
            "emphasis": 1.0 + 0.15 * i,
        }

    # calm (neutral)
    return {
        "rate": 1.0, "pitch": 0.0, "volume_db": 0.0,
        "pause_ms": 160.0, "emphasis": 1.0,
    }


def clamp_tts_params(params: Dict[str, float]) -> Dict[str, float]:
    rate = float(params.get("rate", 1.0))
    pitch = float(params.get("pitch", 0.0))
    vol = float(params.get("volume_db", 0.0))

    rate = max(0.65, min(1.50, rate))
    pitch = max(-7.0, min(7.0, pitch))
    vol = max(-12.0, min(12.0, vol))

    result: Dict[str, float] = {"rate": rate, "pitch": pitch, "volume_db": vol}
    for key in ("pause_ms", "emphasis", "male_base_pitch"):
        if key in params:
            result[key] = float(params[key])
    return result


def pitch_semitones_to_rate(semitones: float) -> float:
    return float(2 ** (float(semitones) / 12.0))
