"""
Fused report: TL;DR hook + Deep Research + full VerityIndex report in one artifact family.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from markdown_it import MarkdownIt
from mdit_py_plugins.attrs import attrs_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

from verityngn.config.settings import AGENT_MODEL_NAME, MAX_OUTPUT_TOKENS_2_0_FLASH, PROJECT_ID, VERTEX_LOCATION
from verityngn.models.report import VerityReport
from verityngn.services.reputation.url_safety import is_safe_url, sanitize_url_list_in_text
from verityngn.services.report.markdown_generator import (
    generate_main_report_content,
    generate_sources_appendix,
)
from verityngn.services.report.notices import PRIVATE_IN_REPORT_NOTICE
from verityngn.utils.llm_utils import invoke_text_prompt_with_fallback

logger = logging.getLogger(__name__)

_UNSAFE_HREF_RE = re.compile(
    r"""(?P<attr>href|src)\s*=\s*["'](?P<url>[^"']+)["']""",
    re.IGNORECASE,
)

_TLDR_PROMPT = ChatPromptTemplate.from_template("""
You are VerityNgn, an independent video verification editor for HotChili Analytics, LLC.

Write a punchy TL;DR for a combined forensic report. Rules:
- Use qualitative verdict language only (Highly Likely True, Likely True, Mixed / Uncertain, Likely False, Highly Likely False). Never use percentages or numeric scores.
- Start with a one-sentence "Bottom line" hook a busy journalist would read.
- Then exactly 3 bullet points: why this matters, biggest red flag, what to verify next.
- Max 180 words total. No URLs in the output.
- End with: "Independent editorial research by HotChili Analytics, LLC — not provided or endorsed by YouTube or Google."

