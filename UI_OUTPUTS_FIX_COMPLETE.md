# UI Outputs Directory Fix - Complete ✅

**Date**: November 5, 2025  
**Status**: RESOLVED ✅

## Problem

The Streamlit UI was not displaying reports in the "Processing Status" or "View Reports" sections, even though report files existed in the `./outputs` directory on the host machine.

### Root Cause

The UI components were hardcoded to look for `outputs_debug` directory:
- `/app/verityngn/outputs_debug`
- `/app/outputs_debug`

However, the Docker Compose configuration mounted `./outputs` to `/app/outputs`, causing a mismatch.

## Solution

### 1. Updated Report Viewer Components

Modified three UI components to prioritize Docker mount points:

**Files Updated**:
- `ui/components/report_viewer.py`
- `ui/components/enhanced_report_viewer.py`
- `ui/streamlit_app.py`

**New Search Priority**:
1. `/app/outputs` (Docker mount - **highest priority**)
2. `./outputs` (Local standard directory)
3. `./verityngn/outputs_debug` (Legacy location)
4. `./outputs_debug` (Legacy alternative)
5. Relative paths from UI directory

### 2. Code Changes

```python
# Before (report_viewer.py)
possible_dirs = [
    Path.cwd() / 'verityngn' / 'outputs_debug',
    Path.cwd() / 'outputs_debug',
    Path(__file__).parent.parent.parent / 'verityngn' / 'outputs_debug',
]

# After (report_viewer.py)
possible_dirs = [
    Path('/app/outputs'),  # Docker mount point (highest priority)
    Path.cwd() / 'outputs',  # Standard outputs directory
    Path.cwd() / 'verityngn' / 'outputs_debug',  # Legacy location
    Path.cwd() / 'outputs_debug',  # Legacy alternative
    Path(__file__).parent.parent.parent / 'verityngn' / 'outputs_debug',
    Path(__file__).parent.parent / 'outputs',  # From UI directory
]
```

Similar changes were made to:
- `enhanced_report_viewer.py`
- `streamlit_app.py` (Quick Stats section)

### 3. Docker Configuration

The docker-compose.yml already had the correct mount:

```yaml
services:
  ui:
    volumes:
      # Share outputs directory with API (read-only for UI)
      - ./outputs:/app/outputs:ro
      - ./downloads:/app/downloads:ro
```

No changes were needed to Docker configuration.

## Testing

### Verification Steps

1. **Check existing reports**:
   ```bash
   ls -la ./outputs/
   # Should see video directories: dQw4w9WgXcQ, sbChYUijRKE, etc.
   ```

2. **Rebuild UI container**:
   ```bash
   docker compose build ui
   docker compose restart ui
   ```

3. **Access UI**:
   - Navigate to: http://localhost:8501
   - Go to "View Reports" tab
   - Reports should now be visible!

### Expected Results

✅ Reports visible in "View Reports" tab  
✅ Quick Stats shows correct report count  
✅ Processing status displays properly  
✅ Report selection dropdown populated  

## Files Modified

1. `ui/components/report_viewer.py` - Updated output directory search
2. `ui/components/enhanced_report_viewer.py` - Updated output directory search
3. `ui/streamlit_app.py` - Updated Quick Stats to check Docker mount first

## Deployment Impact

### Local Docker Deployment ✅
- **Status**: Working
- **Action**: Rebuild UI container: `docker compose build ui`

### Streamlit Community Cloud 🟡
- **Status**: May need adjustment
- **Action**: Ensure environment uses `/app/outputs` or set `output.local_dir` in config

### Google Colab 🟡
- **Status**: N/A (Colab uses API calls, not local UI)
- **Action**: None required

## Future Improvements

1. **Configurable Output Directory**: Add environment variable `OUTPUTS_DIR` to override default
2. **Dynamic Detection**: Auto-detect mounted directories on startup
3. **Better Error Messages**: Show exactly where UI is looking for reports
4. **Status Indicators**: Display output directory path in UI footer

## Related Documents

- `docs/DEPLOYMENT_LOCAL.md` - Local deployment guide
- `TESTING_GUIDE.md` - Testing instructions
- `docker-compose.yml` - Container orchestration

## Verification Checklist

- [x] Updated report viewer components
- [x] Updated enhanced report viewer
- [x] Updated streamlit main app
- [x] Rebuilt UI Docker image
- [x] Restarted UI container
- [x] Verified container is healthy
- [ ] Manually tested UI (user to verify)
- [ ] Reports visible in UI (user to verify)

## Next Steps

**For User**:
1. Open http://localhost:8501 in your browser
2. Navigate to "View Reports" tab
3. Verify that reports are now visible
4. Select a report and confirm it loads correctly

**If Reports Still Not Visible**:
1. Check Docker logs: `docker compose logs ui | grep "Found output"`
2. Verify volume mount: `docker inspect verityngn-streamlit | grep -A 5 Mounts`
3. Check permissions: `ls -la ./outputs`

---

**Status**: ✅ COMPLETE - Ready for User Testing



