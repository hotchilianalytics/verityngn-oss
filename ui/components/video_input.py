"""
Video Input Tab Component

Allows users to submit YouTube URLs for verification.
"""

import streamlit as st
import re
from pathlib import Path


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Strip whitespace from URL first
    url = url.strip()
    
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#\s]+)',
        r'youtube\.com/shorts/([^&\n?#\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1).strip()  # Strip any whitespace from video ID
            return video_id
    
    # Also try to extract just the video ID if it's provided directly
    # Pattern for 11-character video ID
    if len(url.strip()) == 11 and url.strip().replace('-', '').replace('_', '').isalnum():
        return url.strip()
    
    return None


def validate_youtube_url(url: str) -> tuple[bool, str]:
    """
    Validate YouTube URL.
    
    Returns:
        (is_valid, message)
    """
    if not url:
        return False, "Please enter a URL"
    
    video_id = extract_video_id(url)
    if not video_id:
        return False, "Invalid YouTube URL format"
    
    if len(video_id) != 11:
        return False, "Invalid video ID length"
    
    return True, video_id


def render_video_input_tab():
    """Render the video input tab."""
    
    st.header("🎬 Verify YouTube Video")
    
    # Introduction
    st.markdown("""
    Enter a YouTube video URL to analyze its factual claims and assess truthfulness.
    The system will:
    
    1. **Download & Analyze** the video using multimodal AI
    2. **Extract Claims** from audio, visual text, and demonstrations
    3. **Search for Evidence** across the web
    4. **Generate Report** with truthfulness assessment
    """)
    
    st.markdown("---")
    
    def start_verification_callback():
        """Callback to handle verification start and tab switching."""
        # Get current input values
        # NOTE: We must use st.session_state to get values inside a callback
        # But simple variables are not available unless we use keys for widgets
        
        # For now, we set the flags to trigger processing in the next run
        st.session_state.processing_status = 'processing'
        # We need to ensure video_id is correct, but args are passed at render time
        # which is fine for the button click
        pass

    # Main input section
    col1, col2 = st.columns([3, 1])
    
    # Initialize video_id at function scope
    video_id = None
    
    with col1:
        # Check if example URL was set
        default_url = st.session_state.get('example_url', '')
        if default_url:
            # Clear it so it doesn't persist
            st.session_state.pop('example_url', None)
        
        # Video URL input
        video_url = st.text_input(
            "YouTube URL",
            value=default_url,
            placeholder="https://www.youtube.com/watch?v=...",
            help="Enter the full YouTube video URL",
            key="video_url_input"
        )
        
        # Validate URL in real-time
        if video_url:
            is_valid, result = validate_youtube_url(video_url)
            if is_valid:
                st.success(f"✅ Valid video ID: `{result}`")
                video_id = result
            else:
                st.error(f"❌ {result}")
                video_id = None
    
    with col2:
        st.markdown("### Example Videos")
        if st.button("Load Example 1", help="Health supplement claim"):
            st.session_state.example_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            st.rerun()
        if st.button("Load Example 2", help="Product review"):
            st.session_state.example_url = "https://www.youtube.com/watch?v=example123"
            st.rerun()
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            model_name = st.selectbox(
                "Model",
                ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro"],
                help="Select the LLM model for analysis"
            )
            
            max_claims = st.slider(
                "Max Claims",
                min_value=5,
                max_value=50,
                value=25,
                help="Maximum number of claims to extract"
            )
        
        with col_b:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="LLM creativity (lower = more factual)"
            )
            
            enable_llm_logging = st.checkbox(
                "Enable LLM Logging",
                value=True,
                help="Log all LLM interactions for transparency"
            )
        
        # Output format selection
        output_formats = st.multiselect(
            "Output Formats",
            ["JSON", "Markdown", "HTML"],
            default=["JSON", "HTML"],
            help="Select report output formats"
        )
    
    st.markdown("---")
    
    # Action buttons
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([2, 2, 2, 4])
    
    def on_start_click(vid_id, vid_url, config):
        """Callback to handle verification start."""
        st.session_state.processing_status = 'processing'
        st.session_state.current_video_id = vid_id
        
        # Ensure full URL
        if vid_id and not vid_url.startswith('http'):
            vid_url = f"https://www.youtube.com/watch?v={vid_id}"
        
        st.session_state.current_video_url = vid_url
        st.session_state.workflow_logs = []
        st.session_state.verification_config = config
        st.session_state.workflow_started = True
        
        # Switch tab - this works because callback runs before script re-run
        st.session_state.nav_selection = "⚙️ Processing"

    with col_btn1:
        # Prepare config dictionary for callback
        current_config = {
            'model_name': model_name,
            'max_claims': max_claims,
            'temperature': temperature,
            'enable_llm_logging': enable_llm_logging,
            'output_formats': output_formats
        }
        
        start_button = st.button(
            "🚀 Start Verification",
            type="primary",
            disabled=(not video_id or st.session_state.processing_status == 'processing'),
            use_container_width=True,
            on_click=on_start_click,
            args=(video_id, video_url, current_config)
        )
    
    # Handle post-click UI feedback (optional, but nav switch happens immediately)
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = True
    
    if st.session_state.debug_mode and start_button:
         # This might not show if tab switches fast, but good for debug
        st.info(f"🔍 DEBUG: Start triggered for {video_id}")

    with col_btn2:
        if st.session_state.processing_status == 'processing':
            cancel_button = st.button(
                "⏹️ Cancel",
                use_container_width=True
            )
        else:
            cancel_button = False
    
    with col_btn3:
        clear_button = st.button(
            "🗑️ Clear",
            use_container_width=True
        )
    
    # Handle button actions (logic moved to callback for start_button)
    # Cancel and Clear still handled here
    
    if cancel_button:
        st.session_state.processing_status = 'idle'
        st.session_state.workflow_started = False
        st.warning("⚠️ Verification cancelled")
        st.rerun()
    
    if clear_button:
        # Clear using the example_url pattern
        st.session_state.example_url = ""
        st.session_state.processing_status = 'idle'
        st.session_state.current_video_id = None
        st.session_state.current_video_url = None
        st.rerun()
    
    # Status display
    st.markdown("---")
    
    if st.session_state.processing_status != 'idle':
        st.subheader("📊 Current Status")
        
        if st.session_state.processing_status == 'processing':
            st.info("⚙️ Processing in progress. Check the Processing tab for details.")
        elif st.session_state.processing_status == 'complete':
            st.success("✅ Verification complete! View results in the Reports tab.")
        elif st.session_state.processing_status == 'error':
            st.error("❌ Verification failed. Check Processing tab for error details.")
        
        # Show current video
        if st.session_state.current_video_url:
            st.markdown(f"**Current Video:** `{st.session_state.current_video_id}`")
            st.video(st.session_state.current_video_url)
    
    # Recent verifications
    st.markdown("---")
    st.subheader("📜 Recent Verifications")
    
    try:
        output_dir = Path(st.session_state.config.get('output.local_dir', './outputs'))
        if output_dir.exists():
            recent_dirs = sorted(output_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            recent_dirs = [d for d in recent_dirs if d.is_dir()][:5]
            
            if recent_dirs:
                for dir_path in recent_dirs:
                    video_id = dir_path.name
                    report_json = dir_path / 'report.json'
                    
                    if report_json.exists():
                        import json
                        with open(report_json, 'r') as f:
                            report = json.load(f)
                        
                        col_rec1, col_rec2, col_rec3 = st.columns([3, 2, 1])
                        
                        with col_rec1:
                            st.markdown(f"**{report.get('title', video_id)}**")
                        
                        with col_rec2:
                            truth_score = report.get('overall_truthfulness_score', 0)
                            if truth_score >= 0.7:
                                st.markdown(f"🟢 {truth_score:.1%} Truthful")
                            elif truth_score >= 0.4:
                                st.markdown(f"🟡 {truth_score:.1%} Mixed")
                            else:
                                st.markdown(f"🔴 {truth_score:.1%} Questionable")
                        
                        with col_rec3:
                            if st.button("View", key=f"view_{video_id}"):
                                st.session_state.selected_report_id = video_id
                                st.switch_page("pages/reports.py")
            else:
                st.info("No recent verifications found. Start your first verification above!")
        else:
            st.info("No output directory found. Configure settings or start a verification.")
    
    except Exception as e:
        st.warning(f"Could not load recent verifications: {e}")
    
    # Debug log viewer
    if st.session_state.debug_mode:
        st.markdown("---")
        st.subheader("🔍 Debug Logs")
        
        debug_toggle = st.checkbox("Show Debug Logs", value=True, key="show_debug_logs")
        
        if debug_toggle and st.session_state.get('workflow_logs'):
            with st.expander("📋 Workflow Debug Output", expanded=True):
                log_container = st.container()
                with log_container:
                    for log in st.session_state.workflow_logs[-20:]:  # Show last 20
                        level = log.get('level', 'info')
                        msg = log.get('message', '')
                        timestamp = log.get('timestamp', 0)
                        
                        from datetime import datetime
                        ts_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S.%f')[:-3]
                        
                        if level == 'error':
                            st.error(f"[{ts_str}] ❌ {msg}")
                        elif level == 'success':
                            st.success(f"[{ts_str}] ✅ {msg}")
                        elif level == 'warning':
                            st.warning(f"[{ts_str}] ⚠️ {msg}")
                        else:
                            st.info(f"[{ts_str}] ℹ️ {msg}")
        elif debug_toggle:
            st.info("No logs yet. Start a verification to see debug output.")

