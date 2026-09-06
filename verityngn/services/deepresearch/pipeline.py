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
    try:
        from verityngn.services.deepresearch.primary_pack import inject_primary_pack

        sanitized = inject_primary_pack(sanitized)
    except Exception as exc:
        logger.warning("[deep-research] primary pack inject failed: %s", exc)

    # Audit snapshot of exactly what the model saw.
    sanitized_path = os.path.join(out_dir, f"{video_id}_deep_sanitized_input.json")
    with open(sanitized_path, "w", encoding="utf-8") as f:
        json.dump(sanitized, f, indent=2)

    logger.info("[deep-research] running Gemini grounded pass for %s (%d claims)", video_id, claims)
    result = run_deep_research(sanitized)

    from verityngn.services.deepresearch.citation_binder import bind_citations

    allowlist = list(
        sanitized.get("primary_urls")
        or sanitized.get("legislature_primary_urls")
        or []
    )
    grounding_uris = list(result.grounding_uris or [])

    # Layers 2–3: creator secondary + outbound cites before citation bind
    hops_audit: Dict[str, Any] = {}
    try:
        from verityngn.services.deepresearch.source_expander import expand_sources

        hops_audit = expand_sources(
            sanitized,
            layer1_uris=grounding_uris,
            primary_urls=allowlist,
        )
        for u in hops_audit.get("allowlist_urls") or []:
            if u and u not in allowlist:
                allowlist.append(u)
        hops_path = os.path.join(out_dir, f"{video_id}_deep_source_hops.json")
        with open(hops_path, "w", encoding="utf-8") as f:
            json.dump(hops_audit, f, indent=2)
        logger.info(
            "[deep-research] source hops allowlist+=%d → %s",
            len(hops_audit.get("allowlist_urls") or []),
            hops_path,
        )
    except Exception as exc:
        logger.warning("[deep-research] source expander failed: %s", exc)

    md_body = result.markdown or ""
    # Fail closed: only grounding URIs ∪ primary/hop allowlist may remain as Reference URLs.
    # (Developer API often returns grounding_metadata=None even when Search tool ran.)
    if not grounding_uris:
        logger.warning(
            "[deep-research] empty grounding_uris for %s — cite-only allowlist bind",
            video_id,
        )
    md_body = bind_citations(md_body, grounding_uris, allowlist=allowlist)

    md_path = os.path.join(out_dir, f"{video_id}_deep_private_report.md")
    html_path = os.path.join(out_dir, f"{video_id}_deep_private_report.html")
    pdf_path = os.path.join(out_dir, f"{video_id}_deep_private_report.pdf")
    grounding_path = os.path.join(out_dir, f"{video_id}_deep_private_report.grounding.json")

    run_meta = {
        "video_id": video_id,
        "model_id": result.model_id,
        "prompt_version": result.prompt_version,
        "output_bytes": len(md_body.encode("utf-8")),
        "claims": claims,
        "search_queries": result.queries,
        "grounding_uri_count": len(grounding_uris),
        "grounding_uris": grounding_uris,
        "citation_fail_closed": not bool(grounding_uris),
        "source_hops": {
            "hops_requested": hops_audit.get("hops_requested"),
            "allowlist_added": len(hops_audit.get("allowlist_urls") or []),
            "layers": [
                {"layer": L.get("layer"), "kept": len(L.get("kept") or [])}
                for L in (hops_audit.get("layers") or [])
            ],
        },
        "domain_classes": sanitized.get("domain_classes") or [],
    }

    # Persist grounding metadata + run metadata for the audit trail (always).
    with open(grounding_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "run": run_meta,
                "grounding_metadata": result.grounding_metadata,
                "grounding_uris": grounding_uris,
            },
            f,
            indent=2,
        )

    # Quality guard: empty/short output -> failed.
    if run_meta["output_bytes"] < DEEP_RESEARCH_MIN_OUTPUT_BYTES:
        logger.warning(
            "[deep-research] output too small (%d bytes < %d); marking failed",
            run_meta["output_bytes"],
            DEEP_RESEARCH_MIN_OUTPUT_BYTES,
        )
        return {"status": "failed", "reason": "empty_output", **run_meta, "grounding_path": grounding_path}

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_body)

    html = render_markdown_to_html(md_body, video_id, title=title or _derive_title(raw, video_id))
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

    # Stable deep.html alias for consumers (dual-output contract with report.html).
    from verityngn.services.report.artifact_sync import ensure_deep_html_alias, ensure_report_html_alias

    deep_alias = ensure_deep_html_alias(out_dir, video_id)
    report_alias = ensure_report_html_alias(out_dir, video_id)

    return {
        "status": "completed",
        "markdown_path": md_path,
        "html_path": html_path,
        "pdf_path": pdf_path if pdf_ok else None,
        "grounding_path": grounding_path,
        "sanitized_path": sanitized_path,
        "combined": combined_meta,
        "deep_html": deep_alias.get("deep_html"),
        "report_html": report_alias.get("report_html"),
        **run_meta,
    }
