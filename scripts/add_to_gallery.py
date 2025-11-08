#!/usr/bin/env python3
"""
Add reports from outputs_debug to the Streamlit gallery.

This script helps curate reports and add them to the gallery for display
in the Streamlit UI.

Usage:
    # List available reports
    python scripts/add_to_gallery.py --list
    
    # Add a specific report to approved gallery
    python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status approved
    
    # Add to pending (for review)
    python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status pending
    
    # Add with custom title
    python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status approved --title "Health Product Scam Example"
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Directories
OUTPUTS_DEBUG_DIR = Path("./verityngn/outputs_debug")
GALLERY_DIR = Path("./ui/gallery")

def list_available_reports():
    """List all available reports in outputs_debug."""
    if not OUTPUTS_DEBUG_DIR.exists():
        print(f"❌ Outputs debug directory not found: {OUTPUTS_DEBUG_DIR}")
        return
    
    print("📚 Available Reports in outputs_debug:\n")
    print("=" * 80)
    
    for video_dir in sorted(OUTPUTS_DEBUG_DIR.iterdir()):
        if not video_dir.is_dir():
            continue
        
        video_id = video_dir.name
        
        # Look for most recent report
        complete_dirs = sorted(
            [d for d in video_dir.glob('*_complete') if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not complete_dirs:
            continue
        
        report_path = complete_dirs[0] / f'{video_id}_report.json'
        if not report_path.exists():
            report_path = complete_dirs[0] / 'report.json'
        
        if report_path.exists():
            try:
                with open(report_path, 'r') as f:
                    report = json.load(f)
                
                title = report.get('title', 'Unknown Title')[:70]
                verdict = report.get('overall_assessment', ['Unknown'])[0]
                timestamp = complete_dirs[0].name.split('_complete')[0]
                
                print(f"Video ID: {video_id}")
                print(f"  Title: {title}")
                print(f"  Verdict: {verdict}")
                print(f"  Timestamp: {timestamp}")
                print(f"  Path: {report_path}")
                print("-" * 80)
            except Exception as e:
                print(f"⚠️  Error reading {video_id}: {e}")
    
    print("\nUse --video-id <VIDEO_ID> to add a report to the gallery\n")

def add_to_gallery(video_id: str, status: str = "approved", custom_title: str = None):
    """Add a report to the gallery."""
    
    # Validate status
    if status not in ["approved", "pending", "rejected"]:
        print(f"❌ Invalid status: {status}. Must be 'approved', 'pending', or 'rejected'")
        return False
    
    # Find the report
    video_dir = OUTPUTS_DEBUG_DIR / video_id
    if not video_dir.exists():
        print(f"❌ Video directory not found: {video_dir}")
        return False
    
    # Find most recent complete report
    complete_dirs = sorted(
        [d for d in video_dir.glob('*_complete') if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not complete_dirs:
        print(f"❌ No completed reports found for {video_id}")
        return False
    
    source_report_path = complete_dirs[0] / f'{video_id}_report.json'
    if not source_report_path.exists():
        source_report_path = complete_dirs[0] / 'report.json'
    
    if not source_report_path.exists():
        print(f"❌ Report not found: {source_report_path}")
        return False
    
    # Load the report
    try:
        with open(source_report_path, 'r') as f:
            report = json.load(f)
    except Exception as e:
        print(f"❌ Error loading report: {e}")
        return False
    
    # Add gallery metadata
    if custom_title:
        report['gallery_title'] = custom_title
    
    report['gallery_metadata'] = {
        'added_date': datetime.now().isoformat(),
        'status': status,
        'source_video_id': video_id,
        'curator_notes': ""
    }
    
    # Create target directory
    target_dir = GALLERY_DIR / status
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Create descriptive filename
    title_slug = report.get('title', video_id)[:30].replace(' ', '_').replace('/', '_')
    target_filename = f"{video_id}_{title_slug}.json"
    target_path = target_dir / target_filename
    
    # Save to gallery
    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully added report to gallery!")
        print(f"   Video ID: {video_id}")
        print(f"   Title: {report.get('title', 'N/A')[:70]}")
        print(f"   Verdict: {report.get('overall_assessment', ['Unknown'])[0]}")
        print(f"   Status: {status}")
        print(f"   Saved to: {target_path}")
        
        return True
    except Exception as e:
        print(f"❌ Error saving to gallery: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Add reports from outputs_debug to the Streamlit gallery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available reports
  python scripts/add_to_gallery.py --list
  
  # Add a report to approved gallery
  python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status approved
  
  # Add to pending with custom title
  python scripts/add_to_gallery.py --video-id tLJC8hkK-ao --status pending --title "Lipozem Scam Analysis"
        """
    )
    
    parser.add_argument('--list', action='store_true', help='List all available reports')
    parser.add_argument('--video-id', type=str, help='Video ID to add to gallery')
    parser.add_argument('--status', type=str, default='approved', 
                       choices=['approved', 'pending', 'rejected'],
                       help='Gallery status (default: approved)')
    parser.add_argument('--title', type=str, help='Custom gallery title')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_reports()
    elif args.video_id:
        add_to_gallery(args.video_id, args.status, args.title)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()








