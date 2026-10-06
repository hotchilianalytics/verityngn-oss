"""Thin renderer placeholder — markdown is primary for P5; HTML later."""
from __future__ import annotations

from pathlib import Path


def markdown_to_html_stub(md_path: Path, html_path: Path) -> Path:
    text = Path(md_path).read_text(encoding="utf-8")
    # Minimal escape-free wrap for internal demos only
    body = "".join(f"<p>{line}</p>\n" if line.strip() else "<br/>\n" for line in text.splitlines())
    html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Predictions</title></head><body>{body}</body></html>"
    html_path = Path(html_path)
    html_path.write_text(html, encoding="utf-8")
    return html_path
