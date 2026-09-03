"""Transcript+DR sufficiency metrics for tier routing (T-ABL-007).

Pre-flight (no LLM): duration, caption_kind, coverage, speech_density, visual_text_density.
Post-hoc: risk_recall@K, material_miss_list, citation_density, unsupported_assertion_rate.

Caption condition taxonomy (C0–C6) — see module docstring in transcript_providers.
"""
from __future__ import annotations

import logging
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")
_CUE_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})"
)
_REF_RE = re.compile(r"\[Reference:", re.I)
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "have", "has", "had", "not", "but", "you", "your", "our", "their", "about",
    "into", "over", "under", "reference", "currently", "claim", "unverified",
    "video", "risk", "report", "supported", "contested", "unresolved",
}

# Default routing thresholds (calibrated later; env-overridable)
DEFAULT_TAU_COV = float(os.getenv("VN_TAU_COV", "0.70"))
DEFAULT_TAU_VIS = float(os.getenv("VN_TAU_VIS", "0.35"))
DEFAULT_TAU_DUR = float(os.getenv("VN_TAU_DUR", "900"))  # 15 min
DEFAULT_MIN_RECALL = float(os.getenv("VN_MIN_RISK_RECALL", "0.80"))
DEFAULT_MIN_CITATION_DENSITY = float(os.getenv("VN_MIN_CITATION_DENSITY", "1.5"))

SUFFICIENT_CAPTION_KINDS = frozenset(
    {"manual", "asr_auto", "vendor_native", "cached"}
)


def tokenize(text: str) -> Set[str]:
    toks = {t.lower() for t in _TOKEN_RE.findall(text or "")}
    return {t for t in toks if t not in _STOP and len(t) > 2}


