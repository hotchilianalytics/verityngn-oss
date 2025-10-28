"""
VerityNgn Streamlit UI

Interactive web interface for YouTube video verification.

Run: streamlit run ui/streamlit_app.py
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Load .env file FIRST (before checking auth)
try:
    from dotenv import load_dotenv

    env_file = repo_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed
except Exception:
    pass  # .env loading failed, continue anyway


def check_google_cloud_auth():
    """Check if Google Cloud authentication is valid."""
    import os
    import subprocess
    from pathlib import Path

    # Method 1: Check for GOOGLE_APPLICATION_CREDENTIALS env var
    json_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if json_path and Path(json_path).exists():
        return True

    # Method 2: Check for service account JSON in common locations
    common_locations = [
        Path.cwd() / "service-account.json",
        Path.cwd() / "credentials.json",
        Path(__file__).parent.parent / "service-account.json",
        Path(__file__).parent.parent / "credentials.json",
        Path.home() / ".config" / "gcloud" / "service-account.json",
    ]

    for loc in common_locations:
        if loc.exists():
            # Set the environment variable for this session
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(loc)
            return True

    # Method 3: Check gcloud default credentials
    try:
        result = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip()
    except FileNotFoundError:
        return False  # gcloud not installed
    except Exception:
        return False


def show_auth_error():
    """Display authentication error and instructions."""
    st.error("🔐 **Google Cloud Authentication Required**")

    st.markdown(
        """
    ### Choose an authentication method:
    
    #### Option 1: Use .env File (Easiest)
    
    **Add to your `.env` file:**
    ```bash
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
    ```
    
    Or download service account JSON:
    1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
    2. Select your project → Click service account → Keys
    3. Add Key → Create new key → JSON → Download
    
    **Then add to `.env`:**
    ```bash
    GOOGLE_APPLICATION_CREDENTIALS=/Users/ajjc/proj/verityngn-oss/service-account.json
    ```
    
    ---
    
    #### Option 2: Place JSON File Directly
    
    Save your service account JSON as:
    - `/Users/ajjc/proj/verityngn-oss/service-account.json`
    - `/Users/ajjc/proj/verityngn-oss/credentials.json`
    
    ---
    
    #### Option 3: gcloud CLI Authentication
    
    ```bash
    gcloud auth application-default login
    ```
    
    ---
    
    **Then refresh this page** (press R or reload)
    
    ### Need help?
    - Check `SERVICE_ACCOUNT_SETUP.md` in the project root
    - Run `python test_credentials.py` to diagnose issues
    """
    )

    st.stop()


# Page configuration
st.set_page_config(
    page_title="VerityNgn - Video Verification",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Check authentication before continuing
if not check_google_cloud_auth():
    show_auth_error()

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-pending {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .status-processing {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
    }
    .status-complete {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .status-error {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Import components
from components.video_input import render_video_input_tab
from components.processing import render_processing_tab

try:
    # Use enhanced report viewer if available
    from components.enhanced_report_viewer import render_enhanced_report_viewer_tab

    report_viewer_func = render_enhanced_report_viewer_tab
except ImportError:
    # Fallback to standard report viewer
    from components.report_viewer import render_report_viewer_tab

    report_viewer_func = render_report_viewer_tab
from components.gallery import render_gallery_tab
from components.settings import render_settings_tab


def main():
    """Main Streamlit application."""

    # Header
    st.markdown('<div class="main-header">🔍 VerityNgn</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">AI-Powered YouTube Video Verification</div>',
        unsafe_allow_html=True,
    )

    # Initialize session state
    if "processing_status" not in st.session_state:
        st.session_state.processing_status = "idle"  # idle, processing, complete, error
    if "current_video_id" not in st.session_state:
        st.session_state.current_video_id = None
    if "current_video_url" not in st.session_state:
        st.session_state.current_video_url = None
    if "workflow_logs" not in st.session_state:
        st.session_state.workflow_logs = []
    if "config" not in st.session_state:
        # Load default config
        try:
            from verityngn.config.config_loader import get_config

            st.session_state.config = get_config()
        except Exception as e:
            st.error(f"Failed to load configuration: {e}")
            st.session_state.config = None

    # Sidebar navigation
    with st.sidebar:
        # Logo/header
        st.markdown("## 🔍 VerityNgn")
        st.caption("Video Verification Platform")
        st.markdown("---")

        # Navigation tabs
        tab_selection = st.radio(
            "Navigation",
            [
                "🎬 Verify Video",
                "⚙️ Processing",
                "📊 View Reports",
                "🖼️ Gallery",
                "⚙️ Settings",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Quick stats
        st.markdown("### 📈 Quick Stats")
        try:
            from pathlib import Path

            output_dir = Path(
                st.session_state.config.get("output.local_dir", "./outputs")
            )
            if output_dir.exists():
                report_count = len(list(output_dir.glob("*/report.json")))
                st.metric("Total Reports", report_count)
            else:
                st.metric("Total Reports", 0)
        except:
            st.metric("Total Reports", "N/A")

        st.markdown("---")

        # Debug mode toggle
        if "debug_mode" not in st.session_state:
            st.session_state.debug_mode = True

        debug_mode = st.checkbox(
            "🔍 Debug Mode",
            value=st.session_state.debug_mode,
            help="Show detailed logs and debug information",
        )
        st.session_state.debug_mode = debug_mode

        if debug_mode:
            st.caption("Debug logging enabled")

        st.markdown("---")

        # Help section
        with st.expander("ℹ️ Help & Documentation"):
            st.markdown(
                """
            **Quick Start:**
            1. Enter a YouTube URL
            2. Click "Start Verification"
            3. View results in Reports tab
            
            **Need Help?**
            - [Documentation](https://github.com/...)
            - [Tutorial Video](https://youtube.com/...)
            - [Report Issue](https://github.com/.../issues)
            """
            )

        # Footer
        st.markdown("---")
        st.caption("VerityNgn v1.0.0")
        st.caption("MIT License • Open Source")

    # Main content area - render selected tab
    if "🎬 Verify Video" in tab_selection:
        render_video_input_tab()
    elif "⚙️ Processing" in tab_selection:
        render_processing_tab()
    elif "📊 View Reports" in tab_selection:
        report_viewer_func()  # Use enhanced or standard viewer
    elif "🖼️ Gallery" in tab_selection:
        render_gallery_tab()
    elif "⚙️ Settings" in tab_selection:
        render_settings_tab()

    # Show welcome message at bottom when idle
    if (
        st.session_state.processing_status == "idle"
        and not st.session_state.current_video_id
        and "🎬 Verify Video" in tab_selection
    ):
        st.markdown("---")
        st.info(
            """
        🎯 **Enhanced Features Now Available!**
        
        - ✅ **Claim Quality Scoring** - Specificity & verifiability metrics
        - 🚫 **Absence Claims** - Detect missing credentials and sources
        - 📝 **Transcript Analysis** - Counter-evidence from debunking videos
        - 📊 **Visual Quality Badges** - EXCELLENT/GOOD/ACCEPTABLE ratings
        
        Enter a YouTube URL above to get started!
        """
        )


if __name__ == "__main__":
    main()
