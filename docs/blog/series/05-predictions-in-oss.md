# Part 5 — Predictions in OSS

**Series:** VerityNgn OSS  
**Part 5 of 9**  
**Status:** DRAFT · absorb SHA `8d6a8e3` · candidate `b13bcf1`

---

## Thesis

Research RiskFactor **sensors** (S00–S15, quant, fusion, affect, players) live in **Apache OSS**. Commercial keeps hosted scale, billing, credits, and user-scoped gallery — not a second copy of the research tree.

## What moved

Packages under `verityngn/services/{predictions,quant,fusion,players,affect,mediasphere,text_risk,timeseries}` plus vision AU/gaze extractors and `scripts/predictions/`. Absorb commit: `8d6a8e3` on `release/v3.0.0`.

These are **measurement** sleeves for CEO / talking-head delivery and instrument risk. They are not Family B allocation products.

## What stayed closed (hosted)

- Stripe / trial credits  
- `verityindex_commercial` GCS paths  
- SaaS UI (VerityEngine / verityindex.com)  
- Outreach CRM and engagement letters  

## OPEN_CORE rewrite

Boundary scan fails on **commercial markers** (`stripe`, credits paths, commercial gallery prefixes), not on research directory names. See [OPEN_CORE.md](../../OPEN_CORE.md).

## Install

```bash
pip install 'verityngn[predictions]'
# or from source:
pip install -e '.[predictions]'
```

Optional extras — no hard torch/whisper on the default `analyze` path. Predictions scripts are opt-in under `scripts/predictions/`.

## Naming: two RiskFactors

| Name | Meaning |
|------|---------|
| Predictions / RiskFactor **sensors** | This part — OSS S00–S15 |
| ClearFactor disclosure RiskFactor | Item 1A vs 8-K counsel product — engine sleeve Phase 1; services paid |

Do not market them as one blob. Platform map: [COMMERCIAL_MAP.md](../../platform/COMMERCIAL_MAP.md).

## What we do not claim

- No Family B allocation / alpha  
- Measurement and abatement language only  
- S14 (near-chance vocal dissonance) stays refused  

## Cite

- [`docs/OPEN_CORE.md`](../../OPEN_CORE.md)
- [`docs/predictions/OSS_ABSORB.md`](../../predictions/OSS_ABSORB.md)
- [`docs/predictions/RISK_FACTOR_REGISTRY_S00_S15.md`](../../predictions/RISK_FACTOR_REGISTRY_S00_S15.md)

---

*Previous: [Part 4](04-two-videos.md) · Next: [Part 6](06-ceo-audio-video-lanes.md)*
