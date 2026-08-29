"""MediaPipe Face Landmarker adapter (Tasks API — not legacy solutions.face_mesh).

Outputs measured face coverage, 478 landmarks (sampled), 52 blendshapes,
HFAsy_proxy (L vs R blendshape L1 — asymmetry on-ramp, not a clinical HFAsy
replication), and a face valence/arousal proxy for optional congruence cues.

Congruence / delivery-risk / authenticity only — not a lie detector.
Not for employment use.
"""
from __future__ import annotations

import logging
import math
import urllib.request
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

VISION_SOURCE = "mediapipe_face_landmarker"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
# Prefer blendshapes bundle when available
MODEL_URL_BLENDSHAPES = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)

# ARKit-style L/R pairs for hemifacial asymmetry proxy
_LR_PAIRS = (
    ("browDownLeft", "browDownRight"),
    ("browOuterUpLeft", "browOuterUpRight"),
    ("cheekSquintLeft", "cheekSquintRight"),
    ("eyeBlinkLeft", "eyeBlinkRight"),
    ("eyeLookDownLeft", "eyeLookDownRight"),
    ("eyeLookInLeft", "eyeLookInRight"),
    ("eyeLookOutLeft", "eyeLookOutRight"),
    ("eyeLookUpLeft", "eyeLookUpRight"),
    ("eyeSquintLeft", "eyeSquintRight"),
    ("eyeWideLeft", "eyeWideRight"),
    ("mouthDimpleLeft", "mouthDimpleRight"),
    ("mouthFrownLeft", "mouthFrownRight"),
    ("mouthLowerDownLeft", "mouthLowerDownRight"),
    ("mouthPressLeft", "mouthPressRight"),
    ("mouthSmileLeft", "mouthSmileRight"),
    ("mouthStretchLeft", "mouthStretchRight"),
    ("mouthUpperUpLeft", "mouthUpperUpRight"),
)

NOT_FOR_EMPLOYMENT = (
    "Vision features are optional authenticity/congruence cues only. "
    "Not for employment, HR, or education screening "
    "(EU AI Act Art. 5(1)(f)). HFAsy_proxy is not a clinical HFAsy score."
)


class MediaPipeAdapter:
    name = "mediapipe"

    def available(self) -> bool:
        try:
            import mediapipe  # noqa: F401

            return True
        except ImportError:
            return False


def _model_path(cache_dir: Optional[Path] = None) -> Path:
    root = cache_dir or (Path.home() / ".cache" / "verityngn" / "mediapipe")
    root.mkdir(parents=True, exist_ok=True)
    dest = root / "face_landmarker_v2_with_blendshapes.task"
    if dest.exists() and dest.stat().st_size > 1_000_000:
        return dest
    # Try blendshapes-capable bundle, then float16/1
    for url in (MODEL_URL_BLENDSHAPES, MODEL_URL):
        try:
            logger.info("[mediapipe] downloading Face Landmarker model → %s", dest)
            urllib.request.urlretrieve(url, dest)
            if dest.exists() and dest.stat().st_size > 1_000_000:
                return dest
        except Exception as exc:  # noqa: BLE001
            logger.warning("[mediapipe] model download failed (%s): %s", url, exc)
    raise FileNotFoundError(
        f"MediaPipe Face Landmarker model missing at {dest}. "
        "Install mediapipe and allow network to download the .task file."
    )


def _blendshape_map(face_blendshapes) -> dict[str, float]:
    out: dict[str, float] = {}
    if not face_blendshapes:
        return out
    # Tasks API: list of Category with .category_name / .score
    for cat in face_blendshapes:
        name = getattr(cat, "category_name", None) or getattr(cat, "name", None)
        score = getattr(cat, "score", None)
        if name is None or score is None:
            continue
        try:
            out[str(name)] = float(score)
        except (TypeError, ValueError):
            continue
    return out


def _hfasy_proxy(bs: dict[str, float]) -> float:
    """Mean |L−R| over available ARKit L/R blendshape pairs. Higher = more asymmetry."""
    diffs: list[float] = []
    for left, right in _LR_PAIRS:
        if left in bs and right in bs:
            diffs.append(abs(bs[left] - bs[right]))
    if not diffs:
        return 0.0
    return float(sum(diffs) / len(diffs))


