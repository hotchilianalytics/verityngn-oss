"""
AI-generated video/audio detection helpers.

Uses optional librosa for spectral voice analysis (pitch monotony, MFCC variance).
Returns ai_score in [0, 1] and a list of authenticity indicators.
These are soft cues for media provenance review — not a deepfake verdict.
"""

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def analyze_audio_for_ai_indicators(audio_path: str) -> Dict[str, Any]:
    """
    Run spectral/voice analysis on an audio file to detect synthetic voice indicators.

    - Low pitch variance and flat formants suggest TTS/robotic voice.
    - Returns ai_score in [0.0, 1.0] and indicators list.

    Requires librosa (and soundfile) if available; otherwise returns safe default.
    """
    result: Dict[str, Any] = {
        "ai_score": 0.0,
        "indicators": [],
    }
    if not audio_path or not os.path.isfile(audio_path):
        return result

    try:
        import librosa
        import numpy as np
    except ImportError:
        logger.debug("librosa not available; skipping spectral AI detection")
        return result

    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True, duration=120.0)
        if y.size < sr * 2:
            return result

        # Pitch (f0) variance: synthetic speech often has very regular pitch
        try:
            f0_vals, _, _ = librosa.pyin(y, fmin=80, fmax=400, sr=sr)
        except Exception:
            f0_vals = np.array([])
        if f0_vals is not None:
            f0_vals = np.asarray(f0_vals)
            f0_vals = f0_vals[~np.isnan(f0_vals)]
        else:
            f0_vals = np.array([])
        if f0_vals.size > 10:
            f0_std = float(np.nanstd(f0_vals))
            f0_mean = float(np.nanmean(f0_vals))
            if f0_mean > 0 and f0_std / f0_mean < 0.08:
                result["indicators"].append("low_pitch_variance_suggestive_of_tts")
                result["ai_score"] = min(1.0, result["ai_score"] + 0.3)

        # MFCC variance over time: very uniform suggests synthetic
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=2048, hop_length=512)
        mfcc_std = np.std(mfcc, axis=1)
        if np.mean(mfcc_std) < 2.0 and mfcc.shape[1] > 50:
            result["indicators"].append("uniform_mfcc_suggestive_of_synthetic_voice")
            result["ai_score"] = min(1.0, result["ai_score"] + 0.25)

    except Exception as e:
        logger.warning("AI audio analysis failed: %s", e)

    return result
