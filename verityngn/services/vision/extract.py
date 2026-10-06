"""Orchestrate vision extraction for a video / report."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json

from verityngn.services.vision.action_units import extract_action_units
from verityngn.services.vision.gaze_blink import cognitive_load_proxy, extract_gaze_blink
from verityngn.services.vision.landmarks import extract_landmarks
from verityngn.services.vision.ocr_geo import extract_ocr_geo
from verityngn.services.vision.spectral import extract_spectral, rppg_authenticity_check

import os

NOT_FOR_EMPLOYMENT = (
    "Vision/affect features are for markets research only. "
    "Not for employment, HR, or education screening "
    "(EU AI Act Art. 5(1)(f) workplace/education prohibition)."
)


def os_env_allow_synthetic_spectral() -> bool:
    """Synthetic rPPG/sympathetic_arousal is opt-in only (reintroduces leak risk)."""
    return os.environ.get("MULTISENSE_ALLOW_SYNTHETIC_VISION") in {"1", "true", "True"}


@dataclass
class VisionResult:
    video_id: str
    schema_version: str = "1.0"
    authenticity: dict[str, Any] = field(default_factory=dict)
    landmarks: dict[str, Any] = field(default_factory=dict)
    action_units: dict[str, Any] = field(default_factory=dict)
    gaze_blink: dict[str, Any] = field(default_factory=dict)
    spectral: dict[str, Any] = field(default_factory=dict)
    ocr_geo: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = NOT_FOR_EMPLOYMENT

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "schema_version": self.schema_version,
            "authenticity": self.authenticity,
            "landmarks": self.landmarks,
            "action_units": self.action_units,
            "gaze_blink": self.gaze_blink,
            "spectral": self.spectral,
            "ocr_geo": self.ocr_geo,
            "summary": self.summary,
            "disclaimer": self.disclaimer,
            "not_for_employment_use": True,
        }

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


def extract_vision_for_video(
    video_id: str,
    *,
    duration_sec: float = 60.0,
    title: str = "",
    description: str = "",
    authenticity: Optional[dict[str, Any]] = None,
    run_authenticity_with_rppg: bool = True,
    video_path: Optional[str | Path] = None,
) -> VisionResult:
    landmarks = extract_landmarks(video_id, duration_sec=duration_sec)
    aus = extract_action_units(video_id, duration_sec=duration_sec)
    gaze = extract_gaze_blink(video_id, duration_sec=duration_sec)
    spectral = extract_spectral(video_id, duration_sec=duration_sec)
    ocr = extract_ocr_geo(video_id, title=title, description=description)

    pyfeat_summary = None
    mediapipe_summary = None
    if video_path:
        from verityngn.services.vision.adapters.mediapipe import try_face_landmarker
        from verityngn.services.vision.adapters.pyfeat import try_full_fex

        # MediaPipe first (cheap measured face). py-feat optional AU confirm later.
        mediapipe_summary = try_face_landmarker(video_path, video_id=video_id)
        if mediapipe_summary and mediapipe_summary.get("status") == "ok":
            landmarks.backend = "mediapipe_face_landmarker"
            gb = mediapipe_summary.get("gaze_blink") or {}
            if gb:
                gaze.backend = "mediapipe_face_landmarker"
                gaze.blink_rate_per_min = float(gb.get("blink_rate_per_min") or gaze.blink_rate_per_min)
                gaze.gaze_yaw_mean = float(gb.get("gaze_yaw_mean") or 0.0)
                gaze.gaze_pitch_mean = float(gb.get("gaze_pitch_mean") or 0.0)
                gaze.gaze_aversion_ratio = float(gb.get("gaze_aversion_ratio") or 0.0)

        try:
            pyfeat_summary = try_full_fex(video_path)
        except Exception:  # noqa: BLE001
            pyfeat_summary = None
        if pyfeat_summary and pyfeat_summary.get("action_units_mean"):
            aus.backend = "pyfeat_detectorv2"
            # Stamp a single summary frame so mean_intensities() reflects Detectorv2
            from verityngn.services.vision.action_units import AUFrame

            aus.frames = [
                AUFrame(
                    t_sec=0.0,
                    intensities={k: float(v) for k, v in pyfeat_summary["action_units_mean"].items()},
                    source="pyfeat_detectorv2",
                )
            ]

    auth = authenticity
    if run_authenticity_with_rppg and auth is None:
        from verityngn.services.authenticity.gate import run_authenticity_gate

        rppg_check = rppg_authenticity_check(spectral)
        auth_result = run_authenticity_gate(
            video_id=video_id,
            rppg=rppg_check,
        )
        auth = auth_result.to_dict()

    gated = bool((auth or {}).get("gated"))
    if gated:
        landmarks.gated = True
        aus.gated = True
        gaze.gated = True
        spectral.gated = True

    # Prefer MediaPipe face arousal over synthetic spectral sympathetic_arousal
    mp_ok = bool(mediapipe_summary and mediapipe_summary.get("status") == "ok")
    face_arousal = None
    face_valence = None
    if mp_ok and not gated:
        face_arousal = mediapipe_summary.get("sympathetic_arousal")
        face_valence = mediapipe_summary.get("valence")
    elif pyfeat_summary and not gated:
        face_arousal = pyfeat_summary.get("arousal")
        face_valence = pyfeat_summary.get("valence")

    load = cognitive_load_proxy(gaze) if (mp_ok or gaze.backend != "synthetic") else None
    if gated:
        load = None
    # Refuse synthetic spectral arousal when we have no real face extractor
    sympathetic = face_arousal
    if sympathetic is None and not gated and os_env_allow_synthetic_spectral():
        sympathetic = spectral.sympathetic_arousal

    summary = {
        "gated": gated,
        "cognitive_load_proxy": load,
        "sympathetic_arousal": sympathetic,
        "rppg_consistency": spectral.rppg_consistency if sympathetic is not None else None,
        "mean_au": None if gated else aus.mean_intensities(),
        "venues": ocr.venues,
        "pyfeat": pyfeat_summary,
        "mediapipe": mediapipe_summary,
        "valence": face_valence,
        "arousal": face_arousal,
        "hfasy_proxy": None if gated else (mediapipe_summary or {}).get("hfasy_proxy"),
        "face_coverage": None if gated else (mediapipe_summary or {}).get("face_coverage"),
        "vision_source": (
            "mediapipe_face_landmarker"
            if mp_ok
            else ("pyfeat_detectorv2" if pyfeat_summary else "")
        ),
        "backend": {
            "landmarks": landmarks.backend,
            "action_units": aus.backend,
            "gaze_blink": gaze.backend,
            "spectral": spectral.backend,
            "pyfeat": bool(pyfeat_summary),
            "mediapipe": mp_ok,
        },
    }
    return VisionResult(
        video_id=video_id,
        authenticity=auth or {},
        landmarks=landmarks.to_dict(),
        action_units=aus.to_dict(),
        gaze_blink=gaze.to_dict(),
        spectral=spectral.to_dict(),
        ocr_geo=ocr.to_dict(),
        summary=summary,
    )
