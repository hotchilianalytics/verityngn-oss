# Part 9 — From truthfulness report to claim-risk platform

**Series:** VerityNgn OSS  
**Part 9 of 9**  
**Status:** DRAFT · 2026-11-13 · package **`verityngn==3.0.1`** · launch Monday Nov 23, 2026

---

## Thesis

A single HTML “truthfulness report” is the wrong product unit for 2026. The durable artifact is a **claim + evidence + action** object inside a layered platform: open engine, domain packs, agent surface, hosted control plane, paid apps — with **pixel risk** (adaptive 1–6 fps, brand-safety/exhibit sidecars) live default-on in 3.0.1 and congruence sleeves graduating default-on in 3.1/3.2.

## The morph

| Report product | Platform product |
|----------------|------------------|
| One PDF per video | Evidence registry entries (+ `brand_safety_scores.json` / exhibit maps) |
| “Is it true?” | “What residual risk remains, and what action?” |
| CRAAP-only §9 | Domain packs (CRAAP, SIFT, disclosure, legal, health, brand) |
| CLI only | CLI + hosted runs + MCP/skills (3.1) |
| Closed predictions | Sensors in OSS; apps on verityindex.com |
| Transcript-only | Pixel modalities live in 3.0.1; object/action + pose/lip congruence in 3.1/3.2 |

Full layer diagram: [PLATFORM_OVERVIEW.md](../../platform/PLATFORM_OVERVIEW.md).

## Why this matches the market

- **LangChain pattern:** open stack + hosted control plane (LangSmith).  
- **Governance pattern:** packs + evidence trails (Credo / Holistic / Arthur) — we apply packs to *claim domains*, not model GRC.  
- **Glimmer pattern:** decision delivery over data acquisition — we own “connect the dots” and “own-context ground truth” for disclosure and media claims; we refuse crawl/surveil.

Landscape notes: [PLATFORM_LANDSCAPE_2026.md](../../platform/PLATFORM_LANDSCAPE_2026.md).

## Where ClearFactor / Derrick fit

Disclosure RiskFactor (Item 1A hedge ↔ dated own admission) is a **domain pack** with counsel actions Rewrite / Keep / Move / Remove. The matcher engine opens Apache; private vault and counsel briefs stay ClearFactor services. That is the same open-core rule as video: quality in OSS, operations paid.

## Multimodal futures on the same platform spine

S00–S15 heritage (Spot Runner, Mayew, Banker HFAsy, Krykoniuk, Kim disclosure) plus negative-result hygiene merges with new scene research:

| Stage | Default-on |
|-------|------------|
| **3.0.1 (now)** | Visual text / exhibits / brand-safety · 81 pixel claims (10 runs) · 45% SB1507 |
| **3.1** | Object / prop / action semantics · visual–spoken contradiction · splice risk |
| **3.2** | Pose / lip / face / audio congruence (MediaPipe + MultiSense sleeves already in the wheel) |

Capstone brief: [MULTIMODAL_AND_FUTURES_v3.md](../../launch/v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md).

## What readers should try

```bash
pip install 'verityngn[deep]==3.0.1'
verityngn analyze --tier full '<url>' --deep
```

Then read the platform overview, the primary-10 battery, and the multimodal futures brief — not a new accuracy slogan.

## Cite

- [`docs/platform/`](../../platform/)
- [`docs/launch/BATTERY_RESULTS_v3.md`](../../launch/BATTERY_RESULTS_v3.md)
- [`docs/launch/EXEC_SUMMARY_v3.md`](../../launch/EXEC_SUMMARY_v3.md)
- [`docs/launch/v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md`](../../launch/v3_release_pack/MULTIMODAL_AND_FUTURES_v3.md)

---

*Previous: [Part 8](08-open-core-after-absorb.md) · Series index: [README](README.md)*
