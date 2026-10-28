# verityngn-mcp v2 (remote server for SplitRisk)

A remote MCP server on protocol **2026-07-28** (stateless, Streamable HTTP), alongside the 3.1 stdio server in [`MCP.md`](MCP.md), which is unchanged. It implements the SplitRisk concept's Round 2 contracts: 17 tools returning the extended `ClaimRiskRecord` (schema 2.0) with W3C Web Annotation anchors, server-side locks, the Tasks extension for long jobs, MCP Apps widgets, and the OAuth 2.1 resource-server side.

Code: `verityngn/agent/mcp_v2/`. Tests: `test/unit/mcp_v2/`. Gate: `scripts/ci/mcp_ship_gate.py`.

## Run it

```bash
pip install -e '.[mcp]'
python -m verityngn.agent.mcp_v2 --dev            # loopback only; tokens like dev:<tenant>:<role>[:<sub>][:lic=a,b]
python scripts/ci/mcp_ship_gate.py --live         # REAL / BLOCKED / FAIL per tool, over HTTP
```

Production: set `SPLITRISK_RESOURCE_URL` (canonical endpoint; also the token audience), `SPLITRISK_AUTH_ISSUER`, `SPLITRISK_JWKS_URL` and `SPLITRISK_ALLOWED_ORIGINS`. The ASGI app for uvicorn or Cloud Run is `verityngn.agent.mcp_v2.transport.asgi_app(server)`.

| Variable | Used for |
|---|---|
| `SEC_USER_AGENT` | Declared User-Agent on every EDGAR call |
| `YOUTUBE_API_KEY` | `list_company_videos` (uploads playlist only) and video publish dates |
| `SPLITRISK_OWNED_CHANNELS` | Curated owned-channel registry (JSON keyed by CIK; merged with the empty bundled file) |
| `EVENT_REGISTRY_API_KEY` | Default news provider; GDELT covers windows inside the last three months without a key |
| `OPENSANCTIONS_API_KEY` | `sanctions_match` |
| `GEMINI_API_KEY` | `analyze_video` (Gemini direct-URL path) |
| `SPLITRISK_DISCLOSURE_ENGINE` | `module:factory` for the disclosure engine (or the `verityngn.disclosure_engines` entry point) |
| `SPLITRISK_JUDGMENT_WORKSPACES` | Tenants or workspace IDs with the Judgment column switched on |
| `SPLITRISK_AUDIT_LOG` | JSONL audit rows (tenant, user, role, tool, arguments hash, record IDs, time) |

## What is real and what is behind an adapter

| Tool | Status in this build |
|---|---|
| `register_document` | Real for text, HTML (including inline XBRL), WebVTT and URLs (public hosts only). PDF and DOCX need Docling; `upload_ref` needs the hosted object store. Both report `ENGINE_NOT_INSTALLED`. |
| `verify_quote` | Real: exact, fuzzy (with character diff) or failed, plus an anchor. Native matcher, not `rfkit/verify.py`. |
| `resolve_entity`, `filings_search`, `get_filing_section` | Real against SEC EDGAR (submissions index, full-text search, archives); verified live on the Microsoft Item 1.05 8-K. |
| `compose_assessment`, `record_review_action`, `get_record`, `get_report` | Real. |
| `export_assessment` | Real for `json`, `md`, `w3c_annotations` and `xlsx`; `docx_comments` and `audit_pdf` are not built yet. |
| `news_window` | GDELT is real (no key). The Event Registry client follows its public API but has not run against a live key. |
| `list_company_videos` | Real YouTube Data API code (`channels.list` then `playlistItems.list`, never `search.list`), covered by mocked tests. Needs a key and a curated registry entry; the bundled registry is empty. |
| `sanctions_match` | OpenSanctions `/match` client, covered by mocked tests; needs a key. |
| `assess_selection`, `assess_document` | Adapter interface. No disclosure engine ships here; without one they return `ENGINE_NOT_INSTALLED` with an alternative. |
| `analyze_video` | Wired to VerityNgn's Gemini YouTube-URL transcript and claim extractor (no download). Needs the full VerityNgn install and a Gemini key, otherwise `ENGINE_NOT_INSTALLED` or `UPSTREAM`. The `full` tier and Deep Research run on the hosted runs API and report `ENGINE_NOT_INSTALLED`. |
| `search_litigation` | Lock only: `LOCK_NO_LICENCE` without `courtlistener_commercial`; `ENGINE_NOT_INSTALLED` with it. |

**Disclosure engine contract.** An engine is any object with `name`, `version` and `assess(request, progress) -> list[finding]`. `request` carries the normalized text and the range to assess; each finding has `claim_text`, `start` and `end` (inside the range) and optionally `claim_kind`, `verdict_or_action`, `category`, `item_1a_heading`, `confidence`, `illustrative_rewrite`, `junior_obvious`, `lag_clock`, `allegation` and `evidence` (EvidenceItem-shaped, with `source_class` and `stance`). See `adapters/disclosure.py`. The server builds the record, anchors, coverage and severity, and rejects any record that fails the schema.

## Locks (enforced in the server)

| Request | Result |
|---|---|
| Window over 366 days, or ending in the future | `LOCK_WINDOW`, with a valid window to use instead |
| Any schedule, alert or monitor argument | `INVALID`, offering to save and re-run the query |
| Channel not on the issuer's verified owned list | `LOCK_CHANNEL_NOT_OWNED`, listing owned channels and the upload route |
| Litigation without the CourtListener licence | `LOCK_NO_LICENCE` |
| Junior or analyst accept, edit, reject or judgment | `LOCK_ROLE`, offering `propose` |
| Judgment while the workspace column is off | `LOCK_ROLE` |
| Junior search without `confirmed: true` | `NEEDS_CONFIRMATION`, with the resolved entity and window in `details` |
| Junior export with `include_internal` | `LOCK_ROLE` |
| Token without the tool's scope | HTTP 403, `WWW-Authenticate: Bearer error="insufficient_scope"`, with an alternative in the error data |
| Another tenant's handle | The same `NOT_FOUND` as a missing handle |

