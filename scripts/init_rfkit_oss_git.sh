#!/usr/bin/env bash
# Fresh-history init for ~/proj/rfkit-oss. Does not push. Does not create GitHub.
# Run after Derrick reviews OPEN_CLOSED.md.
set -euo pipefail
DEST="${1:-$HOME/proj/rfkit-oss}"
cd "$DEST"
if [ -d .git ]; then
  echo "already a git repo: $DEST"
  git log -1 --oneline
  exit 0
fi
git init -b main
git add LICENSE README.md OPEN_CLOSED.md pyproject.toml .gitignore rfkit ontologies tests scripts
git commit -m "$(cat <<'EOF'
Initial public extract of the disclosure-risk engine.

Matcher, EDGAR adapters, specimen/review CLI, and tests. No vault, outreach, NDA, prices, or GOF jobs. GitHub publish waits on Derrick's open/closed review.
EOF
)"
git log -1 --oneline
echo "Local history only. Do not gh-push until Derrick reviews OPEN_CLOSED.md."
