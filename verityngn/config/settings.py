import os
from typing import List
from pathlib import Path
from enum import Enum

# Load environment variables from .env at project root if present
try:
    from dotenv import load_dotenv
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    load_dotenv(_PROJECT_ROOT / ".env")
except Exception:
    # If python-dotenv is not installed or .env is missing, proceed with OS env only
    pass

# Project information
PROJECT_NAME = "VerityNgn"
PROJECT_VERSION = "0.1.0"
PROJECT_DESCRIPTION = "Video Verification and Analysis Engine"

# Deployment modes
class DeploymentMode(Enum):
    RESEARCH = "research"      # Local development on Mac/laptop with /downloads
    CONTAINER = "container"    # Containerized deployment with /var/tmp storage
    PRODUCTION = "production"  # Cloud Run with GCS storage

# Storage backends
class StorageBackend(Enum):
    LOCAL = "local"       # Local filesystem storage
    GCS = "gcs"          # Google Cloud Storage

# Detect deployment mode from environment
DEPLOYMENT_MODE = DeploymentMode(os.getenv("DEPLOYMENT_MODE", "research"))

# Determine storage backend based on deployment mode
if DEPLOYMENT_MODE == DeploymentMode.PRODUCTION:
    STORAGE_BACKEND = StorageBackend.GCS
else:
    # For research and container modes, use local storage by default
    # but allow override via environment variable
    backend_env = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_BACKEND = StorageBackend(backend_env)

# API settings
API_V1_PREFIX = "/api/v1"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Google Cloud settings
PROJECT_ID = os.getenv("PROJECT_ID", "verityindex-0-0-1")
LOCATION = os.getenv("LOCATION", "us-central1")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "verityindex_bucket")
# Optional GCS bucket for local container outputs (for development/testing)
GCS_LOCAL_OUTPUTS_BUCKET = os.getenv("GCS_LOCAL_OUTPUTS_BUCKET", "vngn_local_outputs")
ENABLE_LOCAL_GCS_BACKUP = os.getenv("ENABLE_LOCAL_GCS_BACKUP", "false").lower() in ("true", "1", "t")

# AI Model settings  
#VERTEX_MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-1.5-pro")
#VERTEX_MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.5-flash")
VERTEX_MODEL_NAME = "gemini-2.5-flash"
#AGENT_MODEL_NAME = os.getenv("AGENT_MODEL_NAME", "gemini-1.5-pro")
AGENT_MODEL_NAME = "gemini-2.5-flash"
# AI Parameter settings
# Read from ENV or default to 32K tokens for Gemini 2.5 Flash
MAX_OUTPUT_TOKENS_2_5_FLASH = int(os.getenv("MAX_OUTPUT_TOKENS_2_5_FLASH", "32768"))
MAX_OUTPUT_TOKENS_2_0_FLASH = int(os.getenv("MAX_OUTPUT_TOKENS_2_0_FLASH", "8192"))
# For genai multimodal calls that input a YouTube video (read from ENV or default to 8K)
GENAI_VIDEO_MAX_OUTPUT_TOKENS = int(os.getenv("GENAI_VIDEO_MAX_OUTPUT_TOKENS", "8192"))
# UNIFIED PRODUCTION PATH: Always use Vertex AI YouTube URL analysis
USE_GENAI_YOUTUBE_URL = False
USE_VERTEX_YOUTUBE_URL = True
YOUTUBE_VIDEO_GCS_URI = os.getenv("YOUTUBE_VIDEO_GCS_URI", "")  # e.g., gs://bucket/path/video.mp4

# Segmented YouTube URL analysis (clipping) controls
SEGMENTED_URL_ANALYSIS = os.getenv("SEGMENTED_URL_ANALYSIS", "true").lower() in ("true", "1", "t")
try:
    SEGMENT_DURATION_SECONDS = int(os.getenv("SEGMENT_DURATION_SECONDS", "3000"))  # 50 minutes
except Exception:
    SEGMENT_DURATION_SECONDS = 3000
try:
    SEGMENT_FPS = float(os.getenv("SEGMENT_FPS", "1.0"))  # lower than 1 for long/static videos
