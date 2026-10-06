"""
audEERING-style dimensional affect (arousal / dominance / valence).

Optional ONNX / transformers backend for wav2vec2-Large-Robust fine-tuned on
MSP-Podcast. Falls back to a prosody-derived proxy when the model is not installed.

Reference: audEERING expression model (wav2vec2, MSP-Podcast) — research use.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import logging
import os
import wave

import numpy as np

from verityngn.services.affect.adapters.base import AffectVendorAdapter, VendorAffectResult
from verityngn.services.affect.prosody import ProsodyFeatures, extract_prosody

logger = logging.getLogger(__name__)

# macOS + numpy/torch can ship two OpenMP runtimes.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

MODEL_ID = "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim"
_FEATURE_EXTRACTOR = None
_NEURAL_MODEL = None
_NEURAL_LOAD_FAILED = False


@dataclass
class DimensionalAffect:
    arousal: float
    dominance: float
    valence: float
    source: str = "proxy"
    raw: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "arousal": self.arousal,
            "dominance": self.dominance,
            "valence": self.valence,
            "source": self.source,
            "raw": self.raw,
            "construct_type": "measured",
        }


def _read_wav_mono_float(path: Path, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        n_ch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        raise ValueError(f"Unsupported sampwidth={sampwidth}")
    if n_ch > 1:
        data = data.reshape(-1, n_ch).mean(axis=1)
    if rate != target_sr and len(data) > 0:
        # Linear resample (avoid requiring librosa)
        duration = len(data) / float(rate)
        n_out = max(1, int(duration * target_sr))
        x_old = np.linspace(0.0, 1.0, num=len(data), endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=n_out, endpoint=False)
        data = np.interp(x_new, x_old, data).astype(np.float32)
        rate = target_sr
    return data, rate


def _proxy_from_prosody(pros: ProsodyFeatures) -> DimensionalAffect:
    """Map open prosody to rough ADV when neural model is unavailable."""
    f0 = pros.f0_mean if pros.f0_mean == pros.f0_mean else 120.0
    f0_std = pros.f0_std if pros.f0_std == pros.f0_std else 8.0
    energy = pros.energy_mean if pros.energy_mean == pros.energy_mean else 0.05
    pause = pros.pause_ratio if pros.pause_ratio == pros.pause_ratio else 0.3
    # Normalize heuristics into [0,1] / [-1,1]
    arousal = float(np.clip(0.35 + 0.4 * min(1.0, f0_std / 40.0) + 0.3 * min(1.0, energy / 0.15), 0.0, 1.0))
    dominance = float(np.clip(0.4 + 0.3 * min(1.0, (f0 - 100.0) / 80.0) - 0.2 * pause, 0.0, 1.0))
    valence = float(np.clip((1.0 - pause) * 0.6 + (0.5 - min(0.5, pros.jitter if pros.jitter == pros.jitter else 0.02)) - 0.3, -1.0, 1.0))
    return DimensionalAffect(arousal=arousal, dominance=dominance, valence=valence, source="prosody_proxy")


def _build_emotion_model_classes(torch, Wav2Vec2Model, Wav2Vec2PreTrainedModel):
    """audEERING's published regression-head graph (not AudioClassification)."""

    class RegressionHead(torch.nn.Module):
        def __init__(self, config):
            super().__init__()
            self.dense = torch.nn.Linear(config.hidden_size, config.hidden_size)
            dropout = getattr(config, "final_dropout", 0.1)
            self.dropout = torch.nn.Dropout(dropout)
            self.out_proj = torch.nn.Linear(config.hidden_size, config.num_labels)

        def forward(self, features):
            x = self.dropout(features)
            x = self.dense(x)
            x = torch.tanh(x)
            x = self.dropout(x)
            return self.out_proj(x)

    class EmotionModel(Wav2Vec2PreTrainedModel):
        def __init__(self, config):
            super().__init__(config)
            self.wav2vec2 = Wav2Vec2Model(config)
            self.classifier = RegressionHead(config)
            self.post_init()

        def forward(self, input_values, attention_mask=None):
            outputs = self.wav2vec2(input_values, attention_mask=attention_mask)
            hidden = torch.mean(outputs[0], dim=1)
            return self.classifier(hidden)

    return EmotionModel


