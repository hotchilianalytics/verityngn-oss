import os
from typing import List
from pathlib import Path
from enum import Enum

# Load configuration using ConfigLoader
from verityngn.config.config_loader import get_config
_config = get_config()

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

# Detect deployment mode from configuration (env var takes priority for cloud deployments)
_deployment_mode_str = os.getenv("DEPLOYMENT_MODE") or _config.get("advanced.deployment_mode", "research")
DEPLOYMENT_MODE = DeploymentMode(_deployment_mode_str)

# Determine storage backend from configuration (env var takes priority for cloud deployments)
_storage_backend_str = os.getenv("STORAGE_BACKEND") or _config.get("advanced.storage_backend", "local")
STORAGE_BACKEND = StorageBackend(_storage_backend_str)

# API settings
API_V1_PREFIX = "/api/v1"
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Google Cloud settings (env vars take priority for cloud deployments)
PROJECT_ID = os.getenv("PROJECT_ID") or _config.get("gcp.project_id", "your-project-id")
LOCATION = os.getenv("LOCATION") or _config.get("gcp.location", "us-central1")
# Vertex AI endpoint location — Gemini 3+ preview models (e.g. gemini-3-flash-preview) require "global"; regional (e.g. us-central1) will fail.
# If you see model-not-found or 404 after switching to gemini-3-flash-preview, ensure VERTEX_LOCATION=global and all LLM clients pass project+location.
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "global")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME") or _config.get("gcp.bucket_name", "your-bucket-name")
# Commercial user-scoped bucket (when set, user_id enables vngn/accounts/{user_id}/videos/ paths)
GCS_COMMERCIAL_BUCKET = (os.getenv("GCS_COMMERCIAL_BUCKET") or _config.get("gcp.commercial_bucket", "") or "").strip() or None
# Optional GCS bucket for local container outputs (for development/testing)
GCS_LOCAL_OUTPUTS_BUCKET = os.getenv("GCS_LOCAL_OUTPUTS_BUCKET", "vngn_local_outputs")
ENABLE_LOCAL_GCS_BACKUP = os.getenv("ENABLE_LOCAL_GCS_BACKUP", "false").lower() in ("true", "1", "t")
# Use timestamped report directories (and completion markers); when True, run_upload_report uses timestamped_dir for notification
USE_TIMESTAMPED_STORAGE = os.getenv("USE_TIMESTAMPED_STORAGE", "true").lower() in ("true", "1", "t") or _config.get("advanced.use_timestamped_storage", True)
# Batch/Cloud Run ADC usually has no private key; signing fails and spams logs. Set true only with a SA JSON key.
GCS_TRY_SIGNED_URL_ON_UPLOAD = os.getenv("GCS_TRY_SIGNED_URL_ON_UPLOAD", "false").lower() in ("true", "1", "t")

# AI Model settings
VERTEX_MODEL_NAME = os.getenv("VERTEX_MODEL_NAME") or os.getenv("LLM_MODEL") or _config.get("models.vertex.model_name", "gemini-2.5-flash")
# Single source of truth for verification (agent + fast-fail); default to newest price-performant model
VERIFICATION_MODEL_NAME = (
    os.getenv("VERIFICATION_MODEL_NAME")
    or os.getenv("AGENT_MODEL_NAME")
    or os.getenv("LLM_MODEL")
    or _config.get("models.agent.model_name", "gemini-2.5-flash")
)
AGENT_MODEL_NAME = VERIFICATION_MODEL_NAME
# AI Parameter settings
MAX_OUTPUT_TOKENS_2_5_FLASH = int(_config.get("models.vertex.max_output_tokens", 32768))
MAX_OUTPUT_TOKENS_2_0_FLASH = int(_config.get("models.agent.max_output_tokens", 8192))
GENAI_VIDEO_MAX_OUTPUT_TOKENS = int(_config.get("models.vertex.max_output_tokens", 8192))
# UNIFIED PRODUCTION PATH: Always use Vertex AI YouTube URL analysis
USE_GENAI_YOUTUBE_URL = True
USE_VERTEX_YOUTUBE_URL = False
VIDEO_LENGTH_LIMIT_MINS = int(os.getenv("VIDEO_LENGTH_LIMIT_MINS", 90))
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
# When unset (0), adaptive sampler may override fps per scene class
SEGMENT_FPS_OVERRIDE = float(os.getenv("SEGMENT_FPS_OVERRIDE", "0") or "0")
ADAPTIVE_SAMPLING = os.getenv("ADAPTIVE_SAMPLING", "true").lower() in ("true", "1", "t")
SEGMENT_MEDIA_RESOLUTION = os.getenv(
    "SEGMENT_MEDIA_RESOLUTION", "MEDIA_RESOLUTION_LOW"
)  # overridden by adaptive sampler when enabled
VIDEO_GENRE_HINT = os.getenv("VIDEO_GENRE_HINT", "")  # lecture|ad|deposition|earnings
try:
    DEFAULT_SEGMENTED_DURATION_SEC = int(os.getenv("DEFAULT_SEGMENTED_DURATION_SEC", "3600"))  # assume 1h if unknown
