# Hacker News "Show HN" Post — VerityNgn OSS 3.0

## Title

```
Show HN: VerityNgn 3.0 – open-source multimodal video claim-risk analysis + Deep Research
```

## Body

---

I am preparing **VerityNgn OSS 3.0.0** on branch `release/v3.0.0` (candidate `5258292`) — a standalone Apache-2.0 engine that turns a YouTube URL or local file into a claim-level **risk** report (not a lie detector). Deep Research ships in OSS. This candidate also adds **analyst-video claim kinds** (facts vs data-derived inferences vs predictions) with dual metrics and a SIFT method review instead of CRAAP when the mix is deep-data analysis.

**Repo:** https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0  
**Demo:** https://verityngn.streamlit.app  
**Gallery:** https://verityindex.com/gallery  
**Series:** `docs/blog/series/` (history, features, release status, two demos)

### What it does

1. Multimodal claim extraction over video + transcript  
2. Counter-intelligence: seeks contradiction and press-release bias  
3. Ordinal likelihoods (TRUE / FALSE / UNCERTAIN) plus evidence confidence / residual reliance risk for analyst genres  
4. Optional Deep Research with citation audit trail  
5. Genre-aware §9: CRAAP for consumer; SIFT for analyst  

### Open-core boundary (honest)

Predictions and RiskFactor stay closed. Pin OSS ≥3.0.0 underneath.

### Ask

Stars, issues, and hard questions welcome. Public demo video: Lipozem `tLJC8hkK-ao`. Analyst charts are in the series assets; full SB1507 report stays private until the creator approves.

---

**Post only after** [`RELEASE_TEST_MATRIX_v3.md`](../RELEASE_TEST_MATRIX_v3.md) live gates are green. Prefer “Show HN” after Reddit ML has had a day.