Video title: {title}
Overall assessment: {verdict}
Key issue: {key_issue}
Main concerns: {concerns}
Deep research excerpt (first 1200 chars): {deep_excerpt}
""")

_COMBINED_CSS = """
:root { color-scheme: light; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.65; color: #1f2933; max-width: 900px; margin: 0 auto; padding: 32px 24px;
  background: #ffffff;
}
h1, h2, h3 { color: #102a43; line-height: 1.25; }
h1 { font-size: 1.9em; border-bottom: 2px solid #e4e7eb; padding-bottom: .3em; }
h2 { font-size: 1.4em; margin-top: 1.6em; }
a { color: #2563eb; text-decoration: none; word-break: break-word; }
a:hover { text-decoration: underline; }
img { max-width: 100%; height: auto; border-radius: 8px; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #f0f4f8; }
.cr-header {
  background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
  color: #f8fafc; padding: 22px 24px; border-radius: 10px; margin-bottom: 20px;
}
.cr-header .badge {
  display: inline-block; font-size: .72em; letter-spacing: .12em; text-transform: uppercase;
  background: rgba(248,250,252,.15); padding: 3px 10px; border-radius: 999px; margin-bottom: 8px;
}
.cr-header h1 { color: #f8fafc; border: none; margin: 4px 0 0; font-size: 1.6em; }
.cr-header .meta { color: #cbd5e1; font-size: .85em; margin-top: 6px; }
.cr-disclaimer {
  border: 1px solid #f0c36d; background: #fff8e6; color: #6b4e09;
  border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; font-size: .9em;
}
.cr-disclaimer p { margin: 6px 0; }
.cr-hero {
  text-align: center; margin: 0 0 28px; padding: 20px 16px;
  border: 1px solid #e4e7eb; border-radius: 10px; background: #f8fafc;
}
.cr-hero h1 { border: none; margin: 0 0 12px; font-size: 1.5em; }
.cr-hero img { display: block; margin: 0 auto 10px; max-width: 560px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }
.cr-hero .video-id { color: #64748b; font-size: .9em; margin: 0; }
details { border: 1px solid #e1e4e8; border-radius: 6px; margin-bottom: 16px; }
details > summary { cursor: pointer; padding: 12px 16px; background: #f6f8fa; font-weight: 600; }
details > div { padding: 16px; border-top: 1px solid #e1e4e8; }
.cr-appendix { margin-top: 2.5em; padding-top: 1.5em; border-top: 3px solid #334155; }
"""


def _strip_leading_h1(md: str) -> str:
    """Remove redundant top-level heading from deep markdown before nesting."""
    if not md:
        return ""
    lines = md.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:]).lstrip()
    return md.strip()


def _video_display_title(report: VerityReport, deep_markdown: Optional[str] = None) -> str:
    media = report.media_embed
    video_id = media.video_id if media else "unknown"
    title = (
        (media.title if media and media.title else None)
        or report.title
        or ""
    ).strip()
    if title and title != video_id and not title.startswith("Video "):
        return title
    if deep_markdown:
        quoted = re.search(
            r'(?:broadcast|video|episode|titled)\s+["“]([^"”\n]+)["”]',
            deep_markdown,
            re.IGNORECASE,
        )
        if quoted:
            return quoted.group(1).strip().rstrip(".")
        for line in deep_markdown.splitlines():
            line = line.strip()
            if line.startswith("# PLATINUM SUMMARY REPORT:"):
                tail = line.split("FORENSIC AUDIT OF", 1)[-1].strip()
                if tail:
                    return tail.title() if tail.isupper() else tail
            if line.startswith("# ") and "PLATINUM" not in line:
                return line[2:].strip()
    return title or f"Video {video_id}"


def _build_video_hero_markdown(report: VerityReport, deep_markdown: Optional[str] = None) -> str:
    """Title + clickable thumbnail above TL;DR (markdown image works in MD/HTML/PDF)."""
    media = report.media_embed
    video_id = media.video_id if media else "unknown"
    title = _video_display_title(report, deep_markdown)
    video_url = (
        (media.video_url if media and media.video_url else None)
        or f"https://www.youtube.com/watch?v={video_id}"
    )
    thumbnail = (
        (media.thumbnail_url if media and media.thumbnail_url else None)
        or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    )
    return f"""# {title}

[![Video thumbnail — open on YouTube]({thumbnail})]({video_url})

*Video ID: `{video_id}`*
"""


def _scrub_unsafe_links_in_html(html_fragment: str) -> str:
    def _repl(match: re.Match) -> str:
        attr = match.group("attr")
        url = match.group("url")
        if is_safe_url(url):
            return match.group(0)
        return f'{attr}="#" data-removed-unsafe-link="true"'

    return _UNSAFE_HREF_RE.sub(_repl, html_fragment or "")


def render_combined_markdown_to_html(
    markdown_text: str,
    video_id: str,
    *,
    display_title: Optional[str] = None,
) -> str:
    """Render combined report markdown with html:true so embeds and accordions survive."""
    md = (
        MarkdownIt("gfm-like", {"html": True, "linkify": True, "typographer": True})
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .use(deflist_plugin)
        .use(tasklists_plugin)
        .use(attrs_plugin)
    )
    body = md.render(markdown_text or "")
    body = _scrub_unsafe_links_in_html(body)

    heading = escape(display_title or "Combined VerityIndex Report")
    generated = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    notice = escape(PRIVATE_IN_REPORT_NOTICE)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Combined Report — {escape(video_id)}</title>
<style>{_COMBINED_CSS}</style>
</head>
<body>
<div class="cr-header">
  <span class="badge">VerityIndex · Combined Report</span>
  <h1>{heading}</h1>
  <div class="meta">Video ID: {escape(video_id)} · Generated {escape(generated)}</div>
</div>
<div class="cr-disclaimer" role="note">
  <p>{notice}</p>
</div>
<main>
{body}
</main>
</body>
</html>"""


async def generate_tldr(report: VerityReport, deep_markdown: Optional[str] = None) -> str:
    """LLM-generated catchy TL;DR / Bottom Line section."""
    qs = report.quick_summary
    verdict = ""
    if report.overall_assessment:
        verdict = str(
            report.overall_assessment[0].value
            if hasattr(report.overall_assessment[0], "value")
            else report.overall_assessment[0]
        )
    concerns = ", ".join(qs.main_concerns[:5]) if qs and qs.main_concerns else "N/A"
    deep_excerpt = (deep_markdown or "")[:1200]

    try:
        text, meta, response = invoke_text_prompt_with_fallback(
            primary_model=AGENT_MODEL_NAME,
            prompt=_TLDR_PROMPT.format(
                title=_video_display_title(report, deep_markdown),
                verdict=verdict,
                key_issue=qs.key_issue if qs else "N/A",
                concerns=concerns,
                deep_excerpt=deep_excerpt,
            ),
            project_id=PROJECT_ID,
            preferred_tokens=MAX_OUTPUT_TOKENS_2_0_FLASH,
            temperature=0.4,
            logger=logger,
        )
        return sanitize_url_list_in_text(text)
    except Exception as exc:
        logger.error("TL;DR generation failed: %s", exc)
        fallback = (
            f"**Bottom line:** {verdict or 'Mixed / Uncertain'} — {qs.key_issue if qs else 'See full report.'}\n\n"
            f"{PRIVATE_IN_REPORT_NOTICE}"
        )
        return fallback


def build_combined_markdown(
    report: VerityReport,
    deep_markdown: Optional[str],
    tldr_md: str,
    *,
    tier: str = "original",
) -> str:
    """Assemble hero + TL;DR + Deep Research + full report + sources appendix."""
    full_body = generate_main_report_content(
        report,
        tier=tier,  # type: ignore[arg-type]
        omit_video_header=True,
        omit_sources=True,
    )
    appendix = generate_sources_appendix(report)

    parts = [
        _build_video_hero_markdown(report, deep_markdown),
        "",
        "---",
        "",
        "# TL;DR / Bottom Line",
        "",
        tldr_md.strip(),
        "",
        "---",
        "",
        "## Deep Research Forensic Summary",
        "",
        _strip_leading_h1(deep_markdown or "_No Deep Research artifact was available for this video._"),
        "",
        "---",
        "",
        "## Full VerityIndex Report",
        "",
        full_body,
        "",
        "---",
        "",
        '<div class="cr-appendix">',
        "",
        appendix.rstrip(),
        "",
        "</div>",
    ]
    return "\n".join(parts)


async def render_combined(
    markdown_text: str,
    video_id: str,
    title: Optional[str] = None,
    out_dir: Optional[Union[str, Path]] = None,
    *,
    generate_pdf: bool = True,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Render combined markdown to HTML and optional PDF.

    Returns (html_path_or_content, pdf_path, md_path) — paths when out_dir set.
    """
    from verityngn.utils.html_to_pdf import async_convert_html_content_to_pdf

    html = render_combined_markdown_to_html(
        markdown_text,
        video_id,
        display_title=title,
    )
    pdf_path: Optional[str] = None
    md_path: Optional[str] = None

    if out_dir:
        base = Path(out_dir)
        base.mkdir(parents=True, exist_ok=True)
        md_path = str(base / f"{video_id}_combined_report.md")
        Path(md_path).write_text(markdown_text, encoding="utf-8")
        html_path = str(base / f"{video_id}_combined_report.html")
        Path(html_path).write_text(html, encoding="utf-8")
        if generate_pdf:
            pdf_path = str(base / f"{video_id}_combined_report.pdf")
            result = await async_convert_html_content_to_pdf(html, pdf_path)
            if not result:
                pdf_path = None
        return html_path, pdf_path, md_path

    if generate_pdf:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
            result = await async_convert_html_content_to_pdf(html, pdf_path)
            if not result:
                pdf_path = None
    return html, pdf_path, None


def _deterministic_tldr(report: VerityReport) -> str:
    verdict = report.overall_assessment[0] if report.overall_assessment else "Mixed / Uncertain"
    if hasattr(verdict, "value"):
        verdict = verdict.value
    return f"**Bottom line:** {verdict} — see full report below."


async def generate_combined_report_artifacts(
    report_json_path: str,
    out_dir: str,
    *,
    video_id: Optional[str] = None,
    deep_markdown_path: Optional[str] = None,
    deep_markdown: Optional[str] = None,
    skip_llm: bool = True,
    generate_pdf: bool = True,
    tier: str = "original",
) -> Dict[str, Any]:
    """
    Build combined report files from an existing report JSON and Deep Research markdown.

    Does not re-run Deep Research or the main verification pipeline. When ``skip_llm``
    is True (default for batch/backfill), uses a deterministic TL;DR hook.
    """
    from verityngn.services.report.regen import normalize_report_dict
    from verityngn.services.reputation.url_safety import sanitize_report_dict_urls

    if not Path(report_json_path).is_file():
        raise FileNotFoundError(f"report json not found: {report_json_path}")

    with open(report_json_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not video_id:
        video_id = (
            raw.get("video_id")
            or (raw.get("media_embed") or {}).get("video_id")
            or Path(report_json_path).name.split("_report.json")[0]
        )

    clean = sanitize_report_dict_urls(raw)
    report = VerityReport(**normalize_report_dict(clean, video_id))

    if deep_markdown is None and deep_markdown_path and Path(deep_markdown_path).is_file():
        deep_markdown = Path(deep_markdown_path).read_text(encoding="utf-8")

    if skip_llm:
        tldr = _deterministic_tldr(report)
    else:
        tldr = await generate_tldr(report, deep_markdown)

    combined = build_combined_markdown(report, deep_markdown, tldr, tier=tier)
    html_path, pdf_path, md_path = await render_combined(
        combined,
        video_id,
        title=_video_display_title(report, deep_markdown),
        out_dir=out_dir,
        generate_pdf=generate_pdf,
    )
    return {
        "status": "completed",
        "video_id": video_id,
        "markdown_path": md_path,
        "html_path": html_path,
        "pdf_path": pdf_path,
    }
