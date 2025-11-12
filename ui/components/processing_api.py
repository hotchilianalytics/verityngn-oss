"""
VerityNgn Streamlit Processing Tab - API Version

This version calls the backend API instead of running workflows in-process.
Provides better scalability and cleaner separation of concerns.
"""

import streamlit as st
import time
import logging
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from ui.api_client import VerityNgnAPIClient, get_default_client

logger = logging.getLogger(__name__)


def render_processing_tab():
    """Render the processing tab with API-based workflow execution."""
    
    st.header("⚙️ Processing Status")
    
    # Initialize session state
    if 'api_client' not in st.session_state:
        st.session_state.api_client = get_default_client()
    
    if 'api_status' not in st.session_state:
        st.session_state.api_status = {}
    
    if 'poll_interval' not in st.session_state:
        st.session_state.poll_interval = 5  # Start with 5 second polling interval
    
    # Check if workflow should be started
    if st.session_state.get('workflow_started', False) and st.session_state.processing_status == 'processing':
        video_url = st.session_state.get('current_video_url', '')
        config = st.session_state.get('verification_config', {})
        
        st.info(f"🚀 Submitting verification request to API...")
        st.markdown(f"**Video URL:** `{video_url}`")
        
        # Check API health first
        is_healthy, health_msg = st.session_state.api_client.health_check()
        
        if not is_healthy:
            st.error(f"❌ API is not accessible: {health_msg}")
            st.markdown("""
            ### Troubleshooting
            
            The API backend is not running or not accessible. Please:
            
            1. **Start the API server** (in a separate terminal):
               ```bash
               python -m verityngn.api
               ```
            
            2. **Or use Docker**:
               ```bash
               docker-compose up api
               ```
            
            3. **Check API URL** in settings (default: `http://localhost:8080`)
            
            4. **Verify connection**:
               ```bash
               curl http://localhost:8080/health
               ```
            """)
            st.session_state.processing_status = 'idle'
            st.session_state.workflow_started = False
            st.stop()
        
        else:
            st.success(f"✅ API is healthy: {health_msg}")
        
        # Submit verification
        try:
            with st.spinner("Submitting to API..."):
                task_id = st.session_state.api_client.submit_verification(
                    video_url=video_url,
                    config=config
                )
            
            st.session_state.current_task_id = task_id
            st.session_state.workflow_started = False  # Mark as handled
            st.success(f"✅ Task submitted: `{task_id}`")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to submit verification: {e}")
            st.session_state.processing_status = 'error'
            st.session_state.workflow_started = False
            st.stop()
    
    # Status overview
    st.subheader("📊 Current Status")
    
    status = st.session_state.processing_status
    
    if status == 'idle':
        st.info("🟢 **Status:** Idle - No verification in progress")
        st.markdown("Submit a video from the **Video Input** tab to begin.")
    
    elif status == 'processing':
        task_id = st.session_state.get('current_task_id')
        
        if not task_id:
            st.warning("⚠️ Processing status set but no task ID found")
            st.session_state.processing_status = 'idle'
            st.stop()
        
        st.info(f"🔵 **Status:** Processing")
        st.markdown(f"**Task ID:** `{task_id}`")
        
        # Create placeholder for live updates
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        stage_placeholder = st.empty()
        
        # Poll for status updates
        try:
            with st.spinner("Fetching status..."):
                api_status = st.session_state.api_client.get_status(task_id)
            
            st.session_state.api_status = api_status
            
            # Display status
            task_status = api_status.get('status', 'unknown')
            progress = api_status.get('progress', 0)
            current_stage = api_status.get('current_stage', 'Unknown')
            
            status_placeholder.markdown(f"**Task Status:** `{task_status}`")
            progress_placeholder.progress(progress / 100.0)
            stage_placeholder.markdown(f"**Current Stage:** {current_stage}")
            
            # Check if complete
            if task_status == 'completed':
                st.success("✅ Verification completed successfully!")
                st.session_state.processing_status = 'complete'
                # Reset polling interval for next task
                st.session_state.poll_interval = 5
                
                video_id = api_status.get('video_id')
                if video_id:
                    st.session_state.current_video_id = video_id
                    st.markdown(f"**Video ID:** `{video_id}`")
                    st.markdown("View results in the **Reports** tab")
                
                st.balloons()
                st.rerun()
            
            elif task_status == 'error':
                error_msg = api_status.get('error_message', 'Unknown error')
                st.error(f"❌ Verification failed: {error_msg}")
                st.session_state.processing_status = 'error'
                # Reset polling interval
                st.session_state.poll_interval = 5
                st.rerun()
            
            else:
                # Still processing - auto-refresh with longer interval to reduce API load
                # Use exponential backoff: start with 5s, max 15s
                poll_interval = st.session_state.get('poll_interval', 5)
                time.sleep(poll_interval)
                # Increase interval gradually (capped at 15s) to reduce load on long-running tasks
                st.session_state.poll_interval = min(poll_interval + 1, 15)
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error checking status: {e}")
            st.markdown("The API may have stopped responding. Check the logs.")
    
    elif status == 'complete':
        st.success("✅ **Status:** Completed")
        
        video_id = st.session_state.get('current_video_id')
        task_id = st.session_state.get('current_task_id')
        
        if video_id:
            st.markdown(f"**Video ID:** `{video_id}`")
            st.markdown(f"**Task ID:** `{task_id}`")
            
            # Offer to view report
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 View HTML Report"):
                    try:
                        report_html = st.session_state.api_client.get_report(video_id, format='html')
                        st.components.v1.html(report_html, height=800, scrolling=True)
                    except Exception as e:
                        st.error(f"Error loading report: {e}")
            
            with col2:
                if st.button("📊 View JSON Data"):
                    try:
                        report_data = st.session_state.api_client.get_report_data(video_id)
                        st.json(report_data)
                    except Exception as e:
                        st.error(f"Error loading data: {e}")
            
            with col3:
                if st.button("🔄 New Verification"):
                    # Reset state
                    st.session_state.processing_status = 'idle'
                    st.session_state.current_task_id = None
                    st.session_state.current_video_id = None
                    st.rerun()
        
        else:
            st.warning("⚠️ Verification completed but video ID not found")
    
    elif status == 'error':
        st.error("❌ **Status:** Error occurred during processing")
        
        if st.button("🔄 Reset and Try Again"):
            st.session_state.processing_status = 'idle'
            st.session_state.current_task_id = None
            st.rerun()
    
    # Display API status info (if available)
    if st.session_state.api_status:
        with st.expander("🔍 Detailed Status"):
            st.json(st.session_state.api_status)
    
    # Help section
    with st.expander("ℹ️ Help & Troubleshooting"):
        st.markdown("""
        ### How It Works
        
        1. **Submit**: Video URL is sent to the API backend
        2. **Process**: API downloads video and runs verification workflow
        3. **Monitor**: This tab polls the API for progress updates
        4. **Complete**: Report is generated and available for viewing
        
        ### Troubleshooting
        
        **"API is not accessible"**
        - Ensure the API server is running: `python -m verityngn.api`
        - Check the API URL in settings (default: `http://localhost:8080`)
        - Try `curl http://localhost:8080/health` to test connectivity
        
        **"Task takes too long"**
        - Video processing typically takes 5-15 minutes
        - Longer videos may take up to 30 minutes
        - Check API logs for detailed progress
        
        **"Error during processing"**
        - Check API server logs for error details
        - Ensure all required API keys are configured (Google Search, Vertex AI)
        - Try a different video to isolate the issue
        
        ### Configuration
        
        Set API URL via environment variable:
        ```bash
        export VERITYNGN_API_URL="http://localhost:8080"
        ```
        
        Or in Streamlit secrets (`.streamlit/secrets.toml`):
        ```toml
        VERITYNGN_API_URL = "http://localhost:8080"
        ```
        """)


if __name__ == "__main__":
    # For testing
    st.set_page_config(page_title="Processing Tab Test", layout="wide")
    render_processing_tab()




