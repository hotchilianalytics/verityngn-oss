# Media pack checklist — VerityNgn OSS v3.0.0 launch

Use this list before HN / Reddit / LinkedIn / X posts.

## Core assets

- [ ] Release paper PDF: `papers/verityngn_oss_v3_release.pdf` (rebuild: `bash scripts/render_release_paper_pdf.sh`)
- [ ] White paper one-pager: `docs/launch/v3_release_pack/WHITE_PAPER_ONE_PAGER.md`
- [ ] Architecture figure: `papers/figures/open_core_architecture.png`
- [ ] Gallery charts: `papers/figures/gallery_*.png`

## Copy drafts

- [ ] Blog: `docs/launch/v3_release_pack/BLOG_POST.md`
- [ ] HN: `docs/launch/v3_release_pack/HN_POST.md`
- [ ] Reddit: `docs/launch/REDDIT_POSTS.md`
- [ ] X thread: `docs/launch/v3_release_pack/X_THREAD.md`
- [ ] LinkedIn: `docs/launch/v3_release_pack/LINKEDIN_POST.md`

## Demo

- [ ] Tutorial script: `docs/launch/DEMO_VIDEO_SCRIPT.md` (light vs full tier)
- [ ] Record ~5 min screen capture: `verityngn analyze --tier light` then `--tier full --deep`
- [ ] Show Modality column in full report markdown
- [ ] Operator tip: `verityngn captions <url>` with fresh cookies

## Technical gates

- [ ] `pytest test/unit/ -m "not live"`
- [ ] `python scripts/ci/open_core_boundary_scan.py`
- [ ] `scripts/run_vtt_json_dr_ablation.py` → T-ABL-005 compare JSON
- [ ] `PARITY_TEST_v3.md` tier rows signed
- [ ] Paper PDF rebuilt: `bash scripts/render_release_paper_pdf.sh`
- [ ] `pip install` smoke in clean venv (no publish until operator go)

## Honest messaging locks

- Not lie detector / not earnings prediction
- Lipozem-class VSL = weak multimodal proof (cite T-ABL-004)
- YouTube API key ≠ `.en.vtt` for third-party videos

## Links

| Asset | URL |
|-------|-----|
| GitHub | https://github.com/hotchilianalytics/verityngn-oss |
| PyPI | https://pypi.org/project/verityngn/3.0.0/ |
| Streamlit demo | https://verityngn.streamlit.app |
| Gallery | https://verityindex.com/gallery |
