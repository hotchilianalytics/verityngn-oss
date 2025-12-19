# X (Twitter) Thread

## Thread (Copy/paste each tweet)

---

### Tweet 1/10 (Hook + Announcement)

I built an AI that fact-checks YouTube videos.

Not by reading transcripts. By watching them.

Today I'm open-sourcing it.

verityngn.streamlit.app

🧵 Thread on how it works and why it's different:

---

### Tweet 2/10 (The Problem)

The problem:

500 hours of video uploaded to YouTube every minute.

Fact-checkers can review maybe 10-20 claims/day.

Video misinformation spreads for DAYS before anyone debunks it.

The math doesn't work.

---

### Tweet 3/10 (Why Existing Tools Fail)

Existing fact-checking tools only analyze text transcripts.

They miss:
- On-screen graphics ("clinically proven!")
- Visual demonstrations
- Audio cues
- The multimodal deception that makes video so persuasive

---

### Tweet 4/10 (The Bigger Problem)

And there's a bigger problem:

When you search for evidence, you often find... promotional press releases.

The misinformation ecosystem is SEO-optimized.

Search results CONFIRM false claims.

---

### Tweet 5/10 (The Solution)

So I built VerityNgn with a counter-intelligence approach:

1. Multimodal analysis (Gemini 2.5 Flash, 1 FPS)
2. Active search for CONTRADICTORY evidence
3. YouTube review detection
4. Press release identification (94% precision)

Hunt the opposition.

---

### Tweet 6/10 (Probabilistic Output)

And instead of binary "true/false":

A calibrated probability distribution.

TRUE: evidence supports
FALSE: evidence contradicts
UNCERTAIN: conflicting/insufficient

Because real claims are rarely simply true or false.

---

### Tweet 7/10 (Results)

The results:

✓ 78% accuracy vs. expert ground truth
✓ +18% improvement from counter-intel alone
✓ Well-calibrated (Brier = 0.12)
✓ $0.50-2.00 per video

Not perfect. But a start.

---

### Tweet 8/10 (Demo)

Try it right now:

1. Go to verityngn.streamlit.app
2. Paste any YouTube URL
3. Click "Start Verification"
4. Check the Gallery for your report

No install. No signup. Just paste and verify.

[ATTACH: GIF of demo if available]

---

### Tweet 9/10 (Open Source)

The whole thing is open source. Apache 2.0.

github.com/hotchilianalytics/verityngn-oss

Includes:
- Full verification engine
- Streamlit UI
- 3 research papers with methodology
- Docker configs

Transparent. Auditable. Improvable.

---

### Tweet 10/10 (Call to Action)

Misinformation is too important to solve behind closed doors.

If you care about this problem:
- Try it: verityngn.streamlit.app
- Star it: github.com/hotchilianalytics/verityngn-oss
- Break it and tell me what's wrong

Let's build something that matters.

---

## Thread Summary Card

| Tweet | Content | Character Count |
|-------|---------|-----------------|
| 1 | Hook + announcement | ~180 |
| 2 | The problem (scale) | ~200 |
| 3 | Why existing tools fail | ~220 |
| 4 | SEO/press release problem | ~180 |
| 5 | Counter-intel solution | ~240 |
| 6 | Probabilistic output | ~200 |
| 7 | Results | ~160 |
| 8 | Demo CTA | ~200 |
| 9 | Open source + repo | ~220 |
| 10 | Final CTA | ~200 |

## Posting Tips

1. **Post tweet 1**, wait 30-60 seconds, then post the rest in quick succession
2. **Attach a GIF** to tweet 8 showing the demo flow
3. **Pin the thread** to your profile for launch day
4. **Quote tweet** the first tweet with personal commentary later in the day
5. **Best times**: Weekdays 8-10 AM ET or 12-1 PM ET

## Reply to Self (Recommended)

After posting, add this reply to Tweet 10:

```
For the technically curious:

Stack:
- Python 3.12
- Gemini 2.5 Flash (1M token context)
- LangChain/LangGraph
- Streamlit + Cloud Run
- yt-dlp

All in the repo. Happy to answer questions.
```


