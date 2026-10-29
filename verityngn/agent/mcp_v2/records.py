"""Build, validate and present extended ClaimRiskRecords (schema 2.0)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from functools import lru_cache
from typing import Any, Optional

from verityngn.agent.mcp_v2.coverage import engine_severity, record_coverage
from verityngn.agent.mcp_v2.errors import ToolFailure
from verityngn.agent.mcp_v2.schema_defs import bundle, ref
from verityngn.agent.mcp_v2.store import new_token
from verityngn.schemas.claim_risk import SCHEMA_VERSION, neutral_verdict

CLAIM_KINDS = {
    "source_backed_fact",
    "data_derived_inference",
    "causal_analytical",
    "reasoned_opinion",
    "prediction",
    "unverified_assertion",
    "disclosure_pair",
    "uncovered_spoken",
    "softening",
}
_EVIDENCE_KEYS = (
    "source", "quote", "date", "url", "source_id", "source_class", "stance", "visibility",
    "anchor", "match_mode", "quote_sha256", "allegation", "licence", "retrieved_at",
)
_PASSTHROUGH = ("category", "item_1a_heading", "illustrative_rewrite", "junior_obvious", "lag_clock", "entity_id")


def record_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def finding_key(source_id: str, engine: str, domain_pack: str, start: Any, claim_text: str) -> str:
    """Identity of one engine finding: same document, engine, pack, position and text."""
    return "|".join([source_id, engine, domain_pack, str(start), " ".join(claim_text.split())])


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_hash(obj: Any) -> str:
    return sha256_text(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str))


def engine_commit() -> str:
    return os.environ.get("VERITYNGN_COMMIT", "")


def _claim_kind(raw: Any) -> str:
    kind = str(raw or "").strip()
    if kind in CLAIM_KINDS:
        return kind
    try:
        from verityngn.workflows.claim_kind import normalize_claim_kind

        kind = normalize_claim_kind(kind)
    except Exception:  # noqa: BLE001
        pass
    return kind if kind in CLAIM_KINDS else "unverified_assertion"


def _evidence(item: dict[str, Any]) -> dict[str, Any]:
    ev = {k: item[k] for k in _EVIDENCE_KEYS if item.get(k) is not None}
    ev["source"] = str(ev.get("source") or "")
    ev["quote"] = str(ev.get("quote") or "")[:400]
    if ev.get("date"):
        ev["date"] = str(ev["date"])[:10]
    ev["url"] = str(ev.get("url") or "")
    if ev["quote"] and "quote_sha256" not in ev:
        ev["quote_sha256"] = sha256_text(ev["quote"])
    if ev.get("allegation") or ev.get("source_class") == "short":
        ev["allegation"] = True
        ev["visibility"] = "internal"
    ev.setdefault("visibility", "public")
    return ev


def build_record(
    raw: dict[str, Any],
    *,
    tenant: str,
    domain_pack: str,
    tool: str,
    engine: str,
    engine_version: str = "",
    model: str = "",
    source_lane: str,
    doc_id: Optional[str] = None,
    target: Optional[dict[str, Any]] = None,
    entity_id: Optional[str] = None,
    extra_disclaimers: tuple[str, ...] = (),
    key: Optional[str] = None,
) -> dict[str, Any]:
    """Build a schema 2.0 record. With ``key``, the record ID is stable for the same finding."""
    kind = _claim_kind(raw.get("claim_kind"))
    evidence = [_evidence(e) for e in raw.get("evidence") or [] if isinstance(e, dict)]
    allegation = bool(raw.get("allegation")) or any(e.get("allegation") for e in evidence)
    rec: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "claim_id": f"sr:rec:{tenant}/{record_key(key) if key else new_token()}",
        "domain_pack": domain_pack,
        "claim_text": str(raw.get("claim_text") or "").strip(),
        "claim_kind": kind,
        "evidence": evidence,
        "verdict_or_action": neutral_verdict(raw.get("verdict_or_action") or "UNRESOLVED", claim_kind=kind),
        "source_lane": source_lane,
        "visibility": "internal" if allegation else str(raw.get("visibility") or "public"),
        "allegation": allegation,
        "role_view": ["analyst", "gc", "junior"],
        "review": {"state": "proposed", "version": 1, "history": []},
        "no_promote": False,
        "provenance": {
            "tool": tool,
            "engine": engine,
            "engine_version": engine_version or str(raw.get("engine_version") or ""),
            "engine_commit": str(raw.get("engine_commit") or engine_commit()),
            "model": model or str(raw.get("model") or ""),
            "generated_at": now_iso(),
        },
    }
    for key in _PASSTHROUGH:
        if raw.get(key) is not None:
            rec[key] = raw[key]
    if entity_id and "entity_id" not in rec:
        rec["entity_id"] = entity_id
    if raw.get("confidence") is not None:
        rec["confidence"] = max(0.0, min(1.0, float(raw["confidence"])))
    if raw.get("residual_reliance_risk"):
        rec["residual_reliance_risk"] = str(raw["residual_reliance_risk"])
    if doc_id:
        rec["doc_id"] = doc_id
    if target:
        rec["target"] = target
    disclaimers = ["not_legal_advice", *extra_disclaimers]
    if allegation:
        disclaimers.append("allegation_only")
    if rec["provenance"]["model"]:
        disclaimers.append("llm_editorial")
    rec["disclaimers"] = list(dict.fromkeys(disclaimers))
    rec["severity"] = raw["severity"] if isinstance(raw.get("severity"), dict) and raw["severity"].get("basis") else engine_severity(rec)
    rec["coverage"] = record_coverage(rec)
    validate_record(rec)
    return rec


@lru_cache(maxsize=1)
def _record_validator() -> Any:
    from jsonschema import Draft202012Validator, FormatChecker

    return Draft202012Validator(bundle(ref("ClaimRiskRecord")), format_checker=FormatChecker())


def validate_record(rec: dict[str, Any]) -> None:
    errors = sorted(_record_validator().iter_errors(rec), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        where = "/".join(str(p) for p in e.path) or "record"
        raise ToolFailure("UPSTREAM", f"Engine produced an invalid record at {where}: {e.message}")


JUDGMENT_ACTIONS = ("set_judgment", "clear_judgment")


def view(rec: dict[str, Any], role: str) -> dict[str, Any]:
    """Judgment, and the history entries that set it, stay in the general counsel workpaper."""
    if role in ("gc", "admin"):
        return rec
    out = dict(rec)
    out.pop("judgment", None)
    review = out.get("review")
    if review and any(h.get("action") in JUDGMENT_ACTIONS for h in review.get("history") or []):
        out["review"] = dict(review, history=[h for h in review["history"] if h.get("action") not in JUDGMENT_ACTIONS])
    return out


def evidence_hash(rec: dict[str, Any]) -> str:
    return "sha256:" + canonical_hash(rec.get("evidence") or [])


REVIEWER_FIELDS = ("verdict_or_action", "illustrative_rewrite")
_IDENTITY_KEYS = ("source", "quote", "url", "source_id", "source_class", "stance")


def _evidence_identity(rec: dict[str, Any]) -> str:
    """Evidence fingerprint that ignores retrieval timestamps."""
    return canonical_hash([{k: e.get(k) for k in _IDENTITY_KEYS} for e in rec.get("evidence") or []])


def carry_review(new: dict[str, Any], old: Optional[dict[str, Any]]) -> dict[str, Any]:
    """Re-assessment of a finding already in the workpaper keeps the reviewer's work.

    Review history, judgment, reviewer severity and fields a reviewer changed
    survive; the engine's evidence is refreshed, and a ``reassessed`` entry is
    appended when the evidence changed.
    """
    if not old:
        return new
    review = old.get("review") or {}
    applied: set[str] = set()
    for entry in review.get("history") or []:
        if entry.get("action") in ("accept", "edit"):
            applied.update((entry.get("changes") or {}).keys())
    for field in REVIEWER_FIELDS:
        if field in applied and field in old:
            new[field] = old[field]
    if (old.get("severity") or {}).get("basis") == "reviewer":
        new["severity"] = old["severity"]
    if "judgment" in old:
        new["judgment"] = old["judgment"]
    review = {**review, "history": list(review.get("history") or [])}
    if _evidence_identity(new) != _evidence_identity(old) and review.get("history"):
        review["history"].append(
            {"action": "reassessed", "label": "Re-assessed by engine", "by": "engine", "role": "engine",
             "at": now_iso(), "evidence_hash": evidence_hash(new)}
        )
        review["version"] = int(review.get("version", 1)) + 1
    new["review"] = review or new["review"]
    validate_record(new)
    return new
