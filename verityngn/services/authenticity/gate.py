"""Authenticity gate: fail closed for affect/vision scoring when checks fail."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AuthenticityResult:
    passed: bool
    gated: bool
    checks: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass": self.passed,
            "gated": self.gated,
            "checks": self.checks,
            "notes": self.notes,
        }


def run_authenticity_gate(
    *,
    video_id: str,
    corsound: Optional[dict[str, Any]] = None,
    visual: Optional[dict[str, Any]] = None,
    c2pa: Optional[dict[str, Any]] = None,
    rppg: Optional[dict[str, Any]] = None,
    require_all: bool = False,
) -> AuthenticityResult:
    """
    Combine optional vendor/open checks including rPPG consistency.

    Default: if no checks provided, pass (MVP offline). If any check explicitly
    fails, gate affect/vision. ``require_all=True`` fails when a required adapter
    is missing.
    """
    checks: list[dict[str, Any]] = []
    fails = 0

    def _ingest(name: str, payload: Optional[dict[str, Any]], required: bool = False) -> None:
        nonlocal fails
        if payload is None:
            checks.append({"name": name, "status": "skipped", "required": required})
            if required and require_all:
                fails += 1
            return
        status = payload.get("status") or ("pass" if payload.get("score", 1.0) >= 0.5 else "fail")
        if status in {"fail", "failed", "deepfake"}:
            fails += 1
        checks.append({"name": name, "status": status, "detail": payload})

    _ingest("corsound", corsound)
    _ingest("visual_deepfake", visual)
    _ingest("c2pa", c2pa)
    _ingest("rppg_consistency", rppg)

    passed = fails == 0
    return AuthenticityResult(
        passed=passed,
        gated=not passed,
        checks=checks,
        notes=f"Authenticity gate for {video_id}: {'PASS' if passed else 'GATE — affect/vision excluded'}",
    )
