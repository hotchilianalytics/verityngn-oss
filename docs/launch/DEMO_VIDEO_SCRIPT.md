# VerityNgn Demo Video Script

**Duration:** 3-5 minutes  
**Format:** Screen recording with voiceover  
**Style:** Conversational, technical but accessible

---

## Pre-Production Checklist

- [ ] Clean browser (no personal bookmarks visible)
- [ ] Streamlit app loaded and working
- [ ] Sample video URL ready (pick something interesting but safe)
- [ ] Gallery has at least 2-3 completed reports to show
- [ ] Screen recording software set up (OBS, Loom, or similar)
- [ ] Microphone tested

---

## Script

### INTRO (0:00 - 0:30)

**[SCREEN: Title card with VerityNgn logo or text]**

**VOICEOVER:**

"Every minute, 500 hours of video are uploaded to YouTube. Health scams. Financial fraud. Pseudoscience. And fact-checkers can maybe review 10 or 20 claims per day.

The math doesn't work.

So I built VerityNgn — an open-source AI that fact-checks YouTube videos. Not by reading transcripts. By actually watching them.

Let me show you how it works."

---

### THE PROBLEM (0:30 - 1:00)

**[SCREEN: Show a typical misleading video thumbnail — blur if needed, or use text overlay describing the type]**

**VOICEOVER:**

"Here's the problem with existing fact-checking tools: they only analyze text.

But video misinformation is multimodal. It's the on-screen graphics claiming 'clinically proven.' It's the visual demonstrations that look convincing. It's the whole package.

And when you search for evidence, you often find promotional press releases that CONFIRM the false claims. The misinformation ecosystem is SEO-optimized.

VerityNgn takes a different approach: counter-intelligence."

---

### LIVE DEMO: STARTING VERIFICATION (1:00 - 1:45)

**[SCREEN: Navigate to verityngn.streamlit.app]**

**VOICEOVER:**

"Let me show you. Here's the VerityNgn app — verityngn.streamlit.app.

I'm going to paste in a YouTube URL..."

**[ACTION: Paste a YouTube URL into the input field]**

"...and click 'Start Verification.'"

**[ACTION: Click the button]**

"Now the system is downloading the video, analyzing it frame by frame using Google's Gemini 2.5 Flash, extracting claims, searching for evidence, and running counter-intelligence.

This usually takes about 3 to 5 minutes depending on the video length."

**[SCREEN: Show the progress indicator briefly, then cut to...]**

---

### LIVE DEMO: THE REPORT (1:45 - 3:00)

**[SCREEN: Navigate to Gallery, open a completed report]**

**VOICEOVER:**

"While that's processing, let me show you what a completed report looks like.

Here's one from the Gallery — you can see all the videos that have been analyzed."

**[ACTION: Click on a report to open it]**

"This is the truthfulness report. At the top, you see the overall assessment and key findings.

Below that, each claim extracted from the video, with:
- The claim text
- The timestamp where it appeared
- The evidence found for and against
- A probability distribution: TRUE, FALSE, or UNCERTAIN

**[ACTION: Scroll to show a specific claim]**

"Look at this claim. The system found 3 sources supporting it, but also found 2 YouTube review videos that contradict it, and identified a press release from the company itself.

That's the counter-intelligence at work. It's not just confirming or denying — it's actively hunting for opposition.

**[ACTION: Scroll to show the probability distribution]**

"And instead of just saying 'true' or 'false,' you get a calibrated probability. This claim shows 25% TRUE, 55% FALSE, 20% UNCERTAIN. The evidence leans against it, but there's still uncertainty.

That's honest fact-checking."

---

### COUNTER-INTELLIGENCE HIGHLIGHT (3:00 - 3:30)

**[SCREEN: Highlight a section showing YouTube review detection or press release detection]**

**VOICEOVER:**

"Let me zoom in on the counter-intelligence.

The system automatically searched YouTube for review videos about this topic. Found one from an independent creator with 400,000 views who tested the claims.

And here — it detected this source as a press release. 94% precision on that detection. Press releases are weighted negatively because they're promotional, not journalistic."

---

### RESULTS + OPEN SOURCE (3:30 - 4:00)

**[SCREEN: Show the GitHub repo or a stats graphic]**

**VOICEOVER:**

"The results: 78% accuracy on a 200-claim test set compared to expert ground truth. The counter-intelligence component alone adds 18 percentage points.

And it's completely open source. Apache 2.0 license.

The code, the methodology papers, everything is on GitHub. Because misinformation is too important a problem to solve behind closed doors."

---

### CALL TO ACTION (4:00 - 4:30)

**[SCREEN: Show both URLs on screen]**

**VOICEOVER:**

"Try it yourself: verityngn.streamlit.app. No signup, no installation. Just paste a URL.

Star the repo: github.com/hotchilianalytics/verityngn-oss.

And if you find bugs or have ideas, open an issue. I want to make this better.

Thanks for watching. Let's build something that matters."

**[SCREEN: End card with URLs and social handles]**

- Demo: verityngn.streamlit.app
- GitHub: github.com/hotchilianalytics/verityngn-oss
- Twitter: @AlanJCoppola

---

## Post-Production Notes

### Suggested Edits

1. **Speed up waiting sections** (2-4x) with a progress indicator overlay
2. **Add lower-third text** for key stats (78% accuracy, +18% counter-intel)
3. **Add subtle background music** (lo-fi, non-distracting)
4. **Add captions** (accessibility + silent autoplay on social)

### Thumbnail Ideas

- "AI Fact-Checks YouTube" with a screenshot of the report
- Split screen: misleading video vs. truthfulness report
- Stats graphic: "78% Accurate"

### Video Settings for Upload

| Platform | Aspect Ratio | Max Length |
|----------|--------------|------------|
| YouTube | 16:9 | Full length |
| Twitter/X | 16:9 or 1:1 | 2:20 max |
| LinkedIn | 16:9 or 1:1 | 10 min max |

For Twitter, create a 60-90 second cut focusing on the demo (1:00-3:00 section).

---

## Sample Videos to Use in Demo

Pick ONE that is:
1. Safe/appropriate for public viewing
2. Contains clear claims that can be verified
3. Already in your Gallery with a good report

**Suggestions from existing gallery:**
- A health/supplement video (common misinformation type)
- A finance/investment video
- A tech product review

Avoid: Political content, anything controversial, content that might get DMCA'd.


