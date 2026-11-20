#!/usr/bin/env python3
"""Rebuild the two v3.0.1 release PDFs from their markdown sources.

Sources (docs/releases/v3.0.1/):
  verity-engine-oss-3-0-1-golden-release.md       -> verity-engine-oss-3.0.1-golden-release-paper.pdf
  verity-engine-oss-3-0-1-release-description.md  -> verity-engine-oss-3.0.1-release-description.pdf

Requires: markdown, playwright (python), and Google Chrome (used via executable_path,
so `playwright install chromium` is not needed).

    python scripts/release/build_v301_release_pdfs.py
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "docs" / "releases" / "v3.0.1"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; color: #1e2a36;
       font-size: 10pt; line-height: 1.45; margin: 0; }
h1.title { font-size: 22pt; line-height: 1.2; margin: 0 0 6px; color: #0f1c2b; }
.subtitle { color: #5b6b7b; font-size: 10pt; margin-bottom: 14px; }
.cards { display: flex; gap: 10px; margin: 12px 0 14px; }
.card { flex: 1; border: 1px solid #d5dde5; border-top: 4px solid #1b9aaa; border-radius: 4px;
        padding: 8px 10px; background: #f7fafc; }
.card .k { font-size: 7pt; letter-spacing: .08em; color: #5b6b7b; font-weight: 700; }
.card .v { font-size: 13pt; font-weight: 800; color: #0f1c2b; margin: 2px 0; }
.card .d { font-size: 8pt; color: #44525f; }
.mission { border-left: 5px solid #1b9aaa; background: #eef6f8; padding: 9px 12px;
           margin: 10px 0 14px; font-size: 10pt; }
h2 { background: #0f1c2b; color: #fff; text-transform: uppercase; letter-spacing: .03em;
     font-size: 11pt; padding: 7px 10px; margin: 22px 0 10px; break-after: avoid; }
h3 { font-size: 12pt; color: #0f1c2b; margin: 16px 0 6px; break-after: avoid;
     border-bottom: 1px solid #d5dde5; padding-bottom: 3px; }
h4 { font-size: 10.6pt; color: #14808d; margin: 12px 0 4px; break-after: avoid; }
p { margin: 5px 0 7px; } ul, ol { margin: 4px 0 8px 20px; padding: 0; } li { margin: 3px 0; }
a { color: #14808d; word-break: break-word; }
code { background: #eef1f4; padding: 0 3px; border-radius: 3px; font-size: 9pt;
       font-family: Menlo, Consolas, monospace; }
img { max-width: 100%; display: block; margin: 8px auto; border: 1px solid #d5dde5; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 8px 0 12px;
        break-inside: avoid; }
th { background: #0f1c2b; color: #fff; text-align: left; padding: 5px 7px; }
td { border: 1px solid #d5dde5; padding: 4px 7px; vertical-align: top; }
tr:nth-child(even) td { background: #f7fafc; }
hr { display: none; }
em { color: #44525f; }
"""

PAPER_COVER = """
<h1 class="title">Verity Engine OSS 3.0.1: An Open Video-to-Text<br>Truthfulness and Risk Engine</h1>
<div class="subtitle">Official Technical Architecture &amp; Release Paper &middot; Apache-2.0 License &middot; Engine Tip 1b2cca8</div>
<div class="cards">
  <div class="card"><div class="k">MULTIMODAL PROOF</div><div class="v">81 Pixel Claims</div><div class="d">across 10 release runs; 45% of Oregon SB 1507</div></div>
  <div class="card"><div class="k">TAXONOMY MODEL</div><div class="v">6 Claim Kinds</div><div class="d">Empirical to Forward Forecast</div></div>
  <div class="card"><div class="k">PRIMARY-10 BATTERY</div><div class="v">342 Claims</div><div class="d">10 rows, 1 documented swap</div></div>
  <div class="card"><div class="k">OPEN CORE ENGINE</div><div class="v">Apache-2.0</div><div class="d">CLI, CI Graph &amp; Deep Research</div></div>
</div>
<div class="mission"><b>Executive Mission Statement:</b> Verity Engine OSS is a dedicated video-to-text truthfulness and risk assessment application. The engine ingests video content (YouTube URLs or local MP4 files), analyzes spoken dialogue and visual frames (1&ndash;6 fps), classifies propositions across a six-kind taxonomy, queries counter-evidence to eliminate confirmation bias, and generates structured, citation-backed audit dossiers for human reviewers.</div>
"""

