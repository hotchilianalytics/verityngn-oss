# RELEASE_TEST_MATRIX v3.0.0

**Candidate SHA:** `8d6a8e3` (predictions/RiskFactor absorb; prior density/SIFT work included)  
**Branch:** `release/v3.0.0`  
**Date:** 2026-10-07  
**Package version:** 3.0.0  
**Video slate:** [`OSS_RELEASE_VIDEO_SLATE_v3.md`](OSS_RELEASE_VIDEO_SLATE_v3.md)

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

## Live (primary-10 expansion — PENDING)

Frozen until hummingbot hackathon clear. Runner: `scripts/run_release_v3_battery.sh` → `outputs/release_v3_battery_<date>/`.

| Gate | Fixture | Pass criteria | Result | Notes |
|------|---------|---------------|--------|-------|
| Karp CEO short | `V7mYWOzdhpc` full+deep | claims>0; talking-head extract | **PENDING** | predictions sleeve face+voice |
| Karp+Huang dual | `ijRuuaaM6XM` full+deep | claims>0; dual-speaker | **PENDING** | fusion / two-speaker |
| Huang CES keynote | `fuq0Ncdsknk` full+deep | claims>0; long-form coverage | **PENDING** | duration / exhibits |
| Karp WEF long | `dRgPbNJ5RJc` full+deep | claims>0; Q/A arcs | **PENDING** | long interview |
| Nadella Stargate | `lb_ZJylekWo` full+deep | claims>0; third CEO player | **PENDING** | `ceo_msft_nadella` |
| Odd Lots podcast | `tSdWpsj1Cyo` full+deep | claims>0; finance-podcast mix | **PENDING** | non-CEO genre |
| Butler Kahn deposition | `7MXE1kDCY-k` full+deep | claims>0; legal spoken | **PENDING** | deposition cadence |
| Carney peptides | `RuinHdlpXvE` full+deep | claims>0; CI preferred | **PENDING** | health counter-intel |

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
| Predictions primary-10 battery | **PENDING** — freeze until hackathon clear |
| Marketing / retag / merge / PyPI | **Blocked on operator ask** after primary-10 green (or operator accepts PENDING expansion) |

## Operator decision

1. Proven CRAAP + SIFT densify + predictions absorb are on `8d6a8e3`.
2. Primary-10 battery is lined up in the slate; do not start Vertex until hackathon clear.
3. Retag / merge / PyPI only on **explicit ask**.
