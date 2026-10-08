# OSS release video slate v3.0.0

**Branch:** `release/v3.0.0`  
**Candidate SHA:** `8d6a8e3` (predictions/RiskFactor absorb)  
**Constraint:** No live Vertex / mass yt-dlp until hummingbot hackathon work is clear. This doc lines up fixtures only.

**Matrix:** [`RELEASE_TEST_MATRIX_v3.md`](RELEASE_TEST_MATRIX_v3.md)  
**Battery script (ready, not run):** `scripts/run_release_v3_battery.sh`  
**Outputs (when runs resume):** `outputs/release_v3_battery_<YYYY-MM-DD>/`

## Sherlock selection criteria

1. Feature coverage — each engine/predictions lane at least once in primary 10  
2. Catalog hygiene — prefer IDs in Karp/NVDA catalogs or quality battery  
3. Source-only interviews/keynotes — not react/debunk uploads  

## Primary 10 — run first after hackathon

| # | ID / source | About | Why it made the cut | Gate class |
|---|-------------|-------|---------------------|------------|
| 1 | [`tLJC8hkK-ao`](https://www.youtube.com/watch?v=tLJC8hkK-ao) Lipozem | Consumer weight-loss supplement claims | Regression: CRAAP §9, clinical % as `source_backed_fact`, gallery continuity | Consumer CRAAP |
| 2 | Local `/Users/ajjc/Downloads/sb1507.mp4` | Analyst deep-data legislative / LRO / QSBS | Regression: SIFT, risk chips, §6.1 ≤ half, dense local extract | Analyst SIFT |
| 3 | [`V7mYWOzdhpc`](https://www.youtube.com/watch?v=V7mYWOzdhpc) Karp / CNBC | Pre-print PLTR CEO (tech dominance / DOGE / book) | Primary Karp face+voice panel; T016/T018 continuity | CEO short |
| 4 | [`ijRuuaaM6XM`](https://www.youtube.com/watch?v=ijRuuaaM6XM) Karp + Huang | Dual-CEO partnership interview | Shared Karp+NVDA catalog; fusion + two-speaker affect | CEO dual |
| 5 | [`fuq0Ncdsknk`](https://www.youtube.com/watch?v=fuq0Ncdsknk) Huang CES 2025 | Long NVIDIA product/AI keynote | Duration / exhibits / claims density; Huang player | CEO keynote |
| 6 | [`dRgPbNJ5RJc`](https://www.youtube.com/watch?v=dRgPbNJ5RJc) Karp WEF 2026 | Long WEF stage interview | Existing corpus Q/A arcs; long vs short CNBC | CEO long |
| 7 | [`lb_ZJylekWo`](https://www.youtube.com/watch?v=lb_ZJylekWo) Nadella Squawk | MSFT CEO on OpenAI / Stargate / chips | Third pilot CEO; breaks Karp/Huang monoculture | CEO Nadella |
| 8 | [`tSdWpsj1Cyo`](https://www.youtube.com/watch?v=tSdWpsj1Cyo) Odd Lots | Franchise / gig economy discussion | Finance-podcast claim mix; quality-battery fixture | Podcast |
| 9 | [`7MXE1kDCY-k`](https://www.youtube.com/watch?v=7MXE1kDCY-k) Butler Kahn | Expert deposition sample | Legal spoken-claim path; deposition cadence | Legal |
| 10 | [`RuinHdlpXvE`](https://www.youtube.com/watch?v=RuinHdlpXvE) Scott Carney | Peptides lab investigation | Counter-intel + contested health; source lab piece (not Asprey react) | Health CI |

### Pass criteria by class

| Class | Pass when |
|-------|-----------|
| Consumer | claims>0; genre consumer/CRAAP; `deep.html` |
| Analyst | genre analyst; SIFT §9; chips; scorecard green if method-dense |
| CEO short | claims>0; optional mediapipe/affect on local media |
| CEO long/keynote | claims>0; no 0-claim Vertex failure; temporal coverage not first-minutes-only |
| Legal / podcast / health | claims>0; CI sources>0 preferred |

### Live status

| # | Status | Notes |
|---|--------|-------|
| 1 | **PASS** (prior) | `outputs/release_v3_lipozem` |
| 2 | **PASS** (prior) | `outputs/release_v3_sb1507_dense` |
| 3–10 | **PENDING** | Frozen until hackathon clear |

## Backup 20 — lined up, not first wave

| # | ID / action | Role |
|---|-------------|------|
| 11 | [`xe84cwQJKaE`](https://www.youtube.com/watch?v=xe84cwQJKaE) | Karp Seema Mody — extra print window |
| 12 | [`WBu9Ai6OX3I`](https://www.youtube.com/watch?v=WBu9Ai6OX3I) | Karp Sara Eisen — Q2'26 pre-print |
| 13 | [`pHu-FarYZlU`](https://www.youtube.com/watch?v=pHu-FarYZlU) | Karp Squawk Nvidia deal (~19m) |
| 14 | [`QNkPpVYagRc`](https://www.youtube.com/watch?v=QNkPpVYagRc) | Karp Davos 2024 — S01–S11 only (too old for earnings panel) |
| 15 | [`cP8pfCJTw4Q`](https://www.youtube.com/watch?v=cP8pfCJTw4Q) | Huang Squawk AMD/OpenAI |
| 16 | [`y2ab3A_pBiY`](https://www.youtube.com/watch?v=y2ab3A_pBiY) | Huang Squawk Musk adjacency (same day as 15) |
| 17 | [`xDjbj_sLy_s`](https://www.youtube.com/watch?v=xDjbj_sLy_s) | Huang GTC Washington keynote |
| 18 | [`ZUPJ1ZnIZvE`](https://www.youtube.com/watch?v=ZUPJ1ZnIZvE) | Nadella long-form (~53m) duration stress |
| 19 | [`nvvw0oslqpE`](https://www.youtube.com/watch?v=nvvw0oslqpE) | Brian Panish punitive damages |
| 20 | [`cBtOIRV4uPE`](https://www.youtube.com/watch?v=cBtOIRV4uPE) | Legal videography deposition sample |
| 21 | SB1507 + `VN_AGENTIC_VIDEO=1` | Agentic vs dense-prompt A/B |
| 22 | Lipozem `--tier light` | DR-direct regression (prior PASS) |
| 23–25 | Cook / Musk / AAPL-MSFT fills | From `pilot_ceos.json` — **register trials_ledger before CAR peek** |
| 26–28 | Huang post-print excluded (`gXUGGZU9bSM`, `3ofWIJ2ScjQ`, …) | Negative controls for victory-lap hygiene |
| 29 | Odd Lots alternate | Swap if `tSdWpsj1Cyo` geo-blocks |
| 30 | Second consumer supplement | CRAAP diversity if gallery needs second public demo |

## Catalogs

- [`docs/karp_pre_earnings_videos.json`](../karp_pre_earnings_videos.json)
- [`docs/nvda_pre_earnings_videos.json`](../nvda_pre_earnings_videos.json)
- [`verityngn/services/players/data/pilot_ceos.json`](../../verityngn/services/players/data/pilot_ceos.json)
- Quality battery: [`scripts/run_quality_battery.sh`](../../scripts/run_quality_battery.sh)

## Diagnostics if a slate video fails

- 0 claims → `VERTEX_LOCATION`, genai backend, `target_claims`, local vs YT prompt path  
- Genre wrong → `infer_report_genre` inputs  
- CEO affect empty → media bytes, VAD/ASR stub vs measured  
- Event-study pollution → assert not in `excluded_on_or_post_print`  

## Ship clicks

Retag `v3.0.0` / merge to `main` / PyPI only on **explicit operator ask** after matrix primary-10 green. See matrix Sign-off.