DESC_COVER = """
<h1 class="title">Verity Engine OSS 3.0.1: Release Description &amp;<br>Syndication Kit</h1>
<div class="subtitle">Cross-Platform Social Distribution Kit &amp; Technical Release Announcement &middot; Apache-2.0 License</div>
"""


def body_html(md_path: Path, strip_front_matter: bool) -> str:
    text = md_path.read_text(encoding="utf-8")
    # drop the H1 and any front-matter lines before the first horizontal rule
    text = re.sub(r"^# .*\n", "", text, count=1)
    if strip_front_matter and "\n***" in text:
        text = text.split("\n***", 1)[1]
    text = text.replace("***", "", 1) if text.lstrip().startswith("***") else text
    # tolerate Read-tool style line-number prefixes if ever present
    text = re.sub(r"(?m)^\s*\d+\|", "", text)
    # lists need a blank line before them for python-markdown
    item = re.compile(r"^\s*(?:[*+-]|\d+\.) ")
    out, prev = [], ""
    for line in text.split("\n"):
        if item.match(line) and prev.strip() and not item.match(prev):
            out.append("")
        out.append(line)
        prev = line
    text = "\n".join(out)
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def render(html: str, out: Path, header: str, footer_left: str) -> None:
    doc = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{html}</body></html>"
    tmp = DIR / "_build_tmp.html"
    tmp.write_text(doc, encoding="utf-8")
    hdr = ("<div style=\"font-size:7pt;width:100%;padding:0 0.6in;color:#5b6b7b;"
           "font-family:Helvetica,Arial,sans-serif;display:flex;justify-content:space-between\">"
           f"<span>{header}</span><span>OSS RELEASE 3.0.1</span></div>")
    ftr = ("<div style=\"font-size:7pt;width:100%;padding:0 0.6in;color:#5b6b7b;"
           "font-family:Helvetica,Arial,sans-serif;display:flex;justify-content:space-between\">"
           f"<span>{footer_left}</span><span>Page <span class='pageNumber'></span> of <span class='totalPages'></span>"
           "</span><span>HotChili Analytics / VerityNgn</span></div>")
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=CHROME)
            pg = b.new_page()
            pg.goto(tmp.as_uri())
            pg.wait_for_load_state("load")
            pg.pdf(path=str(out), format="Letter", print_background=True,
                   display_header_footer=True, header_template=hdr, footer_template=ftr,
                   margin={"top": "0.75in", "bottom": "0.7in", "left": "0.6in", "right": "0.6in"})
            b.close()
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    paper_md = DIR / "verity-engine-oss-3-0-1-golden-release.md"
    desc_md = DIR / "verity-engine-oss-3-0-1-release-description.md"
    render(PAPER_COVER + body_html(paper_md, strip_front_matter=True),
           DIR / "verity-engine-oss-3.0.1-golden-release-paper.pdf",
           "VERITY ENGINE OSS 3.0.1: TECHNICAL RELEASE PAPER",
           "Technical Architecture Paper | Apache-2.0 Engine")
    render(DESC_COVER + body_html(desc_md, strip_front_matter=False),
           DIR / "verity-engine-oss-3.0.1-release-description.pdf",
           "VERITY ENGINE OSS 3.0.1: RELEASE DESCRIPTION &amp; SYNDICATION KIT",
           "Release Description &amp; Syndication Kit | Apache-2.0")
    print("built both PDFs in", DIR)


if __name__ == "__main__":
    main()
