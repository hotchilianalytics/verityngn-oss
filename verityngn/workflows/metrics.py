"""
Run quality metrics and validation for verification workflow.
Writes {video_id}_metrics.json and logs warnings when thresholds are not met.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Warning thresholds from plan
THRESHOLDS = {
    "claims_per_minute": (0.5, "less than 0.5"),
    "temporal_coverage_pct": (60.0, "less than 60%"),
    "segments_with_few_claims": (0, "greater than 0"),
    "google_searches_made": (5, "less than 5"),
    "youtube_searches_made": (3, "less than 3"),
    "evidence_per_claim": (3.0, "less than 3"),
    "ci_sources_found": (0, "0"),
    "context_research_done": (True, "False"),
}


def _timestamp_to_seconds(ts: str) -> Optional[float]:
    """Convert MM:SS or HH:MM:SS to seconds; return None if unparseable.

    Time-range strings like "10:19-10:26" are reduced to the start time
    ("10:19") before parsing so that the range-end digits are not mistaken
    for an hours component.
    """
    if not ts or not isinstance(ts, str):
        return None
    ts = ts.strip()
    if ts.lower() in ("unknown", "n/a", ""):
        return None
    # Strip range suffix: "10:19-10:26" → "10:19"
    ts = re.split(r"\s*[-–]\s*", ts)[0].strip()
    parts = re.findall(r"\d+", ts)
    if not parts:
        return None
    parts = [int(p) for p in parts]
    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) >= 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def compute_run_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute run quality metrics from workflow state.

    Returns a dict with metrics and a 'warnings' list for any below threshold.
    """
    video_id = state.get("video_id", "unknown")
    claims = state.get("claims") or []
    duration_sec = state.get("video_duration_seconds")
    if duration_sec is None:
        video_info = state.get("video_info") or {}
        duration_sec = video_info.get("duration")
    vdm = state.get("video_duration_minutes")
    if duration_sec is None and vdm is not None:
        duration_sec = vdm * 60.0
    duration_min = (
        (duration_sec / 60.0) if duration_sec and duration_sec > 0 else 1.0
    )

    n_claims = len(claims)
    claims_per_minute = n_claims / duration_min if duration_min else 0.0

    # Temporal coverage: max/min timestamp in claims
    times_sec: List[float] = []
    for c in claims:
        if isinstance(c, dict):
            ts = c.get("timestamp") or c.get("timestamp_seconds")
            if ts is not None and isinstance(ts, (int, float)):
                times_sec.append(float(ts))
            elif isinstance(ts, str):
                s = _timestamp_to_seconds(ts)
                if s is not None:
                    times_sec.append(s)
    if times_sec and duration_sec and duration_sec > 0:
        span = max(times_sec) - min(times_sec)
        temporal_coverage_pct = (span / float(duration_sec)) * 100.0
    else:
        temporal_coverage_pct = 0.0

    # Segments with few claims: we don't have segment-level counts in state;
    # use 0 as placeholder unless state has segment_claim_counts
    segments_with_few_claims = 0
    segment_claim_counts = state.get("segment_claim_counts")
    if isinstance(segment_claim_counts, list):
        segments_with_few_claims = sum(1 for n in segment_claim_counts if n < 5)

    # Search counts: optional counters (state["_metrics_google_searches"] etc.)
    google_searches_made = state.get("_metrics_google_searches", 0)
    youtube_searches_made = state.get("_metrics_youtube_searches", 0)

    # Evidence per claim
    total_evidence = 0
    for c in claims:
        if isinstance(c, dict):
            ev = (
                c.get("evidence")
                or c.get("verification_result", {}).get("sources")
                or []
            )
            total_evidence += len(ev) if isinstance(ev, list) else 0
    evidence_per_claim = (total_evidence / n_claims) if n_claims else 0.0

    if evidence_per_claim == 0 and google_searches_made > 0:
        logger.warning(
            "All claims have 0 sources despite evidence searches (evidence_per_claim=0, google_searches_made=%s). "
            "Check Google Custom Search API: 403 Forbidden, billing, API key restrictions, or CSE ID.",
            google_searches_made,
        )

    ci_once = state.get("ci_once") or []
    ci_sources_found = len(ci_once) if isinstance(ci_once, list) else 0
    cr = (state.get("context_research") or "").strip()
    context_research_done = bool(cr)

    metrics = {
        "video_id": video_id,
        "claims_per_minute": round(claims_per_minute, 3),
        "temporal_coverage_pct": round(temporal_coverage_pct, 1),
        "segments_with_few_claims": segments_with_few_claims,
        "google_searches_made": google_searches_made,
        "youtube_searches_made": youtube_searches_made,
        "evidence_per_claim": round(evidence_per_claim, 2),
        "ci_sources_found": ci_sources_found,
        "context_research_done": context_research_done,
        "n_claims": n_claims,
        "video_duration_minutes": round(duration_min, 2),
    }

    warnings: List[str] = []
    cpm_t = THRESHOLDS["claims_per_minute"]
    if claims_per_minute < cpm_t[0]:
        warnings.append(
            f"claims_per_minute={claims_per_minute:.2f} (threshold: {cpm_t[1]})"  # noqa: E501
        )
    tcp_t = THRESHOLDS["temporal_coverage_pct"]
    if temporal_coverage_pct < tcp_t[0]:
        warnings.append(
            f"temporal_coverage_pct={temporal_coverage_pct:.1f}% "
            f"(threshold: {tcp_t[1]})"
        )
    swf_t = THRESHOLDS["segments_with_few_claims"]
    if segments_with_few_claims > swf_t[0]:
        warnings.append(
            f"segments_with_few_claims={segments_with_few_claims} "
            f"(threshold: {swf_t[1]})"
        )
    gs_t = THRESHOLDS["google_searches_made"]
    if google_searches_made < gs_t[0]:
        warnings.append(
            f"google_searches_made={google_searches_made} "
            f"(threshold: {gs_t[1]})"
        )
    ys_t = THRESHOLDS["youtube_searches_made"]
    if youtube_searches_made < ys_t[0]:
        warnings.append(
            f"youtube_searches_made={youtube_searches_made} "
            f"(threshold: {ys_t[1]})"
        )
    epc_t = THRESHOLDS["evidence_per_claim"]
    if n_claims and evidence_per_claim < epc_t[0]:
        warnings.append(
            f"evidence_per_claim={evidence_per_claim:.2f} "
            f"(threshold: {epc_t[1]})"
        )
    ci_t = THRESHOLDS["ci_sources_found"]
    if ci_sources_found == ci_t[0]:
        warnings.append(
            f"ci_sources_found={ci_sources_found} (threshold: {ci_t[1]})"
        )
    cr_t = THRESHOLDS["context_research_done"]
    if not context_research_done:
        warnings.append(
            f"context_research_done={context_research_done} "
            f"(threshold: {cr_t[1]})"
        )

    metrics["warnings"] = warnings
    return metrics


