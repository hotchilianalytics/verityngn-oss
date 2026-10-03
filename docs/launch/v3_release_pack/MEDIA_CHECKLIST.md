# Media pack checklist — VerityNgn OSS v3.0.0 launch

Use this list before HN / Reddit / LinkedIn / X posts.  
**Do not post on the same day as the live test run.**  
**Candidate:** `e12a55b` · matrix: [`../RELEASE_TEST_MATRIX_v3.md`](../RELEASE_TEST_MATRIX_v3.md)

## Core assets

- [ ] Release paper PDF: `papers/verityngn_oss_v3_release.pdf` (rebuild: `bash scripts/render_release_paper_pdf.sh`)
- [ ] White paper one-pager: `docs/launch/v3_release_pack/WHITE_PAPER_ONE_PAGER.md`
- [ ] Architecture figure: `papers/figures/open_core_architecture.png`
- [ ] Gallery charts: `papers/figures/gallery_*.png`
- [ ] Series charts: `docs/blog/series/assets/01_history_timeline.png`
- [ ] Series charts: `docs/blog/series/assets/02_before_after_density.png` (**primary Reddit image**)
- [ ] Series charts: `docs/blog/series/assets/03_kind_mix.png`
- [ ] Series charts: `docs/blog/series/assets/04_three_reports.png`
- [ ] Classification diagram: `docs/blog/assets/verityngn-claim-classification-diagram.png`

## Copy drafts

- [ ] Series: `docs/blog/series/01`–`04` (+ README)
- [ ] Chris walkthrough: `docs/blog/analyst_risk_taxonomy_chris_review_2026-09-25.md` (private share until approved)
- [ ] Blog: `docs/launch/v3_release_pack/BLOG_POST.md`
- [ ] HN: `docs/launch/v3_release_pack/HN_POST.md`
- [ ] Reddit: `docs/launch/REDDIT_POSTS.md` / pack README
- [ ] X thread: `docs/launch/v3_release_pack/X_THREAD.md`
- [ ] LinkedIn: `docs/launch/v3_release_pack/LINKEDIN_POST.md`

## Demo

- [ ] Lipozem public: `outputs/release_v3_lipozem` (CRAAP / deep.html)
- [ ] SB1507 internal: `outputs/release_v3_sb1507` (SIFT / chips) — **no public full HTML without Chris OK**
- [ ] Tutorial script: `docs/launch/DEMO_VIDEO_SCRIPT.md`
- [ ] Optional screen capture: light then full+deep
- [ ] Operator tip: `verityngn captions <url>` with fresh cookies

## Technical gates (release matrix)

- [x] Offline: `pytest test/unit/test_claim_kind.py`
- [x] Offline: `python scripts/ci/open_core_boundary_scan.py`
- [x] Offline: `python scripts/sb1507_risk_taxonomy_scorecard.py`
- [x] Live Lipozem full+deep (**PASS** — CRAAP / 40 facts / deep.html)
- [~] Live SB1507 local-full (**PARTIAL** — SIFT/chips/genre OK; claim under-recall 5 vs 28)
- [ ] Operator accept PARTIAL density **or** re-run SB1507 for §6.1 ≤ half
- [ ] `PARITY_TEST_v3.md` optional after live
- [ ] Paper PDF rebuild if figures changed
- [ ] `pip install` smoke in clean venv (**no PyPI publish until operator go**)
- [ ] **Do not post** until operator clears matrix; stagger 1–2 days; Chris full HTML gated
## Staggered posting order (1–2 days apart)

1. r/MachineLearning `[P]` — method + density chart + **one** repo/branch link  
2. r/LanguageTechnology — six kinds + dual metrics  
3. r/opensource — install, Apache-2.0, open-core boundary  
4. r/OSINT — SIFT vs CRAAP, counter-intel (no hype)  
5. HN → then X → LinkedIn (same claims, shorter)

Public proof: gallery or Lipozem. SB1507 full report gated. Commercial batch pin is **follow-on**, not this announcement ([`OSS_BATCH_COMMERCIAL_PROMOTION.md`](../OSS_BATCH_COMMERCIAL_PROMOTION.md)).

## Honest messaging locks

- Not lie detector / not earnings prediction
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
