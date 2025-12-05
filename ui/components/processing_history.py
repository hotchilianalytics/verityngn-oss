"""
Processing History Component

Displays user's video verification submission history with status tracking.
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional


def get_processing_history() -> List[Dict[str, Any]]:
    """
    Get the processing history from session state.
    
    Returns:
        List of processing history entries, sorted by most recent first
    """
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    # Sort by submitted_at (most recent first)
    history = st.session_state.processing_history.copy()
    history.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    return history


def add_to_history(
    video_id: str,
    video_url: str,
    task_id: str,
    status: str = 'processing'
) -> None:
    """
    Add a new entry to processing history.
    
    Args:
        video_id: YouTube video ID
        video_url: Full YouTube URL
        task_id: Task ID from API
        status: Initial status ('processing', 'completed', 'failed')
    """
    if 'processing_history' not in st.session_state:
        st.session_state.processing_history = []
    
    entry = {
        'video_id': video_id,
        'video_url': video_url,
        'task_id': task_id,
        'submitted_at': datetime.now().isoformat(),
        'status': status,
        'completed_at': None,
        'report_url': None,
        'error_message': None
    }
    
    st.session_state.processing_history.append(entry)


def update_history_entry(
    task_id: str,
    status: str,
    video_id: Optional[str] = None,
    report_url: Optional[str] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Update an existing history entry.
    
    Args:
        task_id: Task ID to update
        status: New status ('processing', 'completed', 'failed')
        video_id: Video ID (if not already set)
        report_url: URL to the report (for completed tasks)
        error_message: Error message (for failed tasks)
        
    Returns:
        True if entry was found and updated, False otherwise
    """
    if 'processing_history' not in st.session_state:
        return False
    
    for entry in st.session_state.processing_history:
        if entry.get('task_id') == task_id:
            entry['status'] = status
            
            if video_id and not entry.get('video_id'):
                entry['video_id'] = video_id
            
            if status == 'completed':
                entry['completed_at'] = datetime.now().isoformat()
                if report_url:
                    entry['report_url'] = report_url
            elif status == 'failed':
                entry['completed_at'] = datetime.now().isoformat()
                if error_message:
                    entry['error_message'] = error_message
            
            return True
    
    return False


def render_processing_history():
    """Render the processing history component."""
    st.markdown("### 📜 My Submissions")
    
    history = get_processing_history()
    
    if not history:
        st.info("📭 No submissions yet. Submit a video from the **Video Input** tab to get started.")
        return
    
    # Filter options
    col_filter, col_sort = st.columns(2)
    
    with col_filter:
        status_filter = st.selectbox(
            "Filter by status:",
            ["All", "Processing", "Completed", "Failed"],
            key="history_status_filter"
        )
    
    with col_sort:
        sort_order = st.selectbox(
            "Sort by:",
            ["Most Recent", "Oldest First"],
            key="history_sort_order"
        )
    
    # Apply filters
    filtered_history = history
    if status_filter != "All":
        filtered_history = [h for h in filtered_history if h.get('status') == status_filter.lower()]
    
    if sort_order == "Oldest First":
        filtered_history = list(reversed(filtered_history))
    
    # Display history entries
    st.markdown("---")
    
    if not filtered_history:
        st.info(f"No submissions found with status '{status_filter}'.")
        return
    
    # Display each entry
    for idx, entry in enumerate(filtered_history):
        video_id = entry.get('video_id', 'Unknown')
        video_url = entry.get('video_url', '')
        task_id = entry.get('task_id', 'N/A')
        status = entry.get('status', 'unknown')
        submitted_at = entry.get('submitted_at', '')
        completed_at = entry.get('completed_at')
        report_url = entry.get('report_url')
        error_message = entry.get('error_message')
        
        # Parse datetime for display
        try:
            if submitted_at:
                submitted_dt = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
                submitted_str = submitted_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                submitted_str = "Unknown"
        except:
            submitted_str = submitted_at
        
        # Status badge
        if status == 'completed':
            status_badge = "✅ Completed"
            status_color = "green"
        elif status == 'failed':
            status_badge = "❌ Failed"
            status_color = "red"
        elif status == 'processing':
            status_badge = "⏳ Processing"
            status_color = "blue"
        else:
            status_badge = f"❓ {status.title()}"
            status_color = "gray"
        
        # Create expandable container for each entry
        with st.expander(f"{status_badge} | {video_id} | {submitted_str}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Video ID:** `{video_id}`")
                if video_url:
                    st.markdown(f"**URL:** {video_url}")
                st.markdown(f"**Task ID:** `{task_id}`")
                st.markdown(f"**Submitted:** {submitted_str}")
                
                if completed_at:
                    try:
                        completed_dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        completed_str = completed_dt.strftime("%Y-%m-%d %H:%M:%S")
                        st.markdown(f"**Completed:** {completed_str}")
                    except:
                        st.markdown(f"**Completed:** {completed_at}")
                
                if error_message:
                    st.error(f"**Error:** {error_message}")
            
            with col2:
                # Action buttons
                if status == 'completed' and report_url:
                    if st.button("📄 View Report", key=f"view_report_{idx}"):
                        st.session_state[f"show_report_{task_id}"] = True
                        st.rerun()
                
                if video_url:
                    st.markdown(f"[🔗 Open Video]({video_url})")
                
                # Copy task ID button
                if st.button("📋 Copy Task ID", key=f"copy_task_{idx}"):
                    st.code(task_id)
                    st.success("Task ID copied!")
        
        # Show report if requested
        if st.session_state.get(f"show_report_{task_id}", False):
            st.markdown("---")
            st.markdown(f"### 📄 Report: {video_id}")
            
            col_close, _ = st.columns([1, 10])
            with col_close:
                if st.button("❌ Close Report", key=f"close_report_{task_id}"):
                    st.session_state[f"show_report_{task_id}"] = False
                    st.rerun()
            
            if report_url:
                try:
                    import requests
                    response = requests.get(report_url, timeout=30)
                    response.raise_for_status()
                    html_content = response.text
                    
                    import streamlit.components.v1 as components
                    components.html(html_content, height=1200, scrolling=True, width=None)
                except Exception as e:
                    st.error(f"Error loading report: {e}")
                    st.markdown(f"[📄 Open Report in New Tab]({report_url})")
            else:
                st.warning("Report URL not available.")
        
        st.markdown("---")
    
    # Summary statistics
    st.markdown("### 📊 Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(history)
    completed = len([h for h in history if h.get('status') == 'completed'])
    failed = len([h for h in history if h.get('status') == 'failed'])
    processing = len([h for h in history if h.get('status') == 'processing'])
    
    with col1:
        st.metric("Total Submissions", total)
    with col2:
        st.metric("Completed", completed)
    with col3:
        st.metric("Failed", failed)
    with col4:
        st.metric("Processing", processing)
    
    # Clear history button
    st.markdown("---")
    if st.button("🗑️ Clear History", help="Remove all history entries"):
        if st.checkbox("Confirm clear history", key="confirm_clear_history"):
            st.session_state.processing_history = []
            st.success("History cleared!")
            st.rerun()

