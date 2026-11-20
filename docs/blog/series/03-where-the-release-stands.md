# Part 3 — Where the release stands

**Series:** VerityNgn OSS  
**Part 3 of 4 · The 3.0 release tip**

---

## This work *is* the 3.0 tip

Package version in [`pyproject.toml`](../../../pyproject.toml) is **3.0.1** (PyPI). Engine tip: tag `v3.0.0` → `1b2cca8`. Branch: `release/v3.0.0`.

| Artifact | Status |
|----------|--------|
| Engine tip | `v3.0.0` → `1b2cca8` (EXAMPLES + SB1507 public copy) |
| PyPI | **`verityngn==3.0.1` live** — install `pip install 'verityngn[deep]==3.0.1'` |
| PyPI `3.0.0` | **Yanked** — do not pin |
| Primary-10 battery | **PASS** — [`BATTERY_RESULTS_v3.md`](../../launch/BATTERY_RESULTS_v3.md) |
| Hosted gallery | Live — https://verityindex.com/gallery |

There is no 5.0.0. If that number appeared in conversation, it was informal. Public install is **3.0.1**.

## What the candidate includes

Everything already on the August–September 3.0 line, plus:

1. Six claim kinds (legacy four names kept as aliases).
2. Dual metrics: evidence confidence, residual reliance risk, risk chips.
3. §6.1 = source-backed facts only; typed §§6.3–6.8.
4. Genre switch: analyst videos get **Method & Reliance Review (SIFT)**; consumer videos keep CRAAP.
5. Offline scorecard + Chris review package builders.

Offline gates (unit tests, open-core scrub, SB1507 scorecard) are **PASS**. Live Lipozem + SB1507 + primary-10 battery are **PASS** in the matrix (Huang Squawk swap documented).

## What launch still decides

- Streamlit wake optional (gallery is the primary proof URL).
- Optional GitHub tag `v3.0.1` after packaging commits land.
- Chris: SB1507 **report/scorecard** is public; source mp4 stays local.

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