except Exception:
    SEGMENT_FPS = 1.0
try:
    DEFAULT_SEGMENTED_DURATION_SEC = int(os.getenv("DEFAULT_SEGMENTED_DURATION_SEC", "3600"))  # assume 1h if unknown
except Exception:
    DEFAULT_SEGMENTED_DURATION_SEC = 3600

# Thinking/Reasoning controls (best-effort; may be ignored by some SDKs)
try:
    THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "0"))  # 0 = adaptive minimal, -1 = disabled (SDK-dependent)
except Exception:
    THINKING_BUDGET = 0

# Vertex-only policy: disable GenAI segmented path
USE_GENAI_SEGMENTED_YOUTUBE = os.getenv("USE_GENAI_SEGMENTED_YOUTUBE", "false").lower() in ("true", "1", "t")
USE_VERTEX_SEGMENTED_YOUTUBE = os.getenv("USE_VERTEX_SEGMENTED_YOUTUBE", "true").lower() in ("true", "1", "t")
# Search API settings
# Toggle Google Custom Search usage in workflows
ENABLE_GOOGLE_SEARCH = os.getenv("ENABLE_GOOGLE_SEARCH", "true").lower() in ("true", "1", "t")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")  # REQUIRED: Set in .env
CSE_ID = os.getenv("CSE_ID", "")  # REQUIRED: Set in .env

# YouTube API settings - using the same key as Google Search
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", GOOGLE_SEARCH_API_KEY)
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# YouTube search backend control
# Allowed values: "api" (default) or "ytdlp"
YOUTUBE_SEARCH_MODE = os.getenv("YOUTUBE_SEARCH_MODE", "api").lower()
YOUTUBE_DISABLE_V3 = os.getenv("YOUTUBE_DISABLE_V3", "true").lower() in ("true", "1", "t")
YOUTUBE_API_FALLBACK = os.getenv("YOUTUBE_API_FALLBACK", "true").lower() in ("true", "1", "t")
YOUTUBE_API_ENABLED = os.getenv("YOUTUBE_API_ENABLED", "true").lower() in ("true", "1", "t")

# Counter-intelligence enhancement (downloading .info.json / .vtt for found videos)
# Disabled by default to avoid heavy I/O during search
CI_ENHANCEMENT_ENABLED = os.getenv("CI_ENHANCEMENT_ENABLED", "False").lower() in ("true", "1", "t")

# YouTube counter-intel breadth controls
try:
    YT_CI_MAX_QUERIES = int(os.getenv("YT_CI_MAX_QUERIES", "20"))
except Exception:
    YT_CI_MAX_QUERIES = 20

try:
    YT_CI_PER_QUERY_RESULTS = int(os.getenv("YT_CI_PER_QUERY_RESULTS", "8"))
except Exception:
    YT_CI_PER_QUERY_RESULTS = 8

try:
    YT_CI_TOTAL_RESULTS = int(os.getenv("YT_CI_TOTAL_RESULTS", "30"))
except Exception:
    YT_CI_TOTAL_RESULTS = 30

# Semantic filter (MiniLM) feature flags (disabled by default per request)
SEMANTIC_FILTER_ENABLED = os.getenv("SEMANTIC_FILTER_ENABLED", "False").lower() in ("true", "1", "t")
try:
    SEMANTIC_FILTER_THRESHOLD = float(os.getenv("SEMANTIC_FILTER_THRESHOLD", "0.25"))
except Exception:
    SEMANTIC_FILTER_THRESHOLD = 0.25

# Caching settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "t")
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
try:
    YOUTUBE_API_TTL_HOURS = int(os.getenv("YOUTUBE_API_TTL_HOURS", "6"))
    TRANSCRIPT_TTL_HOURS = int(os.getenv("TRANSCRIPT_TTL_HOURS", "168"))
except Exception:
    YOUTUBE_API_TTL_HOURS = 6
    TRANSCRIPT_TTL_HOURS = 168

# Report rollup fallback
ENABLE_CI_ROLLUP_FALLBACK = os.getenv("ENABLE_CI_ROLLUP_FALLBACK", "true").lower() in ("true", "1", "t")

