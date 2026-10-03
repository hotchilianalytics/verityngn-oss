# Part 3 — Where the release stands

**Series:** VerityNgn OSS, three parts  
**Part 3 of 3 · The current cut**

---

## The number on the package is 3.0.0

`pyproject.toml` says **3.0.0**. The changelog’s current heading is **3.0.0** (2026-09-03 candidate on branch `release/v3.0.0`). The git tag `v3.0.0` was cut earlier, on 2026-08-29, and has not been moved.

There is **no 5.0.0** tag, branch, or package version in this repository. If “5.0.0” has been used in conversation as the name of the new work, that name has not been applied to the tree. This article describes the work that is actually in the working tree, under the 3.0.0 line.

Bumping the version, retagging, or publishing to PyPI is a separate operator decision. It is not done here.

## What 3.0.0 already is

Shipped on the public engine line:

- Multimodal claim extraction and counter-intelligence verification
- Deep Research in OSS (`deep.html` beside `report.html`)
- Analysis tiers and caption fallbacks
- Gemini 3.8 as the local default, with a Vertex fallback that prefers location `global` (region `us-central1` has returned 404/501 for that model)
- Open-core boundary: this repo does not ship the predictions or risk-factor products

## What the working tree adds (the “new” increment)

On top of that 3.0.0 line, unreleased as its own version number:

1. Six claim kinds, with the old four names kept as aliases.
2. Dual metrics stamped at verification time: evidence confidence, residual reliance risk, abatement notes, and the one-line risk chip.
3. Report layout: section 6.1 is source-backed facts only; other kinds get compact sections.
4. Genre switch: analyst-heavy videos get a **Method & Reliance Review (SIFT)** where consumer videos still get CRAAP.
5. A third artifact for review, built offline from an existing smoke file, so a creator session does not require a new video pass.

Fixture used to check it: Chris Schuermyer’s SB1507 smoke, 28 claims, scorecard green (13 facts, 7 data-derived, 4 causal, 2 predictions, 2 unverified).

## What a joint review should decide

- Are the bins right for this video, claim by claim?
- Is the chip wording usable by someone who will not read ICD 203?
- Should the next **tagged** release stay 3.0.x, or should this genre work be the reason for a new major number?
- Commercial batch is still a pin-and-parity problem. This increment is engine-first on OSS. It is not promoted to the commercial image in this pass.

## What we are not claiming

- We did not re-analyze the SB1507 video to produce the review package. Labels changed; the underlying likelihoods are the September 23 verification.
- We did not rewrite the verifier.
- We did not turn evidence confidence into a peer-review score.
- Vertex location issues still matter the next time someone runs a **live** agentic pass. They do not change the offline re-stamp.

## How to reproduce

```bash
python scripts/sb1507_risk_taxonomy_scorecard.py
python scripts/build_chris_review_package.py
```

Outputs:

- `outputs/sb1507_risk_taxonomy_loop/scorecard.json`
- `outputs/chris_review_package/01_analyst_report.html`
- `docs/blog/series/` (this series and the charts)

---

*Previous: [Part 2 — Features and value](02-features-and-value.md)*

*HotChili Analytics / VerityNgn · OSS engine on `release/v3.0.0`*
