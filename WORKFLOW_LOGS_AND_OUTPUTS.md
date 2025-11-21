# Workflow Logs and Outputs Guide

## 📁 Output Directory Structure

### Base Location
- **Default**: `./outputs/` (in project root)
- **Debug mode**: `./outputs_debug/` (if `DEBUG_OUTPUTS=true`)

### Directory Structure
```
outputs/
├── {video_id}/                    # Video-specific directory
│   ├── {video_id}_workflow.log    # ⭐ WORKFLOW LOG FILE
│   ├── {timestamp}_complete/      # Completed processing runs
│   │   ├── report.json
│   │   ├── report.html
│   │   ├── report.md
│   │   └── ...
│   ├── {timestamp}_processing/   # In-progress runs
│   └── analysis/                  # Analysis artifacts
```

## 📝 Workflow Log Location

### Main Workflow Log
**Location**: `outputs/{video_id}/{video_id}_workflow.log`

**Example**:
```bash
# For video ID: jNQXAC9IVRw
outputs/jNQXAC9IVRw/jNQXAC9IVRw_workflow.log
```

### How to Access

#### Option 1: Command Line
```bash
# View the log file
cat outputs/{video_id}/{video_id}_workflow.log

# Or use tail to follow it in real-time
tail -f outputs/{video_id}/{video_id}_workflow.log

# View last 100 lines
tail -n 100 outputs/{video_id}/{video_id}_workflow.log
```

#### Option 2: Find Latest Log
```bash
# Find all workflow logs
find outputs -name "*workflow.log" -type f

# Find latest workflow log
find outputs -name "*workflow.log" -type f -exec ls -lt {} + | head -1
```

#### Option 3: Streamlit UI
- Go to **"⚙️ Processing"** tab
- View logs in the processing status section
- Or check **"📊 View Reports"** tab for completed runs

## 📊 Output Files Location

### Reports Directory
**Location**: `outputs/{video_id}/{timestamp}_complete/`

**Files**:
- `report.json` - Structured JSON report
- `report.html` - Interactive HTML report
- `report.md` - Markdown report
- `{video_id}_workflow.log` - Complete workflow log

### Example Paths
```bash
# Latest complete run
outputs/jNQXAC9IVRw/2025-11-18_10-30-45_complete/report.html

# Workflow log
outputs/jNQXAC9IVRw/jNQXAC9IVRw_workflow.log
```

## 🔍 Quick Access Commands

### Find Your Current Video's Output
```bash
# Replace {video_id} with your actual video ID
VIDEO_ID="jNQXAC9IVRw"

# View workflow log
cat outputs/${VIDEO_ID}/${VIDEO_ID}_workflow.log

# View latest report
ls -lt outputs/${VIDEO_ID}/*/report.html | head -1

# Open HTML report in browser (macOS)
open outputs/${VIDEO_ID}/*/report.html
```

### List All Recent Workflows
```bash
# List all video directories
ls -lt outputs/ | head -10

# Find latest workflow log
find outputs -name "*workflow.log" -type f -exec ls -lt {} + | head -5
```

## 📋 What's in the Workflow Log?

The workflow log contains:
- ✅ Stage-by-stage progress
- ✅ LLM API calls and responses
- ✅ Token usage and timing
- ✅ Errors and warnings
- ✅ Performance metrics
- ✅ State transitions

**Log Format**:
```
[2025-11-18 10:30:45] [INFO] [verityngn.workflows.pipeline] [run_verification:175] 🚀 Starting verification workflow for: https://www.youtube.com/watch?v=jNQXAC9IVRw
[2025-11-18 10:30:46] [INFO] [verityngn.workflows.pipeline] [run_verification:184] 📹 Video ID: jNQXAC9IVRw
[2025-11-18 10:30:46] [INFO] [verityngn.workflows.pipeline] [run_verification:193] 📁 Output directory: /Users/ajjc/proj/verityngn-oss/outputs/jNQXAC9IVRw
...
```

## 🎯 For Your Current Run

If you're running a video now, check:

1. **Find the video ID** from the URL (e.g., `jNQXAC9IVRw`)

2. **Check if output directory exists**:
   ```bash
   ls -la outputs/{video_id}/
   ```

3. **View workflow log**:
   ```bash
   tail -f outputs/{video_id}/{video_id}_workflow.log
   ```

4. **Check for completed reports**:
   ```bash
   ls -lt outputs/{video_id}/*/report.html
   ```

## 💡 Tips

- **Real-time monitoring**: Use `tail -f` to watch logs as they're written
- **Latest report**: Reports are in timestamped `_complete` directories
- **Multiple runs**: Each run creates a new timestamped directory
- **Debug mode**: Set `DEBUG_OUTPUTS=true` to use `outputs_debug/` instead