def validate_metrics(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pipeline node: compute metrics, write {video_id}_metrics.json,
    log summary and warnings. Call after generate_report.
    """
    video_id = state.get("video_id", "unknown")
    out_dir = state.get("out_dir_path", "")
    metrics = compute_run_metrics(state)

    if out_dir and video_id != "unknown":
        try:
            import os
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, f"{video_id}_metrics.json")
            with open(path, "w") as f:
                json.dump(metrics, f, indent=2)
            logger.info("📊 Metrics written to %s", path)
        except Exception as e:
            logger.warning("Could not write metrics file: %s", e)

    warnings = metrics.get("warnings", [])
    if warnings:
        warn_preview = "; ".join(warnings[:5])
        if len(warnings) > 5:
            warn_preview += " ..."
        logger.warning(
            "⚠️ Run metrics below threshold (%s warnings): %s",
            len(warnings), warn_preview,
        )
    else:
        logger.info("✅ Run metrics: all thresholds met")

    cpm = metrics.get("claims_per_minute", 0)
    tcp = metrics.get("temporal_coverage_pct", 0)
    epc = metrics.get("evidence_per_claim", 0)
    cis = metrics.get("ci_sources_found", 0)
    summary = (
        f"claims_per_min={cpm:.2f} temporal_coverage={tcp:.1f}% "
        f"evidence_per_claim={epc:.2f} ci_sources={cis}"
    )
    logger.info("📈 Metrics summary: %s", summary)
    return state
