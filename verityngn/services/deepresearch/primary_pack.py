"""Domain-class primary source packs for Deep Research / CSE bias.

Inject packs ONLY when claim text matches the class — never always-on Oregon URLs.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence, Tuple

_BILL_RE = re.compile(r"\b((?:SB|HB)\s*\d{2,5})\b", re.IGNORECASE)
_ORS_RE = re.compile(r"\bORS\s*\d+", re.IGNORECASE)
_OR_HINT = re.compile(
    r"\bOregon\b|\bOLIS\b|\bLegislative Revenue Office\b|\bLRO\b", re.IGNORECASE
)
_MED_RE = re.compile(
    r"\b(?:FDA|NIH|CDC|clinical trial|supplement|weight loss|dosage|mg\b|vaccine|"
    r"pharmaceutical|physician|Dr\.)\b",
    re.IGNORECASE,
)
_FIN_RE = re.compile(
    r"\b(?:SEC|EDGAR|earnings|revenue|EPS|GAAP|stock|QSBS|capital gain|"
    r"Federal Reserve|10-[KQ]|IPO)\b",
    re.IGNORECASE,
)

DomainClass = str  # legislative_us_state | medical_health | finance_markets | creator_ugc | none


def _claim_blob(report: Dict[str, Any]) -> str:
    parts: List[str] = []
    for c in report.get("claims_breakdown") or []:
        if isinstance(c, dict):
            parts.append(str(c.get("claim_text") or ""))
    qs = report.get("quick_summary")
    if isinstance(qs, dict):
        parts.append(str(qs.get("title") or ""))
    elif isinstance(qs, str):
        parts.append(qs)
    return " ".join(parts)


def detect_domain_classes(text: str) -> List[DomainClass]:
    """Return matching domain classes (may be empty)."""
    t = text or ""
    classes: List[DomainClass] = []
    if _BILL_RE.search(t) or _ORS_RE.search(t) or _OR_HINT.search(t):
        classes.append("legislative_us_state")
    if _MED_RE.search(t):
        classes.append("medical_health")
    if _FIN_RE.search(t):
        classes.append("finance_markets")
    # Creator/UGC is a soft class when nothing else matches but speaker/channel language appears
    if not classes and re.search(r"\b(?:influencer|affiliate|YouTube|channel|creator)\b", t, re.I):
        classes.append("creator_ugc")
    return classes


def extract_bill_ids(text: str) -> List[str]:
    found: List[str] = []
    seen = set()
    for m in _BILL_RE.finditer(text or ""):
        norm = re.sub(r"\s+", " ", m.group(1).upper())
        norm = re.sub(r"(SB|HB)\s*(\d+)", r"\1 \2", norm)
        if norm not in seen:
            seen.add(norm)
            found.append(norm)
    return found


def _oregon_legislative_pack(text: str) -> List[Dict[str, str]]:
    """Oregon-specific pack — only when Oregon / ORS / OLIS / SB|HB with Oregon hints."""
    if not (_OR_HINT.search(text) or _ORS_RE.search(text)):
        # Bare SB/HB without Oregon context → generic .gov / Ballotpedia only
        bills = extract_bill_ids(text)
        pack: List[Dict[str, str]] = [
            {
                "title": "Ballotpedia — state legislation search",
                "url": "https://ballotpedia.org/",
                "source_type": "encyclopedia",
            }
        ]
        for bill in bills[:2]:
            pack.append(
                {
                    "title": f"{bill} — Ballotpedia / state bill lookup",
                    "url": f"https://ballotpedia.org/wiki/index.php?search={bill.replace(' ', '+')}",
                    "source_type": "encyclopedia",
                }
            )
        return pack

    pack = [
        {
            "title": "Oregon DOR — Summary of Legislation",
            "url": "https://www.oregon.gov/dor/pages/2026-summary-of-legislation.aspx",
            "source_type": "agency",
        },
        {
            "title": "policy.yex.ai — Oregon session helper",
            "url": "https://policy.yex.ai/?session=2026R1",
            "source_type": "legislature_tool",
        },
    ]
    for bill in extract_bill_ids(text)[:3]:
        slug = bill.replace(" ", "")
        pack.append(
            {
                "title": f"{bill} — OLIS measure overview",
                "url": f"https://olis.oregonlegislature.gov/liz/2026R1/Measures/Overview/{slug}",
                "source_type": "legislature",
            }
        )
        if slug == "SB1507":
            pack.append(
                {
                    "title": "SB 1507 — LRO Revenue Impact (94494)",
                    "url": "https://olis.oregonlegislature.gov/liz/2026R1/Downloads/MeasureAnalysisDocument/94494",
                    "source_type": "lro",
                }
            )
    return pack


def _medical_pack() -> List[Dict[str, str]]:
    return [
        {"title": "FDA", "url": "https://www.fda.gov/", "source_type": "agency"},
        {"title": "NIH / PubMed", "url": "https://pubmed.ncbi.nlm.nih.gov/", "source_type": "agency"},
        {"title": "CDC", "url": "https://www.cdc.gov/", "source_type": "agency"},
        {"title": "Cochrane Library", "url": "https://www.cochranelibrary.com/", "source_type": "scientific"},
    ]


def _finance_pack() -> List[Dict[str, str]]:
    return [
        {"title": "SEC EDGAR", "url": "https://www.sec.gov/edgar", "source_type": "agency"},
        {"title": "Federal Reserve", "url": "https://www.federalreserve.gov/", "source_type": "agency"},
        {"title": "Investor.gov", "url": "https://www.investor.gov/", "source_type": "agency"},
    ]


def _creator_ugc_pack() -> List[Dict[str, str]]:
    return [
        {"title": "FactCheck.org", "url": "https://www.factcheck.org/", "source_type": "fact_check"},
        {"title": "Snopes", "url": "https://www.snopes.com/", "source_type": "fact_check"},
        {"title": "PolitiFact", "url": "https://www.politifact.com/", "source_type": "fact_check"},
    ]


def build_primary_pack(report: Dict[str, Any]) -> Tuple[List[Dict[str, str]], List[DomainClass]]:
    """Build domain-appropriate primary pack; empty if no class matches."""
    text = _claim_blob(report)
    classes = detect_domain_classes(text)
    pack: List[Dict[str, str]] = []
    seen_urls = set()

    def _extend(items: Sequence[Dict[str, str]]) -> None:
        for it in items:
            u = it.get("url") or ""
            if u and u not in seen_urls:
                seen_urls.add(u)
                pack.append(dict(it))

    for cls in classes:
        if cls == "legislative_us_state":
            _extend(_oregon_legislative_pack(text))
        elif cls == "medical_health":
            _extend(_medical_pack())
        elif cls == "finance_markets":
            _extend(_finance_pack())
        elif cls == "creator_ugc":
            _extend(_creator_ugc_pack())
    return pack, classes


def primary_hosts_for_cse(classes: Sequence[DomainClass], text: str = "") -> str:
    """Comma-separated as_sitesearch hosts for CSE, or empty."""
    hosts: List[str] = []
    if "legislative_us_state" in classes:
        if _OR_HINT.search(text or "") or _ORS_RE.search(text or ""):
            hosts.extend(
                [
                    "olis.oregonlegislature.gov",
                    "oregonlegislature.gov",
                    "oregon.gov",
                    "ballotpedia.org",
                ]
            )
        else:
            hosts.extend(["ballotpedia.org", "congress.gov"])
    if "medical_health" in classes:
        hosts.extend(["nih.gov", "fda.gov", "cdc.gov", "cochranelibrary.com"])
    if "finance_markets" in classes:
        hosts.extend(["sec.gov", "federalreserve.gov", "investor.gov"])
    if "creator_ugc" in classes:
        hosts.extend(["factcheck.org", "snopes.com", "politifact.com"])
    # dedupe preserve order
    out: List[str] = []
    seen = set()
    for h in hosts:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return ",".join(out)


def inject_primary_pack(sanitized: Dict[str, Any]) -> Dict[str, Any]:
    """Attach primary_pack / primary_urls only when domain classes match."""
    pack, classes = build_primary_pack(sanitized)
    sanitized["domain_classes"] = list(classes)
    if pack:
        sanitized["primary_pack"] = pack
        sanitized["primary_urls"] = [p["url"] for p in pack if p.get("url")]
        # Back-compat aliases for older binder / A-B scripts
        sanitized["legislature_primary_pack"] = pack
        sanitized["legislature_primary_urls"] = list(sanitized["primary_urls"])
    else:
        sanitized.pop("primary_pack", None)
        sanitized.pop("primary_urls", None)
        sanitized.pop("legislature_primary_pack", None)
        sanitized.pop("legislature_primary_urls", None)
    return sanitized


# Back-compat wrappers used by older imports
def inject_legislature_primaries(sanitized: Dict[str, Any]) -> Dict[str, Any]:
    return inject_primary_pack(sanitized)


def build_legislature_primary_pack(report: Dict[str, Any]) -> List[Dict[str, str]]:
    pack, _ = build_primary_pack(report)
    return pack
