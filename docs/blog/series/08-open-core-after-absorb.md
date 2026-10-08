# Part 8 — Open-core after absorb (outline)

**Series:** VerityNgn OSS  
**Part 8 of 8 · Draft with launch pack**  
**Status:** OUTLINE

---

## Thesis

Hosters pin OSS ≥3.0.0 (candidate `8d6a8e3`+). Research features are in the public tree. Commercial overlays must not re-fork predictions/quant — only scale, billing, and SaaS.

## Outline

1. **Dependency model** — `pip install verityngn` vs `verityngn[predictions]`.
2. **Boundary scan** — fails on `stripe`, `dr_credits`, `verityindex_commercial` paths under `verityngn/`.
3. **What never goes closed** — verification, CI, DR quality, RiskFactor sensors.
4. **Ship clicks** — retag / merge / PyPI only on explicit operator ask after matrix green.
5. **Commercial follow-up** — pin absorb SHA; delete duplicated feature packages.

## Cite

- [`docs/OPEN_CORE.md`](../../OPEN_CORE.md)
- [`docs/DEPENDENCY_MODEL.md`](../../DEPENDENCY_MODEL.md)
- [`docs/launch/v3_release_pack/MEDIA_CHECKLIST.md`](../../launch/v3_release_pack/MEDIA_CHECKLIST.md)

## Charts (later)

Open-core architecture before/after absorb.

---

*Previous: [Part 7](07-ten-video-battery.md) · Series index: [README](README.md)*
