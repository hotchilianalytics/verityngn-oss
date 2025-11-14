#!/usr/bin/env python3
"""
Import test results to Streamlit gallery.

This script reads a batch tracking file and imports completed verification
results into the Streamlit gallery for display in the UI.

Usage:
    # Import all completed videos
    python scripts/import_test_results_to_gallery.py --batch-file test_results/batch_.../batch_tracking.json

    # Dry run (preview what would be imported)
    python scripts/import_test_results_to_gallery.py --batch-file ... --dry-run

    # Import with filters
    python scripts/import_test_results_to_gallery.py --batch-file ... --min-claims 10 --verdict-match

    # Import specific category
    python scripts/import_test_results_to_gallery.py --batch-file ... --category "Health & Medicine"
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
TEST_VIDEOS_FILE = project_root / "test_videos.json"
GALLERY_DIR = project_root / "ui" / "gallery" / "approved"
OUTPUTS_DIR = project_root / "outputs"


def load_test_videos() -> Dict[str, Any]:
    """Load test videos metadata."""
    if not TEST_VIDEOS_FILE.exists():
        return {}
    
    with open(TEST_VIDEOS_FILE, 'r') as f:
        return json.load(f)


def load_batch_tracking(tracking_file: Path) -> Dict[str, Any]:
    """Load batch tracking file."""
    with open(tracking_file, 'r') as f:
        return json.load(f)


def find_report_file(video_id: str, result_path: Optional[str] = None) -> Optional[Path]:
    """Find the report JSON file for a video."""
    # Try result_path first if provided
    if result_path:
        result_dir = project_root / result_path
        report_file = result_dir / f"{video_id}_report.json"
        if report_file.exists():
            return report_file
        # Try alternative name
        report_file = result_dir / "report.json"
        if report_file.exists():
            return report_file
    
    # Fallback: search in outputs directory
    video_dir = OUTPUTS_DIR / video_id
    if not video_dir.exists():
        return None
    
    # Find most recent _complete directory
    complete_dirs = sorted(
        [d for d in video_dir.glob("*_complete") if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )
    
    for complete_dir in complete_dirs:
        report_file = complete_dir / f"{video_id}_report.json"
        if report_file.exists():
            return report_file
        # Try alternative name
        report_file = complete_dir / "report.json"
        if report_file.exists():
            return report_file
    
    return None


def find_html_report_file(video_id: str, result_path: Optional[str] = None, json_report_path: Optional[Path] = None) -> Optional[Path]:
    """Find the HTML report file for a video."""
    # If we have the JSON report path, look in the same directory
    if json_report_path:
        html_file = json_report_path.parent / f"{video_id}_report.html"
        if html_file.exists():
            return html_file
        # Try alternative names
        html_file = json_report_path.parent / f"{video_id}_final_report.html"
        if html_file.exists():
            return html_file
        html_file = json_report_path.parent / "report.html"
        if html_file.exists():
            return html_file
    
    # Try result_path first if provided
    if result_path:
        result_dir = project_root / result_path
        html_file = result_dir / f"{video_id}_report.html"
        if html_file.exists():
            return html_file
        html_file = result_dir / f"{video_id}_final_report.html"
        if html_file.exists():
            return html_file
    
    # Fallback: search in outputs directory
    video_dir = OUTPUTS_DIR / video_id
    if not video_dir.exists():
        return None
    
    # Find most recent _complete directory
    complete_dirs = sorted(
        [d for d in video_dir.glob("*_complete") if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )
    
    for complete_dir in complete_dirs:
        html_file = complete_dir / f"{video_id}_report.html"
        if html_file.exists():
            return html_file
        html_file = complete_dir / f"{video_id}_final_report.html"
        if html_file.exists():
            return html_file
        html_file = complete_dir / "report.html"
        if html_file.exists():
            return html_file
    
    return None


def load_report(report_file: Path) -> Dict[str, Any]:
    """Load report JSON file."""
    with open(report_file, 'r') as f:
        return json.load(f)


def get_verdict_from_report(report: Dict[str, Any]) -> Optional[str]:
    """Extract verdict from report."""
    quick_summary = report.get("quick_summary", {})
    verdict = quick_summary.get("verdict")
    if verdict:
        return verdict
    
    overall_assessment = report.get("overall_assessment", [])
    if overall_assessment:
        return overall_assessment[0]
    
    return None


def get_claims_count(report: Dict[str, Any]) -> int:
    """Get number of claims from report."""
    claims = report.get("claims", [])
    return len(claims)


def get_truthfulness_score(report: Dict[str, Any]) -> float:
    """Extract truthfulness score from report."""
    # Try to calculate from claims
    claims = report.get("claims", [])
    if not claims:
        return 0.0
    
    # Count true/likely true claims
    true_count = 0
    for claim in claims:
        verdict = claim.get("verdict", "").lower()
        if "true" in verdict and "false" not in verdict:
            true_count += 1
    
    return true_count / len(claims) if claims else 0.0


def enhance_report_with_test_metadata(
    report: Dict[str, Any],
    test_video: Dict[str, Any],
    batch_entry: Dict[str, Any]
) -> Dict[str, Any]:
    """Add test metadata to report."""
    # Create test_metadata section
    test_metadata = {
        "test_id": test_video.get("id"),
        "category": test_video.get("category"),
        "subcategory": test_video.get("subcategory"),
        "expected_verdict": test_video.get("expected_verdict"),
        "tags": test_video.get("tags", []),
        "imported_at": datetime.now().isoformat(),
        "imported_from": "test_videos.json",
        "batch_id": batch_entry.get("batch_id"),
        "processing_time_seconds": batch_entry.get("processing_time_seconds")
    }
    
    # Add verdict comparison
    actual_verdict = get_verdict_from_report(report)
    if actual_verdict and test_metadata["expected_verdict"]:
        test_metadata["verdict_match"] = (
            actual_verdict.lower() == test_metadata["expected_verdict"].lower() or
            actual_verdict.lower().startswith(test_metadata["expected_verdict"].lower().split()[0])
        )
    
    report["test_metadata"] = test_metadata
    
    # Also add to gallery_metadata for compatibility
    if "gallery_metadata" not in report:
        report["gallery_metadata"] = {}
    
    report["gallery_metadata"].update({
        "added_date": test_metadata["imported_at"],
        "status": "approved",
        "source_video_id": batch_entry.get("video_id"),
        "curator_notes": f"Imported from test suite - Category: {test_metadata['category']}"
    })
    
    return report


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """Sanitize title for use in filename."""
    # Remove special characters
    sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    # Remove multiple underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    # Trim to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized.rstrip('_')


def main():
    parser = argparse.ArgumentParser(
        description="Import test results to Streamlit gallery"
    )
    parser.add_argument(
        "--batch-file",
        type=str,
        required=True,
        help="Path to batch tracking file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be imported without actually importing"
    )
    parser.add_argument(
        "--min-claims",
        type=int,
        help="Minimum claims count to import"
    )
    parser.add_argument(
        "--verdict-match",
        action="store_true",
        help="Only import if verdict matches expected"
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Only import specific category"
    )
    parser.add_argument(
        "--status",
        type=str,
        default="completed",
        help="Only import videos with specific status (default: completed)"
    )
    
    args = parser.parse_args()
    
    # Load batch tracking
    tracking_file = Path(args.batch_file)
    if not tracking_file.exists():
        print(f"❌ Batch tracking file not found: {tracking_file}")
        sys.exit(1)
    
    batch_data = load_batch_tracking(tracking_file)
    print(f"📂 Loaded batch: {batch_data.get('batch_id', 'unknown')}")
    
    # Load test videos metadata
    test_data = load_test_videos()
    test_videos_map = {
        v.get("id"): v for v in test_data.get("test_videos", [])
    }
    
    # Filter videos
    videos_to_import = []
    skipped = []
    
    for entry in batch_data.get("videos", []):
        # Check status
        if entry.get("status") != args.status:
            skipped.append({
                "video_id": entry.get("video_id"),
                "reason": f"Status is '{entry.get('status')}', not '{args.status}'"
            })
            continue
        
        # Check category
        if args.category and entry.get("category") != args.category:
            skipped.append({
                "video_id": entry.get("video_id"),
                "reason": f"Category is '{entry.get('category')}', not '{args.category}'"
            })
            continue
        
        # Find report file
        video_id = entry.get("video_id")
        if not video_id:
            skipped.append({
                "video_id": "unknown",
                "reason": "No video_id in batch entry"
            })
            continue
        
        report_file = find_report_file(video_id, entry.get("result_path"))
        if not report_file:
            skipped.append({
                "video_id": video_id,
                "reason": "Report file not found"
            })
            continue
        
        # Find HTML report file
        html_report_file = find_html_report_file(video_id, entry.get("result_path"), report_file)
        
        # Load report
        try:
            report = load_report(report_file)
        except Exception as e:
            skipped.append({
                "video_id": video_id,
                "reason": f"Failed to load report: {e}"
            })
            continue
        
        # Check filters
        claims_count = get_claims_count(report)
        if args.min_claims and claims_count < args.min_claims:
            skipped.append({
                "video_id": video_id,
                "reason": f"Claims count ({claims_count}) < minimum ({args.min_claims})"
            })
            continue
        
        # Check verdict match
        if args.verdict_match:
            test_video = test_videos_map.get(entry.get("test_id"))
            if test_video:
                expected_verdict = test_video.get("expected_verdict", "")
                actual_verdict = get_verdict_from_report(report)
                if actual_verdict and expected_verdict:
                    verdict_match = (
                        actual_verdict.lower() == expected_verdict.lower() or
                        actual_verdict.lower().startswith(expected_verdict.lower().split()[0])
                    )
                    if not verdict_match:
                        skipped.append({
                            "video_id": video_id,
                            "reason": f"Verdict mismatch: expected '{expected_verdict}', got '{actual_verdict}'"
                        })
                        continue
        
        videos_to_import.append({
            "entry": entry,
            "report": report,
            "report_file": report_file,
            "html_report_file": html_report_file
        })
    
    # Print summary
    print(f"\n📊 Import Summary:")
    print(f"  Total videos in batch: {len(batch_data.get('videos', []))}")
    print(f"  Videos to import: {len(videos_to_import)}")
    print(f"  Videos skipped: {len(skipped)}")
    
    if skipped:
        print(f"\n⏭️  Skipped videos:")
        for skip in skipped[:10]:  # Show first 10
            print(f"  • {skip['video_id']}: {skip['reason']}")
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more")
    
    if not videos_to_import:
        print("\n❌ No videos to import")
        sys.exit(0)
    
    # Show what will be imported
    print(f"\n📋 Videos to import ({len(videos_to_import)}):")
    for item in videos_to_import:
        entry = item["entry"]
        report = item["report"]
        html_report_file = item.get("html_report_file")
        video_id = entry.get("video_id")
        title = report.get("title", "Unknown")[:60]
        verdict = get_verdict_from_report(report) or "Unknown"
        claims_count = get_claims_count(report)
        html_status = "✅" if html_report_file else "⚠️"
        print(f"  • {video_id}: {title}")
        print(f"    Verdict: {verdict}, Claims: {claims_count}, HTML: {html_status}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - No files were imported")
        print("   Remove --dry-run to actually import")
        sys.exit(0)
    
    # Import to gallery
    print(f"\n📤 Importing to gallery...")
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create HTML reports subdirectory
    gallery_html_dir = GALLERY_DIR.parent / "html_reports"
    gallery_html_dir.mkdir(parents=True, exist_ok=True)
    
    imported = []
    failed = []
    
    for item in videos_to_import:
        entry = item["entry"]
        report = item["report"]
        report_file = item["report_file"]
        html_report_file = item.get("html_report_file")
        video_id = entry.get("video_id")
        
        # Get test metadata
        test_video = test_videos_map.get(entry.get("test_id"), {})
        
        # Enhance report
        enhanced_report = enhance_report_with_test_metadata(report, test_video, entry)
        
        # Create filename
        title = enhanced_report.get("title", video_id)
        title_slug = sanitize_filename(title)
        gallery_filename = f"{video_id}_{title_slug}.json"
        gallery_path = GALLERY_DIR / gallery_filename
        
        # Copy HTML report if available
        html_gallery_path = None
        if html_report_file and html_report_file.exists():
            html_gallery_filename = f"{video_id}_{title_slug}.html"
            html_gallery_path = gallery_html_dir / html_gallery_filename
            
            try:
                shutil.copy2(html_report_file, html_gallery_path)
                # Add HTML path to report metadata
                enhanced_report["test_metadata"]["html_report_path"] = str(html_gallery_path.relative_to(project_root))
                print(f"  📄 Copied HTML report: {html_gallery_filename}")
            except Exception as e:
                print(f"  ⚠️  Failed to copy HTML report: {e}")
        
        # Save JSON to gallery
        try:
            with open(gallery_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report, f, indent=2, ensure_ascii=False)
            
            imported_item = {
                "video_id": video_id,
                "title": title[:50],
                "gallery_path": str(gallery_path.relative_to(project_root))
            }
            if html_gallery_path:
                imported_item["html_path"] = str(html_gallery_path.relative_to(project_root))
            
            imported.append(imported_item)
            print(f"  ✅ {video_id}: {title[:50]}")
        except Exception as e:
            failed.append({
                "video_id": video_id,
                "error": str(e)
            })
            print(f"  ❌ {video_id}: Failed to import - {e}")
    
    # Final summary
    print(f"\n✅ Import complete!")
    print(f"  Imported: {len(imported)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Gallery directory: {GALLERY_DIR}")
    print(f"  HTML reports directory: {gallery_html_dir}")
    
    html_count = sum(1 for item in imported if "html_path" in item)
    print(f"  HTML reports copied: {html_count}/{len(imported)}")
    
    if imported:
        print(f"\n📁 Imported files:")
        for item in imported[:10]:  # Show first 10
            print(f"  • {item['gallery_path']}")
            if "html_path" in item:
                print(f"    📄 HTML: {item['html_path']}")
        if len(imported) > 10:
            print(f"  ... and {len(imported) - 10} more")
    
    if failed:
        print(f"\n❌ Failed imports:")
        for item in failed:
            print(f"  • {item['video_id']}: {item['error']}")


if __name__ == "__main__":
    main()