except Exception:
    DEFAULT_SEGMENTED_DURATION_SEC = 3600

# Thinking/Reasoning controls (best-effort; may be ignored by some SDKs)
try:
    THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "0"))  # 0 = adaptive minimal, -1 = disabled (SDK-dependent)
except Exception:
    THINKING_BUDGET = 0

# --- Deep Research premium tier (formerly "Platinum") ---
# Expensive Gemini-3 grounded forensic pass over {video_id}_report.json producing
# {video_id}_deep_private_report.{md,html,pdf}. Gated by dr_credits in the backend.
DEEP_RESEARCH_ENABLED = os.getenv("DEEP_RESEARCH_ENABLED", "true").lower() in ("true", "1", "t")
# Gemini Developer API key (preferred path for the vetted google_search grounding loop).
# Falls back to GOOGLE_API_KEY; if neither set and DEEP_RESEARCH_USE_VERTEX=true, uses Vertex/ADC.
DEEP_RESEARCH_API_KEY = (
    os.getenv("VERITY_GEMINI_KEY")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_AI_STUDIO_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or ""
).strip()
# Use Vertex AI (project+location, ADC) instead of an API key when true.
DEEP_RESEARCH_USE_VERTEX = os.getenv("DEEP_RESEARCH_USE_VERTEX", "false").lower() in ("true", "1", "t")
# Flagship reasoning model. Vetted run used gemini-pro-latest; Gemini 3 target is gemini-3-pro-preview.
DEEP_RESEARCH_MODEL = os.getenv("DEEP_RESEARCH_MODEL", "gemini-3-pro-preview")
# Fallback model if the primary is unavailable on the credentialed project/key.
DEEP_RESEARCH_FALLBACK_MODEL = os.getenv("DEEP_RESEARCH_FALLBACK_MODEL", "gemini-pro-latest")
try:
    DEEP_RESEARCH_TEMPERATURE = float(os.getenv("DEEP_RESEARCH_TEMPERATURE", "0.1"))
except Exception:
    DEEP_RESEARCH_TEMPERATURE = 0.1
# Cost guard: require at least this many claims before a run is allowed.
try:
    DEEP_RESEARCH_MIN_CLAIMS = int(os.getenv("DEEP_RESEARCH_MIN_CLAIMS", "3"))
except Exception:
    DEEP_RESEARCH_MIN_CLAIMS = 3
# Cost guard: minimum acceptable markdown size (bytes) for a successful run; below this -> failed/refund.
try:
    DEEP_RESEARCH_MIN_OUTPUT_BYTES = int(os.getenv("DEEP_RESEARCH_MIN_OUTPUT_BYTES", "1024"))
except Exception:
    DEEP_RESEARCH_MIN_OUTPUT_BYTES = 1024
# Versioned prompt id recorded on every run for reproducibility/comparison.
DEEP_RESEARCH_PROMPT_VERSION = os.getenv("DEEP_RESEARCH_PROMPT_VERSION", "dr_prompt_v1")

# --- QUICK MODE: Faster verification with reduced thoroughness ---
# When enabled, reduces search depth, uses shorter timeouts, and skips some analysis
# Useful for testing, rate-limited scenarios, or when partial results are acceptable
QUICK_MODE = os.getenv("VERITYNGN_QUICK_MODE", "false").lower() in ("true", "1", "t")

# Quick mode configuration (only applied when QUICK_MODE=true)
QUICK_MODE_CONFIG = {
    # Reduced timeouts (in seconds)
    "agent_timeout": 45.0,           # Normal: 90s
    "search_timeout": 30.0,          # Normal: 60s
    "claim_verification_timeout": 60.0,  # Normal: 120s
    
    # Reduced search depth
    "max_evidence_sources": 5,       # Normal: 10-20
    "max_claims_to_verify": 10,      # Normal: 20
    "search_results_per_query": 3,   # Normal: 5-10
    
    # Skip expensive operations
    "skip_scientific_search": True,
    "skip_press_release_search": True,
    "skip_counter_intelligence": False,  # Keep CI as it's valuable
    
    # Rate limiting
    "inter_claim_delay": 3,          # Normal: 8s
    "circuit_breaker_threshold": 1,  # Trigger on first timeout
}