def _valence_arousal_proxy(bs: dict[str, float]) -> tuple[float, float]:
    """Map blendshapes → valence [-1,1] and arousal [0,1] proxies (not FACS)."""
    smile = 0.5 * (bs.get("mouthSmileLeft", 0.0) + bs.get("mouthSmileRight", 0.0))
    frown = 0.5 * (bs.get("mouthFrownLeft", 0.0) + bs.get("mouthFrownRight", 0.0))
    jaw = bs.get("jawOpen", 0.0)
    brow_up = bs.get("browInnerUp", 0.0)
    eye_wide = 0.5 * (bs.get("eyeWideLeft", 0.0) + bs.get("eyeWideRight", 0.0))
    eye_squint = 0.5 * (bs.get("eyeSquintLeft", 0.0) + bs.get("eyeSquintRight", 0.0))
    valence = max(-1.0, min(1.0, (smile - frown) * 2.0 - 0.1 * eye_squint))
    arousal = max(0.0, min(1.0, 0.35 * jaw + 0.35 * eye_wide + 0.20 * brow_up + 0.10 * smile))
    return float(valence), float(arousal)


def _blink_gaze_from_blendshapes(
    frames_bs: list[dict[str, float]],
    *,
    fps: float,
) -> dict[str, float]:
    if not frames_bs:
        return {
            "blink_rate_per_min": 0.0,
            "gaze_yaw_mean": 0.0,
            "gaze_pitch_mean": 0.0,
            "gaze_aversion_ratio": 0.0,
        }
    blink_l = [f.get("eyeBlinkLeft", 0.0) for f in frames_bs]
    blink_r = [f.get("eyeBlinkRight", 0.0) for f in frames_bs]
    blink = [(a + b) / 2.0 for a, b in zip(blink_l, blink_r)]
    # Count rising edges above 0.45 as blinks
    n_blinks = 0
    prev = 0.0
    for v in blink:
        if v >= 0.45 and prev < 0.45:
            n_blinks += 1
        prev = v
    duration_min = max((len(frames_bs) / max(fps, 1e-6)) / 60.0, 1e-6)
    look_out = [
        0.5 * (f.get("eyeLookOutLeft", 0.0) + f.get("eyeLookOutRight", 0.0)) for f in frames_bs
    ]
    look_in = [
        0.5 * (f.get("eyeLookInLeft", 0.0) + f.get("eyeLookInRight", 0.0)) for f in frames_bs
    ]
    look_up = [
        0.5 * (f.get("eyeLookUpLeft", 0.0) + f.get("eyeLookUpRight", 0.0)) for f in frames_bs
    ]
    look_down = [
        0.5 * (f.get("eyeLookDownLeft", 0.0) + f.get("eyeLookDownRight", 0.0)) for f in frames_bs
    ]
    yaw = [o - i for o, i in zip(look_out, look_in)]
    pitch = [u - d for u, d in zip(look_up, look_down)]
    aversion = sum(1 for y, p in zip(yaw, pitch) if abs(y) > 0.35 or abs(p) > 0.35) / len(frames_bs)
    return {
        "blink_rate_per_min": round(n_blinks / duration_min, 2),
        "gaze_yaw_mean": round(sum(yaw) / len(yaw), 4),
        "gaze_pitch_mean": round(sum(pitch) / len(pitch), 4),
        "gaze_aversion_ratio": round(float(aversion), 4),
    }


def try_landmarks(video_id: str, **kwargs: Any) -> Optional[Any]:
    """Legacy hook — prefer try_face_landmarker(video_path=...)."""
    video_path = kwargs.get("video_path")
    if not video_path:
        return None
    return try_face_landmarker(video_path, video_id=video_id, **kwargs)


