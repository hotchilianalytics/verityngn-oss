"""Disclosure engine interface (rfkit lives behind it).

``assess_selection`` and ``assess_document`` hand the engine a range of
normalized text and get findings back. The open-source server ships no
disclosure matcher of its own: it loads one from ``SPLITRISK_DISCLOSURE_ENGINE``
(``package.module:factory``) or from the ``verityngn.disclosure_engines`` entry
point group, and otherwise reports ``ENGINE_NOT_INSTALLED``.

Finding contract (one dict per finding; offsets are into ``request.text``):

``claim_text``, ``start``, ``end`` (required; must lie inside the request range),
``claim_kind``, ``verdict_or_action``, ``category``, ``item_1a_heading``,
``confidence`` (evidence confidence, never likelihood), ``illustrative_rewrite``,
``junior_obvious`` ``{flag, reason}``, ``lag_clock`` ``{event_date, filing_date, days}``,
``allegation``, ``evidence`` (list of EvidenceItem-shaped dicts with
``source_class`` and ``stance``), and provenance keys ``engine_version``,
``engine_commit``, ``model``.

With ``prior_doc_id`` (last year's 10-K, or the previous version of a
registration statement such as DRS/A or S-1 against S-1/A) the request also
carries ``prior_text``, ``prior_outline`` and ``section_pairs``: one entry per
outline key with the ``current`` and ``prior`` spans (either may be null when
a section was added or removed), so the engine can compare like with like.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

from verityngn.agent.mcp_v2.errors import EngineNotInstalled

ENTRY_POINT_GROUP = "verityngn.disclosure_engines"
ENV = "SPLITRISK_DISCLOSURE_ENGINE"


@dataclass
class AssessRequest:
    text: str
    start: int
    end: int
    context_chars: int
    domain_pack: str
    scope: str
    outline: list[dict[str, Any]] = field(default_factory=list)
    entity: Optional[dict[str, Any]] = None
    prior_text: Optional[str] = None
    prior_outline: list[dict[str, Any]] = field(default_factory=list)
    section_pairs: list[dict[str, Any]] = field(default_factory=list)


class DisclosureEngine(Protocol):
    name: str
    version: str

    def assess(self, request: AssessRequest, progress: Callable[[str], None]) -> list[dict[str, Any]]: ...


class UnavailableDisclosureEngine:
    name = "rfkit"
    version = ""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def assess(self, request: AssessRequest, progress: Callable[[str], None]) -> list[dict[str, Any]]:
        raise EngineNotInstalled(
            "rfkit",
            self.reason,
            alternative="Use verify_quote to check specific quotes against the issuer's filings, or filings_search "
            "and get_filing_section to open the issuer's own record; disclosure assessment needs the rfkit engine.",
        )


def _load(spec: str) -> DisclosureEngine:
    module, _, attr = spec.partition(":")
    factory = getattr(importlib.import_module(module), attr or "engine")
    return factory()


def load_disclosure_engine() -> DisclosureEngine:
    spec = os.environ.get(ENV, "").strip()
    if spec:
        try:
            return _load(spec)
        except Exception as exc:  # noqa: BLE001
            return UnavailableDisclosureEngine(f"{ENV}={spec} could not be loaded: {type(exc).__name__}: {exc}")
    try:
        from importlib.metadata import entry_points

        eps = list(entry_points(group=ENTRY_POINT_GROUP))
    except Exception:  # noqa: BLE001
        eps = []
    if eps:
        try:
            return eps[0].load()()
        except Exception as exc:  # noqa: BLE001
            return UnavailableDisclosureEngine(f"Disclosure engine entry point {eps[0].name} failed to load: {exc}")
    if importlib.util.find_spec("rfkit") is not None:
        return UnavailableDisclosureEngine(
            "rfkit is installed but registers no verityngn.disclosure_engines entry point, so it cannot be called yet."
        )
    return UnavailableDisclosureEngine("The rfkit disclosure engine is not installed on this server.")
