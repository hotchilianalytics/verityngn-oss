# Part 9 — From truthfulness report to claim-risk platform

**Series:** VerityNgn OSS  
**Part 9 of 9**  
**Status:** DRAFT · 2026-10-19 platform refresh

---

## Thesis

A single HTML “truthfulness report” is the wrong product unit for 2026. The durable artifact is a **claim + evidence + action** object inside a layered platform: open engine, domain packs, agent surface, hosted control plane, paid apps.

## The morph

| Report product | Platform product |
|----------------|------------------|
| One PDF per video | Evidence registry entries |
| “Is it true?” | “What residual risk remains, and what action?” |
| CRAAP-only §9 | Domain packs (CRAAP, SIFT, disclosure, legal, health, brand) |
| CLI only | CLI + hosted runs + MCP/skills (3.1) |
| Closed predictions | Sensors in OSS; apps on verityindex.com |

Full layer diagram: [PLATFORM_OVERVIEW.md](../../platform/PLATFORM_OVERVIEW.md).

## Why this matches the market

- **LangChain pattern:** open stack + hosted control plane (LangSmith).  
- **Governance pattern:** packs + evidence trails (Credo / Holistic / Arthur) — we apply packs to *claim domains*, not model GRC.  
- **Glimmer pattern:** decision delivery over data acquisition — we own “connect the dots” and “own-context ground truth” for disclosure and media claims; we refuse crawl/surveil.

Landscape notes: [PLATFORM_LANDSCAPE_2026.md](../../platform/PLATFORM_LANDSCAPE_2026.md).

## Where ClearFactor / Derrick fit

Disclosure RiskFactor (Item 1A hedge ↔ dated own admission) is a **domain pack** with counsel actions Rewrite / Keep / Move / Remove. The matcher engine opens Apache; private vault and counsel briefs stay ClearFactor services. That is the same open-core rule as video: quality in OSS, operations paid.

## What readers should try

```bash
verityngn analyze --tier full '<url>' --deep
```

Then read the platform overview and the primary-10 battery results — not a new accuracy slogan.

## Cite

- [`docs/platform/`](../../platform/)
- [`docs/launch/BATTERY_RESULTS_v3.md`](../../launch/BATTERY_RESULTS_v3.md)
- [`docs/launch/EXEC_SUMMARY_v3.md`](../../launch/EXEC_SUMMARY_v3.md)

---

*Previous: [Part 8](08-open-core-after-absorb.md) · Series index: [README](README.md)*
