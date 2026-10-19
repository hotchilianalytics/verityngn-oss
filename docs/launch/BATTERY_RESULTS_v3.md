# Primary-10 battery results — OSS v3.0.0

**Run dir:** `outputs/release_v3_battery_2026-10-18/`  
**Branch:** `release/v3.0.0` @ `e8cb7d8`  
**Env:** `VERTEX_LOCATION=global`  
**Completed:** 2026-10-18T09:47:18Z  
**Script:** `scripts/run_release_v3_battery.sh`  
**Slate:** [`OSS_RELEASE_VIDEO_SLATE_v3.md`](OSS_RELEASE_VIDEO_SLATE_v3.md)  
**Matrix:** [`RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md)

## Verdict

Primary-10 **GREEN** (with one documented Huang swap). All rows claims>0; no retag/merge/PyPI until operator ask.

## Summary table

| # | ID | Title | Claims | Status | Notes |
|---|-----|-------|--------|--------|-------|
| 1 | `tLJC8hkK-ao` | Lipozem | 39 | **PASS** (prior) | `outputs/release_v3_lipozem`; CRAAP; `deep.html` |
| 2 | `sb1507` local | SB1507 Oregon QSBS | 40 | **PASS** (prior) | `outputs/release_v3_sb1507_dense`; SIFT; §6.1=16/40 |
| 3 | `V7mYWOzdhpc` | Karp CNBC tech dominance | 37 | **PASS** | CEO short; `deep.html` |
| 4 | `ijRuuaaM6XM` | Karp + Huang Power Lunch | 32 | **PASS** | Dual-CEO; `deep.html` |
| 5 | `cP8pfCJTw4Q` | Huang Squawk AMD/OpenAI | 16 | **PASS** (swap) | Replaced `fuq0Ncdsknk` (12h LIVE restream; Vertex 500 after seg1). Slate backup #15 |
| 6 | `dRgPbNJ5RJc` | Karp WEF 2026 | 40 | **PASS** | Long interview; report synced from `outputs_debug` |
| 7 | `lb_ZJylekWo` | Nadella Stargate Squawk | 19 | **PASS** | Third CEO player |
| 8 | `tSdWpsj1Cyo` | Odd Lots Franchise | 40 | **PASS** | Finance podcast |
| 9 | `7MXE1kDCY-k` | Butler Kahn deposition | 39 | **PASS** | Legal spoken |
| 10 | `RuinHdlpXvE` | Carney Peptides Lab | 40 | **PASS** | Health CI |

**Live battery claim total (rows 3–10):** 263

## Operational notes

1. **CLI:** URL is positional (`verityngn analyze --tier full URL`), not `-u`.
2. **Proxy:** Keep Cursor sandbox `HTTP(S)_PROXY` — unsetting it breaks Vertex OAuth DNS.
3. **yt-dlp:** May 403 through sandbox proxy; YouTube Data API + Vertex URL analysis still succeed.
4. **Artifact sync:** Some runs write `*_report.json` only under `outputs_debug/<id>/<timestamp>_complete/`. Battery `count_claims` syncs those into the pack dir and falls back to `*_metrics.json` / `*_claims_detailed.json`.
5. **Deep Research:** `deep.html` present for Lipozem/SB1507/Karp short/dual-CEO. Later rows often missed combined deep (`No module named 'verityngn.services.report.regen'`) — standard report + claims still gate.
6. **PDF:** Playwright Chromium missing in this agent environment — HTML/MD/JSON still gate; PDF soft-fail.
7. **Frozen script:** Copy runner to `$OUT/run_battery_frozen.sh` before long runs; do not edit the live script mid-process.

## Swap detail

See `outputs/release_v3_battery_2026-10-18/SWAP_NOTES.md`.

## Sign-off

Primary-10 green (with Huang swap) → operator may ask for retag / merge / PyPI. Ship clicks remain gated on explicit ask.