def token_set_ratio(a: str, b: str) -> float:
    sa, sb = tokenize(a), tokenize(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def _ts_to_seconds(ts: str) -> float:
    parts = ts.replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
    except ValueError:
        return 0.0
    return 0.0


def parse_vtt_cue_coverage(vtt: str) -> Dict[str, Any]:
    """Sum cue durations from WEBVTT; return coverage helpers."""
    total = 0.0
    n_cues = 0
    for m in _CUE_RE.finditer(vtt or ""):
        start = _ts_to_seconds(m.group("start"))
        end = _ts_to_seconds(m.group("end"))
        if end > start:
            total += end - start
            n_cues += 1
    return {"cue_duration_sec": total, "n_cues": n_cues}


def map_caption_kind(source: Optional[str], *, synthetic: bool = False) -> str:
    """Map caption_fetch source string → taxonomy kind."""
    if synthetic or (source or "").startswith("gemini"):
        return "synthetic_gemini"
    s = (source or "").strip().lower()
    if not s or s in ("none", "failed"):
        return "none"
    if s in ("cached", "cached_vtt", "cached_en_vtt"):
        return "cached"
    if s in ("yt-dlp", "ytdlp", "youtube_transcript_api", "api"):
        # Free scrapers usually yield auto-ASR captions for third-party videos
        return "asr_auto"
    if s in ("supadata", "supadata_native", "vendor_native"):
        return "vendor_native"
    if s in ("supadata_generate", "vendor_generated", "asr", "asr_groq", "groq"):
        return "vendor_generated"
    return s


def speech_density(transcript_chars: int, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    return transcript_chars / duration_sec


def caption_coverage(cue_duration_sec: float, duration_sec: float) -> float:
    if duration_sec <= 0:
        return 0.0
    return min(1.0, cue_duration_sec / duration_sec)


def estimate_visual_text_density(
    *,
    youtube_url: str = "",
    video_path: str = "",
    n_frames: int = 12,
) -> Dict[str, Any]:
    """
    Cheap visual-text probe without full multimodal extraction.

    Tries OpenCV frame sampling + optional Tesseract; falls back to 0.0 with reason.
    """
    path = video_path
    downloaded = False
    try:
        if not path and youtube_url:
            # Skip download in probe by default — use metadata-only zero
            if os.getenv("VN_PROBE_DOWNLOAD", "").strip() not in ("1", "true", "yes"):
                return {
                    "visual_text_density": 0.0,
                    "frames_sampled": 0,
                    "frames_with_text": 0,
                    "reason": "probe_download_disabled",
                }
        if not path or not Path(path).is_file():
            return {
                "visual_text_density": 0.0,
                "frames_sampled": 0,
                "frames_with_text": 0,
                "reason": "no_local_video",
            }

        import cv2  # type: ignore

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return {
                "visual_text_density": 0.0,
                "frames_sampled": 0,
                "frames_with_text": 0,
                "reason": "opencv_open_failed",
            }
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if frame_count <= 0:
            cap.release()
            return {
                "visual_text_density": 0.0,
                "frames_sampled": 0,
                "frames_with_text": 0,
                "reason": "empty_video",
            }
        idxs = [int(i * (frame_count - 1) / max(1, n_frames - 1)) for i in range(n_frames)]
        with_text = 0
        sampled = 0
        use_ocr = os.getenv("VN_PROBE_OCR", "").strip().lower() in ("1", "true", "yes")
        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            sampled += 1
            # Edge-density heuristic as OCR-free proxy for on-screen text/graphics
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 80, 160)
            edge_ratio = float(edges.mean()) / 255.0
            textish = edge_ratio > 0.08
            if use_ocr:
                try:
                    import pytesseract  # type: ignore

                    txt = pytesseract.image_to_string(gray) or ""
                    textish = len(txt.strip()) >= 20
                except Exception:  # noqa: BLE001
                    pass
            if textish:
                with_text += 1
        cap.release()
        density = (with_text / sampled) if sampled else 0.0
        return {
            "visual_text_density": round(density, 4),
            "frames_sampled": sampled,
            "frames_with_text": with_text,
            "reason": "edge_density" if not use_ocr else "ocr",
            "downloaded": downloaded,
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("visual_text_density probe failed: %s", exc)
        return {
            "visual_text_density": 0.0,
            "frames_sampled": 0,
            "frames_with_text": 0,
            "reason": f"error:{exc}",
        }


def genre_hint_from_title(title: str = "", explicit: str = "") -> str:
    if explicit:
        return explicit.strip().lower()
    t = (title or "").lower()
    if any(k in t for k in ("earnings", "quarterly", "q1 ", "q2 ", "q3 ", "q4 ", "investor")):
        return "earnings"
    if any(k in t for k in ("hearing", "deposition", "congress", "senate", "exhibit")):
        return "legal"
    if any(k in t for k in ("#ad", "sponsored", "review", "vs ", "supplement", "ag1")):
        return "ad"
    if any(k in t for k in ("weight loss", "lipozem", "vsl", "doctor reveals")):
        return "vsl"
    return "other"


def preflight_features(
    *,
    duration_sec: float = 0.0,
    transcript_chars: int = 0,
    caption_source: str = "",
    vtt_text: str = "",
    title: str = "",
    genre_hint: str = "",
    youtube_url: str = "",
    video_path: str = "",
    synthetic: bool = False,
    visual_probe: bool = False,
) -> Dict[str, Any]:
    cue = parse_vtt_cue_coverage(vtt_text)
    kind = map_caption_kind(caption_source, synthetic=synthetic)
    cov = caption_coverage(cue["cue_duration_sec"], duration_sec)
    dens = speech_density(transcript_chars, duration_sec)
    vis: Dict[str, Any] = {
        "visual_text_density": 0.0,
        "frames_sampled": 0,
        "frames_with_text": 0,
        "reason": "skipped",
    }
    if visual_probe:
        vis = estimate_visual_text_density(youtube_url=youtube_url, video_path=video_path)
    genre = genre_hint_from_title(title, genre_hint)
    return {
        "duration_sec": duration_sec,
        "caption_kind": kind,
        "caption_source": caption_source,
        "caption_coverage": round(cov, 4),
        "speech_density": round(dens, 4),
        "transcript_chars": transcript_chars,
        "cue_duration_sec": round(cue["cue_duration_sec"], 2),
        "n_cues": cue["n_cues"],
        "visual_text_density": vis.get("visual_text_density", 0.0),
        "visual_probe": vis,
        "genre_hint": genre,
    }


def citation_density(markdown: str) -> float:
    refs = len(_REF_RE.findall(markdown or ""))
    chars = max(1, len(markdown or ""))
    return (refs / chars) * 1000.0


def unsupported_assertion_rate(markdown: str) -> float:
    """Share of [Reference: Currently Claim is Unverified] among all references."""
    refs = _REF_RE.findall(markdown or "")
    if not refs:
        return 1.0
    unverified = len(
        re.findall(r"\[Reference:\s*Currently Claim is Unverified\]", markdown or "", re.I)
    )
    return unverified / len(refs)


def _claim_texts(claims: Sequence[Any]) -> List[str]:
    out: List[str] = []
    for c in claims or []:
        if isinstance(c, dict):
            t = str(c.get("claim_text") or c.get("text") or "").strip()
        else:
            t = str(c).strip()
        if t:
            out.append(t)
    return out


def rank_material_claims(
    claims: Sequence[Any],
    k: int = 10,
) -> List[Dict[str, Any]]:
    """Rank claims by crude specificity (length + digit/entity signals)."""
    ranked: List[Tuple[float, Dict[str, Any]]] = []
    for c in claims or []:
        if not isinstance(c, dict):
            c = {"claim_text": str(c)}
        text = str(c.get("claim_text") or c.get("text") or "")
        if len(text) < 20:
            continue
        score = min(100.0, len(text) / 2.0)
        if re.search(r"\d", text):
            score += 15
        if any(w in text.lower() for w in ("fda", "clinical", "percent", "%", "$", "million")):
            score += 10
        st = str(c.get("source_type") or "").lower()
        if st in ("visual_text", "chart", "graphic", "demonstration"):
            score += 12
        ranked.append((score, dict(c, claim_text=text)))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in ranked[:k]]


def match_claim_in_brief(
    claim_text: str,
    brief: str,
    *,
    token_threshold: float = 0.6,
) -> bool:
    """True if claim's token set overlaps a brief sentence above threshold."""
    if not claim_text or not brief:
        return False
    # Check against whole brief and against sentence windows
    if token_set_ratio(claim_text, brief) >= token_threshold:
        return True
    for sent in re.split(r"[.\n]+", brief):
        if len(sent.strip()) < 15:
            continue
        if token_set_ratio(claim_text, sent) >= token_threshold:
            return True
    # Also: all significant tokens present somewhere in brief
    toks = tokenize(claim_text)
    if len(toks) >= 4:
        brief_toks = tokenize(brief)
        hit = len(toks & brief_toks) / len(toks)
        if hit >= 0.7:
            return True
    return False


def risk_recall_at_k(
    full_claims: Sequence[Any],
    light_brief_md: str,
    *,
    k: int = 10,
    token_threshold: float = 0.6,
) -> Dict[str, Any]:
    top = rank_material_claims(full_claims, k=k)
    hits: List[Dict[str, Any]] = []
    misses: List[Dict[str, Any]] = []
    for c in top:
        text = str(c.get("claim_text") or "")
        row = {
            "claim_text": text[:240],
            "source_type": c.get("source_type"),
            "timestamp": c.get("timestamp"),
        }
        if match_claim_in_brief(text, light_brief_md, token_threshold=token_threshold):
            hits.append(row)
        else:
            misses.append(row)
    n = len(top)
    recall = (len(hits) / n) if n else 0.0
    return {
        "k": k,
        "n_material": n,
        "n_hits": len(hits),
        "n_misses": len(misses),
        "risk_recall": round(recall, 4),
        "hits": hits,
        "material_miss_list": misses,
        "token_threshold": token_threshold,
    }


def route_decision(
    features: Dict[str, Any],
    *,
    tau_cov: float = DEFAULT_TAU_COV,
    tau_vis: float = DEFAULT_TAU_VIS,
    tau_dur: float = DEFAULT_TAU_DUR,
) -> Dict[str, Any]:
    """
    Decide light vs full from preflight features.

    route = light if caption_kind sufficient AND coverage>=TAU_COV
            AND visual_text_density<=TAU_VIS AND duration>=TAU_DUR
    """
    kind = str(features.get("caption_kind") or "none")
    cov = float(features.get("caption_coverage") or 0.0)
    vis = float(features.get("visual_text_density") or 0.0)
    dur = float(features.get("duration_sec") or 0.0)
    reasons: List[str] = []

    kind_ok = kind in SUFFICIENT_CAPTION_KINDS
    cov_ok = cov >= tau_cov
    vis_ok = vis <= tau_vis
    # Prefer light when video is long enough that full multimodal is expensive.
    # Unknown duration (0) still allows light if other gates pass.
    allow_short = os.getenv("VN_AUTO_LIGHT_SHORT", "").strip().lower() in ("1", "true", "yes")
    dur_ok = dur <= 0 or dur >= tau_dur or allow_short
    light = kind_ok and cov_ok and vis_ok and dur_ok
    if not kind_ok:
        reasons.append(f"caption_kind={kind} not in sufficient set")
    if not cov_ok:
        reasons.append(f"coverage {cov:.2f} < TAU_COV {tau_cov}")
    if not vis_ok:
        reasons.append(f"visual_text_density {vis:.2f} > TAU_VIS {tau_vis}")
    if not dur_ok:
        reasons.append(f"duration {dur:.0f}s < TAU_DUR {tau_dur} (prefer full when short)")
    elif light and dur >= tau_dur:
        reasons.append(f"duration {dur:.0f}s >= TAU_DUR {tau_dur} (cost crossover)")
    elif light:
        reasons.append("other gates pass (duration unknown or short-light enabled)")

    return {
        "route": "light" if light else "full",
        "reasons": reasons,
        "thresholds": {"TAU_COV": tau_cov, "TAU_VIS": tau_vis, "TAU_DUR": tau_dur},
        "checks": {
            "kind_ok": kind_ok,
            "cov_ok": cov_ok,
            "vis_ok": vis_ok,
            "dur_ok": dur_ok,
        },
        "features": features,
    }


def quality_floor_escalation(
    light_md: str,
    *,
    min_citation_density: float = DEFAULT_MIN_CITATION_DENSITY,
    min_chars: int = 800,
) -> Dict[str, Any]:
    """If light brief is thin or citation-poor, escalate to full."""
    dens = citation_density(light_md)
    chars = len(light_md or "")
    escalate = chars < min_chars or dens < min_citation_density
    return {
        "escalated": escalate,
        "citation_density": round(dens, 4),
        "brief_chars": chars,
        "min_citation_density": min_citation_density,
        "min_chars": min_chars,
        "reason": (
            "thin_or_uncited_brief"
            if escalate
            else "quality_floor_ok"
        ),
    }


def compare_sufficiency(
    *,
    full_claims: Sequence[Any],
    light_brief_md: str,
    full_elapsed: float = 0.0,
    light_elapsed: float = 0.0,
    full_usd: float = 0.0,
    light_usd: float = 0.0,
    k: int = 10,
) -> Dict[str, Any]:
    recall = risk_recall_at_k(full_claims, light_brief_md, k=k)
    cit = citation_density(light_brief_md)
    unsup = unsupported_assertion_rate(light_brief_md)
    latency_ratio = (full_elapsed / light_elapsed) if light_elapsed > 0 else None
    cost_ratio = (full_usd / light_usd) if light_usd > 0 else None
    competitive = recall["risk_recall"] >= DEFAULT_MIN_RECALL
    return {
        **recall,
        "citation_density": round(cit, 4),
        "unsupported_assertion_rate": round(unsup, 4),
        "full_elapsed_sec": full_elapsed,
        "light_elapsed_sec": light_elapsed,
        "latency_speedup": round(latency_ratio, 3) if latency_ratio is not None else None,
        "full_usd": full_usd,
        "light_usd": light_usd,
        "cost_speedup": round(cost_ratio, 3) if cost_ratio is not None else None,
        "decision_hint": (
            "light_competitive"
            if competitive
            else "keep_full_default"
        ),
        "min_risk_recall": DEFAULT_MIN_RECALL,
    }
