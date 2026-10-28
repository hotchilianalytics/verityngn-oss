"""Tool handlers for verityngn-mcp v2."""

from __future__ import annotations

import datetime as dt
import difflib
import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Callable, Optional

from verityngn.agent.mcp_v2 import anchors, coverage, documents, exports, locks
from verityngn.agent.mcp_v2.adapters import Adapters
from verityngn.agent.mcp_v2.adapters.disclosure import AssessRequest
from verityngn.agent.mcp_v2.adapters.edgar import cik_from_entity_id, entity_id_for_cik
from verityngn.agent.mcp_v2.adapters.sanctions import LABEL as SANCTIONS_LABEL
from verityngn.agent.mcp_v2.audit import AuditLog
from verityngn.agent.mcp_v2.auth import Principal
from verityngn.agent.mcp_v2.config import ServerConfig
from verityngn.agent.mcp_v2.contracts import published_tool
from verityngn.agent.mcp_v2.errors import NotFound, ToolFailure
from verityngn.agent.mcp_v2.records import build_record, evidence_hash, now_iso, sha256_text, view
from verityngn.agent.mcp_v2.schema_defs import JUDGMENT_LABEL
from verityngn.agent.mcp_v2.store import Document, MemoryStore, Report
from verityngn.agent.mcp_v2.tasks import Cancelled, TaskContext, TaskManager

VIDEO_URN = anchors.VIDEO_SOURCE


@dataclass
class CallContext:
    principal: Principal
    tasks_ok: bool


def ok(structured: Any, summary: str) -> dict[str, Any]:
    return {
        "resultType": "complete",
        "content": [
            {"type": "text", "text": summary},
            {"type": "text", "text": json.dumps(structured, sort_keys=True)},
        ],
        "structuredContent": structured,
    }


def tool_error(failure: ToolFailure) -> dict[str, Any]:
    text = f"{failure.code}: {failure.message}"
    if failure.alternative:
        text += f" Instead: {failure.alternative}"
    return {
        "resultType": "complete",
        "isError": True,
        "content": [{"type": "text", "text": text}],
        "structuredContent": failure.to_dict(),
    }


@lru_cache(maxsize=None)
def _validator(name: str, which: str) -> Any:
    from jsonschema import Draft202012Validator, FormatChecker

    return Draft202012Validator(published_tool(name)[which], format_checker=FormatChecker())


def validate_input(name: str, arguments: dict[str, Any]) -> None:
    from jsonschema.exceptions import best_match

    err = best_match(_validator(name, "inputSchema").iter_errors(arguments))
    if err is not None:
        where = "/".join(str(p) for p in err.absolute_path) or "arguments"
        raise ToolFailure("INVALID", f"Invalid {where}: {err.message}")


def output_errors(name: str, structured: Any) -> list[str]:
    return [e.message for e in _validator(name, "outputSchema").iter_errors(structured)]


def _plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


