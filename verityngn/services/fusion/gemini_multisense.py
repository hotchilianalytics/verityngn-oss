"""
Gemini multi-sense claim-clip processing — interpreted track.

Tier A: whole-video affect / delivery track (one pass).
Tier B: per-claim clip deep pass (high-stakes / verdict-divergent only).

Outputs are congruence / conviction / delivery-risk signals — never veracity.
Markets research only; not for employment, HR, or education screening
(EU AI Act Art. 5(1)(f)).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import json
import logging
import os
import re

from verityngn.services.fusion.clip_windows import (
    ClipWindow,
    build_clip_windows,
    parse_timestamp,
    tier_b_windows,
)
from verityngn.services.fusion.plutchik import closure, map_affect_to_segments

logger = logging.getLogger(__name__)

SIGNAL_TIER = "interpreted"
SCHEMA_VERSION = "1.0"

DISCLAIMER = (
    "Interpreted multimodal delivery signals for markets research. "
    "Congruence / conviction / delivery-risk only — not a lie detector, "
    "clinical diagnosis, or veracity judgment. "
    "Not for employment, HR, or education screening (EU AI Act Art. 5(1)(f))."
)

TIER_A_PROMPT = """You are analyzing a presentation, interview, or earnings-style video for MARKETS RESEARCH.

Task: Produce a timestamped delivery / affect track. Do NOT judge truthfulness or detect lies.

For each distinct speaking segment (~15–45s), return:
- start_sec, end_sec (numbers)
- speaker (string; Speaker 1 / Speaker 2 if unknown)
- vocal_emotion: one of joy, trust, fear, surprise, sadness, disgust, anger, anticipation, neutral
- arousal: 0..1
- valence: -1..1
- delivery: {pace_band: slow|moderate|fast, pause_pattern: sparse|normal|frequent,
  pitch_variability_band: low|moderate|high, disfluency_count: int}
- delivery_style: short phrase (e.g. "prepared confident", "Q&A pressured")
- confidence: 0..1

Also return overall_summary (2 sentences max).

Output STRICT JSON:
{
  "overall_summary": "...",
  "segments": [ { ... } ]
}
"""

TIER_B_PROMPT = """You are analyzing a SHORT clip from a presentation/interview for MARKETS RESEARCH.

Focus ONLY on this time window. Do NOT judge truthfulness or detect lies.

Return STRICT JSON with:
- spoken_content: brief paraphrase of what was said
- ocr_on_screen: list of visible text/graphics (empty if none)
- facial_expression: short description
- gesture_description: short description
- vocal_delivery: {{pace_band, pause_pattern, pitch_variability_band, disfluency_count}}
- vocal_emotion: Plutchik primary or neutral
- arousal: 0..1
- valence: -1..1
- congruence_statement: does face match voice match words? (observational only)
- congruence_score: 0..1 (1 = channels aligned)
- confidence: 0..1
- sr_primary: one of joy,trust,fear,surprise,sadness,disgust,anger,anticipation,neutral

Context claim text (may be empty): {claim_text}
Window: {start_sec:.1f}s – {end_sec:.1f}s
"""


def _extract_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    text = text.strip()
    # Strip markdown fences if present
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        pass
    # Find outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(text[start : end + 1])
            return obj if isinstance(obj, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _emotion_to_sr(emotion: str, arousal: float, valence: float) -> list[dict[str, Any]]:
    e = (emotion or "neutral").lower().strip()
    if e in {"neutral", ""}:
        return map_affect_to_segments(valence, max(0.0, min(1.0, (arousal + 1) / 2 if arousal > 1 else arousal)), arousal)
    # Map primary → a default tertiary leaf
    primary_map = {
        "joy": "sr_joy_ecstasy_excitement",
        "trust": "sr_trust_acceptance_familiarity",
        "fear": "sr_fear_apprehension_nervousness",
        "surprise": "sr_surprise_amazement_astonishment",
        "sadness": "sr_sadness_pensiveness_reflection",
        "disgust": "sr_disgust_boredom_disinterest",
        "anger": "sr_anger_annoyance_frustration",
        "anticipation": "sr_anticipation_interest_curiosity",
    }
    seg = primary_map.get(e, "sr_anticipation_interest_curiosity")
    return [{"segment_id": seg, "relevance": int(50 + 40 * float(arousal or 0.5)), "closure": closure(seg)}]


def _offline_tier_a(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic offline Tier A when Gemini is unavailable."""
    segments = []
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        t = parse_timestamp(claim.get("timestamp"))
        text = claim.get("claim_text") or ""
        # Cheap text proxies
        valence = 0.1 if any(w in text.lower() for w in ("grow", "strong", "confident", "record")) else (
            -0.1 if any(w in text.lower() for w in ("risk", "challeng", "uncertain", "decline")) else 0.0
        )
        arousal = 0.45 + min(0.3, len(text) / 500.0)
        segments.append(
            {
                "start_sec": max(0.0, t - 10.0),
                "end_sec": t + 10.0,
                "speaker": claim.get("speaker") or "Speaker 1",
                "vocal_emotion": "anticipation" if valence >= 0 else "fear",
                "arousal": arousal,
                "valence": valence,
                "delivery": {
                    "pace_band": "moderate",
                    "pause_pattern": "normal",
                    "pitch_variability_band": "moderate",
                    "disfluency_count": text.lower().count("uh") + text.lower().count("um"),
                },
                "delivery_style": "offline_proxy",
                "confidence": 0.35,
                "signal_tier": SIGNAL_TIER,
                "source": "offline_proxy",
            }
        )
    return {
        "overall_summary": "Offline Tier A proxy (Gemini not invoked).",
        "segments": segments,
        "signal_tier": SIGNAL_TIER,
        "source": "offline_proxy",
    }


