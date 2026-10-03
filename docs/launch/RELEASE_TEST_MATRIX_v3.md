# RELEASE_TEST_MATRIX v3.0.0

**Candidate SHA:** `5258292` (`52582924fb35bc547c25f15a6f518580226689ba`)  
**Branch:** `release/v3.0.0`  
**Date:** 2026-10-03  
**Package version:** 3.0.0

Gates for retag / merge / PyPI. Do not expand to the full `test_videos.json` list for this cut.

## Offline

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Claim-kind unit tests | `pytest test/unit/test_claim_kind.py -q` | **PASS** | 12 passed (kinds, chips, tL ladder, analyst vs consumer genre) |
| Open-core boundary | `python scripts/ci/open_core_boundary_scan.py` | **PASS** | clean |
| SB1507 taxonomy scorecard (Sep 23 smoke JSON) | `python scripts/sb1507_risk_taxonomy_scorecard.py` | **PASS** | 28 claims; §6.1=13; quant→inference 83.3%; `all_green=true` |

## Live (two videos)

| Gate | Fixture | Pass criteria | Result | Notes |
|------|---------|---------------|--------|-------|
| Lipozem old ladder | `tLJC8hkK-ao` full+deep | claims>0; genre `consumer_factual`; §9 CRAAP; `deep.html` present; clinical % stays `source_backed_fact` | **PENDING** | `outputs/release_v3_lipozem` |
| SB1507 analyst lanes | local `sb1507.mp4` local-full | claims>0; genre `analyst`; §9 SIFT; §6.1 ≤ half; risk chips on data-derived; scorecard green on **new** report JSON | **PENDING** | `outputs/release_v3_sb1507` |
| Vertex / 0-claims stop | either run | If claims==0, stop and fix `VERTEX_LOCATION=global` (not a taxonomy bug) | **PENDING** | |

## Scorecard thresholds (analyst fixture)

- quant/method → `data_derived_inference` ≥ 60%
- §6.1 rows ≤ half of total claims
- deeper sleeve not dominated by generic UNCERTAIN facts
- zero predictions labeled LIKELY_FALSE solely for being future-dated

## Sign-off

| Role | Status |
|------|--------|
| Offline gates | **PASS** (2026-10-03) |
| Live gates | pending |
| Marketing / retag | blocked until live all pass + explicit operator ask |
