# Hacker News "Show HN" Post — VerityNgn OSS 3.0.1

## Title

```
Show HN: VerityNgn 3.0 – open-source video claim-risk engine (Deep Research + domain packs)
```

## Body

---

I just shipped **VerityNgn OSS 3.0.1** — a standalone Apache-2.0 engine that turns a YouTube URL (or local video file) into a claim-level **risk** report (not a lie detector), including **Deep Research** in the public CLI.

**Proof:** https://verityindex.com/gallery  
**PyPI:** https://pypi.org/project/verityngn/3.0.1/  
**Install:** `pip install 'verityngn[deep]==3.0.1'`  
**CLI:** `verityngn analyze <url>` · `verityngn analyze <url> --deep` · `verityngn analyze --tier local-full -f clip.mp4`  
**Source / notes:** https://github.com/hotchilianalytics/verityngn-oss · [`RELEASE_NOTES_v3.0.1.md`](https://github.com/hotchilianalytics/verityngn-oss/blob/release/v3.0.0/docs/launch/RELEASE_NOTES_v3.0.1.md)

### What it does

1. Multimodal claim extraction (Gemini) with **adaptive 1–6 fps** over frames + transcript + OCR/exhibits  
2. Pixel-only proof: **45% of SB1507 claims** and Lipozem’s doctor/weight-loss cards exist only in pixels; auto-emits `brand_safety_scores.json` + exhibit maps  
3. Counter-intelligence: seeks contradictory YouTube reviews and press-release bias  
4. THREE-state probabilities (TRUE / FALSE / UNCERTAIN) with residual reliance risk  
5. Optional Deep Research with a `visual_only_claims` lead  
6. Domain packs: CRAAP consumer, SIFT analyst, CEO sensors, legal/health lanes  

Local-file path is the same engine (analyst SIFT example: SB1507 scorecard, 40 claims / 18 pixel-only — source mp4 stays private; method is public). Roadmap hook: 3.1 object/action semantics + visual–spoken contradiction; 3.2 pose/lip/audio congruence atop in-repo MediaPipe + MultiSense sleeves. Launch Monday Nov 16, 2026.

### Open-core boundary (honest)

Engine + research sleeves (predictions/sensors) are OSS. Hosted multi-tenant SaaS and credits live on **verityindex.com** (control plane). ClearFactor disclosure **services** are paid; disclosure **engine** opens as a sleeve. No earnings prediction / allocation alpha in this release.

### Ask

Stars, issues, and PRs welcome. Especially useful: hard negative examples and report-quality diffs vs human review.

---
