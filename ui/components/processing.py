"""
Processing Tab Component

Real-time progress monitoring for video verification workflow.
"""

import streamlit as st
import threading
import time
from pathlib import Path
import asyncio
from queue import Queue


def add_log(level: str, message: str, log_queue=None):
    """Helper to add log entry with timestamp."""
    log_entry = {
        'timestamp': time.time(),
        'level': level,
        'message': message
    }
    
    # If we have a queue (from thread), use it
    if log_queue is not None:
        log_queue.put(log_entry)
    # Otherwise, add directly to session state (main thread)
    else:
        if 'workflow_logs' not in st.session_state:
            st.session_state.workflow_logs = []
        st.session_state.workflow_logs.append(log_entry)
    
    # Always print to console for debugging (visible output)
    import logging
    logger = logging.getLogger(__name__)
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    console_msg = f"[{timestamp}] [{level.upper()}] {message}"
    print(console_msg, flush=True)  # Force immediate output
    
    if level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.info(message)


def run_verification_workflow(video_url: str, config: dict, log_queue: Queue):
    """
    Run the verification workflow in a thread.
    
    Args:
        video_url: YouTube video URL
        config: Verification configuration
        log_queue: Queue for thread-safe logging
    """
    try:
        print("\n" + "="*80, flush=True)
        print("🚀 VERITYNGN WORKFLOW STARTED", flush=True)
        print("="*80 + "\n", flush=True)
        
        add_log('info', f'🚀 Starting verification for {video_url}', log_queue)
        add_log('info', f'📋 Config: model={config.get("model_name")}, max_claims={config.get("max_claims")}', log_queue)
        
        # Import workflow
        add_log('info', '📦 Importing workflow modules...', log_queue)
        from verityngn.workflows.pipeline import run_verification
        add_log('success', '✅ Modules imported', log_queue)
        
        # Update config with user settings
        add_log('info', '⚙️ Loading configuration...', log_queue)
        from verityngn.config.config_loader import get_config
        config_loader = get_config()
        
        # Override with UI settings
        if 'model_name' in config:
            config_loader.set('models.vertex.model_name', config['model_name'])
            add_log('info', f'   Model: {config["model_name"]}', log_queue)
        if 'temperature' in config:
            config_loader.set('models.vertex.temperature', config['temperature'])
            add_log('info', f'   Temperature: {config["temperature"]}', log_queue)
        if 'enable_llm_logging' in config:
            config_loader.set('llm_logging.enabled', config['enable_llm_logging'])
            add_log('info', f'   LLM Logging: {config["enable_llm_logging"]}', log_queue)
        
        # Run workflow
        add_log('info', '🏗️ Initializing workflow pipeline...', log_queue)
        
        # Don't specify output_dir - let pipeline create video-specific subdirectory
        # The pipeline will automatically create: outputs/{video_id}/
        add_log('info', '📁 Output directory: outputs/{video_id}', log_queue)
        
        # Execute workflow (this will take time)
        add_log('info', '▶️ Starting workflow execution (this may take several minutes)...', log_queue)
        add_log('info', '   Stage 1/6: Downloading video...', log_queue)
        
        # Pass None to let pipeline handle directory creation
        final_state, out_dir = run_verification(video_url, out_dir_path=None)
        
        # Update status via queue
        log_queue.put({'type': 'status', 'status': 'complete', 'output_dir': out_dir})
        add_log('success', f'🎉 Verification complete!', log_queue)
        add_log('success', f'📊 Results saved to: {out_dir}', log_queue)
        
    except Exception as e:
        # Update status via queue
        log_queue.put({'type': 'status', 'status': 'error', 'error': str(e)})
        add_log('error', f'💥 Error occurred: {str(e)}', log_queue)
        add_log('error', f'   Type: {type(e).__name__}', log_queue)
        
        # Get traceback
        import traceback
        tb = traceback.format_exc()
        add_log('error', f'   Traceback:\n{tb}', log_queue)
    
    finally:
        # Signal completion
        log_queue.put({'type': 'done'})


