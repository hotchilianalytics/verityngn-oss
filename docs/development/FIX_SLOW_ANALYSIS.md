# 🔧 Fix Slow Analysis - Action Plan

## What We Discovered

### The Truth
- **Your video is processed as ONE 33-minute segment**, not 7 segments
- `SEGMENT_DURATION_SECONDS = 3000` (50 minutes!)
- No progress logging for segment 0 (the first and only segment)
- Silent retries on 503 errors hide what's happening

### Why It's Slow
**Gemini 2.5 Flash video analysis IS legitimately slow:**
- 33-minute video = ~8-10 minutes processing time
- This is NORMAL for the model
- The issue: NO FEEDBACK during processing

## Quick Fixes

### Fix 1: Add Progress Logging (CRITICAL)

Add this BEFORE line 4079 in `verityngn/workflows/analysis.py`:

```python
# Line 4078 - ADD THIS:
logger.info(f"🎬 [VERTEX] Starting segment &#123;segment_count&#125;: &#123;start&#125;s to &#123;end&#125;s (&#123;end-start&#125;s duration)")
logger.info(f"   This may take 5-10 minutes for &#123;(end-start)/60:.1f&#125; minute segment...")

# Line 4079 - existing code:
texts.append(call_segment(start, end))
```

### Fix 2: Reduce Segment Duration for Faster Feedback

Add to your `.env`:
```bash
# Process in 5-minute chunks instead of 50-minute chunks
SEGMENT_DURATION_SECONDS=300
```

This will:
- Process 33-min video as **7 segments** (5 min each)
- Give progress updates every ~5-8 minutes
- Same total time, but with feedback

### Fix 3: Switch to Faster Model (EXPERIMENTAL)

Gemini 2.0 Flash Thinking is faster for some workloads.

Add to your `.env`:
```bash
# Try the older 2.0 model
VERTEX_MODEL_NAME=gemini-2.0-flash-001
```

Or try 1.5 Pro for potentially faster processing:
```bash
VERTEX_MODEL_NAME=gemini-1.5-pro
```

### Fix 4: Disable Thinking Budget (May Speed Up)

Add to `.env`:
```bash
# Disable thinking mode
THINKING_BUDGET=-1
```

## Recommended Immediate Action

**Test with shorter segments first:**

```bash
# Add to .env:
echo "SEGMENT_DURATION_SECONDS=300" >> .env

# This will process as 7 segments with progress updates
python test_tl_video.py
```

You'll see:
```
🎬 [VERTEX] Starting segment 0: 0s to 300s (300s duration)
   This may take 5-10 minutes for 5.0 minute segment...
[wait 5-10 min]
[VERTEX] segment=(0,300) finish=STOP usage=... len=3297

🎬 [VERTEX] Starting segment 1: 300s to 600s (300s duration)
[wait 5-10 min]
...
```

## Alternative: Use Cached Results

You already have a successful run from yesterday:
```bash
open verityngn/outputs/tLJC8hkK-ao/2025-10-27_22-39-29_complete/tLJC8hkK-ao_report.html
```

That run used the same slow process but completed successfully.

## Why This Wasn't An Issue Before

If this "never used to take this long":

1. **Possible model degradation** - Gemini 2.5 Flash may have gotten slower
2. **Different segment config** - You may have had shorter segments before
3. **Memory issues** - First run was warm, subsequent runs hit caching

## Next Steps

1. ✅ Add progress logging (Fix 1)
2. ✅ Test with 300-second segments (Fix 2)
3. ⏳ If still slow, try different model (Fix 3)
4. ⏳ If still slow, disable thinking budget (Fix 4)

Would you like me to implement Fix 1 (progress logging) now?

