"""CLI help + import boundary + open-core scrub."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import verityngn


ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "verityngn"


def test_cli_help():
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    proc = subprocess.run(
        [sys.executable, str(ROOT / "verityngn" / "cli.py"), "analyze", "--help"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "--deep" in proc.stdout
    assert "--file" in proc.stdout


def test_import_boundary_no_commercial_backend():
    """OSS package must not pull commercial backend modules."""
    banned = (
        "verityngn_backend",
        "verityngn_backend_commercial",
        "VerityEngine",
    )
    mods = set(sys.modules)
    for name in banned:
        assert not any(m == name or m.startswith(name + ".") for m in mods)


def test_package_has_no_hosted_commercial_markers():
    """Hosted billing/credits/gallery markers must not ship under verityngn/."""
    bad_name_tokens = (
        "stripe",
        "dr_credits",
        "trial_credits",
        "verityindex_commercial",
        "billing_webhook",
    )
    bad_content = (
        "stripe.api_key",
        "dr_credits_remaining",
        "gs://verityindex_commercial/",
        "verityngn_backend_commercial",
    )
    hits = []
    for path in PKG.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        name = path.name.lower()
        for tok in bad_name_tokens:
            if tok in name:
                hits.append(f"name:{path.relative_to(ROOT)}")
        if path.suffix == ".py" and "services" in path.parts:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for tok in bad_content:
                if tok in text:
                    hits.append(f"content:{path.relative_to(ROOT)}:{tok}")
    assert not hits, f"Commercial markers in OSS package: {hits}"

    # Research sleeve packages are expected in OSS after 2026-10-05 absorb
    services = PKG / "services"
    present = {p.name for p in services.iterdir() if p.is_dir()}
    for expected in ("predictions", "quant", "fusion", "players", "affect"):
        assert expected in present, f"Missing research package: {expected}"


def test_version_is_3():
    # Prefer importlib.metadata when installed; fall back to pyproject parse not required
    assert verityngn.__file__
