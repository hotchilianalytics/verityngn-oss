# Gallery and Secrets Improvements

## Issues Addressed

### 1. Gallery Only Showing 8 Videos
**Problem**: Gallery was only displaying a small number of videos, missing videos like `Jh0EuOxBwwE` and others.

**Root Cause**: Multiple limiting factors in the data fetch pipeline:
- UI was fetching only 100 videos from API
- API default limit was 50 videos
- API max limit was capped at 200

**Solution**: Increased limits throughout the stack:
- **UI Gallery**: Now fetches 200 videos (up from 100)
- **API Default**: Changed from 50 to 100 videos
- **API Maximum**: Increased cap from 200 to 500 videos

**Files Changed**:
- `ui/components/gallery.py` - Line 221: `limit=200` (was 100)
- `ui/components/gallery.py` - Line 20: Default changed to 200
- `verityngn-cloudrun-batch/api/routes/batch.py` - Line 388: Default 100, max 500

**Result**: Gallery will now display up to **200 videos** instead of being limited to ~8-100.

---

### 2. Channel Selector Limited to 20 Videos
**Problem**: Channel video selector was only showing 20 videos from a channel.

**Solution**: Increased to 50 videos for better channel browsing.

**Files Changed**:
- `ui/components/video_input.py` - Line 149: `max_results: int = 50` (was 20)
- `ui/components/video_input.py` - Line 593: `fetch_channel_videos(channel_url, max_results=50)`

**Result**: Channel selector now shows **50 latest videos** from any YouTube channel.

---

### 3. YOUTUBE_API_KEY Not Reading from Streamlit Secrets
**Problem**: Code at line 317-318 in `video_input.py` was importing:
```python
from verityngn.config.settings import YOUTUBE_API_KEY
```

This only reads from `os.environ`, not Streamlit secrets (`st.secrets`), causing API key to be unavailable in Streamlit Community Cloud deployment.

**Root Cause**: 
- `verityngn/config/settings.py` loads from `.env` at import time
- Streamlit Community Cloud uses `st.secrets.toml`, not `.env`
- Import happens before secrets are in `os.environ`

**Solution**: Created helper function `get_youtube_api_key()` that:
1. **Checks `st.secrets` first** (for Streamlit Community Cloud)
2. **Falls back to `os.environ`** (for local development)
3. **Works in both environments**

**Implementation**:
```python
def get_youtube_api_key() -> Optional[str]:
    """Get YouTube API key from st.secrets (priority) or os.environ."""
    # Try Streamlit secrets first (for Streamlit Community Cloud)
    try:
        if hasattr(st, 'secrets') and 'YOUTUBE_API_KEY' in st.secrets:
            return st.secrets['YOUTUBE_API_KEY']
    except Exception:
        pass
    
    # Fall back to environment variable
    return os.getenv('YOUTUBE_API_KEY')
```

**Files Changed**:
- `ui/components/video_input.py` - Lines 162-174: Added helper function
- `ui/components/video_input.py` - Line 324: Updated API code to use helper

**Result**: 
- ✅ Works in **Streamlit Community Cloud** (reads from `st.secrets`)
- ✅ Works in **local development** (reads from `.env` via `os.environ`)
- ✅ Proper priority: Streamlit secrets → environment variables

---

## Testing

### Gallery
1. Open Gallery tab in Streamlit
2. Click "🔄 Refresh" to clear cache
3. Should now see up to 200 videos (previously ~8-100)
4. Scroll through to verify more videos are visible

### Channel Selector
1. Go to "Verify Video" tab
2. Enter a channel URL: `https://www.youtube.com/@NextMedHealth`
3. Should see up to 50 videos in dropdown (previously 20)

### Streamlit Secrets (Cloud)
1. Deploy to Streamlit Community Cloud
2. Verify `YOUTUBE_API_KEY` is set in secrets.toml
3. Channel selector should work without errors
4. Check debug output: Should show "YOUTUBE_API_KEY: SET"

---

## Deployment Status

### ✅ Committed and Pushed
- `verityngn-oss`: Commit `423c34c` - UI changes and secrets helper
- `verityngn-cloudrun-batch`: Commit `93731b9` - API limit increases

### Next Steps
1. **Streamlit Community Cloud**: Will auto-deploy OSS changes
2. **Cloud Run API**: Needs manual redeployment for limit changes
3. **Verify**: Check gallery shows more videos after deployment

---

## API Impact

### Gallery API Endpoint Changes
**Before**:
```
GET /api/v1/gallery/list?limit=50&offset=0
```
- Default: 50 videos
- Max: 200 videos

**After**:
```
GET /api/v1/gallery/list?limit=100&offset=0
```
- Default: 100 videos
- Max: 500 videos

**Backwards Compatible**: ✅ Yes
- Existing calls with explicit `limit` parameter unchanged
- Only affects default behavior and maximum allowed

---

## Future Enhancements

### Pagination Support
Currently fetching all videos in single request. Consider adding:
- **"Load More" button** to fetch next page
- **Infinite scroll** for seamless browsing
- **Virtual scrolling** for performance with 500+ videos

### Channel Selector
Consider adding:
- **"Load All Videos" option** for channels with >50 videos
- **Date range filter** (e.g., "Last 6 months")
- **Sort options** (newest first, most popular, etc.)

### Secrets Management
Consider generalizing the pattern:
```python
def get_secret(key: str, default: Any = None) -> Any:
    """Get secret from st.secrets or os.environ."""
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)
```

---

## Debug Output (Reference)

When channel selector is used, debug output will show:
```
🔍 DEBUG: fetch_channel_videos called
🔍 DEBUG: Channel URL: https://www.youtube.com/@NextMedHealth
🔍 DEBUG: max_results: 50
🔍 DEBUG: YOUTUBE_API_KEY: SET
```

This confirms:
- Function is being called
- Correct URL is passed
- Increased limit is active
- API key is properly loaded

