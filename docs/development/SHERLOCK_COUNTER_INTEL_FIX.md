# Sherlock Mode Analysis: Counter-Intelligence Missing

## 🔍 Problem Identified

Latest run at `/Users/ajjc/proj/verityngn-oss/verityngn/outputs/tLJC8hkK-ao/2025-10-27_11-10-50_complete/` shows:

```markdown
## 8. Counter-Intelligence Analysis
No counter-intelligence analysis data was available for this report.
```

JSON shows empty arrays:

```json
"youtube_counter_intelligence": [],
"press_release_counter_intelligence": []
```

## 📊 Sherlock Mode Analysis

### Step 1: 7 Possible Sources

1. Counter-intel disabled in settings ❌
2. API keys missing ⚠️ (User has keys in .env)
3. **Import errors from private modules** ✅ **ROOT CAUSE**
4. Counter-intel stage not being called ❌ (Verified it's in workflow graph)
5. Empty results being returned silently ✅ **CONTRIBUTING FACTOR**
6. Enhanced features flag disabled ❌ (Checked, it's enabled)
7. Workflow graph changes ❌ (Graph is correctly connected)

### Step 2: Distilled Root Causes

1. **Private repo modules don't exist** (PRIMARY)
   - `verityngn.services.search.deep_ci` - Not in OSS repo
   - `verityngn.services.search.youtube_api` - Not in OSS repo

2. **OSS alternatives exist but not used** (SECONDARY)
   - `verityngn.services.search.youtube_search.py` - **EXISTS and has the functions we need!**
   - `search_youtube_counter_intelligence_with_context()` function available

3. **Silent failures** (CONTRIBUTING)
   - try-except ImportError catches but only logs INFO/WARNING
   - Function continues with empty lists
   - No prominent error shown to user

### Step 3: Code Path Analysis

**Workflow graph (CORRECT):**

```
initial_analysis → counter_intel_once → prepare_claims → claim_verification → ...
```

**Counter-intel execution:**

```python
# Line 124-135: Try private deep_ci module
try:
    from verityngn.services.search.deep_ci import deep_counter_intel_search
    deep_links = deep_counter_intel_search(search_context, max_links=4)
except ImportError:
    logger.info("Deep CI module not available (private repo feature)")  # ⚠️ INFO only
    deep_links = []  # ⚠️ Empty!

# Line 148-165: Try private youtube_api module
try:
    from verityngn.services.search.youtube_api import search_counter_intelligence
    api_results = search_counter_intelligence(...)
except ImportError:
    logger.info("YouTube API module not available (private repo feature)")  # ⚠️ INFO only
    # ⚠️ NO FALLBACK TO OSS MODULE!

# Line 237: Store empty results
state["ci_once"] = merged_results  # Empty list!
logger.info(f"✅ Counter-intelligence complete: 0 total links")  # ⚠️ Says "complete" even with 0 results
```

**What happens:**

1. Both private modules fail with ImportError
2. Logs show INFO messages (not prominent)
3. Function returns empty list
4. Report generation says "No counter-intelligence analysis data was available"
5. User sees Section 8 with no content

### Step 4: The Fix

**Added OSS Fallback Path:**

```python
except ImportError:
    # OSS FALLBACK: Use public youtube_search module
    logger.info("📦 Using OSS YouTube search (private module not available)")
    try:
        from verityngn.services.search.youtube_search import (
            search_youtube_counter_intelligence_with_context,
        )
        
        api_results = search_youtube_counter_intelligence_with_context(
            video_title=title or f"Video &#123;video_id&#125;",
            initial_review_text=initial_text or None,
            video_id=video_id,
            max_results=4,
        )
        logger.info(f"✅ OSS YouTube search found &#123;len(api_results)&#125; counter-intel results")
    except Exception as oss_error:
        logger.error(f"❌ OSS YouTube search also failed: &#123;oss_error&#125;")
        api_results = []
```

**Added Prominent Warning for Zero Results:**

```python
if len(merged_results) == 0:
    logger.warning(
        f"⚠️  Counter-intelligence found ZERO results for video &#123;video_id&#125;. "
        "This may indicate:\n"
        "   1. Private repo modules not available (expected for OSS)\n"
        "   2. YouTube API key not configured (check .env)\n"
        "   3. Google Search API key not configured (check .env)\n"
        "   4. Network/API errors occurred\n"
        "Check logs above for specific errors."
    )
```

## 🎯 What This Fixes

### Before (Broken)

- ❌ Counter-intel returns empty results silently
- ❌ Section 8 says "No counter-intelligence analysis data"
- ❌ OSS users get no counter-intel at all
- ❌ No clear error message about what's wrong

### After (Fixed)

- ✅ Counter-intel uses OSS `youtube_search.py` module as fallback
- ✅ Section 8 will have YouTube counter-intel data
- ✅ Works for OSS users with YouTube API key configured
- ✅ Clear WARNING if still no results (with diagnostic info)

## 📋 Files Modified

- `/Users/ajjc/proj/verityngn-oss/verityngn/workflows/counter_intel.py`
  - Added OSS fallback to `youtube_search.py` module
  - Added prominent warning for zero results
  - Better logging to show which path is taken

## 🧪 Testing Required

1. **With YouTube API key configured** (user has this):

   ```bash
   cd /Users/ajjc/proj/verityngn-oss
   python -m verityngn.workflows.pipeline "https://www.youtube.com/watch?v=tLJC8hkK-ao"
   ```

   **Expected:**
   - Should find counter-intel videos
   - Section 8 should have content
   - Logs show: "📦 Using OSS YouTube search"

2. **Without YouTube API key**:

   ```bash
   unset YOUTUBE_API_KEY
   unset GOOGLE_API_KEY
   python -m verityngn.workflows.pipeline "https://www.youtube.com/watch?v=tLJC8hkK-ao"
   ```

   **Expected:**
   - Should show WARNING about zero results
   - Section 8 says "No counter-intelligence analysis data"
   - Logs explain why (API key not configured)

## 🚀 Next Steps

1. ✅ **Fix applied** - OSS fallback path added
2. ⏳ **Test with tLJC8hkK-ao** - Verify counter-intel works
3. ⏳ **Check Section 8** - Should have YouTube counter-evidence
4. ⏳ **Verify transcript analysis** - Should analyze debunking videos
5. ⏳ **Check enhanced features** - All should be working

## 💡 Additional Improvements Needed

Based on plan in `/i.plan.md`, we still need to:

1. **Enhanced claim extraction** - Multi-pass with specificity scoring
2. **Absence claims** - Extract what's NOT mentioned (Dr. Ross credentials)
3. **Probability-based sampling** - Get claims from distribution tails
4. **Type-specific verification queries** - Better search queries per claim type
5. **Claim quality metrics** - Add specificity and verifiability scores

These are separate from the counter-intel fix and should be tackled next.

## 📊 Success Criteria

Counter-intelligence will be working when:

- ✅ Section 8 has counter-evidence data
- ✅ YouTube debunking videos are found and analyzed
- ✅ Transcript analysis shows counter-arguments
- ✅ Report shows "Claims with YouTube Counter-Intelligence Evidence: N" (N > 0)
- ✅ Logs show successful OSS fallback path

---

**Status:** ✅ FIX APPLIED - Ready for testing


