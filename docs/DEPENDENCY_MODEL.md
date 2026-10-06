# Dependency model — OSS as base (v3.0.0+)

```
verityngn-oss (Apache-2.0) ──► PyPI verityngn==3.0.0
        │  (engine + research: claims, DR, predictions/RiskFactor sensors)
        │
        ├── verityngn-cloudrun-batch   (pin OSS tag / submodule)
        ├── verityngn-core-commercial (overlay: packaging, outreach)
        └── verityngn-backend-commercial (overlay: multi-tenant API, credits, GCS)
```

## How commercial consumes OSS

1. **Preferred:** pin a promoted OSS release/ref inside commercial and batch images.
   - stable: `pip install verityngn==3.0.0`
   - research extras: `pip install verityngn[predictions]`
   - pre-cutover smoke: git ref `release/v3.0.0`
2. **Legacy:** Docker `COPY` / git submodule of `verityngn-oss` (still used by some Cloud Run builds).
3. **Do not fork** predictions/quant/fusion back into commercial after the 2026-10-05 absorb — pin OSS and keep only hosted extras.

## Commercial overlay rule

Commercial repos should:

1. pin the promoted OSS engine
2. run parity / smoke against that pin
3. keep only scale, billing, credits, gallery paths, SaaS UI, outreach
4. document deliberate divergences

## Sync checklist after an OSS release

1. Tag OSS and publish PyPI when asked.
2. Bump pin in `verityngn-cloudrun-batch`.
3. Update commercial open-core boundary docs to match `docs/OPEN_CORE.md`.
4. Drop duplicated feature packages from commercial trees once the absorb is verified.
