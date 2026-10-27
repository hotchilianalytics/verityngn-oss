# Executive summary — VerityNgn OSS 3.0.0

**Date:** 2026-10-25 · **Branch:** `release/v3.0.0` · **HEAD:** `94f62f6` (launch-docs SHA `b13bcf1`; published tag still `c740bad`)

## One sentence

VerityNgn 3.0.0 ships an Apache multimodal **claim-risk engine** (Deep Research, six claim kinds, genre-aware CRAAP/SIFT) as the open core of a **risk platform**: domain packs, agent surface, hosted control plane on verityindex.com, and ClearFactor as the first paid disclosure app.

## Proof

| Gate | Result |
|------|--------|
| Offline unit / boundary / SB1507 scorecard | PASS |
| Lipozem + SB1507 live | PASS |
| Primary-10 battery | PASS (263 claims rows 3–10; Huang Squawk swap) |

Details: [BATTERY_RESULTS_v3.md](BATTERY_RESULTS_v3.md) · [RELEASE_TEST_MATRIX_v3.md](RELEASE_TEST_MATRIX_v3.md).

## Product morph

From a single “truthfulness report” to layered **claim + evidence + action** objects. Marketing line: **risk platform, not lie detector.**

## Commercial placement

| Layer | Owner |
|-------|-------|
| Engine + research sleeves | OSS Apache |
| Predictions / RiskFactor sensors | OSS `verityngn[predictions]` |
| Disclosure engine (rfkit) | OSS sleeve Phase 1 |
| Control plane / gallery / billing | verityindex.com |
| ClearFactor vault + counsel briefs | Paid services |

## Operator ship gate (blocked until explicit ask)

1. Clean-venv install smoke  
2. Retag `v3.0.0` → final SHA  
3. Merge `release/v3.0.0` → `main`  
4. PyPI publish + GitHub release assets  

## Read next

- [PLATFORM_OVERVIEW.md](../platform/PLATFORM_OVERVIEW.md)
- [COMMERCIAL_MAP.md](../platform/COMMERCIAL_MAP.md)
- Series part 9: [09-report-to-platform.md](../blog/series/09-report-to-platform.md)
- Derrick platform brief (unsent): `rfkit/consulting/PLATFORM_BRIEF_OSS.md`
