# Monitoring 11 Reprocessed Videos

## Overview

This document tracks the monitoring of 11 videos that were reprocessed after fixing invalid/placeholder video IDs.

## Quick Commands

### Check Status
```bash
python scripts/check_reprocessed_status.py
```

### Update Status from API
```bash
python scripts/monitor_batch_progress.py --batch-file test_results/batch_2025-11-12T23-07-00/batch_tracking.json --once
```

### Continuous Monitoring (Watch Mode)
```bash
python scripts/monitor_batch_progress.py --batch-file test_results/batch_2025-11-12T23-07-00/batch_tracking.json --watch --interval 60
```

### Import Completed Videos to Gallery
```bash
python scripts/import_test_results_to_gallery.py --batch-file test_results/batch_2025-11-12T23-07-00/batch_tracking.json
```

## Reprocessed Videos

| Test ID | Video ID | Title | Task ID | Status |
|---------|----------|-------|---------|--------|
| 5 | dQw4w9WgXcQ | Essential Oils: Do They Really Work? | 11df841f-46ef-42f8-8767-c65ebaea9d6b | - |
| 6 | YQ_xWvX1n9g | Line Goes Up – The Problem with NFTs | 022a8752-e3dd-4167-9ba2-f5e9d40d4b40 | - |
| 7 | dQw4w9WgXcQ | Coffeezilla: Save the Kids Token Scam | 18963aeb-85b7-45c4-963d-6da6e462334d | - |
| 8 | dQw4w9WgXcQ | The Tinder Swindler | b09cb1b1-5645-4e54-b92e-9571ff8737c0 | - |
| 9 | dQw4w9WgXcQ | The Real Hustle | 6bf7ef59-72b0-47b3-a07c-beeccc126bf3 | - |
| 11 | dQw4w9WgXcQ | Get Rich Quick | f88fa68e-5c16-4c5f-a29e-66cc1343f65b | - |
| 12 | dQw4w9WgXcQ | MLM Schemes | a0d540a6-3e68-4b8d-9602-605f89cf465e | - |
| 14 | dQw4w9WgXcQ | BitConnect | 173d667e-92d2-4c08-9f93-630d2607dfc3 | - |
| 15 | dQw4w9WgXcQ | Bitcoin Prediction | 18ebb5eb-64eb-44e5-ad90-3f86dd8a49fa | - |
| 16 | dQw4w9WgXcQ | Absolute Proof | 55ca6d6a-1bdb-4de1-8170-8a4c248e5e39 | - |
| 19 | VNqNnUJVcVs | In Search of a Flat Earth | d1d45408-2413-4887-8e76-601830f438c3 | - |

## Notes

- Processing time: Previous runs took 3-9 hours per video
- Polling interval: 60 seconds recommended to avoid API rate limiting
- Watch mode: Will automatically exit when all videos complete
- Gallery import: Run after monitoring shows all videos complete

## Status Updates

- **2025-11-13**: Updated batch tracking file with new task IDs
- **2025-11-13**: Initial status check completed
- **2025-11-13**: Continuous monitoring started

