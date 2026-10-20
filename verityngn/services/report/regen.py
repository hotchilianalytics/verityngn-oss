"""
Regenerate report artifact families from a persisted master JSON dict.

Used by combined Deep Research assembly, backfill, and sanitize scripts.
"""
from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from verityngn.models.report import VerityReport
from verityngn.services.reputation.url_safety import sanitize_report_dict_urls, sanitize_url_list_in_text
from verityngn.services.report.fast_html_generator import generate_fast_html_report
from verityngn.services.report.html_generator import generate_html_report
from verityngn.services.report.markdown_generator import generate_markdown_report
from verityngn.utils.html_to_pdf import async_convert_html_content_to_pdf

logger = logging.getLogger(__name__)


def normalize_report_dict(data: Dict[str, Any], video_id: str) -> Dict[str, Any]:
    """Coerce persisted JSON into VerityReport-compatible shape."""
    d = copy.deepcopy(data)
    overall = d.get("overall_assessment")
    if isinstance(overall, list) and len(overall) == 2:
        d["overall_assessment"] = tuple(overall)

    for key in ("evidence_summary", "secondary_sources"):
        for item in d.get(key) or []:
            if isinstance(item, dict) and not item.get("title"):
                item["title"] = item.get("source_name") or item.get("url") or "Source"

    for c in d.get("claims_breakdown") or []:
        if not isinstance(c, dict):
            continue
        cid = c.get("claim_id")
        if isinstance(cid, str) and cid.startswith("claim_"):
            try:
                c["claim_id"] = int(cid.split("_")[-1])
            except Exception:
                c["claim_id"] = 0
        if "initial_assessment" not in c:
            vr = c.get("verification_result") or {}
            c["initial_assessment"] = vr.get("result", "UNVERIFIED")

    if not d.get("evidence_summary"):
        d["evidence_summary"] = []
    if not d.get("media_embed"):
        d["media_embed"] = {"video_id": video_id, "title": d.get("title") or video_id}
    if not d.get("title"):
        me = d.get("media_embed") or {}
        d["title"] = me.get("title") or video_id
    if not d.get("key_findings"):
        d["key_findings"] = []
    return d


async def regenerate_report_family(
    report_dict: Dict[str, Any],
    video_id: str,
    out_dir: Union[str, Path],
    *,
    deep_markdown: Optional[str] = None,
    generate_pdfs: bool = True,
) -> Dict[str, str]:
    """
    Sanitize master JSON and regenerate standard + optional deep report artifacts.

    Returns dict of logical keys -> local file paths.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    clean = sanitize_report_dict_urls(report_dict)
    normalized = normalize_report_dict(clean, video_id)
    report = VerityReport(**normalized)

    paths: Dict[str, str] = {}

    json_path = out / f"{video_id}_report.json"
    json_path.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    paths["json_path"] = str(json_path)

    md_orig, _, _ = generate_markdown_report(report, tier="original")
    md_path = out / f"{video_id}_report.md"
    md_path.write_text(md_orig, encoding="utf-8")
    paths["markdown_path"] = str(md_path)

    html_orig = generate_html_report(report, tier="original")
    html_path = out / f"{video_id}_report.html"
    html_path.write_text(html_orig, encoding="utf-8")
    paths["html_path"] = str(html_path)

    md_pub, _, _ = generate_markdown_report(report, tier="public")
    priv_md = out / f"{video_id}_private_report.md"
    priv_md.write_text(md_pub, encoding="utf-8")
    paths["private_markdown_path"] = str(priv_md)

    html_pub = generate_html_report(report, tier="public")
    priv_html = out / f"{video_id}_private_report.html"
    priv_html.write_text(html_pub, encoding="utf-8")
    paths["private_html_path"] = str(priv_html)

    fast_html = generate_fast_html_report(report, "")
    fast_path = out / f"{video_id}_fast_report.html"
    fast_path.write_text(fast_html, encoding="utf-8")
    paths["fast_html_path"] = str(fast_path)

    if generate_pdfs:
        pdf_path = out / f"{video_id}_report.pdf"
        result = await async_convert_html_content_to_pdf(html_orig, str(pdf_path))
        if result:
            paths["pdf_path"] = str(pdf_path)
        priv_pdf = out / f"{video_id}_private_report.pdf"
        result = await async_convert_html_content_to_pdf(html_pub, str(priv_pdf))
        if result:
            paths["private_pdf_path"] = str(priv_pdf)

    if deep_markdown is not None:
        from verityngn.services.deepresearch.renderer import render_html_to_pdf, render_markdown_to_html

        scrubbed = sanitize_url_list_in_text(deep_markdown)
        dr_md = out / f"{video_id}_deep_private_report.md"
        dr_md.write_text(scrubbed, encoding="utf-8")
        paths["deep_markdown_path"] = str(dr_md)

        dr_html = render_markdown_to_html(scrubbed, video_id, title=report.title or video_id)
        dr_html_path = out / f"{video_id}_deep_private_report.html"
        dr_html_path.write_text(dr_html, encoding="utf-8")
        paths["deep_html_path"] = str(dr_html_path)

        if generate_pdfs:
            dr_pdf = out / f"{video_id}_deep_private_report.pdf"
            ok = await render_html_to_pdf(dr_html, str(dr_pdf))
            if ok:
                paths["deep_pdf_path"] = str(dr_pdf)

    return paths
