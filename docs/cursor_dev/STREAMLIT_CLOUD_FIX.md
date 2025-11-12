# Streamlit Cloud PermissionError Fix ✅

**Date**: November 12, 2025  
**Status**: Fixed and Deployed

## Problem

The Streamlit Community Cloud app was crashing with a `PermissionError` when trying to access the filesystem:

```
PermissionError: This app has encountered an error...
File "/mount/src/verityngn-oss/ui/components/enhanced_report_viewer.py", line 316
    if dir_path.exists():
       ^^^^^^^^^^^^^^^^^
```

## Root Cause

Streamlit Cloud runs apps in a sandboxed environment with restricted filesystem access. The report viewer components were trying to check if directories exist using `Path.exists()`, which triggered permission errors when accessing restricted paths.

## Solution

### 1. API Mode Detection
- Added check for `VERITYNGN_API_URL` environment variable
- When API mode is detected (Streamlit Cloud), show user-friendly message
- Direct users to use the "Process Video" tab to view reports

### 2. Error Handling
- Wrapped all filesystem operations in `try/except` blocks
- Handle `PermissionError` and `OSError` gracefully
- Skip inaccessible directories instead of crashing

### 3. Files Fixed
- `ui/components/enhanced_report_viewer.py`
- `ui/components/report_viewer.py`

## Changes Made

```python
# Added API mode detection
API_MODE = os.getenv("VERITYNGN_API_URL") is not None

if API_MODE:
    st.info("🌐 Using API mode - reports will be fetched from the API")
    st.warning("⚠️ Report viewer in API mode: View reports from the 'Process Video' tab after verification completes.")
    return

# Wrapped filesystem checks in try/except
try:
    if dir_path.exists():
        output_dir = dir_path
        break
except (PermissionError, OSError):
    continue
```

## Result

✅ **No more crashes** - App handles permission errors gracefully  
✅ **User-friendly messages** - Clear instructions for Streamlit Cloud users  
✅ **Backward compatible** - Local users can still access reports from filesystem  
✅ **Deployed** - Changes pushed to GitHub (commit: 7e0bee8)

## Usage

In Streamlit Cloud:
1. Submit a verification via "Process Video" tab
2. After completion, use "View Report" buttons in the processing tab
3. Reports are fetched via API, not filesystem

---

**Commit**: `7e0bee8` - Fix Streamlit Cloud PermissionError in report viewers
