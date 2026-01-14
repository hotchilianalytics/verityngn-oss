# VSCode Debugger Setup

## ✅ Configuration Updated

Your `.vscode/launch.json` now has three debug configurations:

### 1. Python Debugger: Current File
**Use for:** Any Python file you have open
- Press `F5` or click "Run and Debug"
- Loads `.env` automatically
- Works with any file

### 2. Debug: Test TL Video
**Use for:** Debugging the full test workflow (`test_tl_video.py`)
- Runs with all required environment variables
- Includes `.env` file
- `justMyCode: false` - steps into library code if needed
- `PYTHONUNBUFFERED: 1` - immediate output (no buffering)

### 3. Debug: Segmented Analysis Test
**Use for:** Debugging just the segmented analysis (`debug_segmented_analysis.py`)
- Quick test of video segmentation
- Only takes 8-12 minutes
- Good for testing without full workflow

## 🚀 How to Use

### Method 1: Quick Debug (Current File)
1. Open `test_tl_video.py`
2. Set breakpoints (click left of line numbers)
3. Press `F5` or click "Run and Debug"
4. Select "Python Debugger: Current File"

### Method 2: Specific Configuration
1. Click "Run and Debug" icon (left sidebar) or press `Ctrl+Shift+D`
2. Select configuration from dropdown (e.g., "Debug: Test TL Video")
3. Press `F5` or click green play button

## 📍 Useful Breakpoints

### For Investigating Slow Performance
```python
# File: verityngn/workflows/analysis.py

# Line 4087: Before segment processing starts
logger.info(f"🎬 [VERTEX] Segment &#123;segment_count + 1&#125;/&#123;total_segments&#125;...")

# Line 4093: When calling LLM (this takes 8-12 minutes)
texts.append(call_segment(start, end))

# Line 3935: Inside call_segment, before API call
resp = model.generate_content(...)

# Line 4041: After segment completes
logger.info(f"[VERTEX] segment=(&#123;start_s&#125;,&#123;end_s&#125;) finish=&#123;finish&#125;...")
```

### For Investigating Segmentation
```python
# File: verityngn/config/video_segmentation.py

# Line 114: See calculated optimal segment duration
max_segment_seconds = int(available_input_tokens / tokens_per_second)

# Line 157: See actual segment size chosen
segment_duration = max_segment

# File: verityngn/workflows/analysis.py

# Line 3803: Where segment duration is calculated
SEGMENT_DURATION_SECONDS = get_segment_duration_from_env_or_optimal(...)
```

## 🔧 Debugger Controls

| Key | Action |
|-----|--------|
| `F5` | Start/Continue |
| `F9` | Toggle Breakpoint |
| `F10` | Step Over (next line) |
| `F11` | Step Into (enter function) |
| `Shift+F11` | Step Out (exit function) |
| `Shift+F5` | Stop Debugging |

## 🐛 Common Debugger Issues

### Issue 1: "No module named X"
**Problem:** Python environment not activated
**Solution:** 
```bash
# In terminal
conda activate verityngn
# Then start debugger
```

### Issue 2: Environment Variables Not Set
**Problem:** Missing credentials
**Solution:** Check your `.env` file has:
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT=verityindex-0-0-1
PROJECT_ID=verityindex-0-0-1
LOCATION=us-central1
```

### Issue 3: Debugger Hangs at API Call
**Problem:** Waiting for Gemini API response (8-12 minutes)
**Solution:** 
- This is NORMAL! 
- Check terminal output for progress logs
- Don't stop debugger - let it continue
- Set breakpoints AFTER the API call to resume when done

### Issue 4: "Cannot import name X"
**Problem:** Circular import or missing dependency
**Solution:**
```bash
# Check imports are working
python -c "from verityngn.workflows.pipeline import run_verification"
```

### Issue 5: Breakpoint Not Hit
**Problem:** Code path not executed
**Solution:**
- Check condition on breakpoint (right-click breakpoint)
- Verify the code is actually running
- Look for early returns or exceptions

## 💡 Pro Tips

### Conditional Breakpoints
Right-click on breakpoint → "Edit Breakpoint" → Add condition:
```python
# Only break for specific segment
segment_count == 0

# Only break if error occurs
'error' in str(e)

# Only break for long videos
duration_sec > 1800
```

### Log Points (No Stop)
Right-click line → "Add Logpoint" → Enter message:
```python
Segment &#123;segment_count&#125;: &#123;start&#125;s to &#123;end&#125;s
```
Logs without stopping execution!

### Watch Expressions
Add to "Watch" panel:
```python
len(texts)
segment_count
duration_sec
SEGMENT_DURATION_SECONDS
tokens_per_second * duration_sec
```

### Debug Console
While paused, test code:
```python
# Check variable values
print(video_info)

# Test calculations
duration_sec / 60

# Import and test functions
from verityngn.config.video_segmentation import calculate_optimal_segment_duration
calculate_optimal_segment_duration("gemini-2.5-flash")
```

## 🎯 Recommended Debug Workflow

### Quick Test (8-12 minutes)
1. Use "Debug: Segmented Analysis Test"
2. Set breakpoint at line 160 in `debug_segmented_analysis.py` (after response)
3. Run - will break after ~8 minutes when Gemini responds
4. Inspect `response.text` to see claims

### Full Test (with monitoring)
1. Use "Debug: Test TL Video"
2. Set breakpoint at line 4093 in `analysis.py` (before segment call)
3. Run until breakpoint
4. Check `SEGMENT_DURATION_SECONDS` value
5. Continue (will take 8-12 minutes)
6. Inspect `texts[0]` to see response

### Investigating Hangs
1. Start without breakpoints
2. Let it run for 2-3 minutes
3. Pause debugger (⏸️ button)
4. Check call stack to see where it is
5. If at API call in `model.generate_content()` - it's normal!

## 📚 Related Files

- `.vscode/launch.json` - This file
- `test_tl_video.py` - Main test script
- `debug_segmented_analysis.py` - Quick test script
- `verityngn/workflows/analysis.py` - Main analysis logic (line 3748+)
- `verityngn/config/video_segmentation.py` - Segmentation calculations

## ❓ Still Having Issues?

**Error message says:** Tell me the exact error message and I'll help!

**Common scenarios:**
- "Module not found" → Python environment issue
- "Authentication failed" → `.env` credentials issue
- "Hangs forever" → Probably waiting for API (check logs)
- "Breakpoint not hit" → Code path not executed

---

**Ready to debug!** Press `F5` and select "Debug: Segmented Analysis Test" for a quick 8-12 minute test! 🐛

