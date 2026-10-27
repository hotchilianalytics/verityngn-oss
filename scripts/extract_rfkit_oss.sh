#!/usr/bin/env bash
# Phase 1: copy the disclosure engine into a fresh-history public tree.
# Excludes GOF/shorts jobs, outreach, Derrick mail packs, NDA, pricing, EDGAR cache.
set -euo pipefail
SRC="${1:-$HOME/proj/ajjax/downloads/rfkit}"
DEST="${2:-$HOME/proj/rfkit-oss}"
OSS="${3:-$HOME/proj/verityngn-oss}"

mkdir -p "$DEST"
rsync -a --delete \
  --exclude '__pycache__/' \
  --exclude '.venv/' \
  --exclude 'data/' \
  --exclude 'outreach/' \
  --exclude 'consulting/' \
  --exclude 'package/' \
  --exclude '*.zip' \
  --exclude '.git/' \
  --exclude 'EMAIL_TO_DERRICK*' \
  --exclude 'BATCH_RESULTS*' \
  --exclude 'scripts/sweep_adversarial.py' \
  --exclude 'scripts/dump_short_report.py' \
  --exclude 'scripts/build_package.py' \
  "$SRC/rfkit/" "$DEST/rfkit/"

mkdir -p "$DEST/tests" "$DEST/ontologies" "$DEST/scripts"
rsync -a --exclude '__pycache__/' "$SRC/tests/" "$DEST/tests/"
rsync -a "$SRC/ontologies/" "$DEST/ontologies/"

# Drop tests that import the closed riskfactor engine.
rm -f "$DEST/tests/test_scoring.py" "$DEST/tests/test_render_visibility.py" "$DEST/tests/test_runner.py"

cp "$OSS/LICENSE" "$DEST/LICENSE"
cp "$SRC/pyproject.toml" "$DEST/pyproject.toml"

# Keep only engine-facing scripts.
if [ -f "$SRC/scripts/backtest_materialized.py" ]; then
  cp "$SRC/scripts/backtest_materialized.py" "$DEST/scripts/"
fi
if [ -f "$SRC/scripts/pre_commit_visibility_guard.py" ]; then
  cp "$SRC/scripts/pre_commit_visibility_guard.py" "$DEST/scripts/"
fi

echo "Extracted engine into $DEST"
