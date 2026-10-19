# RELEASE_TEST_MATRIX v3.0.0

**Candidate SHA:** `e8cb7d8` (docs/slate; predictions absorb `8d6a8e3`)  
**Branch:** `release/v3.0.0`  
**Date:** 2026-10-18  
**Package version:** 3.0.0  
**Video slate:** [`OSS_RELEASE_VIDEO_SLATE_v3.md`](OSS_RELEASE_VIDEO_SLATE_v3.md)  
**Battery results:** [`BATTERY_RESULTS_v3.md`](BATTERY_RESULTS_v3.md)

## Offline

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Claim-kind unit tests | `pytest test/unit/test_claim_kind.py -q` | **PASS** | 15 passed |
| Signal engine + derailment | `pytest test/unit/test_signal_engine.py test/unit/test_derailment.py -q` | **PASS** | absorbed with predictions |
| Open-core boundary | `python scripts/ci/open_core_boundary_scan.py` | **PASS** | commercial markers scrub (research packages allowed) |
| SB1507 taxonomy scorecard (Sep 23 smoke JSON) | `python scripts/sb1507_risk_taxonomy_scorecard.py` | **PASS** | 28 claims; §6.1=13; quant→inference 83.3%; `all_green=true` |
| Predictions import smoke | `from verityngn.services.predictions import run_predictions_pilot` | **PASS** | + quant/fusion imports; pilot offline smoke ok |

## Live (proven)

| Gate | Fixture | Pass criteria | Result | Notes |
|------|---------|---------------|--------|-------|
| Lipozem old ladder | `tLJC8hkK-ao` full+deep → `outputs/release_v3_lipozem` | claims>0; genre `consumer_factual`; §9 CRAAP; `deep.html`; clinical % stays `source_backed_fact` | **PASS** | 40 claims; CRAAP §9; `deep.html` |
| Lipozem light (supplemental) | `--tier light` → `outputs/release_v3_lipozem_light` | DR-direct completes | **PASS** | `*_direct_risk_report.html` |
| SB1507 analyst lanes | local `sb1507.mp4` → `outputs/release_v3_sb1507_dense` | claims>0; genre `analyst`; §9 SIFT; chips; §6.1 ≤ half; scorecard green | **PASS** | 50→40 claims; §6.1=16/40; quant→inference 88.9% |
| Vertex / 0-claims stop | either run | Fix `VERTEX_LOCATION=global` if 0 claims | **PASS** | google.genai + dense local prompt |

## Live (primary-10 expansion — PASS)

Runner: `scripts/run_release_v3_battery.sh` → `outputs/release_v3_battery_2026-10-18/`.

| Gate | Fixture | Pass criteria | Result | Notes |
|------|---------|---------------|--------|-------|
| Karp CEO short | `V7mYWOzdhpc` full+deep | claims>0; talking-head extract | **PASS** | 37 claims; `deep.html` |
| Karp+Huang dual | `ijRuuaaM6XM` full+deep | claims>0; dual-speaker | **PASS** | 32 claims; `deep.html` |
| Huang CEO (swap) | `cP8pfCJTw4Q` full+deep | claims>0 | **PASS** | 16 claims; replaced `fuq0Ncdsknk` (12h LIVE) |
| Karp WEF long | `dRgPbNJ5RJc` full+deep | claims>0; Q/A arcs | **PASS** | 40 claims |
| Nadella Stargate | `lb_ZJylekWo` full+deep | claims>0; third CEO player | **PASS** | 19 claims |
| Odd Lots podcast | `tSdWpsj1Cyo` full+deep | claims>0; finance-podcast mix | **PASS** | 40 claims |
| Butler Kahn deposition | `7MXE1kDCY-k` full+deep | claims>0; legal spoken | **PASS** | 39 claims |
| Carney peptides | `RuinHdlpXvE` full+deep | claims>0; CI preferred | **PASS** | 40 claims |

## Scorecard thresholds (analyst fixture)

| Threshold | Offline smoke | Live `release_v3_sb1507_dense` |
|-----------|---------------|--------------------------------|
| quant→inference ≥60% | 83.3% PASS | 88.9% PASS |
| §6.1 ≤ half total | 13/28 PASS | 16/40 PASS |
| no future→LIKELY_FALSE | PASS | PASS |
| deeper not flooded | PASS | PASS |

## Sign-off

| Role | Status |
|------|--------|
| Offline gates | **PASS** |
| Lipozem live (old features) | **PASS** |
| SB1507 live (analyst + density) | **PASS** |
| Predictions primary-10 battery | **PASS** — `outputs/release_v3_battery_2026-10-18` (Huang Squawk swap) |
| Marketing / retag / merge / PyPI | **Blocked on operator ask** — matrix primary-10 green |

## Operator decision

1. Proven CRAAP + SIFT densify + predictions absorb on `8d6a8e3`; battery docs on `e8cb7d8`.
2. Primary-10 battery **PASS** with documented Huang swap (`fuq0Ncdsknk` → `cP8pfCJTw4Q`).
3. Retag / merge / PyPI only on **explicit ask**.
