"""SEC EDGAR adapter: entity lookup, filing lists, full-text search, documents.

Uses the public submissions index, EDGAR full-text search and the archives.
Every call sends the declared User-Agent and stays under 10 requests a second.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

from verityngn.agent.mcp_v2.adapters.http import RateLimiter, request, request_json
from verityngn.agent.mcp_v2.documents import user_agent
from verityngn.agent.mcp_v2.errors import ToolFailure

STAFF_FORMS = {"UPLOAD", "CORRESP"}
MAX_DOCUMENT_BYTES = 60 * 1024 * 1024
_LIMIT = RateLimiter(per_second=8)
_CACHE = Path.home() / ".cache" / "verityngn" / "company_tickers.json"


def form_matches(form: str, wanted: list[str]) -> bool:
    """A requested base form also matches its amendments; a requested /A form matches only amendments."""
    return form in wanted or form.removesuffix("/A") in wanted


def entity_id_for_cik(cik: str | int) -> str:
    return f"sr:ent:cik{int(cik):010d}"


def cik_from_entity_id(entity_id: str) -> Optional[str]:
    tail = entity_id.rsplit(":", 1)[-1]
    if tail.startswith("cik") and tail[3:].isdigit():
        return str(int(tail[3:]))
    return None


def accession_url(cik: str, accession: str, document: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{document}"


class EdgarClient:
    provider = "SEC EDGAR"

    def _get_json(self, url: str) -> Any:
        _LIMIT.wait()
        return request_json(url, headers={"User-Agent": user_agent()}, provider=self.provider)

    def get_bytes(self, url: str) -> bytes:
        _LIMIT.wait()
        data = request(url, headers={"User-Agent": user_agent(), "Accept": "*/*"}, provider=self.provider)
        if len(data) > MAX_DOCUMENT_BYTES:
            raise ToolFailure("INVALID", f"The filing document is larger than {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB.")
        return data

    def company_tickers(self) -> list[dict[str, Any]]:
        from verityngn.services.text_risk.edgar import company_tickers

        fresh = _CACHE.exists() and (time.time() - _CACHE.stat().st_mtime) < 86400
        if not fresh and _CACHE.exists():
            _CACHE.unlink()
        _LIMIT.wait()
        rows = company_tickers(cache=_CACHE)
        if not rows:
            raise ToolFailure("UPSTREAM", "SEC company ticker list is unavailable right now.")
        return list(rows.values())

    def submissions(self, cik: str) -> dict[str, Any]:
        return self._get_json(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")

    def resolve(self, *, name: str = "", ticker: str = "", cik: str = "", limit: int = 5) -> list[dict[str, Any]]:
        rows = self.company_tickers()
        hits: list[dict[str, Any]] = []
        if cik:
            hits = [r for r in rows if int(r.get("cik_str", 0)) == int(cik)]
        elif ticker:
            hits = [r for r in rows if str(r.get("ticker", "")).upper() == ticker.strip().upper()]
        elif name:
            needle = name.strip().lower()
            exact = [r for r in rows if str(r.get("title", "")).lower() == needle]
            starts = [r for r in rows if str(r.get("title", "")).lower().startswith(needle) and r not in exact]
            contains = [r for r in rows if needle in str(r.get("title", "")).lower() and r not in exact and r not in starts]
            hits = exact + starts + contains
        by_cik: dict[int, dict[str, Any]] = {}
        for r in hits:
            c = int(r["cik_str"])
            entry = by_cik.setdefault(c, {"cik": str(c), "name": r.get("title", ""), "tickers": []})
            if r.get("ticker") and r["ticker"] not in entry["tickers"]:
                entry["tickers"].append(r["ticker"])
        if not by_cik and cik:
            return [self._registrant(cik)]
        if not by_cik and name:
            return self._registrants_named(name, limit)
        return list(by_cik.values())[:limit]

    def _registrant(self, cik: str) -> dict[str, Any]:
        """Registrants without a ticker (for example before an IPO) are not in the ticker list."""
        data = self.submissions(cik)
        return {"cik": str(int(cik)), "name": str(data.get("name") or ""), "tickers": list(data.get("tickers") or [])}

    def _registrants_named(self, name: str, limit: int) -> list[dict[str, Any]]:
        """EDGAR's company-name lookup: autocomplete for exact names, then the company feed for each CIK."""
        data = self._get_json("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode({"keysTyped": name}))
        names = [str((h.get("_source") or {}).get("entity") or "") for h in (data.get("hits") or {}).get("hits") or []]
        out: list[dict[str, Any]] = []
        for entity in [n for n in names if n][: min(limit, 3)]:
            feed = self.get_bytes(
                "https://www.sec.gov/cgi-bin/browse-edgar?"
                + urllib.parse.urlencode({"company": entity, "action": "getcompany", "type": "", "owner": "include", "count": 1, "output": "atom"})
            ).decode("latin-1", errors="replace")
            head = feed.split("<entry", 1)[0]
            cik_m = re.search(r"<cik>(\d+)</cik>", head)
            name_m = re.search(r"<conformed-name>([^<]+)</conformed-name>", head)
            if cik_m and not any(o["cik"] == str(int(cik_m.group(1))) for o in out):
                out.append({"cik": str(int(cik_m.group(1))), "name": html.unescape(name_m.group(1)) if name_m else entity, "tickers": []})
        return out

    def _recent_rows(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        recent = (data.get("filings") or {}).get("recent") or {}
        keys = ("accessionNumber", "filingDate", "form", "primaryDocument", "items")
        n = len(recent.get("accessionNumber") or [])
        return [{k: (recent.get(k) or [""] * n)[i] for k in keys} for i in range(n)]

    def filings(self, cik: str, forms: list[str], start: dt.date, end: dt.date, items: Optional[list[str]] = None) -> list[dict[str, Any]]:
        data = self.submissions(cik)
        rows = self._recent_rows(data)
        oldest = min((r["filingDate"] for r in rows if r["filingDate"]), default="9999")
        if start.isoformat() < oldest:
            for f in (data.get("filings") or {}).get("files") or []:
                if f.get("filingTo", "") >= start.isoformat() and f.get("filingFrom", "9999") <= end.isoformat():
                    extra = self._get_json(f"https://data.sec.gov/submissions/{f['name']}")
                    rows.extend(self._recent_rows({"filings": {"recent": extra}}))
        out = []
        for r in rows:
            base_form = r["form"].removesuffix("/A")
            if not form_matches(r["form"], forms):
                continue
            if not (start.isoformat() <= r["filingDate"] <= end.isoformat()):
                continue
            row_items = [i for i in (r.get("items") or "").split(",") if i]
            if items and not set(items) & set(row_items):
                continue
            out.append(
                {
                    "accession": r["accessionNumber"],
                    "form": r["form"],
                    "items": row_items,
                    "filed_at": r["filingDate"],
                    "url": accession_url(cik, r["accessionNumber"], r["primaryDocument"]),
                    "source_class": "staff" if base_form in STAFF_FORMS else "own",
                }
            )
        out.sort(key=lambda f: f["filed_at"], reverse=True)
        return out

    def full_text(self, cik: str, query: str, forms: list[str], start: dt.date, end: dt.date, items: Optional[list[str]] = None) -> list[dict[str, Any]]:
        params = {
            "q": f'"{query}"' if " " in query and not query.startswith('"') else query,
            "ciks": f"{int(cik):010d}",
            "forms": ",".join(sorted({f.removesuffix("/A") for f in forms})),
            "dateRange": "custom",
            "startdt": start.isoformat(),
            "enddt": end.isoformat(),
        }
        data = self._get_json("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode(params))
        seen: dict[str, dict[str, Any]] = {}
        for hit in (data.get("hits") or {}).get("hits") or []:
            src = hit.get("_source") or {}
            accession = src.get("adsh") or hit.get("_id", "").split(":", 1)[0]
            document = hit.get("_id", "").split(":", 1)[-1]
            row_items = list(src.get("items") or [])
            if items and not set(items) & set(row_items):
                continue
            if accession in seen:
                continue
            base_form = str(src.get("form", "")).removesuffix("/A")
            if not form_matches(str(src.get("form", "")), forms):
                continue
            seen[accession] = {
                "accession": accession,
                "form": src.get("form", ""),
                "items": row_items,
                "filed_at": src.get("file_date", ""),
                "url": accession_url(cik, accession, document),
                "source_class": "staff" if base_form in STAFF_FORMS else "own",
            }
        return sorted(seen.values(), key=lambda f: f["filed_at"], reverse=True)

    def issuer_cik(self, accession: str) -> str:
        """The registrant's CIK for an accession.

        An accession number's prefix is whoever transmitted the filing, often a
        filing agent (for example 0001193125), so it is only trusted when that
        CIK's own submissions list the accession.
        """
        data = self._get_json("https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode({"q": f'"{accession}"'}))
        ciks = sorted(
            {
                str(int(c))
                for hit in (data.get("hits") or {}).get("hits") or []
                if (hit.get("_source") or {}).get("adsh") == accession
                for c in (hit.get("_source") or {}).get("ciks") or []
                if str(c).isdigit()
            },
            key=int,
        )
        if len(ciks) == 1:
            return ciks[0]
        if len(ciks) > 1:
            raise ToolFailure(
                "INVALID",
                f"Accession {accession} was filed for several registrants.",
                alternative=f"Repeat the call with cik set to one of: {', '.join(ciks)}.",
                details={"ciks": ciks},
            )
        prefix = str(int(accession.split("-", 1)[0]))
        try:
            if any(r["accessionNumber"] == accession for r in self._recent_rows(self.submissions(prefix))):
                return prefix
        except ToolFailure:
            pass
        raise ToolFailure(
            "NOT_FOUND",
            f"Could not determine which registrant filed {accession}; its prefix is the filing agent.",
            alternative="Repeat the call with cik, taken from resolve_entity or filings_search.",
        )

    def filing_document(self, cik: str, accession: str) -> tuple[str, dict[str, Any]]:
        """Return the primary document URL and the submissions row for one accession."""
        data = self.submissions(cik)
        for row in self._recent_rows(data):
            if row["accessionNumber"] == accession:
                return accession_url(cik, accession, row["primaryDocument"]), row
        index = self._get_json(
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/index.json"
        )
        files = [i.get("name", "") for i in (index.get("directory") or {}).get("item") or []]
        docs = [f for f in files if f.lower().endswith((".htm", ".html")) and "index" not in f.lower()]
        if not docs:
            raise ToolFailure("NOT_FOUND", f"No primary document found for accession {accession}.")
        return accession_url(cik, accession, docs[0]), {"accessionNumber": accession, "form": "", "filingDate": ""}

    def last_10k(self, cik: str) -> Optional[dt.date]:
        data = self.submissions(cik)
        dates = [r["filingDate"] for r in self._recent_rows(data) if r["form"] in ("10-K", "10-K/A", "20-F")]
        return dt.date.fromisoformat(max(dates)) if dates else None

    def aliases(self, cik: str) -> list[str]:
        try:
            data = self.submissions(cik)
        except ToolFailure:
            return []
        return [str(f.get("name")) for f in data.get("formerNames") or [] if f.get("name")]
