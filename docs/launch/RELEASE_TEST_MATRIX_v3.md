# RELEASE_TEST_MATRIX v3.0.0

**Candidate SHA:** `7e76a5c` + uncommitted local-extract density fix (`analysis.py` prompt wiring) + claim_kind testimony/LRO heuristics  
**Branch:** `release/v3.0.0`  
**Date:** 2026-10-05  
**Package version:** 3.0.0

## Offline

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Claim-kind unit tests | `pytest test/unit/test_claim_kind.py -q` | **PASS** | 15 passed |
| Open-core boundary | `python scripts/ci/open_core_boundary_scan.py` | **PASS** | clean (prior freeze) |
| SB1507 taxonomy scorecard (Sep 23 smoke JSON) | `python scripts/sb1507_risk_taxonomy_scorecard.py` | **PASS** | 28 claims; §6.1=13; quant→inference 83.3%; `all_green=true` |

## Live

| Gate | Fixture | Pass criteria | Result | Notes |
|------|---------|---------------|--------|-------|
| Lipozem old ladder | `tLJC8hkK-ao` full+deep → `outputs/release_v3_lipozem` | claims>0; genre `consumer_factual`; §9 CRAAP; `deep.html`; clinical % stays `source_backed_fact` | **PASS** | 40 claims; all `source_backed_fact`; CRAAP §9; `deep.html` present |
| Lipozem light (supplemental) | `--tier light` → `outputs/release_v3_lipozem_light` | DR-direct completes | **PASS** | `*_direct_risk_report.html` |
| SB1507 analyst lanes | local `sb1507.mp4` local-full+deep → `outputs/release_v3_sb1507_dense` | claims>0; genre `analyst`; §9 SIFT; risk chips; §6.1 ≤ half; scorecard green on **new** JSON | **PASS** | Extracted **50** → verified **40** (was 5). SIFT §9; 40/40 chips; deep completed. Scorecard `all_green=true` (§6.1=16/40; quant→inference 88.9%). Prior thin run kept at `outputs/release_v3_sb1507` for comparison. |
| Vertex / 0-claims stop | either run | Fix `VERTEX_LOCATION=global` if 0 claims | **PASS** | Local path: google.genai + dense prompt actually sent (was dead-code stub with literal `{target_claims}`). |

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
| SB1507 live (new features + density) | **PASS** |
| Marketing / retag | **Ready for operator ask** — explicit ask still required for retag / merge to main / PyPI |

## Operator decision

1. Dense SB1507 live extract cleared the density + §6.1 gates (`outputs/release_v3_sb1507_dense`).
2. Commit the local-extract prompt wiring + claim_kind heuristics when ready.
3. Retag / merge / PyPI only on explicit ask.
