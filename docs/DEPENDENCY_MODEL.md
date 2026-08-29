# Dependency model — OSS as base (v3.0.0+)

```
verityngn-oss (Apache-2.0) ──► PyPI verityngn==3.0.0
        │
        ├── verityngn-cloudrun-batch   (pin OSS tag / submodule)
        ├── verityngn-core-commercial (overlay: delivery packaging)
        ├── verityngn-backend-commercial (overlay: multi-tenant API)
        ├── predictions branch/repo   (overlay: quant / Karp / fusion)
        └── riskfactor (future)        (overlay: S00–S15 product)
```

## How overlays consume OSS

1. **Preferred:** `pip install verityngn==3.0.0` (or git ref `v3.0.0`) inside commercial/batch images.
2. **Legacy:** Docker `COPY` / git submodule of `verityngn-oss` (still used by some Cloud Run builds).
3. **Predictions / riskfactor:** keep overlay packages only (`services/predictions`, `services/quant`, Karp scripts, S-factor registries). Do **not** fork the entire engine.

## Sync checklist after an OSS release

1. Tag OSS `v3.0.0` and publish PyPI.
2. Bump pin in `verityngn-cloudrun-batch` (see `OSS_VERSION` / Dockerfile comments).
3. Update commercial `docs/marketing/oss_launch/OPEN_CORE_BOUNDARY.md` to match `docs/OPEN_CORE.md`.
4. Predictions worktree README: "requires OSS ≥3.0.0".
5. Riskfactor scaffold: empty overlay depending on OSS; import checkpoint docs separately.
