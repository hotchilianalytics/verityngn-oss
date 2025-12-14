"""
VerityNgn Streamlit UI

Interactive web interface for YouTube video verification.

Run: streamlit run ui/streamlit_app.py
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Load secrets FIRST (handles both .env and Streamlit Cloud secrets)
try:
    from ui import secrets_loader

    # secrets_loader auto-loads on import
except ImportError as e:
    st.warning(f"Could not import secrets_loader: {e}")
    # Fallback: try loading .env directly
    try:
        from dotenv import load_dotenv

        env_file = repo_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except Exception:
        pass


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
    GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
    ```
    
    ---
    
    #### Option 2: Place JSON File Directly
    
    Save your service account JSON as:
    - `/path/to/verityngn-oss/service-account.json`
    - `/path/to/verityngn-oss/credentials.json`
    
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

# Sidebar: debug toggle (safe; does not print secrets)
with st.sidebar:
    st.checkbox(
        "Enable debug output",
        key="ui_debug",
        help="Show diagnostic output and stack traces. Disable for normal use.",
    )

# Check authentication before continuing (skip in API mode - API handles auth)
# In API-first architecture, only the backend needs Google Cloud credentials.
# The UI just makes HTTP calls to the API.
API_MODE = (os.getenv("CLOUDRUN_API_URL") is not None) or (os.getenv("VERITYNGN_API_URL") is not None)

if not API_MODE and not check_google_cloud_auth():
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

# Import both processing components
try:
    from components.processing_api import render_processing_tab as render_processing_tab_api
    HAS_API_COMPONENT = True
except ImportError:
    HAS_API_COMPONENT = False

try:
    from components.processing import render_processing_tab as render_processing_tab_local
    HAS_LOCAL_COMPONENT = True
except ImportError:
    HAS_LOCAL_COMPONENT = False

def render_processing_tab():
    """Route to appropriate processing component based on backend mode."""
    backend_mode = st.session_state.get('backend_mode', 'local')
    
    if backend_mode == 'cloudrun' and HAS_API_COMPONENT:
        render_processing_tab_api()
    elif backend_mode == 'local' and HAS_LOCAL_COMPONENT:
        render_processing_tab_local()
    else:
        st.error(f"❌ Backend mode '{backend_mode}' not available. Available components: API={HAS_API_COMPONENT}, Local={HAS_LOCAL_COMPONENT}")

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
from components.debug import render_debug_tab


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
    if "processing_history" not in st.session_state:
        st.session_state.processing_history = []  # List of processing history entries
    if "config" not in st.session_state:
        # Load default config
        try:
            # Ensure parent directory is in path
            import sys
            from pathlib import Path
            repo_root = Path(__file__).parent.parent
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            
            from verityngn.config.config_loader import get_config
            st.session_state.config = get_config()
        except ImportError as e:
            # If verityngn module not found, use empty config dict
            st.warning(f"⚠️ Could not load verityngn config: {e}. Using default configuration.")
            st.session_state.config = {}
        except Exception as e:
            st.warning(f"⚠️ Failed to load configuration: {e}. Using default configuration.")
            st.session_state.config = {}

    # Sidebar navigation
    with st.sidebar:
        # Logo/header
        st.markdown("## 🔍 VerityNgn")
        st.caption("Video Verification Platform")
        st.markdown("---")

        # Navigation tabs
        # Initialize nav selection in session state if not present
        if "nav_selection" not in st.session_state:
            st.session_state.nav_selection = "🎬 Verify Video"

        tab_selection = st.radio(
            "Navigation",
            [
                "🎬 Verify Video",
                "⚙️ Processing",
                "📊 View Reports",
                "🖼️ Gallery",
                "⚙️ Settings",
                "🏥 System Health",
            ],
            label_visibility="collapsed",
            key="nav_selection"
        )

        st.markdown("---")

        # Backend mode selector
        st.markdown("### 🔌 Backend Mode")
        if "backend_mode" not in st.session_state:
            # Default: use API mode if VERITYNGN_API_URL is set, otherwise local
            default_mode = "cloudrun" if os.getenv("VERITYNGN_API_URL") else "local"
            st.session_state.backend_mode = default_mode
        
        backend_mode = st.radio(
            "Processing Backend",
            ["local", "cloudrun"],
            index=0 if st.session_state.backend_mode == "local" else 1,
            format_func=lambda x: "🏠 Local (OSS)" if x == "local" else "☁️ Cloud Run + Batch",
            help="Local: Direct workflow execution. Cloud Run: API-based processing with Google Cloud Batch.",
            key="backend_mode_radio"
        )
        st.session_state.backend_mode = backend_mode
        
        # Show mode-specific info
        if backend_mode == "local":
            st.caption("✅ Direct workflow execution")
        else:
            cloudrun_url = os.getenv("CLOUDRUN_API_URL", os.getenv("VERITYNGN_API_URL", ""))
            if cloudrun_url:
                st.caption(f"🌐 API: {cloudrun_url[:50]}...")
            else:
                st.warning("⚠️ Set CLOUDRUN_API_URL env var")
        
        st.markdown("---")

        # Quick stats
        st.markdown("### 📈 Quick Stats")
        try:
            from pathlib import Path

            # Check Docker mount first, then local outputs
            output_dir = Path("/app/outputs") if Path("/app/outputs").exists() else Path(
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

        # Debug mode toggle (public-safe default: off)
        if "debug_mode" not in st.session_state:
            st.session_state.debug_mode = False

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
            3. View results in the Gallery tab
            
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
    # If workflow just started, auto-switch to processing tab logic (even if UI hasn't caught up)
    # Check if we should override the tab selection based on workflow state
    if st.session_state.get('workflow_started', False) and st.session_state.processing_status == 'processing':
         render_processing_tab()
    elif "🎬 Verify Video" in tab_selection:
        render_video_input_tab()
    elif "⚙️ Processing" in tab_selection:
        render_processing_tab()
    elif "📊 View Reports" in tab_selection:
        report_viewer_func()  # Use enhanced or standard viewer
    elif "🖼️ Gallery" in tab_selection:
        render_gallery_tab()
    elif "⚙️ Settings" in tab_selection:
        render_settings_tab()
    elif "🏥 System Health" in tab_selection:
        render_debug_tab()

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
