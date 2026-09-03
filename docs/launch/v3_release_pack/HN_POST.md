# Hacker News "Show HN" Post — VerityNgn OSS 3.0

## Title

```
Show HN: VerityNgn 3.0 – open-source multimodal video fact-checking with Deep Research
```

## Body

---

I just shipped **VerityNgn OSS 3.0.0** — a standalone Apache-2.0 engine that turns a YouTube URL (or local video file) into a claim-level truthfulness report, now including the **Deep Research** grounded forensic pass that used to live only on our commercial fork.

**Install:** `pip install verityngn`  
**CLI:** `verityngn analyze <url>` · `verityngn analyze <url> --deep` · `verityngn analyze --file clip.mp4`  
**Repo:** https://github.com/hotchilianalytics/verityngn-oss  
**Demo:** https://verityngn.streamlit.app  
**Paper:** `papers/verityngn_oss_v3_release.md` (+ charts)

### What it does

1. Multimodal claim extraction (Gemini) over video frames + transcript  
2. Counter-intelligence: seeks contradictory YouTube reviews and press-release bias  
3. THREE-state probabilities (TRUE / FALSE / UNCERTAIN), not binary slogans  
4. Optional Deep Research: grounded Gemini summary with citation audit trail  
5. Optional authenticity stubs + spectral voice cues + MediaPipe Face Landmarker  

### Open-core boundary (honest)

Hosted multi-tenant SaaS, **predictions**, and **RiskFactor** products stay closed and are expected to **depend on this OSS base**. This release does **not** include earnings prediction, allocation factors, or “lie detection.”

### Ask

Stars, issues, and PRs welcome. Especially useful: hard negative examples and report-quality diffs vs human review.

---
