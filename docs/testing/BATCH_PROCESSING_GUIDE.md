# Batch Processing Test Videos Guide

**Version**: 2.1.0  
**Date**: November 12, 2025

This guide explains how to batch process test videos from `test_videos.json` and import the results into the Streamlit Community UI gallery.

---

## Overview

The batch processing system consists of three main scripts:

1. **`batch_process_test_videos.py`** - Submits videos to API for verification
2. **`monitor_batch_progress.py`** - Monitors status of verification tasks
3. **`import_test_results_to_gallery.py`** - Imports completed results to gallery

Plus an orchestration script:

4. **`run_test_suite.py`** - Runs the complete workflow

---

## Prerequisites

1. **API Running**: The VerityNgn API must be running
   ```bash
   # Check API health
   curl http://localhost:8080/health
   
   # Or if using Docker
   docker compose up -d api
   ```

2. **Test Videos File**: `test_videos.json` must exist in project root

3. **Python Dependencies**: Ensure `requests` is installed
   ```bash
   pip install requests
   ```

---

## Quick Start

### Process All Videos

```bash
# Step 1: Submit all videos for processing
python scripts/batch_process_test_videos.py

# Step 2: Monitor progress (in another terminal)
python scripts/monitor_batch_progress.py --watch

# Step 3: Import completed videos to gallery
python scripts/import_test_results_to_gallery.py --batch-file test_results/batch_.../batch_tracking.json
```

### Or Use the Orchestration Script

```bash
# Process all videos and auto-import when done
python scripts/run_test_suite.py --process-all --auto-import
```

---

## Detailed Usage

### 1. Batch Processing Script

**File**: `scripts/batch_process_test_videos.py`

**Purpose**: Submits videos from `test_videos.json` to the API for verification.

**Basic Usage**:
```bash
# Process all videos
python scripts/batch_process_test_videos.py

# Process only first 5 videos
python scripts/batch_process_test_videos.py --limit 5

# Process specific category
python scripts/batch_process_test_videos.py --category "Health & Medicine"

# Process single video
python scripts/batch_process_test_videos.py --video-id tLJC8hkK-ao

# Skip videos that already have results
python scripts/batch_process_test_videos.py --skip-existing

# Use custom API URL
python scripts/batch_process_test_videos.py --api-url http://localhost:8080
```

**Output**:
- Creates `test_results/batch_&#123;timestamp&#125;/batch_tracking.json`
- Tracks all submitted videos and their task IDs
- Shows status summary at the end

**Example Output**:
```
✅ Found 20 video(s) to process
✅ API is healthy
📂 Created new batch: batch_2025-11-12T10-30-00

🚀 Submitting 20 video(s) to API...
[1/20] Processing: [LIPOZEM] Exclusive Interview...
  ✅ Submitted successfully (task_id: abc-123-def)
...
```

---

### 2. Status Monitoring Script

**File**: `scripts/monitor_batch_progress.py`

**Purpose**: Polls the API to update status of all verification tasks.

**Basic Usage**:
```bash
# Monitor latest batch (update once)
python scripts/monitor_batch_progress.py

# Watch mode (continuous monitoring)
python scripts/monitor_batch_progress.py --watch

# Monitor specific batch file
python scripts/monitor_batch_progress.py --batch-file test_results/batch_.../batch_tracking.json

# Custom polling interval (default: 10 seconds)
python scripts/monitor_batch_progress.py --watch --interval 30
```

**Output**:
- Updates batch tracking file with latest status
- Shows progress summary:
  - Total videos, completed, processing, pending, errors
  - Currently processing videos
  - Recent completions
  - Estimated time remaining

**Example Output**:
```
📊 Batch Status: batch_2025-11-12T10-30-00
Total videos: 20
  ✅ Completed: 5
  🔄 Processing: 3
  ⏳ Pending: 2
  ❌ Error: 0

🔄 Currently processing (3):
  • tLJC8hkK-ao: [LIPOZEM] Exclusive Interview...
    Progress: 45.2% - Verifying claims...
```

---

### 3. Gallery Import Script

**File**: `scripts/import_test_results_to_gallery.py`

**Purpose**: Imports completed verification results into the Streamlit gallery.

**Basic Usage**:
```bash
# Import all completed videos
python scripts/import_test_results_to_gallery.py --batch-file test_results/batch_.../batch_tracking.json

# Dry run (preview without importing)
python scripts/import_test_results_to_gallery.py --batch-file ... --dry-run

# Import with filters
python scripts/import_test_results_to_gallery.py --batch-file ... --min-claims 10 --verdict-match

# Import specific category
python scripts/import_test_results_to_gallery.py --batch-file ... --category "Health & Medicine"
```

**Filters**:
- `--min-claims N`: Only import videos with at least N claims
- `--verdict-match`: Only import if verdict matches expected
- `--category CATEGORY`: Only import specific category
- `--status STATUS`: Only import videos with specific status (default: completed)

**Output**:
- Copies report JSON files to `ui/gallery/approved/`
- Enhances reports with test metadata
- Shows import summary

**Example Output**:
```
📊 Import Summary:
  Total videos in batch: 20
  Videos to import: 15
  Videos skipped: 5

📋 Videos to import (15):
  • tLJC8hkK-ao: [LIPOZEM] Exclusive Interview...
    Verdict: Likely to be False, Claims: 20

📤 Importing to gallery...
  ✅ tLJC8hkK-ao: [LIPOZEM] Exclusive Interview...
  ...
```

---

### 4. Orchestration Script

