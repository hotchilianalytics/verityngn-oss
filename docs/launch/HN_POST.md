# Hacker News "Show HN" Post

## Title

```
Show HN: VerityNgn – Open-source AI that fact-checks YouTube videos with counter-intelligence
```

## Body (Copy/paste this)

---

I built an open-source system that generates truthfulness reports for YouTube videos using multimodal AI and a counter-intelligence approach.

**Live demo:** https://verityngn.streamlit.app  
**Repo:** https://github.com/hotchilianalytics/verityngn-oss

### The Problem

Existing fact-checking tools only analyze text transcripts. They miss on-screen graphics, visual demonstrations, and the multimodal nature of video. Worse, when you search for evidence, you often get promotional press releases that *confirm* false claims because the misinformation ecosystem is SEO-optimized.

### How VerityNgn Works

1. **Multimodal analysis**: Uses Gemini 2.5 Flash (1M token context) to analyze video frames at 1 FPS — audio, OCR, visuals, and transcript together
2. **Enhanced claim extraction**: Multi-pass extraction with specificity scoring (0-100), filters out vague claims
3. **Counter-intelligence**: Actively searches for contradictory evidence — YouTube review videos from independent creators, press release detection (94% precision)
4. **Probabilistic output**: THREE-state distribution (TRUE/FALSE/UNCERTAIN) with calibrated confidence, not binary verdicts

### Results (200-claim test set)

- 78% accuracy vs. expert ground truth
- +18% improvement from counter-intel alone
- Well-calibrated (Brier score = 0.12, ECE = 0.04)
- Cost: $0.50–$2.00 per video

### Tech Stack

- Python 3.12, Gemini 2.5 Flash via Vertex AI
- LangChain/LangGraph for orchestration
- Streamlit UI, Cloud Run backend
- yt-dlp for video download
- Google Custom Search + YouTube Data API

### Honest Limitations

- English only
- YouTube only (no TikTok/Instagram yet)
- 22% error rate (78% accuracy means 22% wrong)
- Susceptible to coordinated fake review campaigns
- No human-in-the-loop

### Why Open Source

Misinformation is too important to solve behind closed doors. The methodology needs to be transparent and auditable. Full research papers with step-by-step calculations are in the `papers/` directory.

Looking for feedback on the approach and contributions (especially: multi-language support, additional platforms, expanded evidence sources).

---

## Submission URL

Submit to: https://news.ycombinator.com/submit

- **Title**: Show HN: VerityNgn – Open-source AI that fact-checks YouTube videos with counter-intelligence
- **URL**: https://github.com/hotchilianalytics/verityngn-oss
- **Text**: (paste the body above)

## Best Posting Times for HN

- **Optimal**: Tuesday-Thursday, 9-11 AM ET (6-8 AM PT)
- **Avoid**: Weekends, late evenings

## Tips for HN Success

1. Be in the first comment with additional context
2. Respond quickly to questions
3. Be honest about limitations (builds trust)
4. Engage thoughtfully with criticism
5. Don't ask for upvotes


