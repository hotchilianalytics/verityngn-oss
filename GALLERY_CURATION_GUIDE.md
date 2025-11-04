# Gallery Curation Guide

## Overview

The Streamlit gallery displays example verifications to help users understand VerityNgn's capabilities. This guide explains how to curate and add reports from `outputs_debug/` to the gallery.

## Gallery Structure

```
ui/gallery/
├── approved/    # High-quality examples shown in the gallery
├── pending/     # Reports under review (not shown in gallery)
└── rejected/    # Examples not suitable for gallery
```

## Quick Start

### 1. List Available Reports

```bash
python scripts/add_to_gallery.py --list
```

This shows all completed reports in `verityngn/outputs_debug/` with:
- Video ID
- Title
- Verdict
- Timestamp
- File path

### 2. Add a Report to Gallery

#### Add to Approved (shown in gallery)
```bash
python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status approved
```

#### Add to Pending (for review)
```bash
python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status pending
```

#### Add with Custom Title
```bash
python scripts/add_to_gallery.py \
  --video-id tLJC8hkK-ao \
  --status approved \
  --title "Weight Loss Scam Analysis"
```

## Curation Guidelines

### What Makes a Good Gallery Example?

✅ **Good Examples:**
- Clear, unambiguous verdicts
- Diverse content types (health claims, tech products, news)
- Interesting or educational case studies
- Well-structured reports with good evidence
- Range of verdicts (True, False, Uncertain)

❌ **Poor Examples:**
- Incomplete reports
- Processing errors
- Unclear or ambiguous content
- Duplicate or very similar content
- Reports with technical issues

### Recommended Mix

Aim for a diverse gallery:
- **3-5 examples** of clear scams/misinformation
- **2-3 examples** of legitimate content
- **1-2 examples** of uncertain/mixed content
- Different content categories (health, tech, politics, etc.)

## Gallery Metadata

When you add a report to the gallery, the script automatically adds:

```json
{
  "gallery_title": "Custom Title (optional)",
  "gallery_metadata": {
    "added_date": "2025-10-30T...",
    "status": "approved",
    "source_video_id": "tLJC8hkK-ao",
    "curator_notes": ""
  }
}
```

You can manually edit these JSON files to add curator notes or custom descriptions.

## Manual Curation

You can also manually copy and edit reports:

```bash
# Copy report to gallery
cp verityngn/outputs_debug/VIDEO_ID/TIMESTAMP_complete/VIDEO_ID_report.json \
   ui/gallery/approved/VIDEO_ID_custom_name.json

# Edit the JSON to add gallery metadata
```

## Viewing Gallery Items

1. Start Streamlit: `streamlit run ui/app.py`
2. Navigate to the "Gallery" section
3. Only reports in `ui/gallery/approved/` are displayed
4. Reports are shown with their title, verdict, and key findings

## Example Workflow

```bash
# 1. Run a verification
python run_workflow.py https://www.youtube.com/watch?v=VIDEO_ID

# 2. Check if the report is good
# Review the report in outputs_debug/VIDEO_ID/

# 3. List all available reports
python scripts/add_to_gallery.py --list

# 4. Add to gallery
python scripts/add_to_gallery.py --video-id VIDEO_ID --status approved

# 5. Verify in Streamlit
streamlit run ui/app.py
# Check Gallery section
```

## Tips

1. **Review Before Approving**: Always check the report quality before adding to `approved/`
2. **Use Pending**: Add questionable reports to `pending/` first
3. **Diverse Examples**: Aim for variety in content types and verdicts
4. **Update Regularly**: Refresh gallery with better examples as you process more videos
5. **Test Display**: Always check how the report looks in Streamlit before finalizing

## Troubleshooting

**Gallery not showing reports:**
- Ensure reports are in `ui/gallery/approved/` (not `pending/` or `rejected/`)
- Check JSON files are valid (not corrupted)
- Restart Streamlit to reload gallery

**Script can't find report:**
- Verify video ID is correct
- Check report exists in `outputs_debug/VIDEO_ID/*_complete/`
- Ensure report file is named `VIDEO_ID_report.json` or `report.json`

**Reports not loading in Streamlit:**
- Check file permissions
- Verify JSON is valid (run through `python -m json.tool < file.json`)
- Check Streamlit logs for errors


