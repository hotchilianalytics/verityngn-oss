#!/usr/bin/env python3
"""Build print-ready HTML for the OSS v3 release paper (figures + live gallery stats)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "papers" / "figures"
OUT = ROOT / "papers" / "verityngn_oss_v3_release.html"


def _img(rel: str, alt: str, caption: str) -> str:
    return f"""
<figure>
  <img src="{rel}" alt="{alt}"/>
  <figcaption>{caption}</figcaption>
</figure>
"""


def main() -> None:
    live = json.loads((FIG / "gallery_live_stats.json").read_text(encoding="utf-8"))
    local = json.loads((FIG / "gallery_local_claim_stats.json").read_text(encoding="utf-8"))
    rows = "".join(
        f"<tr><td><code>{e['video_id']}</code></td>"
        f"<td>{e['claims']}</td><td>{e['label']}</td>"
        f"<td><a href=\"{e['youtube_url']}\">source</a></td></tr>\n"
        for e in live["reports"]
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>VerityNgn OSS 3.0.0 — Release Paper</title>
<style>
  :root {{ color-scheme: light; }}
  body {{
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    line-height: 1.55; color: #1f2933; max-width: 820px; margin: 0 auto;
    padding: 28px 22px 64px; background: #fff;
  }}
  h1,h2,h3 {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: #0f172a; line-height: 1.25; }}
  h1 {{ font-size: 1.85rem; margin-bottom: 0.2rem; }}
  .meta {{ color: #52606d; font-size: 0.95rem; margin-bottom: 1.4rem; }}
  .badge {{
    display: inline-block; font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
    background: #0f172a; color: #f8fafc; padding: 4px 10px; border-radius: 999px; margin-bottom: 10px;
  }}
  code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.86em; }}
  pre {{ background: #f5f7fa; border: 1px solid #e4e7eb; border-radius: 8px; padding: 12px 14px; overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.92rem; }}
  th, td {{ border: 1px solid #d9e2ec; padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: #f0f4f8; }}
  figure {{ margin: 1.4rem 0; }}
  figure img {{ max-width: 100%; height: auto; border: 1px solid #e4e7eb; border-radius: 6px; }}
  figcaption {{ font-size: 0.88rem; color: #486581; margin-top: 0.45rem; }}
  .callout {{
    border-left: 4px solid #0f766e; background: #f0fdfa; padding: 10px 14px; margin: 1.2rem 0;
  }}
  .warn {{
    border-left: 4px solid #b45309; background: #fffbeb; padding: 10px 14px; margin: 1.2rem 0;
  }}
  a {{ color: #1d4ed8; }}
  @media print {{
    body {{ padding: 0; max-width: none; }}
    a {{ color: inherit; text-decoration: none; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
<span class="badge">VerityNgn OSS · v3.0.0</span>
<h1>VerityNgn OSS 3.0.0 — Public Engine Release</h1>
<p class="meta">HotChili Analytics / VerityNgn Research · 2026-08-29 · Apache-2.0 engine<br/>
Companion to <a href="https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0">GitHub release v3.0.0</a>
· Live gallery: <a href="https://verityindex.com/gallery">verityindex.com/gallery</a></p>

<div class="callout">
<strong>Drop-in public engine.</strong> Deep Research, claim verification, and optional authenticity cues ship in Apache OSS.
Predictions and RiskFactor stay closed overlays that depend on OSS — not the reverse.
</div>

<h2>1. Abstract</h2>
<p>We release <strong>VerityNgn OSS 3.0.0</strong>, a standalone multimodal engine for claim extraction and verification from video.
This release restores <strong>Deep Research</strong> (grounded forensic summarization) to the public tree, adds optional authenticity and spectral voice cues,
and documents the open-core boundary. We do <em>not</em> claim earnings prediction, allocation factors, or lie detection.</p>

{_img("figures/open_core_architecture.png", "Open-core architecture", "Figure 1. OSS Apache engine vs closed commercial and predictions/RiskFactor overlays.")}

<h2>2. System overview</h2>
<pre>Video URL or file
  → multimodal analysis + claim extraction
  → counter-intelligence (YouTube / press-release / Sherlock CI)
  → probabilistic verification (TRUE / FALSE / UNCERTAIN)
  → standard report (MD / HTML / JSON / PDF)
  → optional Deep Research (Gemini grounded pass + combined report)
  → optional authenticity / spectral / Face Landmarker cues</pre>

<p><code>verityngn analyze &lt;url&gt; --deep</code> runs after the standard report JSON exists.</p>

<h2>3. Live gallery evidence (verityindex.com)</h2>
<p>Scraped from the public gallery on <strong>2026-08-29</strong>:
<strong>{live['n_reports']} reports</strong>, <strong>{live['total_claims']} claims</strong> analyzed,
labels = {json.dumps(live['label_counts'])}.</p>

{_img("figures/gallery_thumb_collage.png", "Gallery thumbnails", "Figure 2. Public gallery cards (YouTube thumbnails + claim counts). Source: verityindex.com/gallery.")}
{_img("figures/gallery_live_claims_per_video.png", "Claims per video", "Figure 3. Claims analyzed per public gallery report (teal = Likely to be True, amber = Mixed).")}
{_img("figures/gallery_live_label_mix.png", "Label mix", "Figure 4. Overall gallery labels across the public set.")}

<table>
  <thead><tr><th>Video ID</th><th>Claims</th><th>Gallery label</th><th>Source</th></tr></thead>
  <tbody>
  {rows}
  </tbody>
</table>
<p class="meta">Editorial labels on the gallery are HotChili Analytics LLM assessments — not YouTube data.</p>

<h2>4. In-repo gallery claim mix (OSS report JSONs)</h2>
<p>Claim-level TRUE/FALSE/UNCERTAIN from <code>ui/gallery/approved/</code>
({local['n_videos']} videos, {local['total_claims']} claims with verification results):
{json.dumps(local['verdict_mix'])}.</p>

{_img("figures/gallery_local_verdict_mix.png", "Local verdict mix", "Figure 5. Claim-level verdict mix from in-repo approved gallery JSONs.")}
{_img("figures/gallery_local_verdict_stack.png", "Local verdict stack", "Figure 6. Per-video stacked verdicts (in-repo gallery).")}

{_img("figures/accuracy_stages.png", "Accuracy stages", "Figure 7. Prior evaluation narrative: accuracy lift across verification stages (baseline → counter-intel → Deep Research).")}

<h2>5. Install</h2>
<pre>pip install 'verityngn[deep]'
verityngn analyze 'https://www.youtube.com/watch?v=VIDEO_ID'
verityngn analyze 'https://www.youtube.com/watch?v=VIDEO_ID' --deep
verityngn analyze --file deposition.mp4 --title "Matter clip"</pre>

<h2>6. Open-core dependency model</h2>
<p>Commercial, predictions, and RiskFactor pin <strong>OSS ≥3.0.0</strong>. Boundary CI fails if
<code>services/predictions</code> or <code>services/quant</code> appear under the public package.
See <code>docs/OPEN_CORE.md</code>.</p>

<div class="warn">
<strong>What we will not claim:</strong> earnings prediction / allocation alpha; “lie detector” branding; RiskFactor S00–S15 registry scores in this paper.
</div>

<h2>7. Links</h2>
<ul>
  <li>Release: <a href="https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0">v3.0.0</a></li>
  <li>Repo: <a href="https://github.com/hotchilianalytics/verityngn-oss">verityngn-oss</a></li>
  <li>Gallery: <a href="https://verityindex.com/gallery">verityindex.com/gallery</a></li>
  <li>Demo: <a href="https://verityngn.streamlit.app">verityngn.streamlit.app</a></li>
  <li>Stats snapshot: <code>papers/figures/gallery_live_stats.json</code></li>
</ul>

<p class="no-print meta">Render PDF: <code>bash scripts/render_release_paper_pdf.sh</code></p>
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
