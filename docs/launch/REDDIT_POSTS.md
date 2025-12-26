# Reddit Posts

---

## r/MachineLearning Post

### Title

```
[P] VerityNgn: Open-source multimodal video verification with counter-intelligence (Gemini 2.5 Flash, 75% accuracy)
```

### Body

---

**TL;DR:** Open-source system that generates truthfulness reports for YouTube videos using multimodal LLM analysis + a counter-intelligence pipeline. Achieves 75% accuracy vs ground truth (95% CI: 61-85%), with +18% improvement from counter-intel on misleading content.

**Demo:** https://verityngn.streamlit.app  
**Repo:** https://github.com/hotchilianalytics/verityngn-oss  
**Paper:** [papers/verityngn_research_paper.md](https://github.com/hotchilianalytics/verityngn-oss/blob/main/papers/verityngn_research_paper.md)

---

### Architecture

**Multimodal Analysis:**
- Gemini 2.5 Flash with 1M token context window
- 1 FPS video sampling (frames, audio, OCR, motion)
- Intelligent segmentation: up to 47.7 min per segment (86% fewer API calls than fixed 5-min chunks)
- 65K output tokens for detailed claim extraction

**Claim Extraction Pipeline:**
- Multi-pass extraction with specificity scoring (0-100)
- Absence claim generation ("no peer-reviewed studies cited")
- Type classification: scientific, statistical, causal, testimonial, expert opinion
- Quality filtering to remove vague/unverifiable claims

**Counter-Intelligence (the interesting part):**
- YouTube review search: finds independent review/debunking videos
  - 76% detection rate, 89% stance accuracy
  - Credibility weighting (views, channel age, verification)
- Press release detection: identifies promotional content masquerading as news
  - 94% precision, 87% recall
  - Domain/pattern matching + linguistic markers
- Evidence contradiction weighting: contradictory evidence weighted more heavily

**Probability Model:**
- Bayesian evidence aggregation
- Source credibility weighting (peer-reviewed = 1.5, press release = -1.0)
- Three-state distribution: TRUE / FALSE / UNCERTAIN
- Normalization + human-interpretable thresholds

---

### Evaluation

| Metric | Result |
|--------|--------|
| Accuracy | 75% (95% CI: 61-85%) |
| Counter-intel improvement | +18% |
| Brier score | 0.12 |
| ECE | 0.04 |
| Press release precision | 94% |
| Review detection rate | 76% |

---

### Limitations

- English only
- YouTube only (no TikTok, Instagram)
- 22% error rate
- Susceptible to coordinated fake review campaigns
- No human-in-the-loop
- Stance detection at 89% (not perfect)

---

### Tech Stack

- Python 3.12
- Gemini 2.5 Flash via Vertex AI
- LangChain/LangGraph for orchestration
- Streamlit UI
- Cloud Run backend
- yt-dlp for video download
- Google Custom Search + YouTube Data API

---

### Why Open Source

The methodology needs to be transparent and auditable for work in this space to be credible. Full research papers with step-by-step probability calculations are in the `papers/` directory.

Looking for feedback on:
1. The counter-intelligence approach (is weighted contradiction search the right model?)
2. Probability calibration (Brier = 0.12 is decent but could be better)
3. Evidence source expansion (Reddit? Forums? Specialized DBs?)

Happy to answer questions about the architecture, evaluation, or anything else.

---

## r/LanguageTechnology Post

### Title

```
VerityNgn: Open-source fact-checking for YouTube videos using multimodal LLMs and counter-intelligence
```

### Body

---

I've open-sourced a system for automated video fact-checking that takes a different approach from traditional text-based methods.

**Demo:** https://verityngn.streamlit.app  
**Repo:** https://github.com/hotchilianalytics/verityngn-oss

### The Problem

Most fact-checking systems analyze text only. But video misinformation is multimodal — it combines spoken words, on-screen graphics, visual demonstrations, and audio cues. Transcript-only analysis misses the visual claims that make videos persuasive.

### The Approach

**1. Multimodal Analysis**

Uses Gemini 2.5 Flash to analyze full videos at 1 frame/second:
- Audio transcription
- OCR for on-screen text
- Visual content analysis
- Motion and gesture detection

The 1M token context window allows processing up to 47 minutes in a single pass.

**2. Counter-Intelligence**

Instead of just searching for confirming/denying evidence, the system actively hunts for contradictory content:

- Searches YouTube for review/debunking videos by independent creators
- Detects press releases masquerading as news (94% precision)
- Weights contradictory evidence more heavily than confirming evidence

This is important because the misinformation ecosystem is SEO-optimized — search results often *confirm* false claims because of promotional content.

**3. Probabilistic Output**

Instead of binary true/false, generates a three-state probability distribution:
- TRUE
- FALSE  
- UNCERTAIN

With calibrated confidence scores (Brier = 0.12, ECE = 0.04).

### Results

75% accuracy vs ground truth (95% CI: 61-85%). The counter-intelligence component alone adds +18% accuracy on misleading content.

### Limitations

English only for now. YouTube only. 22% error rate means this is a tool to augment human judgment, not replace it.

### Looking for Feedback

- Multi-language expansion (any experience with multilingual claim verification?)
- Additional evidence sources
- Evaluation methodology

---

## r/artificial Post (Alternative)

### Title

```
I open-sourced an AI that fact-checks YouTube videos by watching them (not just reading transcripts)
```

### Body

---

Built this over the past year and just open-sourced it.

**What it does:** Generates truthfulness reports for YouTube videos. You paste a URL, it analyzes the video, searches for evidence, and gives you a probability distribution (TRUE/FALSE/UNCERTAIN) for each claim.

**What makes it different:**

1. **Multimodal** — Analyzes the actual video at 1 frame/second using Gemini 2.5 Flash. Not just the transcript.

2. **Counter-intelligence** — Actively searches for CONTRADICTORY evidence. Finds YouTube review videos from independent creators. Detects press releases pretending to be news.

3. **Probabilistic** — Gives you calibrated probabilities, not binary verdicts.

**Results:** 75% accuracy. The counter-intel component alone adds +18% on misleading content.

**Try it:** https://verityngn.streamlit.app (no signup, just paste a URL)

**Repo:** https://github.com/hotchilianalytics/verityngn-oss (Apache 2.0)

Built this because video misinformation is growing faster than fact-checkers can keep up. Wanted to contribute something to the problem.

Happy to answer questions.

---

## Posting Guidelines

| Subreddit | Rules | Best Times |
|-----------|-------|------------|
| r/MachineLearning | Use [P] for Project, [R] for Research | Weekdays, morning EST |
| r/LanguageTechnology | Focus on NLP/language aspects | Weekdays |
| r/artificial | General AI discussion | Anytime |

**Tips:**
1. Engage with comments — Reddit rewards participation
2. Don't cross-post simultaneously (looks spammy)
3. Post to r/MachineLearning first (largest audience)
4. Wait 24 hours before r/LanguageTechnology
5. Be honest about limitations (Reddit users will find them anyway)


