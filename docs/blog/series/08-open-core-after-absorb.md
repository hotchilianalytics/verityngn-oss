# Part 8 — Open-core after absorb

**Series:** VerityNgn OSS  
**Part 8 of 9**  
**Status:** DRAFT · candidate `b13bcf1`

---

## Thesis

Hosters pin OSS ≥3.0.0. Research features are in the public tree. Commercial overlays must not re-fork predictions/quant — only scale, billing, SaaS UI, and (for disclosure) vault/services.

## Dependency model

```bash
pip install verityngn                 # engine
pip install 'verityngn[deep]'         # Deep Research extras
pip install 'verityngn[predictions]'  # CEO / sensor sleeve
# Phase 1:
pip install 'verityngn[disclosure]'   # pins public rfkit
```

See [DEPENDENCY_MODEL.md](../../DEPENDENCY_MODEL.md).

## Boundary scan

`scripts/ci/open_core_boundary_scan.py` fails on commercial markers under `verityngn/` (`stripe`, credits paths, commercial gallery prefixes). Research package names are allowed.

## What never goes closed

Verification, counter-intel, Deep Research quality, URL safety, domain tiers, and RiskFactor **sensors**. If hoarded commercially, that is a bug in the open-core model ([OPEN_CORE.md](../../OPEN_CORE.md)).

## Control plane vs engine

**verityindex.com** is the hosted **control plane** (workspaces, runs, gallery, billing, apps) — not a place to hide engine quality. ClearFactor is the first **app**; disclosure engine opens as a sleeve ([COMMERCIAL_MAP.md](../../platform/COMMERCIAL_MAP.md)).

## Ship clicks

Retag / merge / PyPI only on **explicit operator ask** after matrix green. Primary-10 battery is already PASS.

## Cite

- [`docs/OPEN_CORE.md`](../../OPEN_CORE.md)
- [`docs/platform/PLATFORM_OVERVIEW.md`](../../platform/PLATFORM_OVERVIEW.md)
- [`docs/launch/v3_release_pack/MEDIA_CHECKLIST.md`](../../launch/v3_release_pack/MEDIA_CHECKLIST.md)

---

*Previous: [Part 7](07-ten-video-battery.md) · Next: [Part 9](09-report-to-platform.md)*
