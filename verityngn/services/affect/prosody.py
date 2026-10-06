"""Prosody features from mono PCM / WAV (numpy; optional librosa)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional, Tuple
import wave

import numpy as np


@dataclass
class ProsodyFeatures:
    f0_mean: float
    f0_std: float
    jitter: float
    shimmer: float
    rate_sps: float  # rough syllables/sec proxy via energy peaks
    pause_ratio: float
    energy_mean: float
    duration_sec: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_wav_mono(path: Path) -> Tuple[np.ndarray, int]:
    path = Path(path)
    if path.suffix.lower() not in {".wav", ".wave"}:
        # Accept mp4/m4a/webm by decoding a temp mono WAV via ffmpeg.
        import subprocess
        import tempfile

        tmp = Path(tempfile.mkstemp(suffix=".wav")[1])
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(path),
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "wav",
                str(tmp),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return _read_wav_mono(tmp)
        finally:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass

    with wave.open(str(path), "rb") as wf:
        n_ch = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    if sampwidth == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    elif sampwidth == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) * 256.0
    else:
        raise ValueError(f"Unsupported sampwidth={sampwidth}")
    if n_ch > 1:
        data = data.reshape(-1, n_ch).mean(axis=1)
    data = data / 32768.0
    return data, rate


def _autocorr_f0(x: np.ndarray, sr: int, fmin: float = 70.0, fmax: float = 400.0) -> float:
    """Simple autocorrelation pitch estimate for a short frame."""
    if len(x) < sr // 20:
        return float("nan")
    x = x - x.mean()
    if np.std(x) < 1e-8:
        return float("nan")
    corr = np.correlate(x, x, mode="full")
    corr = corr[len(corr) // 2 :]
    i_min = int(sr / fmax)
    i_max = min(int(sr / fmin), len(corr) - 1)
    if i_max <= i_min:
        return float("nan")
    peak = i_min + int(np.argmax(corr[i_min:i_max]))
    if corr[peak] <= 0:
        return float("nan")
    return float(sr / peak)


def _frame_f0(x: np.ndarray, sr: int, frame_ms: float = 40.0, hop_ms: float = 10.0) -> np.ndarray:
    frame = int(sr * frame_ms / 1000.0)
    hop = int(sr * hop_ms / 1000.0)
    if frame < 1 or hop < 1 or len(x) < frame:
        return np.array([])
    vals = []
    for start in range(0, len(x) - frame + 1, hop):
        vals.append(_autocorr_f0(x[start : start + frame], sr))
    return np.asarray(vals, dtype=np.float64)


def extract_prosody(
    audio_path: Optional[Path] = None,
    *,
    samples: Optional[np.ndarray] = None,
    sample_rate: int = 16000,
    window_start_sec: float = 0.0,
    window_dur_sec: float = 3.0,
) -> ProsodyFeatures:
    """
    Extract Tier-1 prosody for a window.

    Prefer ``audio_path`` (WAV). If absent, ``samples`` may be provided.
    If neither, returns NaN-filled features with duration=0 (caller may fall back).
    """
    if audio_path is not None:
        x, sr = _read_wav_mono(Path(audio_path))
    elif samples is not None:
        x = np.asarray(samples, dtype=np.float64)
        sr = sample_rate
    else:
        return ProsodyFeatures(
            f0_mean=float("nan"),
            f0_std=float("nan"),
            jitter=float("nan"),
            shimmer=float("nan"),
            rate_sps=float("nan"),
            pause_ratio=float("nan"),
            energy_mean=float("nan"),
            duration_sec=0.0,
        )

    start = int(max(0.0, window_start_sec) * sr)
    end = int(min(len(x), (window_start_sec + window_dur_sec) * sr))
    seg = x[start:end]
    dur = len(seg) / float(sr) if sr else 0.0
    if len(seg) < sr // 10:
        return ProsodyFeatures(
            f0_mean=float("nan"),
            f0_std=float("nan"),
            jitter=float("nan"),
            shimmer=float("nan"),
            rate_sps=float("nan"),
            pause_ratio=1.0,
            energy_mean=float(np.mean(np.abs(seg))) if len(seg) else 0.0,
            duration_sec=dur,
        )

    f0 = _frame_f0(seg, sr)
    f0_valid = f0[np.isfinite(f0)]
    f0_mean = float(np.mean(f0_valid)) if len(f0_valid) else float("nan")
    f0_std = float(np.std(f0_valid)) if len(f0_valid) else float("nan")

    # Jitter: mean absolute successive F0 difference / mean F0
    if len(f0_valid) > 2 and f0_mean > 0:
        jitter = float(np.mean(np.abs(np.diff(f0_valid))) / f0_mean)
    else:
        jitter = float("nan")

    # Shimmer proxy: successive frame energy ratios
    frame = max(1, int(sr * 0.04))
    hop = max(1, int(sr * 0.01))
    energies = []
    for s in range(0, len(seg) - frame + 1, hop):
        energies.append(float(np.sqrt(np.mean(seg[s : s + frame] ** 2)) + 1e-12))
    energies_a = np.asarray(energies)
    if len(energies_a) > 2:
        shimmer = float(np.mean(np.abs(np.diff(energies_a))) / (np.mean(energies_a) + 1e-12))
    else:
        shimmer = float("nan")

    # Speaking-rate proxy: energy peak count / duration
    thr = float(np.percentile(np.abs(seg), 70))
    peaks = 0
    above = False
    for v in np.abs(seg[:: max(1, sr // 100)]):
        if v >= thr and not above:
            peaks += 1
            above = True
        elif v < thr * 0.5:
            above = False
    rate_sps = float(peaks / dur) if dur > 0 else float("nan")

    pause_ratio = float(np.mean(np.abs(seg) < (thr * 0.25)))
    energy_mean = float(np.mean(np.abs(seg)))

    return ProsodyFeatures(
        f0_mean=f0_mean,
        f0_std=f0_std,
        jitter=jitter,
        shimmer=shimmer,
        rate_sps=rate_sps,
        pause_ratio=pause_ratio,
        energy_mean=energy_mean,
        duration_sec=dur,
    )


def synthesize_demo_wav(
    path: Path,
    *,
    duration_sec: float = 30.0,
    sr: int = 16000,
    base_f0: float = 140.0,
    seed: int = 0,
) -> Path:
    """Write a deterministic voiced+noise WAV for offline MVP demos."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    # mild F0 modulation + harmonics
    f0 = base_f0 + 15.0 * np.sin(2 * np.pi * 0.4 * t) + rng.normal(0, 1.5, size=t.shape)
    phase = 2 * np.pi * np.cumsum(f0) / sr
    sig = 0.4 * np.sin(phase) + 0.15 * np.sin(2 * phase) + 0.05 * rng.normal(0, 1, size=t.shape)
    # insert pauses
    for p0 in np.linspace(0.2, 0.9, 4):
        a = int(p0 * len(sig))
        sig[a : a + int(0.25 * sr)] *= 0.05
    pcm = np.clip(sig * 32767, -32767, 32767).astype(np.int16)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return path
