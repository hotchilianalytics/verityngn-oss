# Figures + examples kit — OSS 3.0.1 push

Use these existing assets. Do not invent new accuracy charts for social.  
**Package:** `verityngn==3.0.1` · engine tip `1b2cca8` · docs tip `f6aeb2e`. **Gallery:** https://verityindex.com/gallery · **PyPI:** https://pypi.org/project/verityngn/3.0.1/

---

## Primary attach map

| Surface | Prefer this file | Why |
|---------|------------------|-----|
| Reddit r/MachineLearning | `docs/blog/series/assets/02_before_after_density.png` | Density / method, not a product splash |
| Show HN / Lobsters | `papers/figures/platform_layers.png` | Platform morph in one glance |
| LinkedIn | `papers/figures/open_core_architecture.png` | OSS vs hosted boundary |
| X / Bluesky | `papers/figures/platform_layers.png` or `docs/blog/assets/verityngn-claim-classification-diagram.png` | Short + legible at mobile width |
| Blog body | Already linked inside [`BLOG_POST.md`](BLOG_POST.md) | Classification + gallery + open-core |

## Full inventory (repo-relative)

### Papers / release figures

| Path | Use |
|------|-----|
| `papers/figures/platform_layers.png` | L1 engine → packs → control plane |
| `papers/figures/open_core_architecture.png` | What is Apache vs hosted |
| `papers/figures/gallery_live_claims_per_video.png` | Battery / gallery claim volume |
| `papers/figures/gallery_thumb_collage.png` | Visual proof collage (secondary) |
| `papers/figures/gallery_live_label_mix.png` | Verdict mix (optional comment image) |

### Blog / series assets

| Path | Use |
|------|-----|
| `docs/blog/assets/verityngn-claim-classification-diagram.png` | Six claim kinds |
| `docs/blog/series/assets/01_history_timeline.png` | Series part 1 |
| `docs/blog/series/assets/02_before_after_density.png` | **Default Reddit image** |
| `docs/blog/series/assets/03_kind_mix.png` | Kind mix |
| `docs/blog/series/assets/04_three_reports.png` | Report family illustration |

---

## Example table (cite correctly)

| Example | ID / source | Lane | Public proof | Claims to cite |
|---------|-------------|------|--------------|----------------|
| **Lipozem** | YouTube `tLJC8hkK-ao` | Consumer CRAAP | Gallery + `docs/launch/EXAMPLES.md` | Primary-10 battery **39**; Monday Batch smoke (2026-11-08, user `oss3-monday`) **37** — always name which run |
| **SB1507** | Local `sb1507.mp4` (**not in git**) | Analyst SIFT | Scorecard + report public (Chris approved); method in EXAMPLES | **40** verified · §6.1 = 16/40 · quant→inference 88.9% · `all_green` |
| **Nadella / Stargate** | YouTube `lb_ZJylekWo` | CEO talking-head | Battery row + EXAMPLES | **19** (primary-10) |

Commands (from EXAMPLES):

```bash
# Lipozem
verityngn analyze --tier full --deep \
  'https://www.youtube.com/watch?v=tLJC8hkK-ao' -o outputs/release_v3_lipozem

# SB1507 — you supply the mp4 path; do not attach the file to posts
verityngn analyze --tier local-full --deep \
  -f /path/to/sb1507.mp4 -o outputs/release_v3_sb1507_dense

# Nadella
verityngn analyze --tier full --deep \
  'https://www.youtube.com/watch?v=lb_ZJylekWo' -o outputs/examples/lb_ZJylekWo
```

Offline SB1507 scorecard (no Vertex): `python scripts/sb1507_risk_taxonomy_scorecard.py`

---

## Caption hygiene

- Prefer “PyPI `3.0.1` / engine tip `1b2cca8` / launch Monday Nov 23, 2026” over “candidate SHA” or floating HEAD language. Never advertise `==3.0.0`.
- Prefer pixel-proof captions (“45% of SB1507 claims are pixel-only”; “Lipozem doctor cards exist only in pixels”) over generic “multimodal.”
- One-sentence futures OK: “3.1 object/action semantics + visual–spoken contradiction; 3.2 pose/lip/audio congruence.”
- Do not attach or redistribute the SB1507 source mp4.
- Do not use Streamlit as the primary demo caption; gallery is the proof URL.
- NotebookLM brief: [`MULTIMODAL_AND_FUTURES_v3.md`](MULTIMODAL_AND_FUTURES_v3.md).
