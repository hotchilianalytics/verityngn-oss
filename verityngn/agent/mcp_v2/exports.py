"""Report exports: JSON, Markdown, W3C Web Annotation collection, xlsx.

Judgment appears only in xlsx (with its fixed label). Allegations and
non-public evidence are left out unless the caller asked for internal content
and the role allows it.
"""

from __future__ import annotations

import io
import json
from typing import Any

from verityngn.agent.mcp_v2.errors import EngineNotInstalled, ToolFailure
from verityngn.agent.mcp_v2.schema_defs import JUDGMENT_LABEL, SOURCE_CLASSES

BANNER = "Not legal advice. Illustrative rewrites are for counsel to edit; no final disclosure is drafted."
MEDIA_TYPES = {
    "json": "application/json",
    "md": "text/markdown",
    "w3c_annotations": "application/ld+json",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def filter_records(records: list[dict[str, Any]], include_internal: bool) -> list[dict[str, Any]]:
    out = []
    for rec in records:
        if not include_internal and (rec.get("allegation") or rec.get("visibility") in ("internal", "private")):
            continue
        rec = dict(rec)
        if not include_internal:
            rec["evidence"] = [e for e in rec.get("evidence") or [] if e.get("visibility", "public") == "public"]
        out.append(rec)
    return out


def _no_judgment(rec: dict[str, Any]) -> dict[str, Any]:
    out = dict(rec)
    out.pop("judgment", None)
    return out


def to_json(report: dict[str, Any], records: list[dict[str, Any]], coverage: dict[str, Any]) -> bytes:
    body = {"report": report, "notice": BANNER, "records": [_no_judgment(r) for r in records], "coverage": coverage}
    return json.dumps(body, indent=2, sort_keys=True).encode("utf-8")


def to_markdown(report: dict[str, Any], records: list[dict[str, Any]], coverage: dict[str, Any]) -> bytes:
    lines = [f"# SplitRisk assessment {report['report_id']}", "", f"> {BANNER}", "", "## Coverage", ""]
    lines.append("| Heading | Severity | " + " | ".join(SOURCE_CLASSES) + " |")
    lines.append("|---|---|" + "---|" * len(SOURCE_CLASSES))
    for row in coverage.get("rows") or []:
        cells = []
        for cls in SOURCE_CLASSES:
            cell = row["cells"].get(cls) or {"state": "none"}
            cells.append("—" if cell["state"] == "none" else f"{cell.get('date', '')} quote")
        lines.append(f"| {row['heading']} | {row['severity']['level']} | " + " | ".join(cells) + " |")
    lines += ["", "## Findings", ""]
    for rec in records:
        sev = (rec.get("severity") or {}).get("level", "")
        lines.append(f"### {rec['verdict_or_action']} · {sev} · {rec['claim_kind']}")
        lines.append("")
        lines.append(rec["claim_text"])
        lines.append("")
        for ev in rec.get("evidence") or []:
            tag = " (Allegation)" if ev.get("allegation") else ""
            lines.append(f"- **{ev.get('source', '')}**{tag}, {ev.get('date', '')}: “{ev.get('quote', '')}” {ev.get('url', '')}")
        if rec.get("illustrative_rewrite"):
            lines += ["", f"_Illustrative rewrite for counsel to edit:_ {rec['illustrative_rewrite']}"]
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def to_w3c(report: dict[str, Any], records: list[dict[str, Any]]) -> bytes:
    items = []
    for rec in records:
        targets = [rec["target"]] if rec.get("target") else []
        targets += [e["anchor"] for e in rec.get("evidence") or [] if e.get("anchor")]
        if not targets:
            continue
        items.append(
            {
                "type": "Annotation",
                "id": rec["claim_id"],
                "motivation": "assessing",
                "body": {
                    "type": "TextualBody",
                    "value": f"{rec['verdict_or_action']} ({(rec.get('severity') or {}).get('level', '')}): {rec['claim_text']}",
                    "format": "text/plain",
                },
                "target": [
                    {k: v for k, v in t.items() if k in ("source", "selector")} for t in targets
                ],
            }
        )
    body = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "AnnotationCollection",
        "id": report["report_id"],
        "label": BANNER,
        "total": len(items),
        "first": {"type": "AnnotationPage", "items": items},
    }
    return json.dumps(body, indent=2).encode("utf-8")


def to_xlsx(report: dict[str, Any], records: list[dict[str, Any]], coverage: dict[str, Any]) -> bytes:
    try:
        from openpyxl import Workbook
    except ImportError:
        raise EngineNotInstalled("openpyxl", "xlsx export needs openpyxl, which is not installed on this server.", alternative="Export as json or md.") from None
    wb = Workbook()
    ws = wb.active
    ws.title = "Coverage"
    ws.append([BANNER])
    ws.append(["Heading", "Severity", "Severity basis", *SOURCE_CLASSES, f"Likelihood ({JUDGMENT_LABEL.lower()})"])
    for row in coverage.get("rows") or []:
        ws.append(
            [
                row["heading"],
                row["severity"]["level"],
                row["severity"]["basis"],
                *[(row["cells"].get(c) or {}).get("date", "") if (row["cells"].get(c) or {}).get("state") != "none" else "" for c in SOURCE_CLASSES],
                "",
            ]
        )
    ws2 = wb.create_sheet("Findings")
    ws2.append(["Record", "Claim", "Kind", "Verdict or action", "Severity", "Basis", "Review state", "Judgment", "Judgment label", "Entered by", "Evidence"])
    for rec in records:
        j = rec.get("judgment") or {}
        ws2.append(
            [
                rec["claim_id"],
                rec["claim_text"],
                rec["claim_kind"],
                rec["verdict_or_action"],
                (rec.get("severity") or {}).get("level", ""),
                (rec.get("severity") or {}).get("basis", ""),
                (rec.get("review") or {}).get("state", ""),
                j.get("likelihood", ""),
                j.get("label", ""),
                j.get("entered_by", ""),
                "; ".join(f"{e.get('source', '')} {e.get('date', '')}: {e.get('quote', '')}" for e in rec.get("evidence") or []),
            ]
        )
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def render(fmt: str, report: dict[str, Any], records: list[dict[str, Any]], coverage: dict[str, Any]) -> tuple[bytes, str]:
    if fmt == "json":
        return to_json(report, records, coverage), MEDIA_TYPES[fmt]
    if fmt == "md":
        return to_markdown(report, records, coverage), MEDIA_TYPES[fmt]
    if fmt == "w3c_annotations":
        return to_w3c(report, records), MEDIA_TYPES[fmt]
    if fmt == "xlsx":
        return to_xlsx(report, records, coverage), MEDIA_TYPES[fmt]
    raise ToolFailure(
        "INVALID",
        f"The {fmt} export is not built in this release.",
        alternative="Export as json, md, xlsx or w3c_annotations.",
    )
