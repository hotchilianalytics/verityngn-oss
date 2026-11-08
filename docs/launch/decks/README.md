# VerityNgn 3.0.0 decks

| File | What it is |
|------|------------|
| `../perplexity_review_2026-10-27/` | Perplexity's review assets as received: Release deck (18 slides), Demolicious cut (7), PDFs, legal-use-case brief |
| `VerityNgn_3_Release_with_examples.pptx` / `.pdf` | Perplexity Release deck plus four real-run example slides (22 slides) |
| `VerityNgn_3_example_slides.pdf` | The four example slides on their own |

## Example slides

They are numbered so the slide numbers in Perplexity's legal brief and presenter notes still apply.

| Slide | After | Shows |
|-------|-------|-------|
| 08A | 08 (disclosure companion) | Microsoft 10-K / 8-K pair from the rfkit Phase 1 companion, set aside by the junior gate |
| 12A | 12 (release evidence) | Claim-kind and assessment-label counts for the 263 claims in battery rows 3–10 |
| 12B | 12A | Deposition (row 9): expert projections routed to prediction and inference lanes, not scored true/false |
| 12C | 12B | Nadella interview (row 7): timestamped claims; bridge to ClearFactor's "own voice" input |

All counts and quotes come from `outputs/release_v3_battery_2026-10-18/*/…_report.json`, which is a local run artifact and not in git, and from the public EDGAR filings cited in each slide's notes.

Two deliberate omissions:

- **Gallery screenshot.** It shows per-video verdict badges, which the launch guardrails keep out of public posts.
- **Nadella's right-of-first-refusal claim.** The run labeled it Supported, but Microsoft's 28 Oct 2025 Ex-99.2 ended that right. The 12C presenter notes explain this.

The Perplexity slides were changed in one way only: each run now carries its own font size, weight, colour, and typeface. The original set these only at paragraph level, which PowerPoint and Keynote may not apply. The text itself is unchanged.

## Rebuild

```bash
python scripts/decks/add_oss_examples.py
```

Needs Google Chrome for the four-slide example PDF, LibreOffice (`soffice`) for the full 22-page PDF from the PPTX, and the local battery outputs (checkpoints are enough if `*_report.json` is gone). Run it outside the Cursor sandbox, because matplotlib can fail inside it. The shared kit (`scripts/decks/slidekit.py`, `charts.py`) also builds the ClearFactor decks in the private rfkit consulting tree.
