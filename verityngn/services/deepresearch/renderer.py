"""
Render the Deep Research markdown into styled HTML (with the private compliance
disclaimer banner) and PDF.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from html import escape
from typing import Optional

from markdown_it import MarkdownIt

from verityngn.services.reputation.url_safety import is_safe_url

logger = logging.getLogger(__name__)

# Strip href/src attributes pointing at unsafe URLs in rendered Deep Research HTML
_UNSAFE_HREF_RE = re.compile(
    r"""(?P<attr>href|src)\s*=\s*["'](?P<url>[^"']+)["']""",
    re.IGNORECASE,
)


def _scrub_unsafe_links_in_html(html_fragment: str) -> str:
    def _repl(match: re.Match) -> str:
        attr = match.group("attr")
        url = match.group("url")
        if is_safe_url(url):
            return match.group(0)
        return f'{attr}="#" data-removed-unsafe-link="true"'

    return _UNSAFE_HREF_RE.sub(_repl, html_fragment or "")


def _disclaimer_html() -> str:
    from verityngn.services.report.notices import PRIVATE_IN_REPORT_NOTICE

    deep_note = (
        "This is a Deep Research report: an opinionated, independently "
        "grounded forensic summary. Citations were produced by an automated "
        "web-grounding model and should be independently verified before any "
        "external use."
    )
    return (
        '<div class="dr-disclaimer" role="note" '
        'aria-label="Deep Research compliance notice">'
        f"<p>{escape(deep_note)}</p>"
        f"<p>{escape(PRIVATE_IN_REPORT_NOTICE)}</p>"
        "</div>"
    )


_CSS = """
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
code, pre { background: #f5f7fa; border-radius: 4px; }
pre { padding: 12px; overflow-x: auto; }
blockquote { border-left: 4px solid #cbd2d9; margin-left: 0; padding-left: 16px; color: #486581; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }
th { background: #f0f4f8; }
.dr-header {
  background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
  color: #f8fafc; padding: 22px 24px; border-radius: 10px; margin-bottom: 20px;
}
.dr-header .badge {
  display: inline-block; font-size: .72em; letter-spacing: .12em; text-transform: uppercase;
  background: rgba(248,250,252,.15); padding: 3px 10px; border-radius: 999px; margin-bottom: 8px;
}
.dr-header h1 { color: #f8fafc; border: none; margin: 4px 0 0; font-size: 1.6em; }
.dr-header .meta { color: #cbd5e1; font-size: .85em; margin-top: 6px; }
.dr-disclaimer {
  border: 1px solid #f0c36d; background: #fff8e6; color: #6b4e09;
  border-radius: 8px; padding: 12px 16px; margin-bottom: 24px; font-size: .9em;
}
.dr-disclaimer p { margin: 6px 0; }
"""


def render_markdown_to_html(markdown_text: str, video_id: str, title: Optional[str] = None) -> str:
    """Render Deep Research markdown into a standalone, styled HTML document."""
    md = (
        MarkdownIt("gfm-like", {"html": False, "linkify": True, "typographer": True})
    )
    body = md.render(markdown_text or "")
    body = _scrub_unsafe_links_in_html(body)
    heading = escape(title or "Deep Research Report")
    generated = datetime.now().strftime("%Y-%m-%d %H:%M UTC%z") or datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Deep Research — {escape(video_id)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="dr-header">
  <span class="badge">VerityNgn · Deep Research</span>
  <h1>{heading}</h1>
  <div class="meta">Video ID: {escape(video_id)} · Generated {escape(generated)}</div>
</div>
{_disclaimer_html()}
<main>
{body}
</main>
</body>
</html>"""


async def render_html_to_pdf(html_content: str, target_pdf_path: str) -> bool:
    """Render HTML to PDF via the shared Playwright helper. Returns success."""
    from verityngn.utils.html_to_pdf import async_convert_html_content_to_pdf

    try:
        result = await async_convert_html_content_to_pdf(html_content, target_pdf_path)
        return bool(result)
    except Exception as exc:  # pragma: no cover - depends on Chromium availability
        logger.error(
            "[deep-research] PDF render failed: %s. Ensure Chromium is installed "
            "(playwright install chromium) in the runtime image.",
            exc,
        )
        return False
