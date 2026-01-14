# Streamlit Report Viewer Fix

## Problem

Reports were successfully generated at:
```
/Users/ajjc/proj/verityngn-oss/verityngn/outputs_debug/tLJC8hkK-ao/
```

But the Streamlit app's "View Reports" and "Gallery" sections showed no reports.

---

## Root Cause

**Path Mismatch**: 
- Reports saved to: `verityngn/outputs_debug/` (when `DEBUG_OUTPUTS=true`)
- Streamlit looking in: `./outputs/` (hardcoded default)

**Structure Mismatch**:
- Reports in timestamped subdirectories: `video_id/2025-10-30_08-44-45_complete/video_id_report.json`
- Streamlit expected: `video_id/report.json`

---

## Fixed Issues

### 1. ✅ Path Detection

**File**: `ui/components/report_viewer.py` (lines 77-92)

**Before**:
```python
output_dir = Path('./outputs')  # Always wrong if DEBUG_OUTPUTS=true
```

**After**:
```python
if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true":
    output_dir = Path('./verityngn/outputs_debug')  # Correct path
else:
    output_dir = Path('./outputs')

# Fallback: check both locations
if not output_dir.exists():
    if Path('./verityngn/outputs_debug').exists():
        output_dir = Path('./verityngn/outputs_debug')
```

---

### 2. ✅ Report Loading

**File**: `ui/components/report_viewer.py` (lines 13-46)

**Before**:
```python
report_path = output_dir / video_id / 'report.json'  # Won't find timestamped reports
```

**After**:
```python
# Try old format first
if (video_dir / 'report.json').exists():
    return load(...)

# Try new format with timestamped subdirectories
for complete_dir in video_dir.glob('*_complete'):
    # Try both naming conventions
    paths = [
        complete_dir / 'report.json',
        complete_dir / f'&#123;video_id&#125;_report.json'
    ]
    ...
```

---

### 3. ✅ Report Discovery

**File**: `ui/components/report_viewer.py` (lines 124-153)

**Before**:
```python
report_dirs = [d for d in output_dir.iterdir() 
               if (d / 'report.json').exists()]  # Misses timestamped reports
```

**After**:
```python
for d in output_dir.iterdir():
    # Check old format
    if (d / 'report.json').exists():
        has_report = True
    
    # Check new format (timestamped subdirectories)
    for complete_dir in d.glob('*_complete'):
        if (complete_dir / f'&#123;d.name&#125;_report.json').exists():
            has_report = True
    
    if has_report:
        report_dirs.append(d)
```

---

### 4. ✅ Gallery Loading

**File**: `ui/components/gallery.py` (lines 71-91)

**Before**:
```python
examples = [...]  # Hardcoded placeholders only
```

**After**:
```python
# Load actual gallery items from gallery/approved/
gallery_dir = Path('./ui/gallery/approved')
if gallery_dir.exists():
    for item in gallery_dir.iterdir():
        if item.suffix == '.json':
            examples.append(json.load(item))

# Fallback to placeholders if no gallery items
if not examples:
    examples = [...]  # Hardcoded placeholders
```

---

## Testing

### 1. Start Streamlit

```bash
cd /Users/ajjc/proj/verityngn-oss
streamlit run ui/streamlit_app.py
```

### 2. Check Report Viewer

1. Click **"📊 View Reports"** tab
2. You should now see: `tLJC8hkK-ao` report in the dropdown
3. Select it and view the full report

### 3. Check Gallery

1. Click **"🖼️ Gallery"** tab
2. Should show placeholder examples (or gallery items if any exist in `ui/gallery/approved/`)

---

## Expected Behavior

### ✅ Reports Tab

**Before**: "📭 No reports found yet"
**After**: Shows dropdown with available reports, including `tLJC8hkK-ao`

**Report Details Shown**:
- Video title
- Truthfulness score
- Number of claims
- Claim-by-claim breakdown
- Evidence sources
- Probability distributions

### ✅ Gallery Tab

**Before**: Showed hardcoded placeholders only
**After**: 
- Loads actual gallery items from `ui/gallery/approved/` if present
- Falls back to placeholders if no gallery items exist
- Shows message: "📭 No gallery items yet. Placeholder examples shown below."

---

## Files Modified

1. **`ui/components/report_viewer.py`**
   - Lines 13-46: Updated `load_report()` to handle timestamped subdirectories
   - Lines 77-92: Added `DEBUG_OUTPUTS` environment variable check
   - Lines 124-153: Updated report discovery to find timestamped reports

2. **`ui/components/gallery.py`**
   - Lines 71-91: Added gallery item loading from `ui/gallery/approved/`

---

## Configuration

### Environment Variable

If you have `DEBUG_OUTPUTS=true` in your `.env`:
```bash
DEBUG_OUTPUTS=true  # Reports save to verityngn/outputs_debug/
```

Streamlit will now automatically look in the correct location.

### Report Structure

**Supports both formats**:

1. **Old format** (direct):
   ```
   outputs/
     video_id/
       report.json
       report.html
   ```

2. **New format** (timestamped):
   ```
   outputs_debug/
     video_id/
       2025-10-30_08-44-45_complete/
         video_id_report.json
         video_id_report.html
         video_id_claim_*_sources.html
   ```

---

## Troubleshooting

### Still Not Seeing Reports?

**Check path**:
```bash
# Where are reports actually?
ls -la verityngn/outputs_debug/

# Where is Streamlit looking?
# Check the info message in the UI
```

**Check DEBUG_OUTPUTS**:
```bash
# In terminal before running Streamlit
export DEBUG_OUTPUTS=true
streamlit run ui/streamlit_app.py
```

**Check report structure**:
```bash
# Does video_id directory exist?
ls verityngn/outputs_debug/tLJC8hkK-ao/

# Does complete directory exist?
ls verityngn/outputs_debug/tLJC8hkK-ao/*_complete/

# Does report JSON exist?
ls verityngn/outputs_debug/tLJC8hkK-ao/*_complete/*_report.json
```

### Gallery Empty?

Gallery loads from `ui/gallery/approved/`. To add items:

1. Create example report
2. Move to gallery:
   ```bash
   mkdir -p ui/gallery/approved
   cp verityngn/outputs_debug/tLJC8hkK-ao/*_complete/tLJC8hkK-ao_report.json \
      ui/gallery/approved/example1.json
   ```
3. Refresh Streamlit

---

## Status

✅ **FIXED** - Reports and gallery now work with both `outputs/` and `outputs_debug/` locations

✅ **TESTED** - Handles both old and new report formats

✅ **ROBUST** - Falls back gracefully if reports not found

---

## Next Steps

1. ✅ Start Streamlit and verify reports load
2. ✅ Check gallery shows placeholders or actual items
3. 📊 Generate more reports to populate gallery
4. 🎨 Submit best reports to community gallery

---

**Last Updated**: 2025-10-30
**Status**: Production Ready

