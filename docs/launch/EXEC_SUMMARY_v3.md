# Executive summary — VerityNgn OSS 3.0.1

**Date:** 2026-11-13 · **Launch lock:** Monday Nov 16, 2026 · **Package:** `verityngn==3.0.1` on PyPI · **Engine tip:** `1b2cca8` · Examples: [`EXAMPLES.md`](EXAMPLES.md) · Multimodal: [`v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md`](v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md)

## One sentence

VerityNgn 3.0.1 ships an Apache multimodal **claim-risk engine** (adaptive 1–6 fps, pixel claims, brand-safety/exhibit sidecars, Deep Research, six claim kinds, CRAAP/SIFT) as the open core of a **risk platform**: domain packs, agent surface, hosted control plane on verityindex.com, and ClearFactor as the first paid disclosure app — install via **`pip install 'verityngn[deep]==3.0.1'`**.

## Proof

| Gate | Result |
|------|--------|
| Offline unit / boundary / SB1507 scorecard | PASS · **18/40 (45%)** pixel-only on SB1507 |
| Lipozem + SB1507 live | PASS · silent credential/testimonial cards extracted |
| Pixel benchmark | **81** visual_text/graphic/chart/demonstration claims |
| Primary-10 battery | PASS |
| PyPI `3.0.1` | Live + secret-scan PASS (immutable for Nov 16) |
| PyPI `3.0.0` | Yanked (do not pin) |

**Roadmap callout:** 3.1 object/action semantics + visual–spoken contradiction · 3.2 pose/lip/audio congruence (MediaPipe + MultiSense sleeves already in the wheel).

Details: [BATTERY_RESULTS_v3.md](BATTERY_RESULTS_v3.md) · [RELEASE_NOTES_v3.0.1.md](RELEASE_NOTES_v3.0.1.md) · [MULTIMODAL_AND_FUTURES_v3.md](v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md).

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

## Go-now

1. Public posts use PyPI **3.0.1** install lock ([`v3_release_pack/`](v3_release_pack/README.md))  
2. Commit packaging + pack updates; optional GitHub `v3.0.1` tag  
3. Do **not** merge `release/v3.0.0` → `main` unless explicitly asked  

## Read next

- [PLATFORM_OVERVIEW.md](../platform/PLATFORM_OVERVIEW.md)
- [COMMERCIAL_MAP.md](../platform/COMMERCIAL_MAP.md)
- Series part 9: [09-report-to-platform.md](../blog/series/09-report-to-platform.md)
