# Part 7 — Ten-video battery

**Series:** VerityNgn OSS  
**Part 7 of 8**  
**Status:** DRAFT — results from `outputs/release_v3_battery_2026-10-18`  
**Full table:** [`docs/launch/BATTERY_RESULTS_v3.md`](../../launch/BATTERY_RESULTS_v3.md)

---

## Thesis

One CRAAP video and one SIFT video are not enough after the predictions absorb. The primary 10 prove genre lanes, CEO multi-player coverage, legal, podcast, and health CI — without publishing private full HTML.

## Coverage matrix (what each gate proves)

| # | Fixture | Lane proved | Claims |
|---|---------|-------------|--------|
| 1 | Lipozem | Consumer CRAAP / gallery continuity | 39 |
| 2 | SB1507 local | Analyst SIFT + density + taxonomy | 40 |
| 3 | Karp CNBC short | CEO talking-head extract | 37 |
| 4 | Karp + Huang | Dual-speaker / fusion adjacency | 32 |
| 5 | Huang Squawk (swap) | Third NVDA CEO cut without LIVE restream | 16 |
| 6 | Karp WEF | Long interview Q/A arcs | 40 |
| 7 | Nadella Squawk | Third pilot CEO (`ceo_msft_nadella`) | 19 |
| 8 | Odd Lots | Finance podcast mix | 40 |
| 9 | Butler Kahn | Legal deposition cadence | 39 |
| 10 | Carney peptides | Health counter-intel | 40 |

## Pass/fail after battery

All ten **PASS** on claims>0. Live rows 3–10: **263 claims** total.  
`deep.html` confirmed on Lipozem, SB1507, Karp short, dual-CEO; later rows often soft-missed combined Deep Research (`report.regen` import gap) while standard reports still wrote.

**Documented swap:** primary Huang CES ID `fuq0Ncdsknk` is a ~12h CNBC-TV18 LIVE restream. Segment 1 extracted; later segments Vertex 500 INTERNAL. Replaced with slate backup #15 `cP8pfCJTw4Q` (339s Squawk).

## What we skip publicly

- Chris / SB1507 full HTML gated  
- No per-video probability banners in launch posts  
- No claim that every row has `deep.html` until regen path is fixed  

## Backup 20

Pull when a primary geo-blocks, duration-pollutes, or needs a second consumer CRAAP demo. See slate backup table.

## Reproduce

```bash
export VERTEX_LOCATION=global
# Optional: skip already-proven Lipozem + SB1507
SKIP_PRIOR=1 bash scripts/run_release_v3_battery.sh
```

Copy the script to `$BATTERY_OUT/run_battery_frozen.sh` before multi-hour runs so mid-session edits cannot break bash.

## Cite

- [`docs/launch/OSS_RELEASE_VIDEO_SLATE_v3.md`](../../launch/OSS_RELEASE_VIDEO_SLATE_v3.md)
- [`docs/launch/RELEASE_TEST_MATRIX_v3.md`](../../launch/RELEASE_TEST_MATRIX_v3.md)
- [`docs/launch/BATTERY_RESULTS_v3.md`](../../launch/BATTERY_RESULTS_v3.md)

---

*Previous: [Part 6](06-ceo-audio-video-lanes.md) · Next: [Part 8](08-open-core-after-absorb.md)*
