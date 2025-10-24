"""
Gallery Moderation System

Handles approval/rejection of community-submitted gallery items.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os


GALLERY_DIR = Path("gallery/")
PENDING_DIR = GALLERY_DIR / "pending"
APPROVED_DIR = GALLERY_DIR / "approved"
REJECTED_DIR = GALLERY_DIR / "rejected"

# Create directories if they don't exist
PENDING_DIR.mkdir(parents=True, exist_ok=True)
APPROVED_DIR.mkdir(parents=True, exist_ok=True)
REJECTED_DIR.mkdir(parents=True, exist_ok=True)


def load_pending_submissions() -> List[Dict[str, Any]]:
    """Load all pending gallery submissions."""
    submissions = []
    
    if not PENDING_DIR.exists():
        return submissions
    
    for file_path in PENDING_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                submission = json.load(f)
                submission['file_path'] = str(file_path)
                submission['submission_id'] = file_path.stem
                submissions.append(submission)
        except Exception as e:
            st.error(f"Error loading {file_path.name}: {e}")
    
    # Sort by submission date (newest first)
    submissions.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    
    return submissions


def approve_submission(submission_id: str, reviewer_notes: str = ""):
    """Approve a gallery submission and move it to approved folder."""
    pending_path = PENDING_DIR / f"{submission_id}.json"
    approved_path = APPROVED_DIR / f"{submission_id}.json"
    
    if not pending_path.exists():
        raise FileNotFoundError(f"Submission {submission_id} not found")
    
    # Load submission
    with open(pending_path, 'r') as f:
        submission = json.load(f)
    
    # Add approval metadata
    submission['approval'] = {
        'status': 'approved',
        'approved_at': datetime.now().isoformat(),
        'reviewer_notes': reviewer_notes
    }
    
    # Save to approved folder
    with open(approved_path, 'w') as f:
        json.dump(submission, f, indent=2)
    
    # Remove from pending
    pending_path.unlink()


def reject_submission(submission_id: str, reason: str):
    """Reject a gallery submission and move it to rejected folder."""
    pending_path = PENDING_DIR / f"{submission_id}.json"
    rejected_path = REJECTED_DIR / f"{submission_id}.json"
    
    if not pending_path.exists():
        raise FileNotFoundError(f"Submission {submission_id} not found")
    
    # Load submission
    with open(pending_path, 'r') as f:
        submission = json.load(f)
    
    # Add rejection metadata
    submission['rejection'] = {
        'status': 'rejected',
        'rejected_at': datetime.now().isoformat(),
        'reason': reason
    }
    
    # Save to rejected folder
    with open(rejected_path, 'w') as f:
        json.dump(submission, f, indent=2)
    
    # Remove from pending
    pending_path.unlink()


def render_moderation_panel():
    """Render the gallery moderation panel (admin only)."""
    
    st.header("🛡️ Gallery Moderation")
    
    # Check if user has moderator permissions
    # TODO: Implement actual authentication
    if not st.session_state.get('is_moderator', False):
        st.warning("⚠️ This panel requires moderator permissions.")
        
        # For development/testing, allow enabling moderator mode
        if st.checkbox("Enable Moderator Mode (Dev Only)", key="dev_mod_mode"):
            st.session_state.is_moderator = True
            st.rerun()
        return
    
    st.markdown("""
    Review and approve/reject community submissions to the gallery.
    Approved items will appear publicly in the gallery.
    """)
    
    # Load pending submissions
    pending = load_pending_submissions()
    
    if not pending:
        st.info("✅ No pending submissions to review")
        return
    
    st.markdown(f"**{len(pending)} submission(s) pending review**")
    st.markdown("---")
    
    # Display each pending submission
    for submission in pending:
        with st.expander(f"📋 {submission.get('title', 'Untitled')} - {submission.get('submitted_at', 'Unknown date')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Video ID:** `{submission.get('video_id', 'N/A')}`")
                st.markdown(f"**Category:** {submission.get('category', 'N/A')}")
                st.markdown(f"**Submitted by:** {submission.get('submitted_by', 'Anonymous')}")
                st.markdown(f"**Tags:** {', '.join(submission.get('tags', []))}")
                
                if submission.get('description'):
                    st.markdown(f"**Description:**")
                    st.markdown(submission['description'])
                
                # Show YouTube embed
                if submission.get('youtube_url'):
                    st.video(submission['youtube_url'])
                
                # Show report preview
                video_id = submission.get('video_id')
                if video_id:
                    st.markdown(f"[📄 View Report](/api/v1/reports/{video_id}/report.html)")
            
            with col2:
                # Moderation metrics
                st.metric("Truth Score", f"{submission.get('truthfulness_score', 0):.0%}")
                st.metric("Claims", submission.get('claims_count', 0))
                
                st.markdown("---")
                
                # Moderation actions
                st.markdown("**Actions:**")
                
                reviewer_notes = st.text_area(
                    "Review Notes (optional)",
                    key=f"notes_{submission['submission_id']}",
                    placeholder="Add internal notes about this submission..."
                )
                
                col_approve, col_reject = st.columns(2)
                
                with col_approve:
                    if st.button(
                        "✅ Approve",
                        key=f"approve_{submission['submission_id']}",
                        type="primary",
                        use_container_width=True
                    ):
                        try:
                            approve_submission(submission['submission_id'], reviewer_notes)
                            st.success(f"✅ Approved: {submission.get('title', 'Submission')}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error approving submission: {e}")
                
                with col_reject:
                    if st.button(
                        "❌ Reject",
                        key=f"reject_{submission['submission_id']}",
                        use_container_width=True
                    ):
                        # Show rejection reason input
                        rejection_reason = st.text_area(
                            "Rejection Reason (required)",
                            key=f"reason_{submission['submission_id']}",
                            placeholder="Explain why this submission is being rejected..."
                        )
                        
                        if st.button(
                            "Confirm Rejection",
                            key=f"confirm_reject_{submission['submission_id']}",
                            type="secondary"
                        ):
                            if rejection_reason.strip():
                                try:
                                    reject_submission(submission['submission_id'], rejection_reason)
                                    st.success(f"❌ Rejected: {submission.get('title', 'Submission')}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error rejecting submission: {e}")
                            else:
                                st.error("Please provide a rejection reason")
                
                # Metadata
                st.markdown("---")
                st.caption(f"**Submitted:** {submission.get('submitted_at', 'Unknown')}")
                st.caption(f"**ID:** {submission['submission_id']}")
    
    # Statistics
    st.markdown("---")
    st.subheader("📊 Moderation Statistics")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.metric("Pending", len(pending))
    
    with stat_col2:
        approved_count = len(list(APPROVED_DIR.glob("*.json")))
        st.metric("Approved", approved_count)
    
    with stat_col3:
        rejected_count = len(list(REJECTED_DIR.glob("*.json")))
        st.metric("Rejected", rejected_count)


def submit_to_gallery(video_id: str, category: str, tags: List[str], description: str, submitted_by: str = "anonymous"):
    """Submit a verification to the gallery for moderation."""
    
    # Load report data
    from pathlib import Path
    outputs_dir = Path("outputs")
    report_dir = outputs_dir / video_id
    
    if not report_dir.exists():
        raise FileNotFoundError(f"Report not found for video ID: {video_id}")
    
    # Load report JSON to get metadata
    report_json_path = report_dir / "report.json"
    if report_json_path.exists():
        with open(report_json_path, 'r') as f:
            report_data = json.load(f)
    else:
        report_data = {}
    
    # Create submission
    submission = {
        'video_id': video_id,
        'title': report_data.get('title', 'Unknown Title'),
        'category': category,
        'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
        'truthfulness_score': report_data.get('overall_assessment', {}).get('score', 0),
        'claims_count': len(report_data.get('claims_breakdown', [])),
        'tags': tags,
        'description': description,
        'submitted_by': submitted_by,
        'submitted_at': datetime.now().isoformat(),
        'report_data': report_data  # Include full report for reference
    }
    
    # Generate submission ID
    submission_id = f"{video_id}_{int(datetime.now().timestamp())}"
    
    # Save to pending folder
    submission_path = PENDING_DIR / f"{submission_id}.json"
    with open(submission_path, 'w') as f:
        json.dump(submission, f, indent=2)
    
    return submission_id

