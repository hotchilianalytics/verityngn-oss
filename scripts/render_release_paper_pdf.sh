#!/usr/bin/env bash
# Render papers/verityngn_oss_v3_release.html → PDF via Playwright/Chromium.
# Run OUTSIDE Cursor (local terminal) so Chromium can download/launch cleanly.
#
# Usage:
#   cd ~/proj/verityngn-oss
#   bash scripts/render_release_paper_pdf.sh
#
# Optional:
#   HTML=papers/verityngn_oss_v3_release.html OUT=papers/verityngn_oss_v3_release.pdf \
#     bash scripts/render_release_paper_pdf.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

HTML_REL="${HTML:-papers/verityngn_oss_v3_release.html}"
OUT_REL="${OUT:-papers/verityngn_oss_v3_release.pdf}"
export VN_HTML="$ROOT/$HTML_REL"
export VN_OUT="$ROOT/$OUT_REL"

if [[ ! -f "$VN_HTML" ]]; then
  echo "Missing $VN_HTML — run: python scripts/build_release_paper_html.py" >&2
  exit 1
fi

if [[ -x "$HOME/miniconda3/envs/verityngn/bin/python" ]]; then
  PYTHON="$HOME/miniconda3/envs/verityngn/bin/python"
elif [[ -x "$HOME/miniconda3/envs/sr/bin/python" ]]; then
  PYTHON="$HOME/miniconda3/envs/sr/bin/python"
else
  PYTHON="$(command -v python3)"
fi

echo "Using Python: $PYTHON"
"$PYTHON" -m pip install -q 'playwright>=1.40'
"$PYTHON" -m playwright install chromium

"$PYTHON" - <<'PY'
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

html = Path(os.environ["VN_HTML"]).resolve()
out = Path(os.environ["VN_OUT"]).resolve()
url = html.as_uri()
print(f"Rendering {url} -> {out}")
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    page.pdf(
        path=str(out),
        format="Letter",
        print_background=True,
        margin={"top": "0.6in", "bottom": "0.6in", "left": "0.65in", "right": "0.65in"},
    )
    browser.close()
print(f"Wrote {out} ({out.stat().st_size:,} bytes)")
PY