def _offline_tier_b(window: ClipWindow, claim_text: str = "") -> dict[str, Any]:
    valence = 0.05 if "grow" in claim_text.lower() else 0.0
    arousal = 0.5
    return {
        "spoken_content": (claim_text[:240] + "…") if len(claim_text) > 240 else claim_text,
        "ocr_on_screen": [],
        "facial_expression": "unavailable_offline",
        "gesture_description": "unavailable_offline",
        "vocal_delivery": {
            "pace_band": "moderate",
            "pause_pattern": "normal",
            "pitch_variability_band": "moderate",
            "disfluency_count": 0,
        },
        "vocal_emotion": "anticipation",
        "arousal": arousal,
        "valence": valence,
        "congruence_statement": "Offline proxy — measured track should be preferred for congruence.",
        "congruence_score": 0.5,
        "confidence": 0.3,
        "sr_primary": "anticipation",
        "signal_tier": SIGNAL_TIER,
        "source": "offline_proxy",
        "window": window.to_dict(),
    }


def _get_genai_client() -> Any:
    """Build google.genai client for Vertex if credentials exist; else None."""
    try:
        from google import genai
    except ImportError:
        logger.info("[multisense] google-genai not installed; offline mode")
        return None

    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
    location = os.environ.get("VERTEX_LOCATION") or os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    use_vertex = os.environ.get("MULTISENSE_USE_VERTEX", "1") not in {"0", "false", "False"}
    api_key = (
        os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("VERITY_GEMINI_KEY")
    )

    try:
        if use_vertex and project:
            return genai.Client(vertexai=True, project=project, location=location)
        if api_key:
            return genai.Client(api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[multisense] client init failed: %s", exc)
    return None


def _model_name() -> str:
    return os.environ.get("MULTISENSE_MODEL") or os.environ.get("VERTEX_MODEL_NAME") or "gemini-2.5-flash"


def _invoke_gemini_video(
    client: Any,
    *,
    prompt: str,
    video_uri: Optional[str] = None,
    youtube_url: Optional[str] = None,
    start_sec: Optional[float] = None,
    end_sec: Optional[float] = None,
    fps: float = 1.0,
) -> dict[str, Any]:
    from google.genai import types

    parts: list[Any] = [prompt]
    vm_kwargs: dict[str, Any] = {}
    if start_sec is not None:
        vm_kwargs["start_offset"] = f"{int(start_sec)}s"
    if end_sec is not None:
        vm_kwargs["end_offset"] = f"{int(end_sec)}s"
    if fps:
        vm_kwargs["fps"] = fps

    if youtube_url:
        file_data = types.FileData(file_uri=youtube_url, mime_type="video/youtube")
        meta = types.VideoMetadata(**vm_kwargs) if vm_kwargs else None
        parts.append(types.Part(file_data=file_data, video_metadata=meta))
    elif video_uri:
        # GCS or Files API URI
        mime = "video/mp4"
        file_data = types.FileData(file_uri=video_uri, mime_type=mime)
        meta = types.VideoMetadata(**vm_kwargs) if vm_kwargs else None
        parts.append(types.Part(file_data=file_data, video_metadata=meta))
    else:
        return {}

    resp = client.models.generate_content(model=_model_name(), contents=parts)
    text = getattr(resp, "text", None) or ""
    if not text and getattr(resp, "candidates", None):
        try:
            text = resp.candidates[0].content.parts[0].text
        except Exception:  # noqa: BLE001
            text = ""
    return _extract_json(text)


@dataclass
class MultisenseResult:
    video_id: str
    schema_version: str = SCHEMA_VERSION
    signal_tier: str = SIGNAL_TIER
    tier_a: dict[str, Any] = field(default_factory=dict)
    tier_b: list[dict[str, Any]] = field(default_factory=list)
    clip_windows: list[dict[str, Any]] = field(default_factory=list)
    claim_delivery: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = DISCLAIMER
    not_for_employment_use: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "schema_version": self.schema_version,
            "signal_tier": self.signal_tier,
            "tier_a": self.tier_a,
            "tier_b": self.tier_b,
            "clip_windows": self.clip_windows,
            "claim_delivery": self.claim_delivery,
            "summary": self.summary,
            "disclaimer": self.disclaimer,
            "not_for_employment_use": self.not_for_employment_use,
        }

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


