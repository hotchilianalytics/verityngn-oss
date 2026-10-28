"""Coverage matrix and severity rules (SplitRisk concept section 2.8).

Coverage cells are a dated quote or nothing; there is no numeric cell value.
Severity measures consequence only, never likelihood. Likelihood exists only
as a reviewer's ``judgment`` and never appears here.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from verityngn.agent.mcp_v2.schema_defs import SOURCE_CLASSES

_LEVEL = {"low": 0, "medium": 1, "high": 2}
EXPOSURE = ("supports_exposure", "contradicts_disclosure")


def _sev(level: str, rule: str, rationale: str) -> dict[str, Any]:
    return {"level": level, "basis": "engine", "rule": rule, "rationale": rationale[:500]}


def engine_severity(record: dict[str, Any]) -> dict[str, Any]:
    """Propose a severity level from the evidence the record carries."""
    evidence = record.get("evidence") or []
    exposure = [e for e in evidence if e.get("stance") in EXPOSURE or e.get("stance") is None]
    classes = {e.get("source_class") for e in exposure if not e.get("allegation")}
    kind = record.get("claim_kind")
    if "own" in classes and kind == "disclosure_pair":
        return _sev("high", "SEV-OWN-PAIR", "The issuer's own record describes the event while the disclosure treats it as hypothetical.")
    if "staff" in classes:
        return _sev("high", "SEV-STAFF", "SEC staff has commented on this topic.")
    if "docket" in classes:
        return _sev("high", "SEV-DOCKET", "A docket names the issuer on this topic.")
    if kind == "uncovered_spoken" or "spoken" in classes:
        return _sev("medium", "SEV-SPOKEN", "A public spoken claim is not reflected in the written risk factors.")
    if kind == "softening":
        return _sev("medium", "SEV-SOFTEN", "Risk language was removed or weakened year over year.")
    if record.get("allegation") or any(e.get("allegation") or e.get("source_class") == "short" for e in evidence):
        return _sev("medium", "SEV-SHORT", "Allegation only; never above medium.")
    if (record.get("junior_obvious") or {}).get("flag"):
        return _sev("low", "SEV-JUNIOR", (record.get("junior_obvious") or {}).get("reason") or "Hygiene issue a junior would catch.")
    return _sev("low", "SEV-CONTEXT", "Context only.")


def record_coverage(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cells: dict[str, dict[str, Any]] = {}
    junior = bool((record.get("junior_obvious") or {}).get("flag"))
    for ev in record.get("evidence") or []:
        cls = ev.get("source_class")
        if cls not in SOURCE_CLASSES or cls in cells:
            continue
        cell: dict[str, Any] = {"state": "junior_obvious" if junior and cls == "own" else "hit"}
        if ev.get("quote"):
            cell["quote"] = ev["quote"][:400]
        if ev.get("date"):
            cell["date"] = ev["date"]
        if ev.get("url"):
            cell["url"] = ev["url"]
        if record.get("claim_id"):
            cell["record_id"] = record["claim_id"]
        if ev.get("allegation") or cls == "short":
            cell["allegation"] = True
        cells[cls] = cell
    return cells


def _earlier(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (b.get("date") or "9999") < (a.get("date") or "9999")


def compose(records: Iterable[dict[str, Any]], group_by: str = "item_1a_heading") -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    uncovered: list[str] = []
    context: list[str] = []
    for rec in records:
        if group_by == "category":
            heading = rec.get("category") or "general"
        else:
            heading = rec.get("item_1a_heading") or (rec.get("category") or "general").replace("_", " ").title()
        row = rows.setdefault(
            heading,
            {"heading": heading, "cells": {c: {"state": "none"} for c in SOURCE_CLASSES}, "severity": None},
        )
        if rec.get("category") and "category" not in row:
            row["category"] = rec["category"]
        for cls, cell in (rec.get("coverage") or record_coverage(rec)).items():
            cur = row["cells"].get(cls, {"state": "none"})
            if cur["state"] == "none" or (cell["state"] != "none" and _earlier(cur, cell)):
                row["cells"][cls] = cell
        sev: Optional[dict[str, Any]] = rec.get("severity")
        if sev and (row["severity"] is None or _LEVEL[sev["level"]] > _LEVEL[row["severity"]["level"]]):
            row["severity"] = dict(sev)
        if rec.get("claim_kind") == "uncovered_spoken":
            uncovered.append(rec["claim_id"])
        evidence = rec.get("evidence") or []
        if evidence and all(e.get("stance") == "context" for e in evidence):
            context.append(rec["claim_id"])
    out_rows = []
    for row in rows.values():
        if row["severity"] is None:
            row["severity"] = _sev("low", "SEV-CONTEXT", "No exposure evidence in this group.")
        out_rows.append(row)
    out_rows.sort(key=lambda r: (-_LEVEL[r["severity"]["level"]], r["heading"]))
    return {
        "columns": list(SOURCE_CLASSES),
        "rows": out_rows,
        "uncovered_spoken": uncovered,
        "context_records": context,
    }
