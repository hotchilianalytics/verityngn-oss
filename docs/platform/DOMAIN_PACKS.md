# Domain packs — VerityNgn 3.0

Domain packs are Credo-style **policy packs** for claim-level risk: each pack names inputs, claim typology, verification sources, §9 method, and action labels. Packs are Apache research/product surfaces on top of the L1 engine.

## Pack catalog

| Pack ID | Domain | Inputs | §9 / method | Primary actions |
|---------|--------|--------|-------------|-----------------|
| `consumer_craap` | Consumer / VSL / supplement | YouTube or file | CRAAP | Supported / Contested / Unresolved + residual reliance |
| `analyst_sift` | Analyst deep-data / legislative | Local mp4 / longform | SIFT + risk chips | Typed §§6.1–6.8; §6.1 = source-backed only |
| `ceo_predictions` | CEO talking-head / keynote | YouTube (pre-print hygiene) | Delivery / instrument sensors | S00–S15 measurement; S14 refuse |
| `securities_disclosure` | Item 1A vs own record (sleeve one of the ClearFactor committee pack) | EDGAR 10-K/Q + 8-K; optional incident log | Same-incident match + `junior_obvious` gate | **Rewrite · Keep · Move to General · Remove**; famous 8-K pairs go to hygiene |
| `legal_deposition` | Spoken deposition / expert | YouTube or file | Claim extract + CI | Claim risk + exhibit map |
| `health_ci` | Contested health / lab claims | Source investigation video | Counter-intel heavy | Contested / Unresolved emphasis |
| `brand_safety` | Sponsor / brand readiness | Video + overlays | Brand safety scores | Visual-only risk buckets |

## Shared claim / evidence / action schema (target)

All packs should emit (or map to) a common JSON shape so video claims and disclosure findings share one evidence registry:

```json
{
  "claim_id": "…",
  "domain_pack": "securities_disclosure",
  "claim_text": "…",
  "claim_kind": "source_backed_fact | prediction | …",
  "evidence": [{"source": "…", "quote": "…", "date": "…", "url": "…"}],
  "verdict_or_action": "REWRITE | KEEP | MOVE | REMOVE | SUPPORTED | CONTESTED | UNRESOLVED",
  "confidence": 0.0,
  "residual_reliance_risk": 0.0
}
```

Video packs use Supported / Contested / Unresolved (display) over TRUE / FALSE / UNCERTAIN (internal). Disclosure pack uses counsel actions only — no heatmap score as the product.

## Primary-10 coverage

| Pack | Proven by |
|------|-----------|
| `consumer_craap` | Lipozem `tLJC8hkK-ao` |
| `analyst_sift` | SB1507 local dense |
| `ceo_predictions` | Karp / Huang / Nadella battery rows |
| `legal_deposition` | Butler Kahn `7MXE1kDCY-k` |
| `health_ci` | Carney `RuinHdlpXvE` |
| `securities_disclosure` | rfkit specimen / review (ClearFactor); OSS sleeve Phase 1 |

Full battery: [BATTERY_RESULTS_v3.md](../launch/BATTERY_RESULTS_v3.md).

## Derrick context-stack alignment

On the 7-step “context” ladder (Glimmer / SonicAlpha market direction):

| Step | Pack posture |
|------|----------------|
| 1–2 Crawl / acquire | **Out of scope** for all packs |
| 3 Transform / extract | Engine L1; not sold alone |
| 4 Connect the dots | Video CI + disclosure same-incident match |
| 5 Own-context ground truth | Paid vault / incident log (disclosure) |
| 6 Optimize workflows | Apps on L5, not a horizontal legal AI |
| 7 Close the loop | Filing cadence / re-analyze — not real-time surveil |

See [PLATFORM_LANDSCAPE_2026.md](PLATFORM_LANDSCAPE_2026.md).
