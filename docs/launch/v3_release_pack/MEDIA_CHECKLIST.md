# Media pack checklist — VerityNgn OSS v3.0.0 launch

Use this list before HN / Reddit / LinkedIn / X posts.  
**Do not post on the same day as the live test run.**  
**Candidate:** `b13bcf1` · matrix: [`../RELEASE_TEST_MATRIX_v3.md`](../RELEASE_TEST_MATRIX_v3.md) · slate: [`../OSS_RELEASE_VIDEO_SLATE_v3.md`](../OSS_RELEASE_VIDEO_SLATE_v3.md) · results: [`../BATTERY_RESULTS_v3.md`](../BATTERY_RESULTS_v3.md) · platform: [`../../platform/PLATFORM_OVERVIEW.md`](../../platform/PLATFORM_OVERVIEW.md)

## Core assets

- [ ] Release paper PDF: `papers/verityngn_oss_v3_release.pdf` (rebuild: `bash scripts/render_release_paper_pdf.sh`)
- [x] White paper one-pager: `docs/launch/v3_release_pack/WHITE_PAPER_ONE_PAGER.md` (refreshed)
- [x] Architecture figure: `papers/figures/open_core_architecture.png`
- [x] Platform layers figure: `papers/figures/platform_layers.png`
- [x] Gallery charts: `papers/figures/gallery_*.png`
- [x] Series charts: `docs/blog/series/assets/01_history_timeline.png`
- [x] Series charts: `docs/blog/series/assets/02_before_after_density.png` (**primary Reddit image**)
- [x] Series charts: `docs/blog/series/assets/03_kind_mix.png`
- [x] Series charts: `docs/blog/series/assets/04_three_reports.png`
- [x] Classification diagram: `docs/blog/assets/verityngn-claim-classification-diagram.png`

## Copy drafts

- [x] Series: `docs/blog/series/01`–`04` (+ README)
- [ ] Series Wave B: `05`–`08` + Part 9 platform morph (fill in this refresh)
- [ ] Chris walkthrough: `docs/blog/analyst_risk_taxonomy_chris_review_2026-09-25.md` (private share until approved)
- [x] Blog: `docs/launch/BLOG_POST.md` (full features / benefits / applications; pack copy synced)
- [x] HN: `docs/launch/v3_release_pack/HN_POST.md`
- [x] Reddit: pack README
- [x] X thread: `docs/launch/v3_release_pack/X_THREAD.md`
- [x] LinkedIn: `docs/launch/v3_release_pack/LINKEDIN_POST.md`
- [ ] Exec summary: `docs/launch/EXEC_SUMMARY_v3.md`

## Demo

- [x] Lipozem public: `outputs/release_v3_lipozem` (CRAAP / deep.html)
- [x] SB1507 internal: `outputs/release_v3_sb1507_dense` (SIFT / chips) — **no public full HTML without Chris OK**
- [x] Primary-10: `outputs/release_v3_battery_2026-10-18`
- [ ] Tutorial script: `docs/launch/DEMO_VIDEO_SCRIPT.md`
- [ ] Optional screen capture: light then full+deep
- [x] Operator tip: `verityngn captions <url>` with fresh cookies

## Technical gates (release matrix)

- [x] Offline: `pytest test/unit/test_claim_kind.py`
- [x] Offline: `python scripts/ci/open_core_boundary_scan.py`
- [x] Offline: `python scripts/sb1507_risk_taxonomy_scorecard.py`
- [x] Live Lipozem full+deep (**PASS**)
- [x] Live SB1507 local-full dense (**PASS**)
- [x] Density gate cleared
- [x] Primary-10 battery (**PASS**)
- [ ] `PARITY_TEST_v3.md` optional after live
- [ ] Paper PDF rebuild if figures changed
- [ ] `pip install` smoke in clean venv (**no PyPI publish until operator go**)
- [ ] **Do not post** until operator clears; stagger 1–2 days; Chris full HTML gated
- [ ] Retag / merge / PyPI — **explicit operator ask only**

## Staggered posting order (1–2 days apart)

1. r/MachineLearning `[P]` — method + density chart + **one** repo/branch link  
2. r/LanguageTechnology — six kinds + dual metrics  
3. r/opensource — install, Apache-2.0, open-core boundary  
4. r/OSINT — SIFT vs CRAAP, counter-intel (no hype)  
5. HN → then X → LinkedIn (same claims, shorter)

Public proof: gallery or Lipozem. SB1507 full report gated.

## Honest messaging locks

- Not lie detector / not earnings prediction
- Risk platform / claim-level abatement — not “truth score”
- Two RiskFactor names: video sensors (OSS) vs ClearFactor disclosure (engine OSS / services paid)
- Lipozem-class VSL = weak multimodal proof
- YouTube API key ≠ `.en.vtt` for third-party videos
- One primary link per post
- Do not claim tag/`pip install verityngn==3.0.0` until retag + publish

## Links

| Asset | URL |
|-------|-----|
| GitHub branch | https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0 |
| Gallery | https://verityindex.com/gallery |
| Streamlit demo | https://verityngn.streamlit.app |
| PyPI | only after explicit publish |