**File**: `scripts/run_test_suite.py`

**Purpose**: Runs the complete workflow in one command.

**Basic Usage**:
```bash
# Process all videos
python scripts/run_test_suite.py --process-all

# Process and auto-import when done
python scripts/run_test_suite.py --process-all --auto-import

# Process specific category
python scripts/run_test_suite.py --category "Health & Medicine" --limit 5

# Monitor existing batch
python scripts/run_test_suite.py --monitor --watch

# Import only (skip processing)
python scripts/run_test_suite.py --import-only --batch-file test_results/batch_.../batch_tracking.json
```

---

## Workflow Examples

### Example 1: Process All Videos

```bash
# Terminal 1: Start API (if not running)
docker compose up -d api

# Terminal 2: Submit all videos
python scripts/batch_process_test_videos.py

# Terminal 2: Monitor progress
python scripts/monitor_batch_progress.py --watch

# Terminal 2: When done, import to gallery
python scripts/import_test_results_to_gallery.py --batch-file test_results/batch_.../batch_tracking.json
```

### Example 2: Process Specific Category

```bash
# Process only Health & Medicine videos
python scripts/batch_process_test_videos.py --category "Health & Medicine"

# Monitor
python scripts/monitor_batch_progress.py --watch

# Import with quality filter
python scripts/import_test_results_to_gallery.py \
  --batch-file test_results/batch_.../batch_tracking.json \
  --min-claims 15 \
  --verdict-match
```

### Example 3: Quick Test with Single Video

```bash
# Process single video (already processed baseline)
python scripts/batch_process_test_videos.py --video-id tLJC8hkK-ao --skip-existing

# Monitor
python scripts/monitor_batch_progress.py --watch

# Import
python scripts/import_test_results_to_gallery.py --batch-file test_results/batch_.../batch_tracking.json
```

---

## File Structure

### Batch Tracking File

Location: `test_results/batch_&#123;timestamp&#125;/batch_tracking.json`

Structure:
```json
&#123;
  "batch_id": "batch_2025-11-12T10-30-00",
  "started_at": "2025-11-12T10:30:00",
  "total_videos": 20,
  "api_url": "http://localhost:8080",
  "videos": [
    &#123;
      "test_id": 1,
      "video_id": "tLJC8hkK-ao",
      "youtube_url": "https://www.youtube.com/watch?v=tLJC8hkK-ao",
      "title": "[LIPOZEM] Exclusive Interview...",
      "category": "Health & Medicine",
      "task_id": "abc-123-def",
      "status": "completed",
      "submitted_at": "2025-11-12T10:30:05",
      "completed_at": "2025-11-12T11:30:00",
      "result_path": "outputs/tLJC8hkK-ao/2025-11-12T10-30-05_complete",
      "processing_time_seconds": 3595,
      "error_message": null
    &#125;
  ]
&#125;
```

### Gallery Files

Location: `ui/gallery/approved/&#123;video_id&#125;_&#123;title_slug&#125;.json`

Structure: Original report JSON + test metadata:
```json
&#123;
  ...original report fields...,
  "test_metadata": &#123;
    "test_id": 1,
    "category": "Health & Medicine",
    "subcategory": "Weight Loss Supplements",
    "expected_verdict": "Likely False",
    "tags": ["supplements", "weight-loss"],
    "imported_at": "2025-11-12T12:00:00",
    "imported_from": "test_videos.json",
    "verdict_match": true
  &#125;
&#125;
```

---

## Troubleshooting

### API Not Responding

**Problem**: `Connection error to http://localhost:8080`

**Solution**:
```bash
# Check if API is running
curl http://localhost:8080/health

# Start API if needed
docker compose up -d api

# Or start directly
python -m verityngn.api
```

### Videos Not Completing

**Problem**: Videos stuck in "processing" status

**Solution**:
- Check API logs: `docker compose logs api -f`
- Check workflow logs in `outputs/&#123;video_id&#125;/&#123;video_id&#125;_workflow.log`
- Verify API has sufficient resources
- Check for rate limiting or API errors

### Import Fails

**Problem**: `Report file not found`

**Solution**:
- Verify video completed successfully
- Check `outputs/&#123;video_id&#125;/` directory
- Ensure `&#123;video_id&#125;_report.json` exists in `*_complete` directory
- Try running import with `--dry-run` first

### Batch File Not Found

**Problem**: `No batch tracking file found`

**Solution**:
- Run `batch_process_test_videos.py` first to create batch file
- Or specify `--batch-file` with full path
- Check `test_results/` directory for existing batches

---

## Best Practices

1. **Start Small**: Test with `--limit 1` or `--video-id` first
2. **Monitor Progress**: Use `--watch` mode to track progress
3. **Quality Filter**: Use `--min-claims` and `--verdict-match` when importing
4. **Dry Run**: Always use `--dry-run` before importing to gallery
5. **Backup**: Keep batch tracking files for reference
6. **Review**: Manually review imported videos in gallery before making public

---

## Next Steps

After importing videos to gallery:

1. **Verify in Streamlit UI**: Check that videos display correctly
2. **Review Reports**: Ensure reports are complete and accurate
3. **Update Gallery**: Add more videos or remove low-quality ones
4. **Share**: Gallery is ready for Streamlit Community Cloud deployment

---

## See Also

- `docs/testing/TEST_VIDEOS_v2.1.0.md` - Test video list and descriptions
- `scripts/add_to_gallery.py` - Manual gallery import script
- `ui/components/gallery.py` - Gallery display component

