"""
Deep Research orchestration.

read {video_id}_report.json -> counter-intel sanitize -> Gemini grounded run ->
write {video_id}_deep_private_report.{md,html,pdf} + grounding/sanitized audit
artefacts into ``out_dir`` (local filesystem). GCS upload is handled by callers
(batch job / unified flow) so this module stays storage-agnostic and testable.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

from verityngn.config.settings import (
    DEEP_RESEARCH_MIN_CLAIMS,
    DEEP_RESEARCH_MIN_OUTPUT_BYTES,
)
from verityngn.services.deepresearch.client import run_deep_research
from verityngn.services.deepresearch.renderer import (
    render_html_to_pdf,
    render_markdown_to_html,
)
from verityngn.services.deepresearch.sanitize import count_claims, sanitize_report_data

logger = logging.getLogger(__name__)


class DeepResearchGateError(RuntimeError):
    """Raised when an eligibility gate blocks the run (too few claims, etc.)."""


def _derive_title(report: Dict[str, Any], video_id: str) -> str:
    for key in ("title", "video_title"):
        val = report.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    qs = report.get("quick_summary")
    if isinstance(qs, dict):
        t = qs.get("title")
        if isinstance(t, str) and t.strip():
            return t.strip()
    return f"Forensic Audit — {video_id}"


async def generate_deep_research_report(
    report_json_path: str,
    out_dir: str,
    *,
    video_id: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate the Deep Research artefacts from an existing report JSON.

    Returns a dict with ``status`` ("completed" | "failed"), output file paths,
    and run metadata (model_id, prompt_version, output_bytes, claims). On a
    gating failure raises ``DeepResearchGateError``.
    """
    if not os.path.exists(report_json_path):
        raise FileNotFoundError(f"report json not found: {report_json_path}")

    with open(report_json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not video_id:
        video_id = (
            raw.get("video_id")
            or (raw.get("media_embed") or {}).get("video_id")
            or os.path.basename(report_json_path).split("_report.json")[0]
        )

    claims = count_claims(raw)
    if claims < DEEP_RESEARCH_MIN_CLAIMS:
        raise DeepResearchGateError(
            f"Deep Research requires >= {DEEP_RESEARCH_MIN_CLAIMS} claims; found {claims}."
        )

    os.makedirs(out_dir, exist_ok=True)
    sanitized = sanitize_report_data(raw)

    # Audit snapshot of exactly what the model saw.
    sanitized_path = os.path.join(out_dir, f"{video_id}_deep_sanitized_input.json")
    with open(sanitized_path, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, indent=2)

    logger.info("[deep-research] running Gemini grounded pass for %s (%d claims)", video_id, claims)
    result = run_deep_research(sanitized)

    md_path = os.path.join(out_dir, f"{video_id}_deep_private_report.md")
    html_path = os.path.join(out_dir, f"{video_id}_deep_private_report.html")
    pdf_path = os.path.join(out_dir, f"{video_id}_deep_private_report.pdf")
    grounding_path = os.path.join(out_dir, f"{video_id}_deep_private_report.grounding.json")

    run_meta = {
        "video_id": video_id,
        "model_id": result.model_id,
        "prompt_version": result.prompt_version,
        "output_bytes": result.output_bytes,
        "claims": claims,
        "search_queries": result.queries,
    }

    # Persist grounding metadata + run metadata for the audit trail (always).
    with open(grounding_path, "w", encoding="utf-8") as f:
        json.dump(
            {"run": run_meta, "grounding_metadata": result.grounding_metadata},
            f,
            indent=2,
        )

    # Quality guard: empty/short output -> failed.
    if result.output_bytes < DEEP_RESEARCH_MIN_OUTPUT_BYTES:
        logger.warning(
            "[deep-research] output too small (%d bytes < %d); marking failed",
            result.output_bytes,
            DEEP_RESEARCH_MIN_OUTPUT_BYTES,
        )
        return {"status": "failed", "reason": "empty_output", **run_meta, "grounding_path": grounding_path}

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(result.markdown)

    html = render_markdown_to_html(result.markdown, video_id, title=title or _derive_title(raw, video_id))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    pdf_ok = await render_html_to_pdf(html, pdf_path)

    combined_meta: Dict[str, Any] = {}
    try:
        from verityngn.services.report.combined_report import generate_combined_report_artifacts

        combined_meta = await generate_combined_report_artifacts(
            report_json_path,
            out_dir,
            video_id=video_id,
            deep_markdown_path=md_path,
            skip_llm=True,
        )
        logger.info(
            "[deep-research] combined report for %s -> %s",
            video_id,
            combined_meta.get("html_path"),
        )
    except Exception as exc:
        logger.warning("[deep-research] combined report generation failed for %s: %s", video_id, exc)
        combined_meta = {"status": "failed", "reason": str(exc)}

    logger.info("[deep-research] completed %s -> %s (pdf=%s)", video_id, md_path, pdf_ok)
    return {
        "status": "completed",
        "markdown_path": md_path,
        "html_path": html_path,
        "pdf_path": pdf_path if pdf_ok else None,
        "grounding_path": grounding_path,
        "sanitized_path": sanitized_path,
        "combined": combined_meta,
        **run_meta,
    }
