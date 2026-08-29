#!/usr/bin/env bash
# Publish verityngn 3.0.0 to PyPI (requires TWINE credentials / API token).
set -euo pipefail
cd "$(dirname "$0")/../.."
rm -rf dist build *.egg-info
python -m pip install -U build twine
python -m build
python -m twine check dist/*
echo "Uploading — ensure TWINE_USERNAME=__token__ and TWINE_PASSWORD are set"
python -m twine upload dist/*
