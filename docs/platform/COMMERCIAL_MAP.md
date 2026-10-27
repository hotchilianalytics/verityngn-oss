# Commercial map — VerityNgn / verityindex / ClearFactor

**Decision (2026-10-19):** OSS owns L1–L3 (engine, sleeves, agent surface). **verityindex.com** is the L4 hosted control plane plus a catalog of domain apps. **ClearFactor** is the first paid app on that plane; vault / counsel engagements are services.

## Who owns what

| Surface | Role | Repo / home |
|---------|------|-------------|
| `verityngn-oss` | Canonical engine + research sleeves | GitHub `hotchilianalytics/verityngn-oss` |
| `verityngn[predictions]` | CEO / RiskFactor **sensors** (S00–S15) | Extra on OSS |
| `verityngn[disclosure]` (Phase 1) | Pins public `rfkit` disclosure engine | Extra on OSS |
| `rfkit` (Phase 1 public) | Item 1A vs 8-K matcher, specimen, review CLI | New Apache repo (fresh history) |
| verityindex.com | Workspaces, runs API, gallery, billing, app catalog | VerityEngine (Replit) + commercial backend |
| ClearFactor Advisory | Paid disclosure app + services brand | Offer sheet private; engine OSS |

## Open vs paid (disclosure sleeve)

| Open (Apache) | Paid (services / app) |
|---------------|------------------------|
| Typed same-incident matcher | Private vault + NDA workflow |
| EDGAR public fetch | Client incident-log ingest |
| `specimen` / `review` CLI on public filings | Counsel brief packaging under privilege |
| Ontologies + unit tests | Quarterly monitor ops |
| Public Microsoft / UnitedHealth-style examples (cleared) | Pricing, engagement letter, SRI print kit |

**Never open:** GOF / short-seller jobs, outreach CRM, engagement/NDA drafts, prices, uncleared issuer outreach.

## verityindex.com as control plane

Target capabilities (Phase 2):

1. Auth + workspaces (existing Supabase path)
2. Runs API over OSS `analyze` / disclosure review
3. Evidence / audit registry (claim JSON + citations)
4. Public gallery (already live) + private user gallery
5. Stripe credits / tiers
6. Domain app catalog — ClearFactor first; sponsor-readiness later
7. Later: BYOC / marketplace listing (LangSmith × GCP pattern)

## Two RiskFactor names (buyer language)

| Phrase for buyers | Product |
|-------------------|---------|
| “Video RiskFactor / predictions sleeve” | OSS sensors on CEO media |
| “ClearFactor disclosure RiskFactor” | Item 1A pre-filing review app |

Internal docs may say “RiskFactor” for either; public collateral must disambiguate.

## Code flow

```
OSS (features + quality)
        ↑ pin / depend
Commercial backend + VerityEngine (scale, billing, UI, vault)
        ↑
ClearFactor app + bespoke services
```

Mature features still land in OSS first ([OPEN_CORE.md](../OPEN_CORE.md)). Commercial does not re-fork predictions/quant/disclosure engines.

## Related private packs

- Offer / SRI: `~/proj/ajjax/downloads/rfkit/consulting/OFFER_SHEET.md`
- Context stack: `~/proj/ajjax/downloads/rfkit/consulting/CONTEXT_STACK.md`
