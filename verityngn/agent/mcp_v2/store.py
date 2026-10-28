"""Tenant-scoped handle store.

Every handle embeds its tenant (``sr:doc:<tenant>/...``). Reads with another
tenant's principal raise the same ``NotFound`` as a missing handle, so a probe
learns nothing. ``MemoryStore`` is the open-source default; the hosted service
swaps in Postgres with row-level security behind the same interface.
"""

from __future__ import annotations

import datetime as dt
import secrets
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

from verityngn.agent.mcp_v2.errors import NotFound


def new_token(nbytes: int = 12) -> str:
    return secrets.token_urlsafe(nbytes).replace("-", "_")


def handle_tenant(handle: str) -> str:
    try:
        rest = handle.split(":", 2)[2]
    except IndexError:
        return ""
    return rest.split("/", 1)[0]


@dataclass
class Document:
    doc_id: str
    tenant: str
    text: str
    source_hash: str
    media_type: str
    normalizer: str
    outline: list[dict[str, Any]]
    title: str = ""
    url: Optional[str] = None
    rights: str = ""
    cues: list[dict[str, Any]] = field(default_factory=list)
    video_id: Optional[str] = None
    registered_at: str = ""


@dataclass
class Report:
    report_id: str
    tenant: str
    kind: str
    status: str = "running"
    status_message: str = ""
    record_ids: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    error: Optional[dict[str, Any]] = None
    created_at: str = ""


@dataclass
class Export:
    export_id: str
    tenant: str
    media_type: str
    data: bytes
    expires_at: dt.datetime


class MemoryStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.docs: dict[str, Document] = {}
        self.url_index: dict[tuple[str, str], str] = {}
        self.records: dict[str, dict[str, Any]] = {}
        self.reports: dict[str, Report] = {}
        self.exports: dict[str, Export] = {}
        self.entities: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _own(handle: str, tenant: str) -> None:
        if handle_tenant(handle) != tenant:
            raise NotFound(handle)

    def put_document(self, doc: Document) -> Document:
        with self._lock:
            existing = self.docs.get(doc.doc_id)
            if existing:
                return existing
            self.docs[doc.doc_id] = doc
            if doc.url:
                self.url_index[(doc.tenant, doc.url)] = doc.doc_id
            return doc

    def get_document(self, doc_id: str, tenant: str) -> Document:
        self._own(doc_id, tenant)
        with self._lock:
            doc = self.docs.get(doc_id)
        if doc is None:
            raise NotFound(doc_id)
        return doc

    def document_for_url(self, url: str, tenant: str) -> Optional[Document]:
        with self._lock:
            doc_id = self.url_index.get((tenant, url))
            return self.docs.get(doc_id) if doc_id else None

    def put_record(self, record: dict[str, Any]) -> None:
        with self._lock:
            self.records[record["claim_id"]] = record

    def get_record(self, record_id: str, tenant: str) -> dict[str, Any]:
        self._own(record_id, tenant)
        with self._lock:
            rec = self.records.get(record_id)
        if rec is None:
            raise NotFound(record_id)
        return rec

    def new_report(self, tenant: str, kind: str) -> Report:
        rep = Report(
            report_id=f"sr:rep:{tenant}/{new_token()}",
            tenant=tenant,
            kind=kind,
            created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        with self._lock:
            self.reports[rep.report_id] = rep
        return rep

    def get_report(self, report_id: str, tenant: str) -> Report:
        self._own(report_id, tenant)
        with self._lock:
            rep = self.reports.get(report_id)
        if rep is None:
            raise NotFound(report_id)
        return rep

    def add_report_record(self, report: Report, record: dict[str, Any]) -> None:
        with self._lock:
            self.records[record["claim_id"]] = record
            report.record_ids.append(record["claim_id"])

    def put_export(self, tenant: str, media_type: str, data: bytes, ttl_hours: int = 24) -> Export:
        exp = Export(
            export_id=new_token(16),
            tenant=tenant,
            media_type=media_type,
            data=data,
            expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=ttl_hours),
        )
        with self._lock:
            self.exports[exp.export_id] = exp
        return exp

    def get_export(self, export_id: str, tenant: str) -> Export:
        with self._lock:
            exp = self.exports.get(export_id)
        if exp is None or exp.tenant != tenant or exp.expires_at < dt.datetime.now(dt.timezone.utc):
            raise NotFound(f"splitrisk://exports/{export_id}")
        return exp

    def remember_entity(self, entity: dict[str, Any]) -> None:
        with self._lock:
            self.entities[entity["entity_id"]] = entity

    def entity(self, entity_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            return self.entities.get(entity_id)
