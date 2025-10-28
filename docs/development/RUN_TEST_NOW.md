# 🚀 Run Test NOW - Quick Instructions

## What We Learned

The test wasn't hung - it's just **VERY SLOW**:
- ✅ **8 minutes per segment** (we tested this)
- ✅ **7 segments for 33-min video**  
- ✅ **Expected: 30-60 minutes total**

## Step 1: Check Your .env Has Required Variables

Your `.env` file needs these lines:

```bash
# Required for Vertex AI
GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/verityngn/config/verityindex-0-0-1-6a21e94ca0a3.json
GOOGLE_CLOUD_PROJECT=verityindex-0-0-1
PROJECT_ID=verityindex-0-0-1
LOCATION=us-central1

# Optional (for enhanced features)
YOUTUBE_API_KEY=AIza...
GOOGLE_SEARCH_API_KEY=AIza...
GOOGLE_CSE_ID=your-cse-id
```

**Check your .env:**
```bash
./check_env_complete.sh
```

If it says missing variables, edit your `.env` file to add them.

## Step 2: Run the Test

```bash
python test_tl_video.py
```

## Step 3: Be Patient!

### Expected Timeline

| Stage | Duration | Notes |
|-------|----------|-------|
| Video Download | 1-2 min | Downloads metadata + subtitles |
| Multimodal Analysis | **30-60 min** | **7 segments × 8 min each** |
| Counter-Intelligence | 2-3 min | YouTube search |
| Claim Verification | 5-10 min | Web search + evidence |
| Report Generation | 1-2 min | JSON + HTML + MD |
| **TOTAL** | **40-80 min** | **For 33-minute video** |

### What's Normal

✅ **NORMAL:**
- No output for 10+ minutes during multimodal analysis
- Each segment takes ~8 minutes
- Total runtime: 40-80 minutes

❌ **NOT NORMAL:**
- Error messages scrolling continuously
- Process exits with error
- No output for 2+ hours

### How to Monitor

Open a second terminal:
```bash
# Watch for segment completion
watch -n 10 "ls -lth verityngn/outputs/tLJC8hkK-ao/analysis/"

# Check logs (if any)
tail -f verityngn/outputs/tLJC8hkK-ao/analysis/*.log 2>/dev/null
```

## What You'll See

```
🚀 VERITYNGN WORKFLOW TEST - tLJC8hkK-ao (LIPOZEM)
📹 Video ID: tLJC8hkK-ao
⏱️  EXPECTED RUNTIME: 30-60 minutes for 33-minute video

📦 Importing verification workflow...
✅ Modules imported successfully

🏗️ Starting verification workflow...
    Stage 1: Initial Analysis (download + multimodal LLM)
    
[Downloads metadata... ~2 minutes]

✅ Video metadata extracted

[LONG SILENCE - 30-60 minutes - THIS IS NORMAL]

✅ Initial analysis completed

[Counter-intelligence... ~3 minutes]

[Claim verification... ~10 minutes]

[Report generation... ~2 minutes]

✅ WORKFLOW COMPLETED SUCCESSFULLY!
```

## If It Actually Hangs

**Only kill it if:**
- No output for > 2 hours
- Continuous errors
- System resources maxed out

**To kill:**
```bash
# In the terminal running the test:
^C  # Press Ctrl+C
```

## After Completion

View the report:
```bash
# HTML (best)
open verityngn/outputs/tLJC8hkK-ao/*/tLJC8hkK-ao_report.html

# JSON
cat verityngn/outputs/tLJC8hkK-ao/*/tLJC8hkK-ao_report.json | jq .

# Markdown
cat verityngn/outputs/tLJC8hkK-ao/*/tLJC8hkK-ao_report.md
```

## Why So Slow?

Each Gemini API call:
1. Accepts YouTube URL (no download needed ✅)
2. Processes video segment with time windows
3. **Takes ~8 minutes to analyze 300 seconds of video**
4. This is normal Gemini processing time for video

The system works correctly - it's just legitimately slow for long videos!

---

**Ready? Run it now!**

```bash
python test_tl_video.py
```

Then grab coffee ☕ and wait 40-60 minutes.