Coverage cells are a dated quote or nothing. Severity is consequence only (rules `SEV-OWN-PAIR`, `SEV-STAFF`, `SEV-DOCKET`, `SEV-SPOKEN`, `SEV-SOFTEN`, `SEV-SHORT`, `SEV-CONTEXT`, `SEV-JUNIOR`); reviewer overrides set `basis: reviewer`. Likelihood exists only as the GC's labelled `judgment`. It is stripped, together with the history entries that set it, from every non-GC view, from `compose_assessment` and from JSON, Markdown and W3C exports, and appears only in GC `xlsx` exports.

## Wire details checked against the published specs

Checked on 28 October 2026 against the [2026-07-28 changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog), [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http), [server/discover](https://modelcontextprotocol.io/specification/2026-07-28/server/discover), [authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), the [ext-tasks 2026-07-28 schema](https://github.com/modelcontextprotocol/ext-tasks) and [MCP Apps 2026-01-26](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx).

- One POST endpoint. `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` (base64 sentinel decoded) must match the body, otherwise HTTP 400 with `-32020`; an unsupported version returns HTTP 400 with `-32022` and `{supported, requested}`. GET and DELETE return 405, notifications 202, unknown methods 404 with `-32601`. Session IDs and `Last-Event-ID` are ignored. Responses are always `application/json`.
- Every result carries `resultType` and `_meta["io.modelcontextprotocol/serverInfo"]`. Discover, list and read results carry `ttlMs` and `cacheScope`.
- `server/discover` advertises `extensions: {"io.modelcontextprotocol/tasks": {}, "io.modelcontextprotocol/ui": {"mimeTypes": ["text/html;profile=mcp-app"]}}` and needs no token.
- Tasks: the server returns `{"resultType": "task", taskId, status, createdAt, lastUpdatedAt, ttlMs, pollIntervalMs}` only when the request's `clientCapabilities.extensions` includes the tasks extension. `tasks/get` returns `result` on `completed`; `tasks/update` takes `inputResponses`; `tasks/cancel` is cooperative. Without the capability, the task methods return `-32021`.
- Auth: RFC 9728 metadata at `/.well-known/oauth-protected-resource` and `/.well-known/oauth-protected-resource/mcp`; 401 challenges carry `resource_metadata`; JWTs are checked for issuer, audience (the resource URL), expiry, `sub`, `tenant_id` and `role`.

## Deviations from the concept doc (Round 2)

1. **Tasks wire names.** The published extension has no tool-level `execution.taskSupport` and no client request for task execution. The server decides, and the task policy (video and document: always; selection: above 90,000 characters) is internal. The task carries `report_id` in `_meta["com.verityindex.splitrisk/report_id"]` and `records_ready` in `_meta["com.verityindex.splitrisk/records_ready"]`.
2. **Tool errors inside tasks** finish as `completed` with an `isError` result carrying the `ToolError`. The spec reserves `failed` for JSON-RPC errors; the doc had `failed` carry a `ToolError`.
3. **Schema references.** `urn:splitrisk:schema:v1#/$defs/…` references are bundled into each tool's own `$defs`, because clients must not fetch, and should reject, unresolved external `$ref`s. The full definitions document is also served as `splitrisk://schema/v1`.
4. **MCP Apps network access** is declared in `_meta.ui.csp.connectDomains`, not `_meta.ui.domain`, which sets the sandbox origin. Widgets declare no connect domains at all: every call goes through the host bridge. The video widget declares `frameDomains` for youtube-nocookie.com, and the assessment widget asks for `clipboardWrite`.
5. **Workpaper widget** is linked to `get_report` for every role, because `tools/list` is public-cacheable and cannot vary by caller. It renders read-only for non-GC callers, and the server strips judgment.
6. **Added to `ToolError`:** the code `ENGINE_NOT_INSTALLED` and an optional `details` object.
7. **Added inputs:** `confirmed` on `filings_search`, `get_filing_section` and `search_litigation` (section 2.2 needs it, but those schemas omitted it); `resolve_entity` is exempt. `get_filing_section` also takes an optional `cik`, because an accession number's prefix is the filer agent, not always the issuer.
8. **`search_litigation`** is listed as a lock-only tool, because the doc says it returns `LOCK_NO_LICENCE` while blocked.
9. **Pending output.** Task-required tools use an output schema of `oneOf` the final result or `{report_id, status: "running"}`, the documented fallback for hosts without Tasks.
10. **Scope failures** use HTTP 403 with an `insufficient_scope` challenge, as the auth spec says. Role and argument locks stay tool errors with alternatives.
11. **Strict inputs** (`additionalProperties: false`). Schedule-like arguments get `INVALID` with an alternative; the doc has no dedicated lock code.
12. **Not built here:** multi round-trip confirmation (`input_required` on the original request), `docx_comments` and `audit_pdf` exports, cost caps, rate limits, durable storage with row-level security (this build uses an in-memory store and an in-process task pool), `subscriptions/listen` and `notifications/tasks`.
13. **Video evidence date** is the YouTube publish date when a key is configured. Otherwise it is the retrieval date, labelled as such in `source` and `retrieved_at`.
14. **Native stand-ins for unpublished rfkit pieces:** quote matching, the SEC Item outline (no risk-factor sub-headings yet) and a short-seller domain list.
15. **Server version** is 4.0.0 in `serverInfo`; the package version stays 3.0.0, because there is no release in this change.
