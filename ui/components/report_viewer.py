"""
Report Viewer Tab Component - SIMPLIFIED VERSION

Just displays the HTML report directly instead of parsing JSON.
Much simpler and more reliable!
"""

import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from components.ui_debug import ui_debug_enabled


def render_report_viewer_tab():
    """Render the report viewer tab - displays HTML reports directly."""
    
    st.header("📊 View Enhanced Reports")
    
    # API-first mode: UI talks to backend API (Cloud Run / local API), so UI doesn't need GCP auth
    import os
    API_MODE = (os.getenv("CLOUDRUN_API_URL") is not None) or (os.getenv("VERITYNGN_API_URL") is not None)
    
    if API_MODE:
        # Use API-based report retrieval for Streamlit Cloud
        try:
            import sys
            from pathlib import Path
            # Ensure ui directory is in path
            ui_dir = Path(__file__).parent.parent
            if str(ui_dir) not in sys.path:
                sys.path.insert(0, str(ui_dir))
            from api_client import get_default_client
            api_client = get_default_client()
            
            st.info("🌐 Using API mode - reports will be fetched from the API")
            st.warning("⚠️ Report viewer in API mode: View reports from the 'Process Video' tab after verification completes.")
            st.info("💡 Tip: After submitting a verification, use the 'View Report' buttons in the processing tab.")
            return
            
        except Exception as e:
            st.error(f"❌ Error initializing API client: {e}")
            return
    
    # 🎯 SIMPLIFIED: Find the outputs directory
    # Priority: Gallery html_reports > /app/outputs (Docker mount) > outputs (local) > outputs_debug (legacy)
    possible_dirs = [
        Path(__file__).parent.parent / 'gallery' / 'html_reports',  # Gallery HTML reports (highest priority)
        Path('/app/outputs'),  # Docker mount point
        Path.cwd() / 'outputs',  # Standard outputs directory
        Path.cwd() / 'verityngn' / 'outputs_debug',  # Legacy location
        Path.cwd() / 'outputs_debug',  # Legacy alternative
        Path(__file__).parent.parent.parent / 'verityngn' / 'outputs_debug',  # Relative to this file
        Path(__file__).parent.parent / 'outputs',  # From UI directory
    ]
    
    output_dir = None
    for dir_path in possible_dirs:
        try:
            if dir_path.exists():
                output_dir = dir_path
                print(f"✅ Found output directory: {output_dir.absolute()}")
                break
        except (PermissionError, OSError):
            # Skip directories we don't have permission to access (e.g., Streamlit Cloud)
            continue
    
    if not output_dir:
        st.warning(f"⚠️ No reports directory found. Run a verification first!")
        with st.expander("🔍 Debug Info"):
            st.info(f"Searched in:\n" + "\n".join([f"- {d}" for d in possible_dirs]))
        return
    
    # 🎯 SIMPLIFIED: Find all HTML reports
    report_options = {}
    
    try:
        # Check if this is the gallery html_reports directory
        if output_dir.name == 'html_reports':
            # Load from gallery HTML reports directory
            for html_file in output_dir.glob('*.html'):
                try:
                    video_id = html_file.stem.split('_')[0]  # Extract video_id from filename
                    title = html_file.stem.replace(f'{video_id}_', '').replace('_', ' ')
                    
                    # Try to get title from corresponding JSON in approved directory
                    approved_dir = output_dir.parent / 'approved'
                    json_file = approved_dir / f"{html_file.stem}.json"
                    if json_file.exists():
                        try:
                            import json
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                                title = data.get('title', title)
                        except:
                            pass
                    
                    report_options[f"{title} ({video_id})"] = {
                        'video_id': video_id,
                        'html_path': html_file,
                        'timestamp': 'gallery'
                    }
                except (PermissionError, OSError):
                    continue
        else:
            # Standard outputs directory structure
            for video_dir in output_dir.iterdir():
                try:
                    if not video_dir.is_dir():
                        continue
                except (PermissionError, OSError):
                    continue
                
                video_id = video_dir.name
                
                # Look for HTML reports in timestamped _complete directories
                try:
                    complete_dirs = sorted(
                        [d for d in video_dir.glob('*_complete') if d.is_dir()],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True  # Most recent first
                    )
                except (PermissionError, OSError):
                    continue
                
                for complete_dir in complete_dirs:
                    html_path = complete_dir / f'{video_id}_report.html'
                    try:
                        if html_path.exists():
                            # Try to get title from JSON if available
                            json_path = complete_dir / f'{video_id}_report.json'
                            title = video_id
                            try:
                                if json_path.exists():
                                    import json
                                    with open(json_path, 'r') as f:
                                        data = json.load(f)
                                        title = data.get('title', video_id)
                            except:
                                pass
                            
                            report_options[f"{title} ({video_id})"] = {
                                'video_id': video_id,
                                'html_path': html_path,
                                'timestamp': complete_dir.name
                            }
                            break  # Use most recent report
                    except (PermissionError, OSError):
                        continue
    except (PermissionError, OSError) as e:
        st.error(f"❌ Permission error accessing reports directory: {e}")
        st.info("💡 In Streamlit Cloud, use API mode to view reports via the API.")
        return
    
    if not report_options:
        st.info("📭 No HTML reports found yet. Complete a verification to generate reports.")
        st.info(f"📂 Looking in: {output_dir.absolute()}")
        return
    
    # Report selector
    st.subheader("📋 Select Report")
    
    selected_option = st.selectbox(
        "Choose a report:",
        options=list(report_options.keys()),
        index=0
    )
    
    selected_report = report_options[selected_option]
    selected_video_id = selected_report['video_id']
    html_path = selected_report['html_path']
    timestamp = selected_report['timestamp']
    
    st.markdown("---")
    
    # Display report info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"📅 Report generated: {timestamp.replace('_', ' ')}")
    with col2:
        st.info(f"📁 Video ID: {selected_video_id}")
    
    # 🎯 SIMPLE: Just display the HTML report directly! FULL PAGE
    st.subheader("📄 Full Report")
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Display the HTML in full page - no clipping, use full width
        components.html(html_content, height=1200, scrolling=True, width=None)
        
        st.markdown("---")
        
        # Download section
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.download_button(
                label="📥 Download HTML Report",
                data=html_content,
                file_name=f"{selected_video_id}_report.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col_d2:
            # Check if JSON also exists
            json_path = html_path.parent / f'{selected_video_id}_report.json'
            if json_path.exists():
                with open(json_path, 'r') as f:
                    json_content = f.read()
                st.download_button(
                    label="📥 Download JSON Data",
                    data=json_content,
                    file_name=f"{selected_video_id}_report.json",
                    mime="application/json",
                    use_container_width=True
                )
        
    except Exception as e:
        st.error(f"❌ Error loading report: {e}")
        st.info(f"Report path: {html_path}")
        import traceback
        if ui_debug_enabled():
            with st.expander("Error Details (debug)"):
                st.code(traceback.format_exc())


