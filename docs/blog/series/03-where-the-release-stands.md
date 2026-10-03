# Part 3 — Where the release stands

**Series:** VerityNgn OSS  
**Part 3 of 4 · The 3.0.0 candidate**

---

## This work *is* the 3.0.0 candidate

Package version in [`pyproject.toml`](../../../pyproject.toml) is **3.0.0**. Branch: `release/v3.0.0`.

| Artifact | Status |
|----------|--------|
| Candidate SHA | `5258292` (analyst taxonomy + SIFT genre report frozen) |
| Git tag `v3.0.0` | Still at `131ac87` (2026-08-29). Moves **only** after [`RELEASE_TEST_MATRIX_v3.md`](../../launch/RELEASE_TEST_MATRIX_v3.md) is all pass **and** an operator explicitly asks to retag. |
| Merge to `main` / PyPI | Explicit ask required. Not part of drafting blogs. |

There is no 5.0.0. If that number appeared in conversation, it was informal. The tree ships under 3.0.0.

## What the candidate includes

Everything already on the August–September 3.0 line, plus:

1. Six claim kinds (legacy four names kept as aliases).
2. Dual metrics: evidence confidence, residual reliance risk, risk chips.
3. §6.1 = source-backed facts only; typed §§6.3–6.8.
4. Genre switch: analyst videos get **Method & Reliance Review (SIFT)**; consumer videos keep CRAAP.
5. Offline scorecard + Chris review package builders.

Offline gates (unit tests, open-core scrub, SB1507 scorecard on the Sep 23 smoke JSON) are **PASS**. Live Lipozem + SB1507 gates are recorded in the matrix as they finish.

## What a launch should decide

- Live matrix green?
- Chris: public charts only, or excerpts from the analyst report?
- Retag / merge / PyPI when you say so — not when the blog goes live.

## Reproduce

```bash
python scripts/sb1507_risk_taxonomy_scorecard.py
python scripts/build_chris_review_package.py
# Live proof dirs (after runs):
#   outputs/release_v3_lipozem
#   outputs/release_v3_sb1507
```

---

*Previous: [Part 2 — Features](02-features-and-value.md) · Next: [Part 4 — Two videos](04-two-videos.md)*