def render_processing_tab():
    """Render the processing tab with real-time progress."""
    
    st.header("⚙️ Processing Status")
    
    # Initialize workflow logs if needed
    if 'workflow_logs' not in st.session_state:
        st.session_state.workflow_logs = []
    
    # Process messages from worker thread queue
    if 'log_queue' in st.session_state:
        try:
            while True:
                msg = st.session_state.log_queue.get_nowait()
                
                if msg.get('type') == 'status':
                    # Status update
                    st.session_state.processing_status = msg.get('status', 'error')
                    if 'output_dir' in msg:
                        st.session_state.final_output_dir = msg['output_dir']
                    if 'error' in msg:
                        st.session_state.workflow_error = msg['error']
                elif msg.get('type') == 'done':
                    # Workflow finished
                    pass
                else:
                    # Regular log message
                    st.session_state.workflow_logs.append(msg)
        except:
            # Queue empty, that's fine
            pass
    
    # Check if workflow should be started
    if st.session_state.get('workflow_started', False) and st.session_state.processing_status == 'processing':
        # Start workflow in background thread
        if 'workflow_thread' not in st.session_state or not st.session_state.workflow_thread.is_alive():
            config = st.session_state.get('verification_config', {})
            video_url = st.session_state.get('current_video_url', '')
            
            # Create thread-safe queue
            st.session_state.log_queue = Queue()
            
            thread = threading.Thread(
                target=run_verification_workflow,
                args=(video_url, config, st.session_state.log_queue),
                daemon=True
            )
            thread.start()
            st.session_state.workflow_thread = thread
            st.session_state.workflow_started = False  # Mark as handled
    
    # Status overview
    st.subheader("📊 Current Status")
    
    status = st.session_state.processing_status
    
    if status == 'idle':
        st.info("💤 No active verification. Go to 'Verify Video' tab to start.")
        return
    
    elif status == 'processing':
        st.markdown("""
        <div class="status-box status-processing">
            <h4>⚙️ Processing in Progress</h4>
            <p>The verification workflow is currently running. This may take several minutes depending on video length.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show spinner
        with st.spinner("Processing..."):
            # Progress indicator (simulated stages)
            progress_stages = [
                "📥 Downloading video",
                "🎬 Analyzing video content",
                "🔍 Extracting claims",
                "🌐 Searching for evidence",
                "📊 Verifying claims",
                "📝 Generating report"
            ]
            
            # Display stages
            cols = st.columns(len(progress_stages))
            for i, (col, stage) in enumerate(zip(cols, progress_stages)):
                with col:
                    # Simple visual indicator (in real implementation, track actual progress)
                    if i < 3:  # Simulate first 3 stages done
                        st.success(stage)
                    elif i == 3:  # Current stage
                        st.info(stage)
                    else:
                        st.text(stage)
        
        # Auto-refresh every 2 seconds while processing
        time.sleep(0.1)  # Small delay to prevent too frequent updates
        st.rerun()
        
    elif status == 'complete':
        st.markdown("""
        <div class="status-box status-complete">
            <h4>✅ Verification Complete</h4>
            <p>The video has been successfully analyzed and verified.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show results summary
        if 'final_output_dir' in st.session_state:
            output_dir = Path(st.session_state.final_output_dir)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Status", "✅ Complete")
            
            with col2:
                # Try to load report for stats
                report_json = output_dir / 'report.json'
                if report_json.exists():
                    import json
                    with open(report_json, 'r') as f:
                        report = json.load(f)
                    
                    claims_count = len(report.get('verified_claims', []))
                    st.metric("Claims Verified", claims_count)
                else:
                    st.metric("Claims Verified", "N/A")
            
            with col3:
                if report_json.exists():
                    truth_score = report.get('overall_truthfulness_score', 0)
                    st.metric("Truthfulness Score", f"{truth_score:.1%}")
                else:
                    st.metric("Truthfulness Score", "N/A")
            
            # Action buttons
            st.markdown("---")
            col_a, col_b, col_c = st.columns([1, 1, 2])
            
            with col_a:
                if st.button("📊 View Report", type="primary", use_container_width=True):
                    st.session_state.selected_report_id = st.session_state.current_video_id
                    st.info("Switch to 'View Reports' tab to see the full report")
            
            with col_b:
                if st.button("🎬 Verify Another", use_container_width=True):
                    st.session_state.processing_status = 'idle'
                    st.session_state.workflow_logs = []
                    st.rerun()
    
    elif status == 'error':
        st.markdown("""
        <div class="status-box status-error">
            <h4>❌ Verification Failed</h4>
            <p>An error occurred during the verification process.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show error details
        if 'workflow_error' in st.session_state:
            with st.expander("🔍 Error Details"):
                st.code(st.session_state.workflow_error, language="text")
        
        # Retry button
        if st.button("🔄 Retry Verification"):
            st.session_state.processing_status = 'processing'
            st.session_state.workflow_started = True
            st.session_state.workflow_logs = []
            st.rerun()
    
    # Video info
    if st.session_state.current_video_url:
        st.markdown("---")
        st.subheader("🎥 Video Being Processed")
        
        col_vid1, col_vid2 = st.columns([2, 1])
        
        with col_vid1:
            st.video(st.session_state.current_video_url)
        
        with col_vid2:
            st.markdown(f"""
            **Video ID:** `{st.session_state.current_video_id}`
            
            **Configuration:**
            - Model: {st.session_state.get('verification_config', {}).get('model_name', 'N/A')}
            - Max Claims: {st.session_state.get('verification_config', {}).get('max_claims', 'N/A')}
            - LLM Logging: {'✅' if st.session_state.get('verification_config', {}).get('enable_llm_logging') else '❌'}
            """)
    
    # Workflow logs
    st.markdown("---")
    st.subheader("📜 Workflow Logs")
    
    if st.session_state.workflow_logs:
        # Display logs in reverse chronological order
        logs_container = st.container()
        
        with logs_container:
            for log_entry in reversed(st.session_state.workflow_logs[-50:]):  # Show last 50
                level = log_entry.get('level', 'info')
                message = log_entry.get('message', '')
                timestamp = log_entry.get('timestamp', 0)
                
                # Format timestamp
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp)
                time_str = dt.strftime('%H:%M:%S')
                
                # Color code by level
                if level == 'error':
                    st.error(f"[{time_str}] {message}")
                elif level == 'success':
                    st.success(f"[{time_str}] {message}")
                elif level == 'warning':
                    st.warning(f"[{time_str}] {message}")
                else:
                    st.info(f"[{time_str}] {message}")
        
        # Download logs button
        if st.button("💾 Download Logs"):
            log_text = "\n".join([
                f"[{datetime.fromtimestamp(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{log['level'].upper()}: {log['message']}"
                for log in st.session_state.workflow_logs
            ])
            st.download_button(
                "Download Full Logs",
                log_text,
                file_name=f"verification_logs_{st.session_state.current_video_id}.txt",
                mime="text/plain"
            )
    else:
        st.info("No logs available yet. Start a verification to see workflow logs.")
    
    # Real-time monitoring section
    if status == 'processing':
        st.markdown("---")
        st.subheader("📈 Real-Time Monitoring")
        
        # Resource usage (placeholder - could integrate psutil)
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric("CPU Usage", "45%", delta="5%")
        
        with col_m2:
            st.metric("Memory", "2.3 GB", delta="0.2 GB")
        
        with col_m3:
            st.metric("Elapsed Time", "3m 42s")
        
        # Auto-refresh every 5 seconds
        st.info("⏱️ Page will auto-refresh every 5 seconds during processing")
        time.sleep(5)
        st.rerun()