class ToolRunner:
    def __init__(
        self,
        *,
        store: MemoryStore,
        adapters: Adapters,
        tasks: TaskManager,
        config: ServerConfig,
        audit: AuditLog,
    ) -> None:
        self.store = store
        self.adapters = adapters
        self.tasks = tasks
        self.config = config
        self.audit = audit
        self._handlers: dict[str, Callable[[dict[str, Any], CallContext], dict[str, Any]]] = {
            "register_document": self.register_document,
            "assess_selection": self.assess_selection,
            "assess_document": self.assess_document,
            "verify_quote": self.verify_quote,
            "resolve_entity": self.resolve_entity,
            "list_company_videos": self.list_company_videos,
            "analyze_video": self.analyze_video,
            "news_window": self.news_window,
            "filings_search": self.filings_search,
            "get_filing_section": self.get_filing_section,
            "sanctions_match": self.sanctions_match,
            "search_litigation": self.search_litigation,
            "compose_assessment": self.compose_assessment,
            "record_review_action": self.record_review_action,
            "get_record": self.get_record,
            "get_report": self.get_report,
            "export_assessment": self.export_assessment,
        }

    # ------------------------------------------------------------------ entry

    def call(self, name: str, arguments: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        record_ids: list[str] = []
        try:
            locks.reject_schedule_arguments(arguments)
            validate_input(name, arguments)
            result = self._handlers[name](arguments, ctx)
            sc = result.get("structuredContent")
            if isinstance(sc, dict):
                record_ids = [r["claim_id"] for r in sc.get("records") or [] if isinstance(r, dict) and "claim_id" in r]
                if "claim_id" in sc:
                    record_ids.append(sc["claim_id"])
            self.audit.write(
                principal=ctx.principal,
                tool=name,
                arguments=arguments,
                record_ids=record_ids,
                outcome="task" if result.get("resultType") == "task" else "ok",
                extra={"rights": arguments["rights"]} if name == "register_document" else None,
            )
            return result
        except ToolFailure as failure:
            self.audit.write(
                principal=ctx.principal, tool=name, arguments=arguments, record_ids=[], outcome="error", error_code=failure.code
            )
            return tool_error(failure)

    # --------------------------------------------------------------- helpers

    def _doc_for_source(self, source: str, principal: Principal) -> Document:
        if source.startswith(VIDEO_URN):
            doc = self.store.document_for_url(source, principal.tenant)
            if doc is None:
                raise NotFound(source)
            return doc
        if source.startswith("sr:doc:"):
            return self.store.get_document(source, principal.tenant)
        doc = self.store.document_for_url(source, principal.tenant)
        if doc is None:
            raise ToolFailure(
                "NOT_FOUND",
                f"{source} is not registered.",
                alternative="Call register_document with this URL first.",
            )
        return doc

    def _entity(self, entity_id: str) -> dict[str, Any]:
        known = self.store.entity(entity_id)
        if known:
            return known
        cik = cik_from_entity_id(entity_id)
        if not cik:
            raise NotFound(entity_id)
        found = self.adapters.edgar.resolve(cik=cik)
        if not found:
            raise NotFound(entity_id)
        ent = {
            "entity_id": entity_id,
            "name": found[0]["name"],
            "cik": cik,
            "tickers": found[0]["tickers"],
            "owned_channels": self.adapters.channels.channels(cik),
        }
        self.store.remember_entity(ent)
        return ent

    @staticmethod
    def _confirm(name: str, args: dict[str, Any], ctx: CallContext, resolved: dict[str, Any]) -> None:
        locks.needs_confirmation(name, ctx.principal.role, args, resolved)

    def _long_job(
        self,
        ctx: CallContext,
        *,
        report: Report,
        poll_ms: int,
        work: Callable[[TaskContext], tuple[dict[str, Any], str]],
        force_task: bool,
    ) -> dict[str, Any]:
        """Run ``work`` as a task, or detached with a report_id for hosts without Tasks."""

        def job(tctx: TaskContext) -> dict[str, Any]:
            try:
                structured, summary = work(tctx)
                report.status = "complete"
                report.status_message = summary
                return ok(structured, summary)
            except Cancelled:
                report.status = "failed"
                report.error = {"code": "INVALID", "message": "Cancelled by the user."}
                raise
            except ToolFailure as failure:
                report.status = "failed"
                report.error = failure.to_dict()
                return tool_error(failure)
            except Exception as exc:  # noqa: BLE001
                report.status = "failed"
                report.error = {"code": "UPSTREAM", "message": f"Engine error: {type(exc).__name__}"}
                return tool_error(ToolFailure("UPSTREAM", f"Engine error: {type(exc).__name__}"))

        if ctx.tasks_ok:
            created = self.tasks.start(ctx.principal.tenant, job, poll_ms=poll_ms)
            created["_meta"] = {"com.verityindex.splitrisk/report_id": report.report_id}
            return created
        if not force_task:
            return job(TaskContext(None))
        self.tasks.run_detached(job)
        pending = {"report_id": report.report_id, "status": "running"}
        return ok(
            pending,
            f"Started. This takes a few minutes; call get_report with report_id {report.report_id} to read the results.",
        )

    # ------------------------------------------------------------ documents

    def register_document(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        tenant = ctx.principal.tenant
        if args.get("upload_ref"):
            raise ToolFailure(
                "ENGINE_NOT_INSTALLED",
                "upload_ref needs the hosted SplitRisk object store, which this server does not have.",
                alternative="Pass the document's text, or a public URL.",
                details={"engine": "splitrisk-object-store"},
            )
        if args.get("url"):
            existing = self.store.document_for_url(args["url"], tenant)
            if existing:
                doc = existing
            else:
                data, _ctype = documents.fetch_url(args["url"])
                doc = documents.register(
                    self.store, tenant=tenant, media_type=args["media_type"], rights=args["rights"],
                    data=data, url=args["url"], title=args.get("title", ""),
                )
        else:
            doc = documents.register(
                self.store, tenant=tenant, media_type=args["media_type"], rights=args["rights"],
                text=args["text"], title=args.get("title", ""),
            )
        out = {
            "doc_id": doc.doc_id,
            "source_hash": doc.source_hash,
            "normalizer": doc.normalizer,
            "length": len(doc.text),
            "outline": doc.outline,
        }
        items = ", ".join(e["item"] for e in doc.outline) or "none"
        return ok(out, f"Registered {doc.doc_id} ({len(doc.text):,} characters; SEC Items found: {items}).")

    # ------------------------------------------------------------ assessment

    def _assess(
        self,
        tctx: TaskContext,
        *,
        report: Report,
        doc: Document,
        start: int,
        end: int,
        scope: str,
        domain_pack: str,
        context_chars: int,
        entity: Optional[dict[str, Any]],
        prior: Optional[Document],
        tool: str,
    ) -> list[dict[str, Any]]:
        engine = self.adapters.disclosure
        request = AssessRequest(
            text=doc.text,
            start=start,
            end=end,
            context_chars=context_chars,
            domain_pack=domain_pack,
            scope=scope,
            outline=doc.outline,
            entity=entity,
            prior_text=prior.text if prior else None,
        )
        def progress(msg: str) -> None:
            tctx.check()
            tctx.progress(msg)

        progress("assessing")
        findings = engine.assess(request, progress)
        records = []
        for i, f in enumerate(findings):
            tctx.check()
            fs, fe = int(f.get("start", -1)), int(f.get("end", -1))
            if not (start <= fs < fe <= end):
                continue
            rec = build_record(
                f,
                tenant=doc.tenant,
                domain_pack=domain_pack,
                tool=tool,
                engine="rfkit",
                engine_version=getattr(engine, "version", ""),
                source_lane="disclosure",
                doc_id=doc.doc_id,
                target=anchors.span_target(doc, fs, fe, status="exact"),
                entity_id=(entity or {}).get("entity_id"),
            )
            self.store.add_report_record(report, rec)
            records.append(rec)
            tctx.progress(f"{i + 1} of {len(findings)} done", records_ready=len(report.record_ids))
        return records

    def assess_selection(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        target = args["target"]
        doc = self._doc_for_source(target["source"], ctx.principal)
        res = anchors.resolve_input(target, doc)
        echoed = anchors.echo_target(target, doc, res)
        entity = self._entity(args["entity_id"]) if args.get("entity_id") else None
        report = self.store.new_report(ctx.principal.tenant, "selection")
        role = ctx.principal.role

        def work(tctx: TaskContext) -> tuple[dict[str, Any], str]:
            records = self._assess(
                tctx, report=report, doc=doc, start=res.start, end=res.end, scope=target["scope"],
                domain_pack=args["domain_pack"], context_chars=args.get("context_chars", 1200),
                entity=entity, prior=None, tool="assess_selection",
            )
            out = {"target": echoed, "records": [view(r, role) for r in records], "report_id": report.report_id}
            return out, f"{_plural(len(records), 'finding')} in the selection (anchor {res.status})."

        large = (res.end - res.start) > self.config.large_section_chars
        return self._long_job(
            ctx, report=report, poll_ms=self.config.document_poll_ms, work=work, force_task=False
        ) if large else self._direct(report, work)

    def _direct(self, report: Report, work: Callable[[TaskContext], tuple[dict[str, Any], str]]) -> dict[str, Any]:
        try:
            structured, summary = work(TaskContext(None))
        except ToolFailure as failure:
            report.status = "failed"
            report.error = failure.to_dict()
            raise
        report.status = "complete"
        return ok(structured, summary)

    def assess_document(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        doc = self.store.get_document(args["doc_id"], ctx.principal.tenant)
        prior = self.store.get_document(args["prior_doc_id"], ctx.principal.tenant) if args.get("prior_doc_id") else None
        entity = self._entity(args["entity_id"]) if args.get("entity_id") else None
        report = self.store.new_report(ctx.principal.tenant, "document")
        role = ctx.principal.role

        def work(tctx: TaskContext) -> tuple[dict[str, Any], str]:
            records = self._assess(
                tctx, report=report, doc=doc, start=0, end=len(doc.text), scope="document",
                domain_pack=args["domain_pack"], context_chars=0, entity=entity, prior=prior, tool="assess_document",
            )
            cov = coverage.compose(records)
            report.extra["coverage"] = cov
            out = {"report_id": report.report_id, "records": [view(r, role) for r in records], "coverage": cov}
            return out, f"{_plural(len(records), 'finding')} across {_plural(len(cov['rows']), 'heading')}."

        return self._long_job(ctx, report=report, poll_ms=self.config.document_poll_ms, work=work, force_task=True)

    # ---------------------------------------------------------- verify_quote

    def verify_quote(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        source = args["source"]
        if source.startswith("sr:doc:"):
            doc = self.store.get_document(source, ctx.principal.tenant)
        else:
            doc = self.store.document_for_url(source, ctx.principal.tenant)
            if doc is None:
                data, ctype = documents.fetch_url(source)
                media = "text/html" if "html" in ctype or source.lower().endswith((".htm", ".html")) else "text/plain"
                doc = documents.register(
                    self.store, tenant=ctx.principal.tenant, media_type=media, rights="public_source", data=data, url=source
                )
        out = match_quote(doc, args["quote"], args.get("fuzzy_threshold", 0.9))
        msg = {"exact": "Exact match", "fuzzy": f"Fuzzy match (score {out.get('score', 0):.2f})", "failed": "Quote not found"}
        return ok(out, f"{msg[out['match_mode']]} in {doc.doc_id}.")

    # ------------------------------------------------------- directed queries

    def resolve_entity(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        found = self.adapters.edgar.resolve(name=args.get("name", ""), ticker=args.get("ticker", ""), cik=args.get("cik", ""))
        candidates = []
        for i, row in enumerate(found):
            ent = {
                "entity_id": entity_id_for_cik(row["cik"]),
                "name": row["name"],
                "cik": row["cik"],
                "tickers": row["tickers"],
                "aliases": self.adapters.edgar.aliases(row["cik"]) if i < 3 else [],
                "owned_channels": self.adapters.channels.channels(row["cik"]),
            }
            self.store.remember_entity(ent)
            candidates.append(ent)
        if not candidates:
            return ok({"candidates": []}, "No SEC registrant matched. Try the ticker or the CIK.")
        top = candidates[0]
        return ok({"candidates": candidates}, f"{_plural(len(candidates), 'candidate')}; best: {top['name']} (CIK {top['cik']}).")

    def list_company_videos(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        ent = self._entity(args["entity_id"])
        owned = ent.get("owned_channels") or []
        if args.get("channel_id"):
            locks.require_channel_owned(args["channel_id"], owned, ent["name"])
            channels = [args["channel_id"]]
        elif not owned:
            raise ToolFailure(
                "LOCK_CHANNEL_NOT_OWNED",
                f"{ent['name']} has no verified owned YouTube channel in the registry yet, and no other channel can be listed.",
                alternative="Upload a video you already have rights to with register_document, or ask ClearFactor to verify the issuer's channel.",
            )
        else:
            channels = [c["channel_id"] for c in owned]
        if args.get("window"):
            start, end = locks.check_window(args["window"])
        else:
            preset = args.get("preset", "last_90_days")
            last_10k = self.adapters.edgar.last_10k(ent["cik"]) if preset == "since_last_10k" else None
            w = locks.preset_window(preset, last_10k=last_10k)
            start, end = locks.check_window(w)
        window = locks.window_dict(start, end)
        self._confirm("list_company_videos", args, ctx, {"entity": {"entity_id": ent["entity_id"], "name": ent["name"]}, "window": window, "channels": channels})
        videos: list[dict[str, Any]] = []
        for ch in channels:
            videos += self.adapters.youtube.uploads(ch, start, end, args.get("max_results", 25))
        videos = sorted(videos, key=lambda v: v.get("published_at", ""), reverse=True)[: args.get("max_results", 25)]
        return ok({"window": window, "videos": videos}, f"{_plural(len(videos), 'video')} from {ent['name']}'s owned channels, {window['from']} to {window['to']}.")

    def analyze_video(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        video_id = args["video_id"]
        entity = self._entity(args["entity_id"]) if args.get("entity_id") else None
        principal = ctx.principal
        rider = "deep_research_rider" in principal.licences
        if args.get("deep_research") and not rider and not ctx.tasks_ok:
            raise ToolFailure(
                "LOCK_NO_LICENCE",
                "Deep Research needs the tenant's terms-rider acknowledgement on file.",
                alternative="Run analyze_video without deep_research, or have an admin acknowledge the terms rider.",
            )
        report = self.store.new_report(principal.tenant, "video")
        engine = self.adapters.video

        def work(tctx: TaskContext) -> tuple[dict[str, Any], str]:
            if args.get("deep_research") and not rider:
                answer = tctx.request_input(
                    "deep_research_rider",
                    {
                        "method": "elicitation/create",
                        "params": {
                            "mode": "form",
                            "message": "Deep Research sends this video's claims to external research. Acknowledge the tenant terms rider to continue.",
                            "requestedSchema": {
                                "type": "object",
                                "properties": {"acknowledge": {"type": "boolean"}},
                                "required": ["acknowledge"],
                            },
                        },
                    },
                    message="waiting for the Deep Research terms-rider acknowledgement",
                )
                content = (answer or {}).get("content") or {}
                if (answer or {}).get("action") != "accept" or not content.get("acknowledge"):
                    raise ToolFailure(
                        "LOCK_NO_LICENCE",
                        "The Deep Research terms rider was not acknowledged.",
                        alternative="Run analyze_video without deep_research.",
                    )
            def progress(msg: str) -> None:
                tctx.check()
                tctx.progress(msg)

            result = engine.analyze(video_id, tier=args.get("tier", "light"), domain_pack=args["domain_pack"], progress=progress)
            tctx.check()
            if args.get("deep_research"):
                raise ToolFailure(
                    "ENGINE_NOT_INSTALLED",
                    "Deep Research runs on the hosted runs API, not in this open-source adapter.",
                    alternative="Use the light-tier records returned without deep_research.",
                    details={"engine": "verityngn-deep-research"},
                )
            urn = VIDEO_URN + video_id
            doc = documents.register(
                self.store, tenant=principal.tenant, media_type="text/vtt", rights="public_source",
                text=result["vtt"], url=urn, title=f"YouTube {video_id} transcript", video_id=video_id,
            )
            published = self.adapters.youtube.published_date(video_id) if hasattr(self.adapters.youtube, "published_date") else None
            retrieved = now_iso()
            claims = result.get("claims") or []
            records = []
            for i, claim in enumerate(claims):
                tctx.check()
                tctx.progress(f"{i} of {len(claims)} done", records_ready=len(report.record_ids))
                rec = self._video_record(claim, doc=doc, video_id=video_id, published=published, retrieved=retrieved,
                                         domain_pack=args["domain_pack"], entity=entity, model=result.get("model", ""),
                                         engine=engine)
                self.store.add_report_record(report, rec)
                records.append(rec)
            tctx.progress(f"{len(claims)} of {len(claims)} done", records_ready=len(report.record_ids))
            out = {"report_id": report.report_id, "transcript_doc_id": doc.doc_id, "records": [view(r, principal.role) for r in records]}
            return out, f"{_plural(len(records), 'spoken claim')} from video {video_id}, anchored to the transcript."

        return self._long_job(ctx, report=report, poll_ms=self.config.video_poll_ms, work=work, force_task=True)

    def _video_record(self, claim: dict[str, Any], *, doc: Document, video_id: str, published: Optional[str], retrieved: str,
                      domain_pack: str, entity: Optional[dict[str, Any]], model: str, engine: Any) -> dict[str, Any]:
        start_s = claim.get("start_s")
        cue = None
        if start_s is not None and doc.cues:
            cue = min(doc.cues, key=lambda c: 0 if c["start_s"] <= start_s < c["end_s"] else min(abs(c["start_s"] - start_s), abs(c["end_s"] - start_s)))
        if cue is None:
            found = anchors.fuzzy_find(doc.text, claim["claim_text"], None)
            span = (found[0], found[1]) if found else None
            hit = anchors.cues_for(doc, span[0], span[1]) if span else []
            cue = hit[0] if hit else None
        target = anchors.span_target(doc, cue["start"], cue["end"], status="exact") if cue else anchors.document_target(doc, status="approximate")
        t0 = int(cue["start_s"]) if cue else int(start_s or 0)
        quote = doc.text[cue["start"]:cue["end"]] if cue else claim["claim_text"]
        kind = claim.get("claim_kind")
        if not kind:
            from verityngn.workflows.claim_kind import classify_claim_kind

            kind = classify_claim_kind(claim["claim_text"])
        date_label = "" if published else f" (retrieved {retrieved[:10]}; publication date not available)"
        evidence = [
            {
                "source": f"YouTube {video_id} at {t0 // 60}:{t0 % 60:02d}{date_label}",
                "quote": quote,
                "date": published or retrieved[:10],
                "url": f"https://www.youtube.com/watch?v={video_id}&t={t0}s",
                "source_id": f"{video_id}+t={t0}",
                "source_class": "spoken",
                "stance": "context",
                "visibility": "public",
                "anchor": anchors.video_target(video_id, cue["start_s"], cue["end_s"], quote) if cue else anchors.video_target(video_id, t0, t0),
                "match_mode": "exact" if cue else "failed",
                "retrieved_at": retrieved,
            }
        ]
        return build_record(
            {"claim_text": claim["claim_text"], "claim_kind": kind, "verdict_or_action": "UNRESOLVED", "evidence": evidence},
            tenant=doc.tenant, domain_pack=domain_pack, tool="analyze_video", engine="verityngn",
            engine_version=getattr(engine, "version", ""), model=model, source_lane="video", doc_id=doc.doc_id,
            target=target, entity_id=(entity or {}).get("entity_id"), extra_disclaimers=("youtube_editorial",),
        )

    def news_window(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        ent = self._entity(args["entity_id"])
        start, end = locks.check_window(args["window"])
        window = locks.window_dict(start, end)
        self._confirm("news_window", args, ctx, {"entity": {"entity_id": ent["entity_id"], "name": ent["name"]}, "window": window})
        er, gdelt = self.adapters.event_registry, self.adapters.gdelt
        if er.available(ctx.principal.licences):
            provider, attribution = er, "News data: Event Registry (https://eventregistry.org/)"
        elif gdelt.covers(start, locks.today()):
            provider, attribution = gdelt, "News index: The GDELT Project (https://www.gdeltproject.org/)"
        else:
            raise ToolFailure(
                "UPSTREAM",
                "News older than three months needs the Event Registry plan, which this tenant does not have.",
                alternative=f"Narrow the window to the last three months (from {(locks.today() - dt.timedelta(days=90)).isoformat()}).",
            )
        articles = provider.search(ent["name"], start, end, args.get("query", ""), args.get("langs", ["eng"]), args.get("max_results", 50))
        out = {"provider": provider.name, "attribution": attribution, "window": window, "articles": articles}
        flagged = sum(1 for a in articles if a.get("allegation"))
        note = f" ({flagged} flagged as Allegation)" if flagged else ""
        return ok(out, f"{_plural(len(articles), 'article')} about {ent['name']}, {window['from']} to {window['to']}{note}.")

    def filings_search(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        start, end = locks.check_window(args["window"])
        window = locks.window_dict(start, end)
        self._confirm("filings_search", args, ctx, {"cik": args["cik"], "forms": args["forms"], "window": window})
        edgar = self.adapters.edgar
        if args.get("query"):
            filings = edgar.full_text(args["cik"], args["query"], args["forms"], start, end, args.get("items"))
        else:
            filings = edgar.filings(args["cik"], args["forms"], start, end, args.get("items"))
        return ok({"filings": filings}, f"{_plural(len(filings), 'filing')} for CIK {args['cik']}, {window['from']} to {window['to']}.")

    def get_filing_section(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        accession = args["accession"]
        cik = args.get("cik") or str(int(accession.split("-", 1)[0]))
        self._confirm("get_filing_section", args, ctx, {"cik": cik, "accession": accession, "item": args["item"]})
        url, row = self.adapters.edgar.filing_document(cik, accession)
        doc = self.store.document_for_url(url, ctx.principal.tenant)
        if doc is None:
            data = self.adapters.edgar.get_bytes(url)
            doc = documents.register(
                self.store, tenant=ctx.principal.tenant, media_type="text/html", rights="public_source", data=data, url=url,
                title=f"{row.get('form', '')} {row.get('filingDate', '')} {accession}".strip(),
            )
        wanted = args["item"].upper().split(":", 1)[-1]
        entry = next((e for e in doc.outline if e["item"].upper() == wanted), None)
        if entry is None:
            raise ToolFailure(
                "ANCHOR_UNRESOLVED",
                f"Item {args['item']} was not found in {accession}.",
                alternative=f"Open the whole filing ({doc.doc_id}) and assess it as a document.",
                details={"doc_id": doc.doc_id, "items_found": [e["item"] for e in doc.outline]},
            )
        target = anchors.section_target(doc, entry, status="exact")
        return ok({"doc_id": doc.doc_id, "target": target, "url": url}, f"Item {entry['item']} of {accession} registered as {doc.doc_id}.")

    def sanctions_match(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        self._confirm("sanctions_match", args, ctx, {"name": args["name"], "schema": args["schema"]})
        cands = self.adapters.sanctions.match(args["name"], args["schema"], args.get("country", ""), args.get("birth_date", ""))
        return ok({"label": SANCTIONS_LABEL, "candidates": cands}, f"{_plural(len(cands), 'candidate')} for human review, not determinations.")

    def search_litigation(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        locks.check_window(args["window"])
        locks.require_licence(ctx.principal.licences, "courtlistener_commercial", "Litigation search")
        raise ToolFailure(
            "ENGINE_NOT_INSTALLED",
            "The CourtListener adapter is not built yet.",
            alternative="Use filings_search for the issuer's own litigation disclosures (10-K Item 3, 8-K).",
            details={"engine": "courtlistener"},
        )

    # -------------------------------------------------------- records/review

    def compose_assessment(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        recs = [view(self.store.get_record(rid, ctx.principal.tenant), "analyst") for rid in args["record_ids"]]
        cov = coverage.compose(recs, args.get("group_by", "item_1a_heading"))
        return ok(cov, f"Coverage for {_plural(len(recs), 'record')} in {_plural(len(cov['rows']), 'row')}.")

    def record_review_action(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        p = ctx.principal
        action = args["action"]
        locks.require_decide_role(p.role, action)
        rec = self.store.get_record(args["record_id"], p.tenant)
        review = rec.setdefault("review", {"state": "proposed", "version": 1, "history": []})
        if args.get("expected_version") is not None and args["expected_version"] != review.get("version"):
            raise ToolFailure(
                "INVALID",
                f"The record changed since you loaded it (version {review.get('version')}, you sent {args['expected_version']}).",
                alternative="Reload the record with get_record and apply your change again.",
                details={"current_version": review.get("version")},
            )
        if action in ("set_judgment", "clear_judgment"):
            if not self.config.judgment_enabled(p.tenant, p.workspace_ids):
                raise ToolFailure(
                    "LOCK_ROLE",
                    "The Judgment column is switched off for this workspace.",
                    alternative="Record the view as a note with action 'edit', or ask an admin to switch the Judgment column on.",
                )
            if action == "set_judgment" and not args.get("judgment_likelihood"):
                raise ToolFailure("INVALID", "set_judgment needs judgment_likelihood (remote, possible or likely).")
        elif args.get("judgment_likelihood"):
            raise ToolFailure(
                "INVALID",
                "judgment_likelihood is only accepted with action set_judgment.",
                alternative="Call record_review_action with action 'set_judgment'.",
            )
        changes = {k: args[k] for k in ("verdict_or_action", "severity_level", "illustrative_rewrite") if k in args}
        entry: dict[str, Any] = {
            "action": action,
            "by": p.sub,
            "role": p.role,
            "at": now_iso(),
            "evidence_hash": evidence_hash(rec),
        }
        if args.get("note"):
            entry["note"] = args["note"]
        if changes:
            entry["changes"] = changes
        if action == "propose":
            review["state"] = "proposed"
        elif action == "accept":
            review["state"] = "accepted"
            self._apply(rec, changes, args.get("note"))
        elif action == "edit":
            review["state"] = "edited"
            self._apply(rec, changes, args.get("note"))
        elif action == "reject":
            review["state"] = "rejected"
        elif action == "set_judgment":
            rec["judgment"] = {
                "likelihood": args["judgment_likelihood"],
                "label": JUDGMENT_LABEL,
                "entered_by": p.sub,
                "entered_at": entry["at"],
            }
            entry["judgment"] = args["judgment_likelihood"]
        elif action == "clear_judgment":
            rec.pop("judgment", None)
        review.setdefault("history", []).append(entry)
        review["version"] = int(review.get("version", 1)) + 1
        self.store.put_record(rec)
        return ok(view(rec, p.role), f"{action} recorded on {rec['claim_id']} (version {review['version']}).")

    @staticmethod
    def _apply(rec: dict[str, Any], changes: dict[str, Any], note: Optional[str]) -> None:
        if "verdict_or_action" in changes:
            rec["verdict_or_action"] = changes["verdict_or_action"]
        if "illustrative_rewrite" in changes:
            rec["illustrative_rewrite"] = changes["illustrative_rewrite"]
        if "severity_level" in changes:
            rec["severity"] = {"level": changes["severity_level"], "basis": "reviewer", "rationale": (note or "Reviewer override.")[:500]}

    def get_record(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        rec = self.store.get_record(args["record_id"], ctx.principal.tenant)
        return ok(view(rec, ctx.principal.role), f"{rec['verdict_or_action']}: {rec['claim_text'][:120]}")

    def _report_records(self, report: Report) -> list[dict[str, Any]]:
        return [self.store.records[r] for r in list(report.record_ids) if r in self.store.records]

    def get_report(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        p = ctx.principal
        report = self.store.get_report(args["report_id"], p.tenant)
        records = self._report_records(report)
        status = {"running": "running", "complete": "complete", "failed": "failed"}[report.status]
        out: dict[str, Any] = {
            "report_id": report.report_id,
            "status": status,
            "records_ready": len(records),
            "records": [view(r, p.role) for r in records],
            "coverage": report.extra.get("coverage") or coverage.compose([view(r, "analyst") for r in records]),
            "viewer_role": p.role,
            "judgment_enabled": self.config.judgment_enabled(p.tenant, p.workspace_ids),
        }
        if report.status_message:
            out["status_message"] = report.status_message
        if report.error:
            out["error"] = report.error
        return ok(out, f"Report {status}: {_plural(len(records), 'record')} ready.")

    def export_assessment(self, args: dict[str, Any], ctx: CallContext) -> dict[str, Any]:
        p = ctx.principal
        include_internal = bool(args.get("include_internal"))
        if include_internal and p.role == "junior":
            raise ToolFailure(
                "LOCK_ROLE",
                "Internal content (allegations, private evidence) cannot be exported by the junior role.",
                alternative="Export without include_internal, or ask general counsel or an analyst to export.",
            )
        report = self.store.get_report(args["report_id"], p.tenant)
        if report.status != "complete":
            raise ToolFailure("INVALID", f"Report is {report.status}; only complete reports can be exported.", alternative="Poll get_report until it is complete.")
        records = exports.filter_records(self._report_records(report), include_internal)
        if args["format"] != "xlsx" or p.role not in ("gc", "admin"):
            records = [view(r, "analyst") for r in records]
        cov = coverage.compose(records)
        data, media = exports.render(args["format"], {"report_id": report.report_id}, records, cov)
        exp = self.store.put_export(p.tenant, media, data)
        uri = f"splitrisk://exports/{exp.export_id}"
        return ok(
            {"resource_uri": uri, "media_type": media, "expires_at": exp.expires_at.isoformat().replace("+00:00", "Z")},
            f"Export ready at {uri} ({len(data):,} bytes); it expires in 24 hours.",
        )


def match_quote(doc: Document, quote: str, threshold: float) -> dict[str, Any]:
    """Exact, fuzzy or failed match of ``quote`` in the normalized text of ``doc``."""
    needle = documents.normalize_text(quote)
    out: dict[str, Any] = {"quote_sha256": sha256_text(needle)}
    idx = doc.text.find(needle) if needle else -1
    if idx >= 0:
        end = idx + len(needle)
        out.update(match_mode="exact", score=1.0, matched_text=doc.text[idx:end], target=anchors.span_target(doc, idx, end, status="exact"))
        return out
    best = anchors.fuzzy_find(doc.text, needle, None, accept=threshold)
    if best:
        s, e, score = best
        matched = doc.text[s:e]
        out.update(
            match_mode="fuzzy",
            score=round(score, 4),
            matched_text=matched,
            diff=char_diff(needle, matched),
            target=anchors.span_target(doc, s, e, status="fuzzy"),
        )
        return out
    out.update(match_mode="failed", score=round(anchors.best_alignment(doc.text, needle), 4))
    return out


def char_diff(a: str, b: str) -> str:
    """Compact character diff: ``[-removed-]{+added+}`` around unchanged text."""
    parts = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            parts.append(a[i1:i2])
        if op in ("delete", "replace"):
            parts.append(f"[-{a[i1:i2]}-]")
        if op in ("insert", "replace"):
            parts.append(f"{{+{b[j1:j2]}+}}")
    return "".join(parts)