# Helper function to get quick mode setting with fallback
def get_quick_mode_setting(key: str, default=None):
    """Get a quick mode setting if quick mode is enabled, otherwise return default."""
    if QUICK_MODE:
        return QUICK_MODE_CONFIG.get(key, default)
    return default

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
YOUTUBE_DISABLE_V3 = os.getenv("YOUTUBE_DISABLE_V3", "false").lower() in ("true", "1", "t")
YOUTUBE_API_FALLBACK = os.getenv("YOUTUBE_API_FALLBACK", "true").lower() in ("true", "1", "t")
YOUTUBE_API_ENABLED = os.getenv("YOUTUBE_API_ENABLED", "true").lower() in ("true", "1", "t")
USE_SHERLOCK_CI = os.getenv("USE_SHERLOCK_CI", "true").lower() in ("true", "1", "t")

# Counter-intelligence enhancement (downloading .info.json / .vtt for found videos)
# Disabled by default to avoid heavy I/O during search
CI_ENHANCEMENT_ENABLED = os.getenv("CI_ENHANCEMENT_ENABLED", "False").lower() in ("true", "1", "t")

# YouTube counter-intel breadth controls
try:
    YT_CI_MAX_QUERIES = int(os.getenv("YT_CI_MAX_QUERIES", "2"))
except Exception:
    YT_CI_MAX_QUERIES = 2

try:
    YT_CI_PER_QUERY_RESULTS = int(os.getenv("YT_CI_PER_QUERY_RESULTS", "8"))
except Exception:
    YT_CI_PER_QUERY_RESULTS = 8

try:
    YT_CI_TOTAL_RESULTS = int(os.getenv("YT_CI_TOTAL_RESULTS", "30"))
except Exception:
    YT_CI_TOTAL_RESULTS = 30

# Semantic filter (MiniLM) feature flags
SEMANTIC_FILTER_ENABLED = _config.get("features.enable_semantic_filtering", False)
SEMANTIC_FILTER_THRESHOLD = float(_config.get("performance.semantic_filter_threshold", 0.25))

# Caching settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ("true", "1", "t")
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
try:
    YOUTUBE_API_TTL_HOURS = int(os.getenv("YOUTUBE_API_TTL_HOURS", "6"))
    TRANSCRIPT_TTL_HOURS = int(os.getenv("TRANSCRIPT_TTL_HOURS", "168"))
except Exception:
    YOUTUBE_API_TTL_HOURS = 6
    TRANSCRIPT_TTL_HOURS = 168

# YouTube API Services data-retention compliance (ToS III.E.4)
# Stored YouTube API statistics (view counts, likes, etc.) must be purged within this window.
try:
    YOUTUBE_DATA_RETENTION_DAYS = int(os.getenv("YOUTUBE_DATA_RETENTION_DAYS", "30"))
except Exception:
    YOUTUBE_DATA_RETENTION_DAYS = 30

# Report rollup fallback
ENABLE_CI_ROLLUP_FALLBACK = os.getenv("ENABLE_CI_ROLLUP_FALLBACK", "true").lower() in ("true", "1", "t")

# Other API keys from secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # OPTIONAL: Set in .env if using OpenAI
TWL_API_KEY = os.getenv("TWL_API_KEY", "")  # OPTIONAL: Set in .env if using TWL
GOOGLE_AI_STUDIO_KEY = os.getenv("GOOGLE_AI_STUDIO_KEY", "")  # OPTIONAL: Set in .env if using AI Studio
# Google Fact Check Tools API (free, 1000 req/day) - inject IFCN/ClaimReview as Tier 3 evidence
GOOGLE_FACTCHECK_API_KEY = os.getenv("GOOGLE_FACTCHECK_API_KEY", "").strip() or None

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

# Environment-aware directory configuration - move up to project root
BASE_DIR = Path(__file__).parent.parent.parent

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
TEMPLATE_PATH = Path(__file__).parent.parent / "template.html"

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
        "commercial_bucket": GCS_COMMERCIAL_BUCKET,  # User-scoped bucket when set
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