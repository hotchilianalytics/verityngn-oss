"""Copy standard + deep report artifacts into the user -o directory.

UnifiedReportGenerator writes under outputs_debug/{vid}/*_complete/.
Deep Research writes into out_dir. Consumers expect both report.html and
deep.html (stable aliases) beside {vid}_report.json in -o.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical names consumers may rely on (stable contract).
ALIAS_REPORT_HTML = "report.html"
ALIAS_DEEP_HTML = "deep.html"


def _latest_debug_complete(video_id: str) -> Optional[Path]:
    debug_root = Path("outputs_debug") / video_id
    if not debug_root.is_dir():
        return None
    completes = sorted(
        [p for p in debug_root.glob("*_complete") if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return completes[0] if completes else None


def sync_standard_report_artifacts(
    out_dir: str | Path,
    video_id: str,
    *,
    patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Copy {vid}_report.{json,html,md,pdf} (and private/fast variants) from the
    latest timestamped complete dir into out_dir when missing or older.
    Also writes stable alias report.html when the canonical HTML exists.
    """
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)
    names = patterns or [
        f"{video_id}_report.json",
        f"{video_id}_report.html",
        f"{video_id}_report.md",
        f"{video_id}_report.pdf",
        f"{video_id}_private_report.pdf",
        f"{video_id}_private_report.html",
        f"{video_id}_fast_report.html",
    ]
    src_dir = _latest_debug_complete(video_id)
    copied: List[str] = []
    if src_dir:
        for name in names:
            src = src_dir / name
            if not src.is_file():
                continue
            target = dest / name
            try:
                if not target.is_file() or src.stat().st_mtime > target.stat().st_mtime:
                    shutil.copy2(src, target)
                    copied.append(name)
            except Exception as exc:  # noqa: BLE001
                logger.warning("artifact_sync: failed to copy %s: %s", src, exc)
    else:
        # Fallback: search any report.json under outputs_debug
        debug_root = Path("outputs_debug") / video_id
        if debug_root.is_dir():
            for cand in sorted(
                debug_root.rglob(f"{video_id}_report.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ):
                try:
                    shutil.copy2(cand, dest / cand.name)
                    copied.append(cand.name)
                    sibling_html = cand.with_name(f"{video_id}_report.html")
                    if sibling_html.is_file():
                        shutil.copy2(sibling_html, dest / sibling_html.name)
                        copied.append(sibling_html.name)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("artifact_sync: fallback copy failed: %s", exc)
                break

    alias_info = ensure_report_html_alias(dest, video_id)
    logger.info(
        "artifact_sync: out_dir=%s video_id=%s copied=%s alias=%s",
        dest,
        video_id,
        copied,
        alias_info.get("report_html"),
    )
    return {
        "out_dir": str(dest),
        "video_id": video_id,
        "copied": copied,
        "src_dir": str(src_dir) if src_dir else None,
        **alias_info,
    }


def ensure_report_html_alias(out_dir: str | Path, video_id: str) -> Dict[str, Any]:
    """Stable report.html alias next to {vid}_report.html (consumer contract)."""
    dest = Path(out_dir)
    canonical = dest / f"{video_id}_report.html"
    alias = dest / ALIAS_REPORT_HTML
    if canonical.is_file():
        try:
            shutil.copy2(canonical, alias)
            return {"report_html": str(alias), "report_html_canonical": str(canonical)}
        except Exception as exc:  # noqa: BLE001
            logger.warning("artifact_sync: report.html alias failed: %s", exc)
    return {"report_html": str(alias) if alias.is_file() else None}


def ensure_deep_html_alias(out_dir: str | Path, video_id: str) -> Dict[str, Any]:
    """Stable deep.html alias next to {vid}_deep_private_report.html."""
    dest = Path(out_dir)
    canonical = dest / f"{video_id}_deep_private_report.html"
    alias = dest / ALIAS_DEEP_HTML
    if canonical.is_file():
        try:
            shutil.copy2(canonical, alias)
            return {"deep_html": str(alias), "deep_html_canonical": str(canonical)}
        except Exception as exc:  # noqa: BLE001
            logger.warning("artifact_sync: deep.html alias failed: %s", exc)
    return {"deep_html": str(alias) if alias.is_file() else None}


def checklist_artifacts(out_dir: str | Path, video_id: str) -> Dict[str, Any]:
    """Log-friendly presence check for dual-output contract."""
    dest = Path(out_dir)
    checks = {
        "report_json": (dest / f"{video_id}_report.json").is_file(),
        "report_html_canonical": (dest / f"{video_id}_report.html").is_file(),
        "report_html_alias": (dest / ALIAS_REPORT_HTML).is_file(),
        "report_pdf": (dest / f"{video_id}_report.pdf").is_file(),
        "deep_html_canonical": (dest / f"{video_id}_deep_private_report.html").is_file(),
        "deep_html_alias": (dest / ALIAS_DEEP_HTML).is_file(),
        "deep_pdf_canonical": (dest / f"{video_id}_private_report.pdf").is_file(),
    }
    logger.info(
        "artifacts_in_out_dir video_id=%s %s",
        video_id,
        " ".join(f"{k}={'yes' if v else 'NO'}" for k, v in checks.items()),
    )
    return checks
