#!/usr/bin/env python3
"""Build print-ready HTML for the v3 ablation archive paper."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "papers" / "verityngn_v3_ablation_archive.md"
FIG = ROOT / "papers" / "figures"
OUT = ROOT / "papers" / "verityngn_v3_ablation_archive.html"
STATS = FIG / "t007_ablation_stats.json"
STATS_T006 = FIG / "t006_ablation_stats.json"


def _md_to_html_body(md: str) -> str:
    """Minimal markdown→HTML for archive paper (headings, tables, images, code)."""
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_code = False
    in_table = False
    table_rows: list[str] = []

    def flush_table() -> None:
        nonlocal table_rows, in_table
        if not table_rows:
            return
        html_rows = []
        for ri, row in enumerate(table_rows):
            cells = [c.strip() for c in row.strip("|").split("|")]
            tag = "th" if ri == 0 else "td"
            if ri == 1 and all(re.match(r"^:?-+:?$", c or "") for c in cells):
                continue
            html_rows.append(
                "<tr>" + "".join(f"<{tag}>{_inline(c)}</{tag}>" for c in cells) + "</tr>"
            )
        out.append("<table>\n" + "\n".join(html_rows) + "\n</table>")
        table_rows = []
        in_table = False

    def _inline(text: str) -> str:
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        return text

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                flush_table()
                out.append("<pre><code>")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(line.replace("&", "&amp;").replace("<", "&lt;") + "\n")
            i += 1
            continue
        if line.strip().startswith("|"):
            in_table = True
            table_rows.append(line)
            i += 1
            continue
        else:
            flush_table()

        m_img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if m_img:
            alt, src = m_img.group(1), m_img.group(2)
            out.append(f'<figure><img src="{src}" alt="{alt}"/><figcaption>{alt}</figcaption></figure>')
            i += 1
            # skip italic caption line if present
            if i < len(lines) and lines[i].strip().startswith("*") and lines[i].strip().endswith("*"):
                i += 1
            continue
        if line.startswith("# "):
            out.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.startswith("## "):
            out.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("### "):
            out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.strip() == "---":
            out.append("<hr/>")
        elif line.strip() == "":
            out.append("")
        elif line.startswith("- "):
            # gather list
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{_inline(lines[i][2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        else:
            out.append(f"<p>{_inline(line)}</p>")
        i += 1
    flush_table()
    return "\n".join(out)


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    body = _md_to_html_body(md)
    stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.is_file() else {}
    t007 = stats.get("t007") or stats
    t006 = json.loads(STATS_T006.read_text(encoding="utf-8")) if STATS_T006.is_file() else {}
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>VerityNgn v3.0.0 — Sufficiency Routing Archive</title>
<style>
  body {{
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
    line-height: 1.55; color: #1f2933; max-width: 820px; margin: 0 auto;
    padding: 28px 22px 64px; background: #fff;
  }}
  h1,h2,h3 {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    color: #0f172a; line-height: 1.25; }}
  h1 {{ font-size: 1.75rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; margin: 1rem 0; }}
  th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f1f5f9; }}
  code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.85rem; }}
  pre {{ background: #f8fafc; padding: 12px; overflow-x: auto; border: 1px solid #e2e8f0; }}
  figure {{ margin: 1.2rem 0; }}
  img {{ max-width: 100%; height: auto; }}
  figcaption {{ font-size: 0.85rem; color: #52606d; margin-top: 0.35rem; }}
  .meta {{ color: #52606d; font-size: 0.95rem; margin-bottom: 1.2rem; }}
  a {{ color: #0f766e; }}
</style>
</head>
<body>
<div class="meta">
T-ABL-007 mean latency ×{t007.get('mean_latency_speedup', '?')} ·
cost ×{t007.get('mean_cost_speedup', '?')} ·
risk_recall {t007.get('mean_risk_recall', '?')} ·
T-ABL-006 sleeve {t006.get('n_sleeve_validated', '?')}/3
</div>
{body}
</body>
</html>
"""
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
