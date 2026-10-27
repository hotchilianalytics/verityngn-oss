# Hacker News "Show HN" Post — VerityNgn OSS 3.0

## Title

```
Show HN: VerityNgn 3.0 – open-source video claim-risk engine (Deep Research + domain packs)
```

## Body

---

I just shipped **VerityNgn OSS 3.0.0** — a standalone Apache-2.0 engine that turns a YouTube URL (or local video file) into a claim-level **risk** report (not a lie detector), including **Deep Research** in the public CLI.

**Install:** `pip install verityngn` (after PyPI; until then `pip install -e '.[deep]'` from `release/v3.0.0`)  
**CLI:** `verityngn analyze <url>` · `verityngn analyze <url> --deep` · `verityngn analyze --file clip.mp4`  
**Repo:** https://github.com/hotchilianalytics/verityngn-oss/tree/release/v3.0.0  
**Demo:** https://verityngn.streamlit.app  
**Platform:** `docs/platform/PLATFORM_OVERVIEW.md`  
**Paper:** `papers/verityngn_oss_v3_release.md`

### What it does

1. Multimodal claim extraction (Gemini) over video frames + transcript  
2. Counter-intelligence: seeks contradictory YouTube reviews and press-release bias  
3. THREE-state probabilities (TRUE / FALSE / UNCERTAIN) with residual reliance risk  
4. Optional Deep Research: grounded summary with citation audit trail  
5. Domain packs: CRAAP consumer, SIFT analyst, CEO sensors, legal/health lanes  

### Open-core boundary (honest)

Engine + research sleeves (predictions/sensors) are OSS. Hosted multi-tenant SaaS and credits live on **verityindex.com** (control plane). ClearFactor disclosure **services** are paid; disclosure **engine** opens as a sleeve. No earnings prediction / allocation alpha in this release.

### Ask

Stars, issues, and PRs welcome. Especially useful: hard negative examples and report-quality diffs vs human review.

---
