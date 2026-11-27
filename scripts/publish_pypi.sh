#!/usr/bin/env bash
# Publish verityngn to PyPI (requires TWINE credentials / API token).
# Refuses to upload if SA/credential JSON or private_key material is in the artifacts.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

VERSION="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
echo "Publishing verityngn==${VERSION}"

rm -rf dist build *.egg-info verityngn.egg-info
python -m pip install -U build twine
python -m build

python - <<'PY'
import sys, zipfile, tarfile
from pathlib import Path

bad = []
for p in Path("dist").glob("*"):
    data = p.read_bytes()
    if b"BEGIN PRIVATE KEY" in data or b"private_key_id" in data:
        bad.append(f"{p.name}: credential material in bytes")
    names = []
    if p.name.endswith(".whl"):
        with zipfile.ZipFile(p) as z:
            names = z.namelist()
    elif p.name.endswith(".tar.gz"):
        with tarfile.open(p) as t:
            names = t.getnames()
    for n in names:
        low = n.lower().replace("\\", "/")
        if low.endswith("credentials.json") or ("verityindex" in low and low.endswith(".json")):
            bad.append(f"{p.name}: {n}")
        if "/config/" in f"/{low}" and low.endswith(".json"):
            bad.append(f"{p.name}: {n}")
if bad:
    print("REFUSING UPLOAD — secrets in artifacts:", *bad, sep="\n  ")
    sys.exit(2)
print("secret_scan: PASS")
PY

python -m twine check dist/*

echo "Uploading — ensure TWINE_USERNAME=__token__ and TWINE_PASSWORD are set"
python -m twine upload "dist/verityngn-${VERSION}-py3-none-any.whl" "dist/verityngn-${VERSION}.tar.gz"
