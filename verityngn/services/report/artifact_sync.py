"""Copy standard + deep report artifacts into the user -o directory.

UnifiedReportGenerator writes under STORAGE_CONFIG local outputs
(`outputs_debug/{vid}/*_complete/` when DEBUG_OUTPUTS=true).
Deep Research writes into out_dir. Consumers (CLI `-o`, Batch OUTPUTS_DIR,
gallery/GCS upload) expect `{vid}_report.json/html` plus stable aliases
`report.html` / `deep.html` in the job dir.
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)

ALIAS_REPORT_HTML = "report.html"
ALIAS_DEEP_HTML = "deep.html"


def _unique_paths(paths: Iterable[Path]) -> List[Path]:
    seen = set()
    out: List[Path] = []
    for p in paths:
        try:
            key = str(p.resolve()) if p.exists() else str(p)
        except OSError:
            key = str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _debug_roots() -> List[Path]:
    """Candidate parents of `{video_id}/*_complete/` report trees."""
    roots: List[Path] = []
    try:
        from verityngn.config.settings import BASE_DIR, OUTPUTS_DIR, STORAGE_CONFIG

        local_out = (STORAGE_CONFIG or {}).get("local", {}).get("outputs_dir")
        if local_out:
            roots.append(Path(local_out))
        roots.append(Path(OUTPUTS_DIR))
        roots.append(Path(BASE_DIR) / "outputs_debug")
        roots.append(Path(BASE_DIR) / "outputs")
    except Exception:  # noqa: BLE001
        pass
    env_out = os.environ.get("OUTPUTS_DIR")
    if env_out:
        roots.append(Path(env_out))
    roots.append(Path("outputs_debug"))
    roots.append(Path("outputs"))
    return _unique_paths(roots)


def _latest_debug_complete(video_id: str, extra_roots: Optional[Sequence[Path]] = None) -> Optional[Path]:
    candidates: List[Path] = []
    roots = list(extra_roots or []) + _debug_roots()
    for root in _unique_paths(roots):
        debug_root = root / video_id
        if not debug_root.is_dir():
            continue
        candidates.extend(p for p in debug_root.glob("*_complete") if p.is_dir())
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _copy_file(src: Path, dest_dir: Path) -> Optional[str]:
    if not src.is_file():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / src.name
    try:
        if not target.is_file() or src.stat().st_mtime > target.stat().st_mtime:
            shutil.copy2(src, target)
            return src.name
    except Exception as exc:  # noqa: BLE001
        logger.warning("artifact_sync: failed to copy %s: %s", src, exc)
    return None


def sync_standard_report_artifacts(
    out_dir: str | Path,
    video_id: str,
    *,
    patterns: Optional[List[str]] = None,
    src_dir: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Copy `{vid}_report.*` (and private/fast/deep variants) from the latest
    timestamped complete dir into out_dir. Also writes stable aliases
    `report.html` / `deep.html`.
    """
    dest = Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)

    explicit = Path(src_dir) if src_dir else None
    if explicit and explicit.name.endswith("_processing"):
        complete = explicit.with_name(explicit.name.replace("_processing", "_complete", 1))
        if complete.is_dir():
            explicit = complete

    src_complete = None
    if explicit and explicit.is_dir():
        src_complete = explicit
    else:
        extra = [explicit.parent] if explicit else None
        src_complete = _latest_debug_complete(video_id, extra_roots=extra)

    copied: List[str] = []
    if src_complete:
        names = patterns or [
            f"{video_id}_report.json",
            f"{video_id}_report.html",
            f"{video_id}_report.md",
            f"{video_id}_report.pdf",
            f"{video_id}_private_report.md",
            f"{video_id}_private_report.html",
            f"{video_id}_private_report.pdf",
            f"{video_id}_fast_report.html",
            f"{video_id}_deep_private_report.json",
            f"{video_id}_deep_private_report.html",
            f"{video_id}_deep_private_report.md",
            f"{video_id}_deep_private_report.pdf",
            ALIAS_REPORT_HTML,
            ALIAS_DEEP_HTML,
        ]
        wanted = set(names)
        for src in src_complete.iterdir():
            if not src.is_file():
                continue
            if src.name in wanted or src.name.startswith(f"{video_id}_"):
                name = _copy_file(src, dest)
                if name:
                    copied.append(name)
    else:
        for root in _debug_roots():
            debug_root = root / video_id
            if not debug_root.is_dir():
                continue
            for cand in sorted(
                debug_root.rglob(f"{video_id}_report.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ):
                name = _copy_file(cand, dest)
                if name:
                    copied.append(name)
                for sibling_name in (
                    f"{video_id}_report.html",
                    f"{video_id}_report.md",
                    f"{video_id}_private_report.html",
                    f"{video_id}_fast_report.html",
                ):
                    sibling = cand.with_name(sibling_name)
                    copied_name = _copy_file(sibling, dest)
                    if copied_name:
                        copied.append(copied_name)
                break
            if copied:
                break

    alias_info = ensure_report_html_alias(dest, video_id)
    deep_alias = ensure_deep_html_alias(dest, video_id)
    logger.info(
        "artifact_sync: out_dir=%s video_id=%s copied=%s src_dir=%s alias=%s",
        dest,
        video_id,
        copied,
        src_complete,
        alias_info.get("report_html"),
    )
    return {
        "out_dir": str(dest),
        "video_id": video_id,
        "copied": copied,
        "src_dir": str(src_complete) if src_complete else None,
        **alias_info,
        **deep_alias,
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
