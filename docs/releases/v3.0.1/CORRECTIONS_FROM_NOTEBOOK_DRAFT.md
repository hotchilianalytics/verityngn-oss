# Corrections applied to the Notebook-generated 3.0.1 artifacts

The Google Notebook drafts were fact-checked against the repository and `outputs/release_v3_*` before release.
This file lists what changed so the released article, PDFs, and engine tip stay consistent.
PDFs are rebuilt from the markdown with `scripts/release/build_v301_release_pdfs.py`.

| Draft claim | Corrected to | Evidence |
|---|---|---|
| "81 claims across the 10-video benchmark" | 81 pixel-only claims across **10 release runs**; **69** within the final primary-10 battery (the other 12 come from the swapped-out CES restream `fuq0Ncdsknk`) | `outputs/release_v3_*/**/*_exhibit_map.json` |
| "zero pipeline failures" / "100% extraction reliability" | 10 of 10 rows produced claim ledgers (342 claims) after one documented swap | `outputs/release_v3_battery_2026-10-18/SWAP_NOTES.md` |
| Speech via "Whisper" | Gemini multimodal pass plus YouTube captions (VTT); Groq Whisper ASR is opt-in | `verityngn/services/video/transcript_providers/asr_groq.py` |
| "high-precision OCR on every keyframe", "exact millisecond timestamp" | Multimodal model reads sampled frames; exhibit map stores timestamp **ranges** (`01:21 - 01:25`) | exhibit map schema |
| "1 fps static, up to 6 fps on documents" | Content classes: lecture 1.0, montage 3.0, exhibit slide 4.0, flash text 6.0 fps | `verityngn/services/vision/adaptive_sampler.py` |
| Oregon SB 1507 "visual exhibits dominated" | 18 of 40 claims (45%) pixel-only | exhibit map for `3f70063ddbd` |
| Pack 3: tested against SEC filings; Pack 4: trial discovery exhibits; Pack 5: searches PubMed / trial registers | Counter-intelligence web search with source-reputation weighting; no dedicated SEC, discovery, or PubMed search in the wheel | codebase search |
| Pack 6 (disclosure) as part of 3.0.1 | Delivered by the rfkit / ClearFactor companion; the `[disclosure]` extra is an empty placeholder | `pyproject.toml` |
| "3.0.1 introduces" captions CLI, sidecars | 3.0.1 is the first clean PyPI publication of the 3.0 engine cut | `CHANGELOG.md` |
| "invented" characteristic column in the battery table | Replaced with measured per-row pixel-only counts | exhibit maps |
| Executive header whiteboard: "Spoken Audio (Whisper)" | "Spoken Audio (captions)" | pixel edit |
| Description PDF Figure 2 (Streamlit "app has gone to sleep" screen) | Removed | visual check |
| Deck slide 2 (fabricated Lipozem trial, fictional researcher, "98.7% confidence") | Replaced with a factual slide | visual check |
| Deck slide 6 ("Predictions / RiskFactor (closed overlays)") | Predictions ship as the opt-in `[predictions]` sleeve; RiskFactor is a companion | `pyproject.toml` |
| Deck slide 8 ("Primary-10 Battery Passed. 81 verified pixel-only claims.") | "10 of 10 rows produced claims. 69 pixel-only (81 over 10 runs)" | exhibit maps |

Framing reminder: delivery, conviction, and disclosure risk for human review. Not lie detection.