# Other API keys from secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # OPTIONAL: Set in .env if using OpenAI
TWL_API_KEY = os.getenv("TWL_API_KEY", "")  # OPTIONAL: Set in .env if using TWL
GOOGLE_AI_STUDIO_KEY = os.getenv("GOOGLE_AI_STUDIO_KEY", "")  # OPTIONAL: Set in .env if using AI Studio

# Video processing settings
DEFAULT_CHUNK_DURATION = 1500  # in seconds
ALLOWED_EXTENSIONS = ["mp4", "avi", "mov", "mkv"]

# User agents for video download
USER_AGENTS: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.2210.144",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

# Environment-aware directory configuration
BASE_DIR = Path(__file__).parent.parent

def get_storage_directories():
    """Get storage directories based on deployment mode."""
    if DEPLOYMENT_MODE == DeploymentMode.RESEARCH:
        # Research mode: use project directories
        downloads_dir = BASE_DIR / "downloads"
        outputs_dir = BASE_DIR / "outputs_debug" if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true" else BASE_DIR / "outputs"
        compare_dir = BASE_DIR / "compare_debug" if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true" else BASE_DIR / "outputs" / "compare"
        
    elif DEPLOYMENT_MODE == DeploymentMode.CONTAINER:
        # Container mode: use environment variable or fallback to /var/tmp
        outputs_env = os.getenv("OUTPUTS_DIR", "/var/tmp/verityngn/outputs")
        downloads_env = os.getenv("DOWNLOADS_DIR", "/var/tmp/verityngn/downloads")
        
        downloads_dir = Path(downloads_env)
        outputs_dir = Path(outputs_env)
        compare_dir = outputs_dir / "compare"
        
        # Ensure directories exist
        downloads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        compare_dir.mkdir(parents=True, exist_ok=True)
        
    elif DEPLOYMENT_MODE == DeploymentMode.PRODUCTION:
        # Production mode: minimal local storage, everything goes to GCS
        base_path = Path("/tmp/verityngn")
        downloads_dir = base_path / "downloads"
        outputs_dir = base_path / "outputs"
        compare_dir = base_path / "compare"
        
        # Ensure directories exist
        downloads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        compare_dir.mkdir(parents=True, exist_ok=True)
    
    else:
        raise ValueError(f"Unknown deployment mode: {DEPLOYMENT_MODE}")
    
    return downloads_dir, outputs_dir, compare_dir

# Get directories based on current mode
DOWNLOADS_DIR, OUTPUTS_DIR, COMPARE_DIR = get_storage_directories()

# Template path (always relative to project)
TEMPLATE_PATH = BASE_DIR / "template.html"

# Debug flag
DEBUG_OUTPUTS = os.getenv("DEBUG_OUTPUTS", "true").lower() == "true"

# Storage configuration
STORAGE_CONFIG = {
    "backend": STORAGE_BACKEND,
    "local": {
        "downloads_dir": str(DOWNLOADS_DIR),
        "outputs_dir": str(OUTPUTS_DIR),
        "compare_dir": str(COMPARE_DIR),
    },
    "gcs": {
        "bucket_name": GCS_BUCKET_NAME,
        "project_id": PROJECT_ID,
        "base_path": "vngn_reports",  # Base path in GCS bucket (migrated from reports)
    }
}

# Logging configuration
import logging

def setup_logging():
    """Setup logging configuration based on deployment mode."""
    if DEPLOYMENT_MODE == DeploymentMode.PRODUCTION:
        # Production: JSON structured logging for Cloud Logging
        log_level = logging.WARNING
        log_format = '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "deployment_mode": "' + DEPLOYMENT_MODE.value + '"}'
    else:
        # Research/Container: Human-readable logging
        log_level = logging.INFO if DEBUG else logging.WARNING
        log_format = "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        force=True  # Override any existing logging configuration
    )
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(f"VerityNgn starting in {DEPLOYMENT_MODE.value} mode with {STORAGE_BACKEND.value} storage")
    logger.info(f"Storage directories: downloads={DOWNLOADS_DIR}, outputs={OUTPUTS_DIR}")

# Setup logging immediately
setup_logging() 