def _load_neural_model():
    """Load wav2vec2 once per process. Reloading per claim window is unusable."""
    global _FEATURE_EXTRACTOR, _NEURAL_MODEL, _NEURAL_LOAD_FAILED
    if _NEURAL_LOAD_FAILED:
        return None
    if _NEURAL_MODEL is not None:
        return _FEATURE_EXTRACTOR, _NEURAL_MODEL
    try:
        import torch
        from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2Model, Wav2Vec2PreTrainedModel
    except ImportError:
        _NEURAL_LOAD_FAILED = True
        return None
    try:
        extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
        EmotionModel = _build_emotion_model_classes(torch, Wav2Vec2Model, Wav2Vec2PreTrainedModel)
        model = EmotionModel.from_pretrained(MODEL_ID)
        model.eval()
        state_keys = set(model.state_dict().keys())
        needed = ("classifier.dense.weight", "classifier.out_proj.weight")
        if not all(k in state_keys for k in needed):
            raise RuntimeError(f"classifier heads missing from state_dict: {needed}")
        if int(getattr(model.config, "num_labels", 0) or 0) < 3:
            raise RuntimeError("expected 3-dim ADV head")
        _FEATURE_EXTRACTOR = extractor
        _NEURAL_MODEL = model
        logger.info("[audeering_vad] loaded %s", MODEL_ID)
        return extractor, model
    except Exception as exc:  # noqa: BLE001
        logger.info("[audeering_vad] model load failed: %s", exc)
        _NEURAL_LOAD_FAILED = True
        return None


def _try_transformers_model(samples: np.ndarray, sr: int) -> Optional[DimensionalAffect]:
    loaded = _load_neural_model()
    if loaded is None:
        return None
    extractor, model = loaded
    try:
        import torch

        inputs = extractor(samples, sampling_rate=sr, return_tensors="pt", padding=True)
        input_values = inputs["input_values"]
        attention_mask = inputs.get("attention_mask")
        with torch.no_grad():
            logits = model(input_values, attention_mask=attention_mask)
            if hasattr(logits, "logits"):
                logits = logits.logits
            logits = logits[0].detach().cpu().numpy()
        # MSP-Podcast dimensional heads typically ordered arousal, dominance, valence in [0,1]
        # Some checkpoints output 3 dims already in 0..1; clamp defensively.
        if logits.shape[0] >= 3:
            a, d, v = float(logits[0]), float(logits[1]), float(logits[2])
        else:
            return None
        # If valence looks like 0..1, map to -1..1
        if 0.0 <= v <= 1.0 and 0.0 <= a <= 1.0:
            valence = v * 2.0 - 1.0
            arousal = a
            dominance = d
        else:
            # sigmoid then map
            def _sig(x: float) -> float:
                return 1.0 / (1.0 + float(np.exp(-x)))

            arousal = _sig(a)
            dominance = _sig(d)
            valence = _sig(v) * 2.0 - 1.0
        return DimensionalAffect(
            arousal=float(np.clip(arousal, 0, 1)),
            dominance=float(np.clip(dominance, 0, 1)),
            valence=float(np.clip(valence, -1, 1)),
            source="audeering_wav2vec2",
            raw={"logits": [float(x) for x in logits[:3]], "model_id": MODEL_ID},
        )
    except Exception as exc:  # noqa: BLE001
        logger.info("[audeering_vad] model load/infer failed: %s", exc)
        return None


def extract_dimensional_affect(
    audio_path: Optional[Path] = None,
    *,
    window_start_sec: float = 0.0,
    window_dur_sec: float = 3.0,
    prefer_neural: bool = True,
) -> DimensionalAffect:
    """
    Extract arousal / dominance / valence for an audio window.

    Prefer neural MSP-Podcast model when installed; otherwise prosody proxy.
    """
    if audio_path is None or not Path(audio_path).exists():
        return DimensionalAffect(arousal=0.5, dominance=0.5, valence=0.0, source="missing_audio")

    pros = extract_prosody(
        Path(audio_path),
        window_start_sec=window_start_sec,
        window_dur_sec=window_dur_sec,
    )
    if prefer_neural:
        try:
            samples, sr = _read_wav_mono_float(Path(audio_path))
            start = int(max(0.0, window_start_sec) * sr)
            end = int(min(len(samples), (window_start_sec + window_dur_sec) * sr))
            seg = samples[start:end]
            if len(seg) >= sr // 4:
                neural = _try_transformers_model(seg, sr)
                if neural is not None:
                    return neural
        except Exception as exc:  # noqa: BLE001
            logger.info("[audeering_vad] wav read failed: %s", exc)
    return _proxy_from_prosody(pros)


class AudEeringVADAdapter(AffectVendorAdapter):
    """Measured-track adapter (construct_type=measured despite adapter base)."""

    name = "audeering_vad"

    def analyze_audio(self, audio_path: str, **kwargs: Any) -> VendorAffectResult:
        start = float(kwargs.get("window_start_sec") or 0.0)
        dur = float(kwargs.get("window_dur_sec") or 3.0)
        prefer = bool(kwargs.get("prefer_neural", True))
        dim = extract_dimensional_affect(
            Path(audio_path) if audio_path else None,
            window_start_sec=start,
            window_dur_sec=dur,
            prefer_neural=prefer,
        )
        return VendorAffectResult(
            vendor=self.name,
            construct_type="measured",
            vectors={
                "arousal": dim.arousal,
                "dominance": dim.dominance,
                "valence": dim.valence,
            },
            raw=dim.to_dict(),
        )
