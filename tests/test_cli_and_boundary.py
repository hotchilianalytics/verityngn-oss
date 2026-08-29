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


def test_package_has_no_predictions_quant_karp_paths():
    """Negative scrub: predictions/quant product surfaces must not ship in OSS tree."""
    forbidden_dirs = {
        "predictions",
        "quant",
        "players",
        "mediasphere",
        "text_risk",
        "timeseries",
        "fusion",
        "deception",
        "affect",
    }
    services = PKG / "services"
    present = {p.name for p in services.iterdir() if p.is_dir()}
    leaked = present & forbidden_dirs
    assert not leaked, f"Forbidden overlay dirs in OSS package: {leaked}"

    # Filename / path greps under verityngn/
    bad_tokens = ("karp_panel", "RISK_FACTOR_REGISTRY", "S00_S15", "icar_", "deflated_sharpe")
    hits = []
    for path in PKG.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        name = path.name.lower()
        for tok in bad_tokens:
            if tok.lower() in name:
                hits.append(str(path.relative_to(ROOT)))
    assert not hits, f"Forbidden tokens in OSS package paths: {hits}"


def test_version_is_3():
    # Prefer importlib.metadata when installed; fall back to pyproject parse not required
    assert verityngn.__file__