def try_face_landmarker(
    video_path: str | Path,
    *,
    video_id: str = "",
    sample_fps: float = 2.0,
    max_frames: int = 600,
    model_path: Optional[str | Path] = None,
    num_faces: int = 1,
) -> Optional[dict[str, Any]]:
    """Run Face Landmarker on a local mp4. Returns None if deps/model missing.

    Never returns synthetic/hash-seeded values.
    """
    path = Path(video_path)
    if not path.exists():
        logger.warning("[mediapipe] missing video %s", path)
        return None
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision as mp_vision
        import cv2
        import numpy as np
    except ImportError as exc:
        logger.warning("[mediapipe] import failed: %s", exc)
        return None

    try:
        model = Path(model_path) if model_path else _model_path()
    except FileNotFoundError as exc:
        logger.warning("%s", exc)
        return None

    base_options = mp_python.BaseOptions(
        model_asset_path=str(model),
        delegate=mp_python.BaseOptions.Delegate.CPU,
    )
    # IMAGE mode: per-frame detect(). VIDEO mode crashes on some macOS Metal builds
    # (DrishtiMetalHelper "Service is unavailable") even with CPU delegate.
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        running_mode=mp_vision.RunningMode.IMAGE,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        num_faces=max(1, int(num_faces)),
    )
    landmarker = mp_vision.FaceLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        logger.warning("[mediapipe] cannot open %s", path)
        landmarker.close()
        return None

    native_fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
    n_frames_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_sec = n_frames_total / native_fps if native_fps > 0 and n_frames_total > 0 else 0.0
    step = max(1, int(round(native_fps / max(sample_fps, 0.1))))
    # Skip opening slate / lower-thirds common on CNBC (first ~3s)
    start_frame = int(min(native_fps * 3.0, max(0, n_frames_total // 20)))

    frames_bs: list[dict[str, float]] = []
    hfasy_series: list[float] = []
    valence_series: list[float] = []
    arousal_series: list[float] = []
    face_hits = 0
    multi_face_hits = 0
    sampled = 0
    frame_idx = 0
    if start_frame:
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frame_idx = start_frame

    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        if (frame_idx - start_frame) % step != 0:
            frame_idx += 1
            continue
        if sampled >= max_frames:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)
        sampled += 1
        frame_idx += 1
        n_faces = len(result.face_landmarks) if result.face_landmarks else 0
        if n_faces == 0:
            continue
        face_hits += 1
        if n_faces > 1:
            multi_face_hits += 1
        # Use first face (talking-head assumption); multi-face flagged
        bs_list = result.face_blendshapes[0] if result.face_blendshapes else []
        bs = _blendshape_map(bs_list)
        if not bs:
            continue
        frames_bs.append(bs)
        h = _hfasy_proxy(bs)
        v, a = _valence_arousal_proxy(bs)
        hfasy_series.append(h)
        valence_series.append(v)
        arousal_series.append(a)

    cap.release()
    landmarker.close()

    coverage = face_hits / max(sampled, 1)
    if face_hits == 0 or not arousal_series:
        return {
            "source": VISION_SOURCE,
            "video_id": video_id or path.stem,
            "status": "no_face",
            "face_coverage": 0.0,
            "n_frames_sampled": sampled,
            "n_frames_with_face": 0,
            "multi_face_frame_share": 0.0,
            "duration_sec": round(duration_sec, 2),
            "hfasy_proxy": None,
            "valence": None,
            "arousal": None,
            "sympathetic_arousal": None,
            "blendshapes_mean": {},
            "gaze_blink": {},
            "disclaimer": NOT_FOR_EMPLOYMENT,
            "not_for_employment_use": True,
            "caveat": "HFAsy_proxy omitted — no face detected (two-shot / coverage fail).",
        }

    def _mean(xs: list[float]) -> float:
        return float(sum(xs) / len(xs))

    def _std(xs: list[float]) -> float:
        if len(xs) < 2:
            return 0.0
        m = _mean(xs)
        return float(math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)))

    # Mean blendshapes across frames
    keys = set().union(*(f.keys() for f in frames_bs))
    bs_mean = {k: round(_mean([f.get(k, 0.0) for f in frames_bs]), 4) for k in sorted(keys)}
    gaze = _blink_gaze_from_blendshapes(frames_bs, fps=sample_fps)
    arousal = _mean(arousal_series)
    valence = _mean(valence_series)
    hfasy = _mean(hfasy_series)

    return {
        "source": VISION_SOURCE,
        "video_id": video_id or path.stem,
        "status": "ok",
        "face_coverage": round(coverage, 4),
        "n_frames_sampled": sampled,
        "n_frames_with_face": face_hits,
        "multi_face_frame_share": round(multi_face_hits / max(sampled, 1), 4),
        "duration_sec": round(duration_sec, 2),
        "sample_fps": sample_fps,
        "hfasy_proxy": round(hfasy, 4),
        "hfasy_proxy_std": round(_std(hfasy_series), 4),
        "valence": round(valence, 4),
        "arousal": round(arousal, 4),
        # Crossmodal uses sympathetic_arousal as the face channel for S01
        "sympathetic_arousal": round(arousal, 4),
        "blendshapes_mean": bs_mean,
        "gaze_blink": gaze,
        "disclaimer": NOT_FOR_EMPLOYMENT,
        "not_for_employment_use": True,
        "caveat": (
            "HFAsy_proxy = mean |L−R| ARKit blendshapes — not Banker et al. "
            "CNN hemifacial asymmetry (MS 2024). Congruence / delivery-risk only."
        ),
    }


__all__ = [
    "MediaPipeAdapter",
    "VISION_SOURCE",
    "try_landmarks",
    "try_face_landmarker",
]