def _normalize_delivery(block: Any) -> dict[str, Any]:
    """Fill missing vocal/delivery bands so partial Gemini JSON still parses."""
    if not isinstance(block, dict):
        block = {}
    out = dict(block)
    out.setdefault("pace_band", "moderate")
    out.setdefault("pause_pattern", "normal")
    out.setdefault("pitch_variability_band", "moderate")
    out.setdefault("disfluency_count", 0)
    return out


def _attach_sr(segment: dict[str, Any]) -> dict[str, Any]:
    emotion = segment.get("vocal_emotion") or segment.get("sr_primary") or "neutral"
    arousal = float(segment.get("arousal") or 0.5)
    valence = float(segment.get("valence") or 0.0)
    segs = _emotion_to_sr(str(emotion), arousal, valence)
    out = dict(segment)
    if "delivery" in out:
        out["delivery"] = _normalize_delivery(out.get("delivery"))
    if "vocal_delivery" in out:
        out["vocal_delivery"] = _normalize_delivery(out.get("vocal_delivery"))
    out["sr_segments"] = segs
    out["signal_tier"] = SIGNAL_TIER
    return out


def run_gemini_multisense(
    report: dict[str, Any] | Path,
    *,
    video_uri: Optional[str] = None,
    youtube_url: Optional[str] = None,
    offline: Optional[bool] = None,
    margin_sec: float = 15.0,
    max_tier_b: int = 12,
    fps: float = 1.0,
) -> MultisenseResult:
    """
    Run Tier A (+ optional Tier B) multi-sense pass for a finished claims report.

    Set MULTISENSE_OFFLINE=1 or pass offline=True to force the deterministic proxy
    (no API calls). When Gemini client cannot be created, offline is used automatically.
    """
    if isinstance(report, (str, Path)) and str(report).endswith(".json"):
        report = json.loads(Path(report).read_text(encoding="utf-8"))
    assert isinstance(report, dict)

    video_id = str(
        report.get("video_id")
        or (report.get("metadata") or {}).get("video_id")
        or (report.get("media_embed") or {}).get("video_id")
        or "unknown"
    )
    claims = [c for c in (report.get("claims_breakdown") or []) if isinstance(c, dict)]
    force_offline = offline
    if force_offline is None:
        force_offline = os.environ.get("MULTISENSE_OFFLINE", "0") in {"1", "true", "True"}

    client = None if force_offline else _get_genai_client()
    use_live = client is not None and (video_uri or youtube_url)

    windows = build_clip_windows(claims, margin_sec=margin_sec)
    b_windows = tier_b_windows(windows, max_clips=max_tier_b)

    # --- Tier A ---
    if use_live:
        try:
            tier_a_raw = _invoke_gemini_video(
                client,
                prompt=TIER_A_PROMPT,
                video_uri=video_uri,
                youtube_url=youtube_url,
                fps=fps,
            )
            if not tier_a_raw.get("segments"):
                logger.warning("[multisense] empty Tier A response; falling back offline")
                tier_a_raw = _offline_tier_a(claims)
            else:
                tier_a_raw["source"] = "gemini"
                tier_a_raw["signal_tier"] = SIGNAL_TIER
        except Exception as exc:  # noqa: BLE001
            logger.warning("[multisense] Tier A failed (%s); offline proxy", exc)
            tier_a_raw = _offline_tier_a(claims)
    else:
        tier_a_raw = _offline_tier_a(claims)

    tier_a_segments = [_attach_sr(s) for s in (tier_a_raw.get("segments") or []) if isinstance(s, dict)]
    tier_a = {
        "overall_summary": tier_a_raw.get("overall_summary"),
        "segments": tier_a_segments,
        "source": tier_a_raw.get("source", "offline_proxy"),
        "signal_tier": SIGNAL_TIER,
    }

    # --- Tier B ---
    claim_by_id = {c.get("claim_id"): c for c in claims}
    tier_b_results: list[dict[str, Any]] = []
    for w in b_windows:
        texts = []
        for cid in w.claim_ids:
            ct = (claim_by_id.get(cid) or {}).get("claim_text") or ""
            if ct:
                texts.append(ct)
        claim_text = " | ".join(texts)
        if use_live:
            try:
                prompt = TIER_B_PROMPT.format(
                    claim_text=claim_text or "(none)",
                    start_sec=w.start_sec,
                    end_sec=w.end_sec,
                )
                raw = _invoke_gemini_video(
                    client,
                    prompt=prompt,
                    video_uri=video_uri,
                    youtube_url=youtube_url,
                    start_sec=w.start_sec,
                    end_sec=w.end_sec,
                    fps=fps,
                )
                if not raw:
                    raw = _offline_tier_b(w, claim_text)
                else:
                    raw["source"] = "gemini"
                    raw["window"] = w.to_dict()
            except Exception as exc:  # noqa: BLE001
                logger.warning("[multisense] Tier B window %s failed (%s)", w.start_sec, exc)
                raw = _offline_tier_b(w, claim_text)
        else:
            raw = _offline_tier_b(w, claim_text)
        tier_b_results.append(_attach_sr(raw))

    # Per-claim delivery_signals rollup (for report.py attachment)
    claim_delivery: list[dict[str, Any]] = []
    for claim in claims:
        cid = claim.get("claim_id")
        t = parse_timestamp(claim.get("timestamp"))
        # nearest Tier A segment
        nearest = None
        best_dist = 1e18
        for s in tier_a_segments:
            mid = 0.5 * (float(s.get("start_sec") or 0) + float(s.get("end_sec") or 0))
            d = abs(mid - t)
            if d < best_dist:
                best_dist = d
                nearest = s
        # Tier B hit?
        b_hit = None
        for b in tier_b_results:
            win = b.get("window") or {}
            ids = win.get("claim_ids") or []
            if cid in ids:
                b_hit = b
                break
        delivery = {
            "claim_id": cid,
            "timestamp_sec": t,
            "signal_tier": SIGNAL_TIER,
            "tier_a": {
                "vocal_emotion": (nearest or {}).get("vocal_emotion"),
                "arousal": (nearest or {}).get("arousal"),
                "valence": (nearest or {}).get("valence"),
                "delivery": (nearest or {}).get("delivery"),
                "sr_segments": (nearest or {}).get("sr_segments"),
                "confidence": (nearest or {}).get("confidence"),
            }
            if nearest
            else None,
            "tier_b": {
                "congruence_score": b_hit.get("congruence_score"),
                "congruence_statement": b_hit.get("congruence_statement"),
                "facial_expression": b_hit.get("facial_expression"),
                "ocr_on_screen": b_hit.get("ocr_on_screen"),
                "vocal_delivery": b_hit.get("vocal_delivery"),
                "sr_segments": b_hit.get("sr_segments"),
                "confidence": b_hit.get("confidence"),
            }
            if b_hit
            else None,
            "disclaimer": DISCLAIMER,
        }
        claim_delivery.append(delivery)

    summary = {
        "n_claims": len(claims),
        "n_clip_windows": len(windows),
        "n_tier_a_segments": len(tier_a_segments),
        "n_tier_b_clips": len(tier_b_results),
        "source": tier_a.get("source"),
        "live_gemini": bool(use_live and tier_a.get("source") == "gemini"),
    }
    return MultisenseResult(
        video_id=video_id,
        tier_a=tier_a,
        tier_b=tier_b_results,
        clip_windows=[w.to_dict() for w in windows],
        claim_delivery=claim_delivery,
        summary=summary,
    )
