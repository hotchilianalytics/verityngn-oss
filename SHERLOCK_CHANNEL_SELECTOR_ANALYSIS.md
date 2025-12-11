# 🔍 Sherlock Mode Analysis: Channel Selector Failure

## Problem Statement
Channel URL `https://www.youtube.com/@NextMedHealth` produces error:
```
No videos found. Channel may be empty or private.
```

## Investigation Summary

### Step 1: Possible Sources (7 identified)
1. **YouTube API key not configured** - Code checks for key but might fail silently
2. **Channel handle resolution failing** - API search not finding the channel
3. **API permissions/quota issue** - Key might lack permissions or quota exhausted
4. **Exception being swallowed** - Bare `except:` blocks hiding real errors
5. **yt-dlp fallback not triggering** - Fallback logic has bugs
6. **`@st.cache_data` causing stale errors** - Cached error state being returned
7. **Import failure** - `from verityngn.config.settings import YOUTUBE_API_KEY` failing in Streamlit

### Step 2: Most Likely Sources (3 distilled)
1. **Exception handling masking real errors** - Bare `except:` blocks everywhere
2. **Import path issue** - `verityngn.config.settings` import in Streamlit context
3. **Cache returning stale error** - `@st.cache_data` caching failure state

### Step 3: Code Path Analysis

#### Current Flow for @handle URLs
```python
# In fetch_channel_videos()
channel_info = parse_channel_url(url)  # Returns {'type': 'handle', 'identifier': 'NextMedHealth'}

if channel_info['type'] == 'handle':
    # Use yt-dlp for handles
    try:
        import yt_dlp
        url = channel_url + "/videos"  # https://www.youtube.com/@NextMedHealth/videos
        
        ydl_opts = {'quiet': True, 'extract_flat': True, ...}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        entries = info.get('entries', [])
        # Process entries...
        
        if videos:
            return videos, None
        else:
            return [], "No videos found. Channel may be empty or private."
    
    except Exception as ytdlp_error:
        # Error handling...
```

### Step 4: Comprehensive Analysis

#### Issue #1: Silent Import Failures ⚠️

**Location**: Line 233 in `video_input.py`
```python
from verityngn.config.settings import YOUTUBE_API_KEY
```

**Problem**:
- This import happens inside `fetch_channel_videos()` for the API code path
- For @handles, we use yt-dlp directly and never import this
- **BUT**: If the import fails due to Streamlit environment issues, the bare `except:` blocks will hide it

**Evidence**: `verityngn/config/settings.py` line 105:
```python
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", GOOGLE_SEARCH_API_KEY)
```
If both are unset, `YOUTUBE_API_KEY = ""` (empty string, not None!)

#### Issue #2: yt-dlp Failure Modes 🎯

**Possible yt-dlp failures**:
1. **Network timeout** - Channel page not loading
2. **YouTube blocking** - Detecting bot behavior
3. **Empty entries** - `info.get('entries', [])` returns `[]`
4. **Missing video IDs** - Entries exist but `entry.get('id')` returns None
5. **Cookies required** - Some channels need authentication

**Current handling**:
```python
entries = info.get('entries', []) if isinstance(info, dict) else []
# If entries is [], we get "No videos found" message
```

#### Issue #3: Cache Masking Real Errors 🗄️

**Location**: Line 148
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_channel_videos(channel_url: str, max_results: int = 20):
```

**Problem**:
- If yt-dlp fails once, the error message is cached for 5 minutes
- User sees stale "No videos found" even if underlying issue is fixed
- Cache key is based on `(channel_url, max_results)` only

#### Issue #4: Bare Except Blocks Everywhere 🤐

**Locations**:
- Line 204-205: `except:` in date parsing
- Line 256-257: `except:` in API username lookup  
- Line 285-286: `except:` in API search
- Line 296-297: `except:` in legacy username lookup

**Problem**: These hide real errors like:
- `ImportError` if modules missing
- `KeyError` if data structure changed
- `AttributeError` if API response format changed

## Diagnostic Logs Added

Added comprehensive logging to trace execution:

```python
# Entry point
st.write("🔍 DEBUG: fetch_channel_videos called")
st.write(f"🔍 DEBUG: Channel URL: {channel_url}")
st.write(f"🔍 DEBUG: YOUTUBE_API_KEY from os.environ: {'SET' if os.getenv('YOUTUBE_API_KEY') else 'NOT SET'}")

# After parsing
st.write(f"🔍 DEBUG: Parsed channel info: {channel_info}")

# yt-dlp path
st.write("🔍 DEBUG: Using yt-dlp for @handle")
st.write("🔍 DEBUG: yt-dlp imported successfully")
st.write(f"🔍 DEBUG: Extracting info from: {url}")
st.write(f"🔍 DEBUG: Info extracted, type: {type(info)}")
st.write(f"🔍 DEBUG: Found {len(entries)} entries")
st.write(f"🔍 DEBUG: Processed {len(videos)} videos")

# Exception handling
st.error(f"🔍 DEBUG: yt-dlp exception caught: {ytdlp_msg}")
import traceback
st.code(traceback.format_exc())
```

## What to Watch For

When you test with `https://www.youtube.com/@NextMedHealth`, look for:

1. **Does `parse_channel_url` return the right info?**
   - Should be: `{'type': 'handle', 'identifier': 'NextMedHealth'}`

2. **Does yt-dlp import succeed?**
   - If "yt-dlp imported successfully" doesn't show, it's an import error

3. **What does `ydl.extract_info()` return?**
   - Check if `info` is a dict
   - Check if `entries` is an empty list or has items

4. **Are video IDs present?**
   - Check if entries have `'id'` field

5. **Is there a full stack trace?**
   - If exception occurs, full traceback will show

## Next Steps

### Option A: If logs show empty entries
- yt-dlp is working but channel has no videos OR
- YouTube is blocking the request
- **Fix**: Add cookies.txt support or user-agent rotation

### Option B: If logs show import error
- `yt_dlp` module not installed in Streamlit environment
- **Fix**: Verify `requirements.txt` has `yt-dlp>=2024.12.13`

### Option C: If logs show network error
- Timeout or connection refused
- **Fix**: Increase timeout or add retry logic

### Option D: If no logs appear at all
- Cache is returning stale error
- **Fix**: Clear cache with `st.cache_data.clear()` or wait 5 minutes

## Proposed Fixes (After Diagnosis)

### Fix #1: Remove bare except blocks
```python
except Exception as e:  # Specific exception type when possible
    logger.error(f"Error: {e}", exc_info=True)
```

### Fix #2: Add cookies support
```python
ydl_opts = {
    'quiet': True,
    'cookiefile': 'cookies.txt',  # If exists
    ...
}
```

### Fix #3: Add user-agent rotation
```python
from verityngn.config.settings import USER_AGENTS
import random

ydl_opts = {
    'user_agent': random.choice(USER_AGENTS),
    ...
}
```

### Fix #4: Add cache invalidation button
```python
if st.button("🔄 Clear Cache & Retry"):
    st.cache_data.clear()
    st.rerun()
```

## Test Instructions

1. **Deploy to Streamlit Community Cloud** (changes pushed)
2. **Open Verify Video page**
3. **Enter**: `https://www.youtube.com/@NextMedHealth`
4. **Observe debug output** - should see all 🔍 DEBUG messages
5. **Share screenshot** of debug output for analysis

## Conclusion

The root cause is likely:
1. **yt-dlp returning empty entries** (most likely)
2. **YouTube blocking the request** (second most likely)
3. **Cache returning stale error** (possible)

The debug logs will definitively identify which one.

