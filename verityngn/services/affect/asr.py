"""Optional word-level ASR for disfluency (S07) and Q/A pairing (S05/S11).

Tries faster-whisper, then falls back to None. Caption VTT is a secondary path.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")


_WHISPER_MODELS: dict[tuple[str, str, str], Any] = {}


def _whisper_model(model_size: str, device: str, compute: str) -> Any:
    key = (model_size, device, compute)
    cached = _WHISPER_MODELS.get(key)
    if cached is not None:
        return cached
    from faster_whisper import WhisperModel  # type: ignore

    model = WhisperModel(model_size, device=device, compute_type=compute)
    _WHISPER_MODELS[key] = model
    return model


def transcribe_audio(
    audio_path: Path | str,
    *,
    model_size: str = "base",
    language: str = "en",
) -> Optional[dict[str, Any]]:
    """Return {text, words: [{word, start, end}], source} or None if unavailable."""
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return None
    try:
        from faster_whisper import WhisperModel  # noqa: F401  # type: ignore
    except ImportError:
        return None
    device = os.environ.get("WHISPER_DEVICE", "cpu")
    compute = os.environ.get("WHISPER_COMPUTE", "int8")
    try:
        model = _whisper_model(model_size, device, compute)
        segments, info = model.transcribe(str(audio_path), language=language, word_timestamps=True)
        words = []
        parts = []
        for seg in segments:
            parts.append(seg.text or "")
            for w in getattr(seg, "words", None) or []:
                words.append(
                    {
                        "word": (w.word or "").strip(),
                        "start": float(getattr(w, "start", 0.0) or 0.0),
                        "end": float(getattr(w, "end", 0.0) or 0.0),
                    }
                )
        return {
            "text": " ".join(t.strip() for t in parts if t.strip()),
            "words": words,
            "language": getattr(info, "language", language),
            "source": "faster_whisper",
            "model": model_size,
        }
    except Exception:  # noqa: BLE001
        return None


def words_in_window(transcript: dict[str, Any], start_sec: float, end_sec: float) -> list[str]:
    out = []
    for w in transcript.get("words") or []:
        s = float(w.get("start") or 0.0)
        if start_sec <= s < end_sec and w.get("word"):
            out.append(str(w["word"]))
    return out
