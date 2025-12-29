import logging
from typing import Dict, Any, List, Optional, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage  # Add for multimodal messages
from langgraph.graph import StateGraph, END
import os
import base64
import time  # Add time module for debugging measurements
import requests  # Add for network debugging
import subprocess  # Add for video downloading
from datetime import datetime
import json as json_lib
try:
    import psutil  # Add for memory monitoring (optional)
except ImportError:
    psutil = None  # Make psutil optional
import gc  # Add for garbage collection monitoring
import random  # Add for exponential backoff

from verityngn.models.workflow import InitialAnalysisState
from verityngn.config.prompts import INITIAL_ANALYSIS_PROMPT
from verityngn.config.settings import (
    AGENT_MODEL_NAME,
    DOWNLOADS_DIR,
    OUTPUTS_DIR,
    MAX_OUTPUT_TOKENS_2_5_FLASH,
    MAX_OUTPUT_TOKENS_2_0_FLASH,
    GENAI_VIDEO_MAX_OUTPUT_TOKENS,
    GOOGLE_AI_STUDIO_KEY,
    USE_GENAI_YOUTUBE_URL,
    USE_VERTEX_YOUTUBE_URL,
    YOUTUBE_VIDEO_GCS_URI,
    PROJECT_ID,
    LOCATION,
)
from verityngn.services.video.transcription import get_video_transcript
from verityngn.llm_logging.logger import log_llm_call, log_llm_response

# Initialize logger for this module
logger = logging.getLogger(__name__)
# Set to INFO level to ensure diagnostic logs are shown
logger.setLevel(logging.INFO)


def structure_claim(
    claim_data: Union[str, Dict[str, Any]], claim_id: int
) -> Dict[str, Any]:
    """
    Structure a claim into the required format.

    Args:
        claim_data (Union[str, Dict[str, Any]]): The raw claim data
        claim_id (int): The ID to assign to the claim

    Returns:
        Dict[str, Any]: The structured claim
    """
    if isinstance(claim_data, str):
        return {
            "claim_id": claim_id,
            "claim_text": claim_data,
            "timestamp": "00:00",  # Default timestamp
            "speaker": "Unknown",  # Default speaker
            "initial_assessment": "Requires verification",  # Default assessment
        }
    elif isinstance(claim_data, dict):
        return {
            "claim_id": claim_data.get("claim_id", claim_id),
            "claim_text": claim_data.get("claim_text", "Unknown claim"),
            "timestamp": claim_data.get("timestamp", "00:00"),
            "speaker": claim_data.get("speaker", "Unknown"),
            "initial_assessment": claim_data.get(
                "initial_assessment", "Requires verification"
            ),
        }
    else:
        return {
            "claim_id": claim_id,
            "claim_text": "Unknown claim",
            "timestamp": "00:00",
            "speaker": "Unknown",
            "initial_assessment": "Requires verification",
        }


def log_memory_usage(stage: str, logger: logging.Logger):
    """Log current memory usage with detailed breakdown."""
    if psutil is None:
        # psutil not installed, skip memory logging
        return
    
    try:
        process = psutil.Process()
        memory_info = process.memory_info()

        # Get memory usage in MB
        rss_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024

        # Get system memory
        system_memory = psutil.virtual_memory()
        available_mb = system_memory.available / 1024 / 1024
        percent_used = system_memory.percent

        logger.info(f"🧠 MEMORY USAGE [{stage}]:")
        logger.info(f"   Process RSS: {rss_mb:.1f} MB")
        logger.info(f"   Process VMS: {vms_mb:.1f} MB")
        logger.info(f"   System Available: {available_mb:.1f} MB")
        logger.info(f"   System Used: {percent_used:.1f}%")

        # Log if memory usage is concerning
        if rss_mb > 8000:  # Over 8GB
            logger.warning(f"⚠️ HIGH MEMORY USAGE: {rss_mb:.1f} MB")
        if available_mb < 2000:  # Less than 2GB available
            logger.warning(f"⚠️ LOW SYSTEM MEMORY: {available_mb:.1f} MB available")

    except Exception as e:
        logger.warning(f"Failed to get memory info: {e}")


def log_file_access(file_path: str, operation: str, logger: logging.Logger) -> bool:
    """Log file access operations with detailed debugging."""
    try:
        if not file_path or not os.path.exists(file_path):
            logger.error(
                f"📁 FILE ACCESS [{operation}] FAILED: {file_path} - File does not exist"
            )
            return False

        stat_info = os.stat(file_path)
        size_mb = stat_info.st_size / 1024 / 1024

        logger.info(f"📁 FILE ACCESS [{operation}]: {file_path}")
        logger.info(f"   Size: {size_mb:.1f} MB")
        logger.info(f"   Permissions: {oct(stat_info.st_mode)[-3:]}")
        logger.info(f"   Modified: {datetime.fromtimestamp(stat_info.st_mtime)}")

        # Check if file is too large
        if size_mb > 100:
            logger.warning(f"⚠️ LARGE FILE: {size_mb:.1f} MB - may cause memory issues")

        # Test read access
        try:
            with open(file_path, "rb") as f:
                first_bytes = f.read(1024)  # Read first 1KB
            logger.info(f"   ✅ Read access confirmed - first 1KB readable")
            return True
        except Exception as e:
            logger.error(f"   ❌ Read access failed: {e}")
            return False

    except Exception as e:
        logger.error(f"📁 FILE ACCESS [{operation}] ERROR: {e}")
        return False


def monitor_garbage_collection(logger: logging.Logger):
    """Monitor garbage collection to detect memory leaks."""
    try:
        gc_stats = gc.get_stats()
        logger.info(f"🗑️ GC STATS: {len(gc_stats)} generations")
        for i, stats in enumerate(gc_stats):
            logger.info(
                f"   Gen {i}: collections={stats['collections']}, collected={stats['collected']}"
            )

        # Force garbage collection
        collected = gc.collect()
        if collected > 0:
            logger.info(f"🗑️ GC FORCED: Collected {collected} objects")
    except Exception as e:
        logger.warning(f"Failed to get GC stats: {e}")


def test_youtube_connectivity(logger: logging.Logger) -> Dict[str, Any]:
    """Test network connectivity to YouTube from Cloud Run environment."""
    connectivity_results = {
        "youtube_accessible": False,
        "youtube_api_accessible": False,
        "video_accessible": False,
        "error_details": [],
    }

    test_urls = [
        ("YouTube Main", "https://www.youtube.com"),
        ("YouTube API", "https://www.googleapis.com/youtube/v3"),
        ("Sample Video", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ]

    logger.info("🌐 NETWORK CONNECTIVITY TEST: Testing YouTube access from Cloud Run")

    for name, url in test_urls:
        try:
            logger.info(f"🔗 Testing {name}: {url}")
            response = requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "VerityNgn/1.0 (Cloud Run Analysis Service)"},
            )

            if response.status_code == 200:
                logger.info(f"✅ {name}: SUCCESS (HTTP {response.status_code})")
                if "youtube.com" in url and "watch?v=" not in url:
                    connectivity_results["youtube_accessible"] = True
                elif "googleapis.com" in url:
                    connectivity_results["youtube_api_accessible"] = True
                elif "watch?v=" in url:
                    connectivity_results["video_accessible"] = True
            elif response.status_code in [301, 302, 403]:
                # These might still indicate YouTube is accessible
                logger.info(
                    f"🔄 {name}: REDIRECT/BLOCKED but accessible (HTTP {response.status_code})"
                )
                if "youtube.com" in url and "watch?v=" not in url:
                    connectivity_results["youtube_accessible"] = True
                elif "watch?v=" in url:
                    connectivity_results["video_accessible"] = True
            else:
                logger.warning(f"⚠️ {name}: HTTP {response.status_code}")
                connectivity_results["error_details"].append(
                    f"{name}: HTTP {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ {name}: Connection failed - {e}")
            connectivity_results["error_details"].append(f"{name}: {str(e)}")
        except Exception as e:
            logger.error(f"❌ {name}: Unexpected error - {e}")
            connectivity_results["error_details"].append(f"{name}: {str(e)}")

    # Test DNS resolution
    try:
        import socket

        logger.info("🔍 Testing DNS resolution for youtube.com")
        ip = socket.gethostbyname("youtube.com")
        logger.info(f"✅ DNS: youtube.com resolves to {ip}")
    except Exception as e:
        logger.error(f"❌ DNS: Failed to resolve youtube.com - {e}")
        connectivity_results["error_details"].append(f"DNS: {str(e)}")

    return connectivity_results


def extract_metadata_youtube_api(
    video_id: str, logger: logging.Logger
) -> Dict[str, Any]:
    """
    Extract YouTube metadata using YouTube Data API v3.
    Returns data in yt-dlp compatible format.
    """
    try:
        from googleapiclient.discovery import build
        from verityngn.config.settings import YOUTUBE_API_KEY

        if not YOUTUBE_API_KEY:
            raise ValueError("YouTube API key not configured")

        logger.info(f"🔑 Using YouTube Data API v3 for video: {video_id}")

        # Build YouTube service
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

        # Request video details
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics", id=video_id
        )
        response = request.execute()

        if not response.get("items"):
            raise ValueError(f"Video {video_id} not found or not accessible")

        video_data = response["items"][0]
        snippet = video_data.get("snippet", {})
        content_details = video_data.get("contentDetails", {})
        statistics = video_data.get("statistics", {})

        # Parse duration from ISO 8601 format (PT4M13S -> 253 seconds)
        duration_str = content_details.get("duration", "PT0S")
        duration_seconds = parse_youtube_duration(duration_str)

        # Convert to yt-dlp compatible format
        video_info = {
            "id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "uploader": snippet.get("channelTitle", ""),
            "uploader_id": snippet.get("channelId", ""),
            "upload_date": snippet.get("publishedAt", "")
            .replace("-", "")
            .replace("T", "")
            .split(".")[0],
            "duration": duration_seconds,
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "tags": snippet.get("tags", []),
            "categories": snippet.get("categoryId", ""),
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
            "extractor": "youtube_api_v3",
            "extractor_key": "YoutubeAPI",
        }

        logger.info(
            f"✅ YouTube API extracted: {video_info['title']} ({duration_seconds}s)"
        )
        logger.info(
            f"📝 Description length: {len(video_info['description'])} characters"
        )

        return video_info

    except Exception as e:
        logger.error(f"❌ YouTube Data API extraction failed: {e}")
        raise


def parse_youtube_duration(duration_str: str) -> int:
    """
    Parse YouTube API duration format (PT4M13S) to seconds.
    """
    import re

    # Remove PT prefix
    duration_str = duration_str.replace("PT", "")

    # Extract hours, minutes, seconds
    hours = 0
    minutes = 0
    seconds = 0

    # Match patterns like 1H, 30M, 45S
    hour_match = re.search(r"(\d+)H", duration_str)
    if hour_match:
        hours = int(hour_match.group(1))

    minute_match = re.search(r"(\d+)M", duration_str)
    if minute_match:
        minutes = int(minute_match.group(1))

    second_match = re.search(r"(\d+)S", duration_str)
    if second_match:
        seconds = int(second_match.group(1))

    return hours * 3600 + minutes * 60 + seconds


def extract_video_metadata_reliable(
    video_url: str, output_dir: str, logger: logging.Logger
) -> Dict[str, Any]:
    """
    Extract YouTube metadata using YouTube Data API v3 for Cloud Run compatibility.
    Falls back to yt-dlp if API fails.
    """
    import json  # Import at function level for use throughout

    metadata_result = {
        "success": False,
        "info_json_path": None,
        "subtitle_path": None,
        "video_info": {},
        "error": None,
    }

    logger.info(f"📋 METADATA EXTRACTION: Starting for {video_url}")

    try:
        from verityngn.utils.file_utils import extract_video_id

        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")

        # Create analysis directory
        analysis_dir = os.path.join(output_dir, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)

        # Set up file paths
        info_json_path = os.path.join(analysis_dir, f"{video_id}.info.json")
        subtitle_path = os.path.join(analysis_dir, f"{video_id}.en.vtt")

        logger.info(f"📁 Metadata directory: {analysis_dir}")
        logger.info(f"📄 Info JSON target: {info_json_path}")
        logger.info(f"📝 Subtitle target: {subtitle_path}")

        # TRY YOUTUBE DATA API V3 FIRST (Cloud Run compatible)
        try:
            logger.info("🌐 Attempting YouTube Data API v3 metadata extraction...")
            video_info = extract_metadata_youtube_api(video_id, logger)

            if video_info and video_info.get("title"):
                logger.info(
                    f"✅ YouTube API success: {video_info.get('title', 'Unknown')}"
                )

                # Save info JSON in yt-dlp compatible format
                with open(info_json_path, "w", encoding="utf-8") as f:
                    json.dump(video_info, f, indent=2, ensure_ascii=False)

                metadata_result["video_info"] = video_info
                metadata_result["info_json_path"] = info_json_path
                metadata_result["success"] = True

                logger.info(f"📄 Info JSON saved via YouTube API: {info_json_path}")
                return metadata_result

        except Exception as e:
            logger.warning(f"⚠️ YouTube API failed: {e}, falling back to yt-dlp...")

        # FALLBACK TO YT-DLP (for local development or when API fails)
        import yt_dlp

        ydl_opts = {
            # NO VIDEO DOWNLOAD - metadata only
            "skip_download": True,
            "writeinfojson": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "vtt",
            # Output paths
            "outtmpl": os.path.join(analysis_dir, f"{video_id}.%(ext)s"),
            # Reliability settings
            "ignoreerrors": True,
            "no_warnings": False,
            "quiet": False,
            "retries": 3,
            "socket_timeout": 30,
            # User agent for reliability
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            # Cookies to bypass YouTube bot detection
            "cookiefile": "cookies.txt",
        }

        logger.info("🚀 Extracting metadata and subtitles...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info without downloading
            info_dict = ydl.extract_info(video_url, download=False)

            if info_dict:
                logger.info(f"✅ Info extracted: {info_dict.get('title', 'Unknown')}")

                # Save info JSON manually to ensure we have it
                with open(info_json_path, "w", encoding="utf-8") as f:
                    json.dump(info_dict, f, indent=2, ensure_ascii=False)

                metadata_result["video_info"] = info_dict
                metadata_result["info_json_path"] = info_json_path
                logger.info(f"📄 Info JSON saved: {info_json_path}")

                # Try to download subtitles separately if they exist
                if info_dict.get("subtitles") or info_dict.get("automatic_captions"):
                    try:
                        # Download subtitles only
                        sub_ydl_opts = {
                            "skip_download": True,
                            "writesubtitles": True,
                            "writeautomaticsub": True,
                            "subtitleslangs": ["en"],
                            "subtitlesformat": "vtt",
                            "outtmpl": os.path.join(
                                analysis_dir, f"{video_id}.%(ext)s"
                            ),
                            "ignoreerrors": True,
                            "quiet": True,
                        }

                        with yt_dlp.YoutubeDL(sub_ydl_opts) as sub_ydl:
                            sub_ydl.download([video_url])

                        # Check for subtitle files
                        possible_sub_files = [
                            os.path.join(analysis_dir, f"{video_id}.en.vtt"),
                            os.path.join(analysis_dir, f"{video_id}.vtt"),
                            os.path.join(analysis_dir, f"{video_id}.en.srt"),
                            os.path.join(analysis_dir, f"{video_id}.srt"),
                        ]

                        for sub_file in possible_sub_files:
                            if os.path.exists(sub_file):
                                metadata_result["subtitle_path"] = sub_file
                                logger.info(f"📝 Subtitles saved: {sub_file}")
                                break

                    except Exception as e:
                        logger.warning(f"⚠️ Subtitle extraction failed: {e}")

                metadata_result["success"] = True
                logger.info("✅ METADATA EXTRACTION SUCCESS")

            else:
                logger.error("❌ No info dict returned from yt-dlp")
                metadata_result["error"] = "No info dict returned"

    except Exception as e:
        error_msg = str(e)
        metadata_result["error"] = error_msg
        logger.error(f"❌ METADATA EXTRACTION FAILED: {error_msg}")

    return metadata_result


def download_video_robust_cloud_config(
    video_url: str, output_path: str, logger: logging.Logger
) -> Dict[str, Any]:
    """
    Download video using robust Cloud Run optimized yt-dlp configuration.
    Based on Perplexity research for production-grade YouTube downloading.
    Organizes files in analysis directory structure.
    """
    download_result = {
        "success": False,
        "video_path": None,
        "file_size_mb": 0,
        "download_time_seconds": 0,
        "error": None,
        "analysis_files": {},  # Track all downloaded files
    }

    logger.info(f"📥 ROBUST CLOUD CONFIG DOWNLOAD: Starting download from {video_url}")
    start_time = time.time()

    try:
        # Import yt-dlp and other required modules
        import yt_dlp
        import tempfile
        from verityngn.utils.file_utils import extract_video_id

        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")

        # Create analysis directory structure
        output_dir = os.path.dirname(output_path)
        analysis_dir = os.path.join(output_dir, "analysis")
        os.makedirs(analysis_dir, exist_ok=True)

        # Set up file paths for organized structure
        video_file = os.path.join(analysis_dir, f"{video_id}.mp4")
        info_file = os.path.join(analysis_dir, f"{video_id}.info.json")
        description_file = os.path.join(analysis_dir, f"{video_id}.description")
        subtitle_file = os.path.join(analysis_dir, f"{video_id}.en.vtt")

        logger.info(f"📁 Analysis directory: {analysis_dir}")
        logger.info(f"🎬 Video file: {video_file}")

        # ROBUST CLOUD RUN OPTIMIZED CONFIG (from Perplexity research)
        ydl_opts = {
            # Format selection optimized for Cloud Run constraints
            "format": "best[height<=1080]",  # Limit to 1080p to manage size and bandwidth
            "outtmpl": video_file,  # Use organized path
            # Audio/video options
            "extractaudio": False,
            "writesubtitles": False,  # Disable to prevent "Did not get any data blocks"
            "writeautomaticsub": False,  # Disable to prevent YouTube bot detection
            "writedescription": True,
            "writeinfojson": True,
            # Error handling and reliability
            "ignoreerrors": True,
            "no_warnings": False,
            "quiet": False,
            "verbose": True,
            # Cloud Run optimized network settings
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "file_access_retries": 3,
            "extractor_retries": 3,
            "http_chunk_size": 10485760,  # 10MB chunks for Cloud Run
            # Additional reliability options
            "force_json": False,
            "no_check_certificate": True,
            "prefer_insecure": False,
            # Subtitle handling (enable for downstream use)
            "writesubtitles": False,  # Disable to prevent "Did not get any data blocks"
            "writeautomaticsub": False,  # Disable to prevent YouTube bot detection
            "subtitleslangs": ["en"],  # English subtitles for downstream processing
            # User agent and headers
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            # Network optimization
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            },
        }

        logger.info(f"🔧 Using ROBUST CLOUD CONFIG: {ydl_opts['format']}")
        logger.info(f"📊 Chunk size: {ydl_opts['http_chunk_size']} bytes")
        logger.info(f"⏱️ Socket timeout: {ydl_opts['socket_timeout']} seconds")

        # Single attempt with robust configuration (no manual retries)
        try:
            logger.info(f"🚀 Starting robust download")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info and download
                info_dict = ydl.extract_info(video_url, download=True)

                # Log video information
                if info_dict:
                    logger.info(f"📺 Title: {info_dict.get('title', 'Unknown')}")
                    logger.info(f"⏱️ Duration: {info_dict.get('duration', 0)} seconds")
                    logger.info(f"👤 Uploader: {info_dict.get('uploader', 'Unknown')}")
                    logger.info(
                        f"📅 Upload date: {info_dict.get('upload_date', 'Unknown')}"
                    )

            # Check downloaded files and organize analysis structure
            analysis_files = {}

            # Check main video file
            if os.path.exists(video_file):
                file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
                analysis_files["video"] = video_file
                logger.info(f"✅ Video file: {video_file} ({file_size_mb:.1f} MB)")

            # Check info JSON file
            if os.path.exists(info_file):
                analysis_files["info_json"] = info_file
                logger.info(f"✅ Info JSON: {info_file}")

            # Check description file
            if os.path.exists(description_file):
                analysis_files["description"] = description_file
                logger.info(f"✅ Description: {description_file}")

            # Check for subtitle files (various formats)
            possible_subtitle_files = [
                os.path.join(analysis_dir, f"{video_id}.en.vtt"),
                os.path.join(analysis_dir, f"{video_id}.en.srt"),
                os.path.join(analysis_dir, f"{video_id}.vtt"),
                os.path.join(analysis_dir, f"{video_id}.srt"),
            ]

            for sub_file in possible_subtitle_files:
                if os.path.exists(sub_file):
                    analysis_files["subtitles"] = sub_file
                    logger.info(f"✅ Subtitles: {sub_file}")
                    break

            if analysis_files:
                end_time = time.time()
                download_time = end_time - start_time

                download_result.update(
                    {
                        "success": True,
                        "video_path": analysis_files.get("video", video_file),
                        "file_size_mb": (
                            file_size_mb if "file_size_mb" in locals() else 0
                        ),
                        "download_time_seconds": download_time,
                        "error": None,
                        "analysis_files": analysis_files,
                        "analysis_dir": analysis_dir,
                    }
                )

                logger.info(
                    f"✅ ROBUST DOWNLOAD SUCCESS: {len(analysis_files)} files in {download_time:.1f}s"
                )
                logger.info(f"📁 Analysis ready at: {analysis_dir}")
                return download_result
            else:
                download_result["error"] = (
                    f"Download completed but no files found in: {analysis_dir}"
                )
                logger.error(f"❌ NO FILES FOUND in analysis directory: {analysis_dir}")

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            download_result["error"] = error_msg
            logger.error(f"❌ yt-dlp Download Error: {error_msg}")

            # Check for specific errors and suggest fallbacks
            if "Did not get any data blocks" in error_msg:
                logger.info(
                    "💡 Suggestion: This error often indicates network/server issues"
                )
            elif "Sign in to confirm" in error_msg:
                logger.info(
                    "💡 Suggestion: YouTube bot detection - try different approach"
                )

        except Exception as e:
            download_result["error"] = str(e)
            logger.error(f"❌ Unexpected download error: {e}")

        end_time = time.time()
        download_result["download_time_seconds"] = end_time - start_time
        logger.error(
            f"❌ ROBUST DOWNLOAD FAILED after {download_result['download_time_seconds']:.1f} seconds"
        )

        # FALLBACK: Try metadata-only extraction when video download fails
        logger.info("🔄 FALLBACK: Attempting metadata-only extraction...")
        try:
            metadata_result = extract_video_metadata_reliable(
                video_url, output_dir, logger
            )
            if metadata_result.get("success") and metadata_result.get("info_json_path"):
                # Update download result with metadata info
                download_result.update(
                    {
                        "analysis_files": (
                            {
                                "info_json": metadata_result["info_json_path"],
                                "subtitles": metadata_result.get("subtitle_path"),
                            }
                            if metadata_result.get("subtitle_path")
                            else {"info_json": metadata_result["info_json_path"]}
                        ),
                        "analysis_dir": analysis_dir,
                        "metadata_only": True,  # Flag to indicate we only have metadata
                    }
                )
                logger.info(
                    f"✅ METADATA FALLBACK SUCCESS: Extracted info and subtitles"
                )
                logger.info(f"📄 Info JSON: {metadata_result['info_json_path']}")
                if metadata_result.get("subtitle_path"):
                    logger.info(f"📝 Subtitles: {metadata_result['subtitle_path']}")

            else:
                logger.warning("⚠️ Metadata fallback also failed")

        except Exception as fallback_error:
            logger.error(f"❌ Metadata fallback error: {fallback_error}")

        return download_result

    except Exception as e:
        end_time = time.time()
        download_result.update(
            {
                "success": False,
                "error": str(e),
                "download_time_seconds": end_time - start_time,
            }
        )
        logger.error(f"❌ ROBUST DOWNLOAD EXCEPTION: {e}")
        return download_result


def analyze_video_content(state):
    """
    Analyze video content using multimodal approach with download fallback.
    Handles both dict and Pydantic object inputs for compatibility.
    """
    from verityngn.utils.file_utils import extract_video_id

    # Configure logging
    logger = logging.getLogger(__name__)

    # Handle both dict and Pydantic object inputs
    if isinstance(state, dict):
        video_id = state.get("video_id")
        video_url = state.get("video_url")
        video_path = state.get("video_path", "")
    else:
        video_id = getattr(state, "video_id", None)
        video_url = getattr(state, "video_url", None)
        video_path = getattr(state, "video_path", "")

    if not video_id:
        logger.error("No video_id provided in state")
        return state

    if not video_url:
        logger.error("No video_url provided in state")
        return state

    logger.info(f"🎬 AGGRESSIVE MULTIMODAL ANALYSIS START: {video_id}")

    # STEP 1: Initial memory and system status
    log_memory_usage("ANALYSIS_START", logger)
    monitor_garbage_collection(logger)

    # Debug print with enhanced tracking
    print(
        f"\n==== AGGRESSIVE MULTIMODAL ANALYSIS START [{datetime.now().isoformat()}] ===="
    )
    print(f"🎯 MISSION: Extract claims from video frames (1 frame/second)")
    print(f"Video ID: {video_id}")
    print(f"Video Path: {video_path}")
    print(f"Video URL: {video_url}")

    try:
        # STEP 2: Network connectivity debugging
        logger.info("🌐 TESTING NETWORK CONNECTIVITY TO YOUTUBE")
        connectivity = test_youtube_connectivity(logger)

        if not connectivity["youtube_accessible"]:
            logger.warning("⚠️ YouTube access issues detected from Cloud Run")
            print("⚠️ YouTube access may be restricted from Cloud Run environment")

        # STEP 3: File system debugging
        if video_path:
            logger.info(f"🔍 CHECKING VIDEO FILE ACCESS")
            file_readable = log_file_access(video_path, "VIDEO_READ", logger)
            if not file_readable:
                logger.error(f"❌ Cannot access video file: {video_path}")
                print(f"❌ Cannot access video file: {video_path}")

        # STEP 4: Memory check before LLM initialization
        log_memory_usage("BEFORE_LLM_INIT", logger)

        # Create the LLM with AGGRESSIVE multimodal capabilities
        logger.info(f"🤖 INITIALIZING AGGRESSIVE MULTIMODAL LLM: {AGENT_MODEL_NAME}")
        from verityngn.utils.llm_utils import build_langchain_vertex_kwargs

        llm = ChatVertexAI(
            **build_langchain_vertex_kwargs(
                AGENT_MODEL_NAME, preferred_tokens=32768, temperature=0.2, top_p=0.95
            ),
            top_k=40,
            verbose=True,
            streaming=False,
        )

        # STEP 5: Memory check after LLM initialization
        log_memory_usage("AFTER_LLM_INIT", logger)

        # STEP 6: Prepare AGGRESSIVE multimodal content

        def create_robust_video_analysis_prompt() -> str:
            """
            Creates a balanced prompt that encourages valid JSON without being overly restrictive
            """
            return f"""
🎬 VIDEO ANALYSIS - EXTRACT FACTUAL CLAIMS 🎬

Please analyze this video and extract factual claims. Respond with valid JSON only.

ANALYSIS REQUIREMENTS:
1. Extract 7-25 specific factual claims from the video
2. Include timestamps for each claim  
3. Identify the source of each claim (speaker name or "Visual Text")
4. Assess if each claim is verifiable

JSON FORMAT - Use this structure:

{{
  "initial_report": "Brief summary of video content and main themes in 2-3 sentences",
  "claims": [
    {{
      "claim_text": "Exact factual claim from the video",
      "timestamp": "MM:SS",
      "speaker": "Speaker name or Visual Text", 
      "initial_assessment": "Brief assessment of claim verifiability"
    }}
  ],
  "video_analysis_summary": "One sentence summary of analysis process and findings"
}}

JSON GUIDELINES:
- Use straight quotes " not curly quotes
- Keep claim_text under 200 characters
- Use timestamps like "05:30" 
- Extract claims from ACTUAL video content only

Respond with only the JSON object.
        """

        prompt_text = f"""
AGGRESSIVE VIDEO FRAME ANALYSIS - CLAIMS EXTRACTION MISSION

CRITICAL INSTRUCTIONS FOR MULTIMODAL VIDEO ANALYSIS:
- Analyze this video with MAXIMUM detail at 1 FRAME PER SECOND sampling rate
- Extract ALL factual claims, statements, assertions from ACTUAL VIDEO CONTENT
- Focus on SPOKEN WORDS, VISUAL TEXT, ON-SCREEN GRAPHICS, DEMONSTRATIONS and ACTIONS
- Use the CRAAP categories to focus extraction on (CRAAP = (Currency, Relevance, Authority, Accuracy, and Popularity)
- Goal is to extract claims that address the Truthfulness , verity  and scope of the video
- Ignore background music, decorative elements, or irrelevant visuals
- Extract 7-50 specific, verifiable claims from the actual video frames and audio

Video ID: {video_id}
Video URL: {video_url}

AGGRESSIVE MULTIMODAL REQUIREMENTS:
1. Sample video at 1 frame per second (aggressive temporal resolution)
2. Transcribe ALL spoken content with timestamps
3. Extract text from visual overlays, graphics, slides, captions
4. Identify claims from demonstrations, charts, or visual evidence
5. Note precise timestamps for each claim
6. Distinguish between speaker statements and visual text

FRAME-BY-FRAME ANALYSIS FOCUS:
- What is being SAID in the audio track?
- What TEXT appears on screen?
- What DEMONSTRATIONS or EVIDENCE is shown?
- What GRAPHICS or CHARTS contain factual information?
- What CLAIMS can be verified from external sources?

🚨 EXTRACT CLAIMS FROM ACTUAL VIDEO FRAMES & AUDIO - NOT METADATA OR DESCRIPTIONS! 🚨
"""

        prompt_text = create_robust_video_analysis_prompt()

        # STEP 7: AGGRESSIVE multimodal analysis with uploaded video file
        video_file_uri = None
        if video_path and os.path.exists(video_path):
            logger.info(f"🎯 ATTEMPTING AGGRESSIVE MULTIMODAL ANALYSIS WITH VIDEO FILE")
            print(f"🎯 Starting aggressive multimodal analysis with video file...")

            try:
                # Upload video to GCS for Gemini analysis
                from verityngn.services.storage.gcs_storage import upload_to_gcs

                gcs_path = f"tmp/analysis/{video_id}/aggressive_analysis.mp4"

                # Trim video for analysis if it's too long (60 minutes max for Cloud Run)
                analysis_video_path = video_path
                if os.path.exists(video_path):
                    try:
                        # Check video duration and trim if needed
                        import subprocess

                        result = subprocess.run(
                            [
                                "ffprobe",
                                "-v",
                                "quiet",
                                "-print_format",
                                "json",
                                "-show_format",
                                video_path,
                            ],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        if result.returncode == 0:
                            import json

                            info = json.loads(result.stdout)
                            duration = float(info["format"].get("duration", 0))

                            if duration > 3600:  # 60 minutes
                                logger.info(
                                    f"📏 Video too long ({duration}s), trimming to 30 minutes for analysis"
                                )
                                analysis_video_path = trim_video_for_analysis(
                                    video_path, max_duration=300
                                )
                                if not analysis_video_path or not os.path.exists(
                                    analysis_video_path
                                ):
                                    logger.warning(
                                        "Failed to trim video, using original"
                                    )
                                    analysis_video_path = video_path
                    except Exception as e:
                        logger.warning(f"Could not check/trim video duration: {e}")
                        analysis_video_path = video_path

                # Upload to GCS
                video_file_uri = upload_to_gcs(analysis_video_path, gcs_path)
                logger.info(f"✅ Video uploaded to GCS: {video_file_uri}")
                print(f"✅ Video uploaded for aggressive analysis")

                # Create proper message format for Vertex AI multimodal with GCS URI
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "media",
                            "file_uri": video_file_uri,
                            "mime_type": "video/mp4",
                        },
                    ]
                )

                logger.info("✅ AGGRESSIVE MULTIMODAL CONTENT PREPARED")
                print(f"✅ GCS video configured for aggressive 1fps analysis")

                # STEP 8: Memory check before LLM invocation
                log_memory_usage("BEFORE_AGGRESSIVE_LLM", logger)

                # STEP 9: AGGRESSIVE LLM invocation with extended timeout
                logger.info(
                    f"🚀 AGGRESSIVE LLM INVOCATION STARTED at {datetime.now().isoformat()}"
                )
                print("🚀 Invoking LLM with aggressive multimodal capabilities...")

                start_time = time.time()

                call_id = log_llm_call(
                    operation="analyze_video_content_multimodal",
                    prompt=prompt_text,
                    model=AGENT_MODEL_NAME,
                    video_id=video_id,
                    metadata={"video_file_uri": video_file_uri}
                )

                try:
                    # Give more time for aggressive analysis
                    response = llm.invoke([message], timeout=1800)  # 15 minute timeout
                    duration = time.time() - start_time
                    log_llm_response(call_id, response, duration=duration)
                    end_time = time.time()

                    # STEP 10: Memory check after LLM completion
                    log_memory_usage("AFTER_AGGRESSIVE_LLM", logger)
                    processing_time = end_time - start_time

                    logger.info(
                        f"⏱️ AGGRESSIVE LLM PROCESSING COMPLETE: {processing_time:.1f} seconds"
                    )
                    print(
                        f"✅ Aggressive analysis completed in {processing_time:.1f} seconds"
                    )

                    if response and hasattr(response, "content") and response.content:
                        logger.info(
                            f"📊 RESPONSE LENGTH: {len(response.content)} characters"
                        )
                        return parse_llm_response(response.content, video_id, logger)
                    else:
                        logger.warning(
                            "⚠️ Empty response from aggressive multimodal analysis"
                        )

                except Exception as e:
                    end_time = time.time()
                    processing_time = end_time - start_time
                    logger.error(
                        f"❌ AGGRESSIVE MULTIMODAL ANALYSIS FAILED after {processing_time:.1f}s: {e}"
                    )
                    print(f"❌ Multimodal analysis failed: {e}")

            except Exception as e:
                logger.error(f"❌ Failed to upload video for multimodal analysis: {e}")
                print(f"❌ Video upload failed: {e}")

        # STEP 7b: YouTube URL analysis using Vertex AI multimodal (direct YouTube URL support)
        elif video_url and USE_VERTEX_YOUTUBE_URL:
            logger.info(
                "🎯 Using Vertex AI multimodal analysis with direct YouTube URL (no AI Studio, no GCS upload)"
            )
            try:
                # Import Vertex AI modules (Updated for latest SDK)
                import vertexai
                from vertexai.generative_models import (
                    GenerativeModel,
                    Part,
                    GenerationConfig,
                )

                # Initialize Vertex AI with updated pattern
                vertexai.init(project=PROJECT_ID, location=LOCATION)
                model = GenerativeModel("gemini-2.5-flash")

                # Create prompt for 1 frame/sec analysis
                analysis_prompt = f"""
                {prompt_text}
                
                CRITICAL REQUIREMENTS:
                - Analyze this YouTube video at 1 frame per second resolution
                - Extract factual claims with precise timestamps
                - Focus on speaker credibility claims (minimum 20% of total)
                - Identify visual text, graphics, and demonstrations
                - Provide comprehensive frame-by-frame analysis
                
                Return as valid JSON with claims array containing:
                - claim_text: The specific factual claim
                - timestamp: MM:SS format where claim appears
                - speaker: Who made the claim or "Visual Text" for on-screen content
                - source_type: spoken|visual_text|demonstration|graphic|chart
                - initial_assessment: Brief assessment of claim verifiability
                """

                # Create YouTube video part using direct URL
                video_part = Part.from_uri(video_url, mime_type="video/youtube")

                # Set generation config with high token limit for comprehensive analysis
                generation_config = GenerationConfig(
                    max_output_tokens=65535,  # Use full 64k limit
                    temperature=0.2,
                    top_p=0.95,
                    top_k=40,
                )

                log_memory_usage("BEFORE_VERTEX_YT_DIRECT_LLM", logger)
                logger.info("🚀 Invoking Vertex AI with direct YouTube URL...")

                start_time = time.time()
                call_id = log_llm_call(
                    operation="analyze_video_content_vertex_yt_direct",
                    prompt=analysis_prompt,
                    model="gemini-2.5-flash",
                    video_id=video_id,
                    metadata={"video_url": video_url}
                )

                # Generate content with streaming to handle large outputs
                response = model.generate_content(
                    contents=[analysis_prompt, video_part],
                    generation_config=generation_config,
                    stream=True,  # Enable streaming for large responses
                )

                # Collect full response from stream
                full_response = ""
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                
                duration = time.time() - start_time
                log_llm_response(call_id, full_response, duration=duration)

                log_memory_usage("AFTER_VERTEX_YT_DIRECT_LLM", logger)

                if full_response:
                    logger.info(
                        f"✅ Vertex AI YouTube analysis completed: {len(full_response)} characters"
                    )

                    # Save LLM response for debugging if DEBUG_OUTPUTS is enabled
                    if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true":
                        import json
                        from datetime import datetime
                        from pathlib import Path

                        debug_dir = Path(f"./sherlock_analysis_{video_id}/llm_calls")
                        debug_dir.mkdir(parents=True, exist_ok=True)

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        debug_file = (
                            debug_dir / f"vertex_youtube_analysis_{timestamp}.json"
                        )

                        debug_data = {
                            "timestamp": datetime.now().isoformat(),
                            "video_id": video_id,
                            "llm_model": "gemini-2.5-flash",
                            "analysis_type": "vertex_youtube_url",
                            "prompt_text": analysis_prompt,
                            "prompt_length": len(analysis_prompt),
                            "response_content": full_response,
                            "response_length": len(full_response),
                            "response_type": "vertexai_streaming_response",
                            "success": bool(full_response),
                        }

                        with open(debug_file, "w") as f:
                            json.dump(debug_data, f, indent=2)
                        logger.info(
                            f"🔍 DEBUG: Saved Vertex AI LLM response to {debug_file}"
                        )

                    return parse_llm_response(full_response, video_id, logger)
                else:
                    logger.warning("⚠️ Empty response from Vertex AI YouTube analysis")

            except Exception as e:
                logger.error(f"❌ Vertex AI YouTube URL analysis failed: {e}")
                logger.error(f"Error details: {str(e)}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

        # STEP 7c: YouTube URL analysis using proper genai client
        elif video_url and USE_GENAI_YOUTUBE_URL:
            logger.info(f"🎯 Using YouTube URL analysis with genai client (enabled)")
            print(f"🎯 Starting YouTube URL analysis with genai client...")

            try:
                from google import genai
                from google.genai.types import HttpOptions, Part

                # Initialize genai client with API key from settings
                client = genai.Client(
                    api_key=GOOGLE_AI_STUDIO_KEY,
                    http_options=HttpOptions(api_version="v1"),
                )

                logger.info("✅ GENAI CLIENT INITIALIZED")
                print(f"✅ genai client configured for YouTube URL analysis")

                # STEP 8: Memory check before LLM invocation
                log_memory_usage("BEFORE_GENAI_LLM", logger)

                # STEP 9: genai LLM invocation with YouTube URL
                logger.info(
                    f"🚀 GENAI LLM INVOCATION STARTED at {datetime.now().isoformat()}"
                )
                print("🚀 Invoking genai client with YouTube URL...")

                start_time = time.time()
                call_id = log_llm_call(
                    operation="analyze_video_content_genai_yt_direct",
                    prompt=prompt_text,
                    model="gemini-2.0-flash",
                    video_id=video_id,
                    metadata={"video_url": video_url}
                )

                try:
                    # Use proper genai format for YouTube URL
                    response = client.models.generate_content(
                        # Force 2.0 flash for YouTube URL to respect 8k limit
                        model="gemini-2.0-flash",
                        contents=[
                            Part.from_uri(
                                file_uri=video_url,
                                mime_type="video/youtube",  # Correct mime type for YouTube URLs
                            ),
                            prompt_text,  # The analysis prompt
                        ],
                        config={
                            "response_mime_type": "application/json",
                            "max_output_tokens": GENAI_VIDEO_MAX_OUTPUT_TOKENS,
                        },
                    )
                    duration = time.time() - start_time
                    log_llm_response(call_id, response, duration=duration)

                    end_time = time.time()

                    # STEP 10: Memory check after LLM completion
                    log_memory_usage("AFTER_GENAI_LLM", logger)
                    processing_time = end_time - start_time

                    logger.info(
                        f"⏱️ GENAI LLM PROCESSING COMPLETE: {processing_time:.1f} seconds"
                    )
                    print(
                        f"✅ genai analysis completed in {processing_time:.1f} seconds"
                    )

                    if response and hasattr(response, "text") and response.text:
                        logger.info(
                            f"📊 RESPONSE LENGTH: {len(response.text)} characters"
                        )
                        return parse_llm_response(response.text, video_id, logger)
                    else:
                        logger.warning(
                            "⚠️ Empty response from genai YouTube URL analysis"
                        )

                except Exception as e:
                    end_time = time.time()
                    processing_time = end_time - start_time
                    logger.error(
                        f"❌ GENAI URL ANALYSIS FAILED after {processing_time:.1f}s: {e}"
                    )
                    print(f"❌ genai YouTube URL analysis failed: {e}")

            except Exception as setup_error:
                logger.error(f"❌ GENAI SETUP FAILED: {setup_error}")
                print(f"❌ Failed to setup genai client: {setup_error}")
        elif video_url and not USE_GENAI_YOUTUBE_URL:
            logger.info(
                "🎯 Skipping genai YouTube URL path (disabled); proceeding with Vertex-based fallback"
            )

        # STEP 11: ALWAYS extract metadata first - ensures we have .json and .vtt files
        logger.info("📋 STEP 11: Extracting reliable metadata and subtitles")
        print("📋 Extracting video metadata and subtitles...")

        if video_url:
            # Create download path using output directory structure
            if isinstance(state, dict):
                out_dir_path = state.get("out_dir_path", "/tmp/verity_outputs")
            else:
                out_dir_path = getattr(state, "out_dir_path", "/tmp/verity_outputs")

            # Extract metadata FIRST - this always runs regardless of download success
            metadata_result = extract_video_metadata_reliable(
                video_url, out_dir_path, logger
            )

            if metadata_result["success"]:
                logger.info(
                    f"✅ METADATA EXTRACTED: {metadata_result['video_info'].get('title', 'Unknown')}"
                )
                print(
                    f"✅ Video metadata extracted: {metadata_result['video_info'].get('title', 'Unknown')}"
                )

                # Store metadata info for report generation
                video_info_extracted = metadata_result["video_info"]
                info_json_path = metadata_result["info_json_path"]
                subtitle_path = metadata_result["subtitle_path"]

                logger.info(f"📄 Info JSON: {info_json_path}")
                if subtitle_path:
                    logger.info(f"📝 Subtitles: {subtitle_path}")
            else:
                logger.warning(
                    f"⚠️ METADATA EXTRACTION FAILED: {metadata_result.get('error', 'Unknown error')}"
                )
                video_info_extracted = {}
                info_json_path = None
                subtitle_path = None

        # STEP 12: FALLBACK - Aggressive video download and local analysis
        logger.info("🔄 FALLBACK: Attempting aggressive video download")
        print("🔄 Fallback: Downloading video file for local analysis...")

        if video_url:
            # Use organized analysis directory
            analysis_dir = os.path.join(out_dir_path, "analysis")
            video_file_path = os.path.join(analysis_dir, f"{video_id}.mp4")

            logger.info(f"📁 Using output directory: {out_dir_path}")
            logger.info(f"📁 Analysis directory: {analysis_dir}")

            # Attempt download using robust cloud configuration with try-catch
            try:
                download_result = download_video_robust_cloud_config(
                    video_url, video_file_path, logger
                )
            except Exception as e:
                logger.warning(f"⚠️ Video download failed: {e}")
                download_result = {"success": False, "error": str(e)}

            if download_result["success"]:
                logger.info(
                    f"✅ ROBUST DOWNLOAD SUCCESS: {download_result['file_size_mb']:.1f} MB"
                )
                print(f"✅ Video downloaded: {download_result['file_size_mb']:.1f} MB")

                analysis_files = download_result.get("analysis_files", {})
                logger.info(
                    f"📁 Analysis files available: {list(analysis_files.keys())}"
                )

                # STEP 12: Analyze downloaded video file
                try:
                    log_memory_usage("BEFORE_FILE_ANALYSIS", logger)

                    # Read video file for multimodal analysis
                    video_path = analysis_files.get("video", video_file_path)
                    with open(video_path, "rb") as f:
                        video_data = base64.b64encode(f.read()).decode("utf-8")

                    # Prepare content with downloaded video for Vertex AI
                    file_message = HumanMessage(
                        content=[
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "media",
                                "data": video_data,
                                "mime_type": "video/mp4",
                            },
                        ]
                    )

                    logger.info("🎬 STARTING LOCAL VIDEO FILE ANALYSIS")
                    start_time = time.time()
                    call_id = log_llm_call(
                        operation="analyze_video_content_local_file",
                        prompt=prompt_text,
                        model=AGENT_MODEL_NAME,
                        video_id=video_id,
                        metadata={"video_path": video_path}
                    )

                    response = llm.invoke([file_message], timeout=900)
                    duration = time.time() - start_time
                    log_llm_response(call_id, response, duration=duration)
                    end_time = time.time()

                    log_memory_usage("AFTER_FILE_ANALYSIS", logger)
                    processing_time = end_time - start_time

                    logger.info(
                        f"⏱️ FILE ANALYSIS COMPLETE: {processing_time:.1f} seconds"
                    )

                    # Extract claims from response
                    parsed_result = parse_llm_response(
                        response.content, video_id, logger
                    )
                    claims = parsed_result.get("claims", [])

                    if claims:
                        logger.info(
                            f"🎯 CLAIMS EXTRACTED FROM LOCAL FILE: {len(claims)} claims"
                        )
                        print(f"🎯 Claims extracted: {len(claims)}")

                        result = {
                            "initial_analysis": {
                                "claims": claims,
                                "analysis_source": "local_video_file",
                                "processing_time_seconds": processing_time,
                                "file_size_mb": download_result["file_size_mb"],
                                "download_time_seconds": download_result[
                                    "download_time_seconds"
                                ],
                                "total_time_seconds": processing_time
                                + download_result["download_time_seconds"],
                            },
                            "claims": claims,
                            "analysis_method": "local_video_file",
                            "video_path": video_path,
                            "analysis_files": analysis_files,  # Pass analysis files for downstream use
                            "analysis_dir": download_result.get("analysis_dir"),
                            "download_success": True,
                            "video_info": (
                                video_info_extracted
                                if "video_info_extracted" in locals()
                                else {}
                            ),
                            "info_json_path": (
                                info_json_path if "info_json_path" in locals() else None
                            ),
                            "subtitle_path": (
                                subtitle_path if "subtitle_path" in locals() else None
                            ),
                        }

                        log_memory_usage("FINAL_LOCAL_FILE", logger)
                        return result
                    else:
                        logger.warning(
                            "❌ NO CLAIMS from local file analysis - falling back to URL analysis"
                        )

                except Exception as e:
                    logger.error(f"❌ LOCAL FILE ANALYSIS FAILED: {e}")
                    logger.info("🔄 Falling back to URL analysis")

            else:
                logger.error(
                    f"❌ ROBUST DOWNLOAD FAILED: {download_result.get('error', 'Unknown error')}"
                )
                logger.info("🔄 Falling back to URL analysis")
                print(
                    f"❌ Download failed: {download_result.get('error', 'Unknown error')}"
                )

        # STEP 13: Fallback to YouTube URL analysis (multimodal)
        logger.info("🔄 ATTEMPTING YOUTUBE URL MULTIMODAL ANALYSIS")
        print("🔄 Attempting YouTube URL analysis...")

        # Use extract_claims_with_gemini_multimodal_sync for URL analysis
        try:
            claims = extract_claims_with_gemini_multimodal_sync(video_url, logger)

            if claims:
                logger.info(f"🎯 CLAIMS EXTRACTED FROM URL: {len(claims)} claims")
                print(f"🎯 Claims extracted: {len(claims)}")

                result = {
                    "initial_analysis": {
                        "claims": claims,
                        "analysis_source": "youtube_url_multimodal",
                        "processing_time_seconds": 0,  # Will be updated by sync wrapper
                        "fallback_reason": (
                            "download_failed" if video_url else "no_download_attempted"
                        ),
                    },
                    "claims": claims,
                    "analysis_method": "youtube_url_multimodal",
                    "video_path": None,
                    "download_success": False,
                    "video_info": (
                        video_info_extracted
                        if "video_info_extracted" in locals()
                        else {}
                    ),
                    "info_json_path": (
                        info_json_path if "info_json_path" in locals() else None
                    ),
                    "subtitle_path": (
                        subtitle_path if "subtitle_path" in locals() else None
                    ),
                }

                log_memory_usage("FINAL_URL_MULTIMODAL", logger)
                return result
            else:
                logger.error("❌ NO CLAIMS from URL analysis")
                print("❌ No claims extracted from URL analysis")

        except Exception as e:
            logger.error(f"❌ URL MULTIMODAL ANALYSIS FAILED: {e}")
            print(f"❌ URL analysis failed: {e}")

        # STEP 14: Final fallback - return empty result with error
        logger.error("❌ ALL ANALYSIS METHODS FAILED")
        print("❌ All analysis methods failed")

        result = {
            "initial_analysis": {
                "claims": [],
                "analysis_source": "failed",
                "error": "Both local download and URL analysis failed",
            },
            "claims": [],
            "analysis_method": "failed",
            "video_path": None,
            "download_success": False,
            "video_info": (
                video_info_extracted if "video_info_extracted" in locals() else {}
            ),
            "info_json_path": info_json_path if "info_json_path" in locals() else None,
            "subtitle_path": subtitle_path if "subtitle_path" in locals() else None,
        }

        log_memory_usage("FINAL_FAILED", logger)
        return result

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR IN AGGRESSIVE ANALYSIS: {e}")
        log_memory_usage("CRITICAL_ERROR", logger)

        return {
            "error": str(e),
            "initial_report": f"Critical error during aggressive analysis of video {video_id}: {str(e)}",
            "claims": [],
            "video_info": (
                video_info_extracted if "video_info_extracted" in locals() else {}
            ),
            "info_json_path": info_json_path if "info_json_path" in locals() else None,
            "subtitle_path": subtitle_path if "subtitle_path" in locals() else None,
        }

    finally:
        # STEP 15: Final cleanup and memory check
        log_memory_usage("ANALYSIS_END", logger)
        monitor_garbage_collection(logger)

        # Force cleanup
        if "video_data" in locals():
            del video_data
        gc.collect()

        print(
            f"==== AGGRESSIVE MULTIMODAL ANALYSIS END [{datetime.now().isoformat()}] ====\n"
        )


def preprocess_json_string(json_str: str, logger: logging.Logger) -> str:
    """Pre-process JSON string to fix common issues before parsing."""
    # Remove any leading/trailing whitespace
    json_str = json_str.strip()

    # Fix common quote issues
    json_str = json_str.replace('"', '"').replace('"', '"')  # Replace curly quotes
    json_str = json_str.replace(""", "'").replace(""", "'")  # Replace curly apostrophes

    # Fix common escape issues
    # json_str = json_str.replace('\\"', '"')  # REMOVED: Breaks valid JSON escapes
    json_str = json_str.replace("\\n", " ")  # Replace newlines with spaces
    json_str = json_str.replace("\\t", " ")  # Replace tabs with spaces

    # Remove any non-printable characters
    json_str = "".join(
        char for char in json_str if char.isprintable() or char in "\n\t\r"
    )

    logger.info(f"🔧 Pre-processed JSON string: {len(json_str)} characters")
    return json_str


def fix_common_json_issues(json_str: str) -> str:
    """Fix common JSON syntax issues."""
    import re

    # Fix trailing commas before closing brackets/braces
    json_str = re.sub(r",(\s*[}\]])", r"\1", json_str)

    # Fix missing quotes around keys (but avoid already quoted keys)
    json_str = re.sub(r"(\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*):", r'\1"\2"\3:', json_str)

    # Fix single quotes to double quotes
    json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)

    # Fix common escape sequence issues
    # json_str = json_str.replace('\\"', '"')  # REMOVED: Breaks valid JSON escapes
    json_str = json_str.replace("\\\\", "\\")  # Fix double backslashes

    # Fix newlines and tabs in strings
    json_str = re.sub(r"\\n", " ", json_str)
    json_str = re.sub(r"\\t", " ", json_str)

    # Remove any control characters
    json_str = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", json_str)

    return json_str


def balance_json_brackets(json_str: str) -> str:
    """Balance JSON brackets and braces."""
    # Count brackets and braces
    open_braces = json_str.count("{") - json_str.count("}")
    open_brackets = json_str.count("[") - json_str.count("]")

    # Add missing closing brackets/braces
    if open_brackets > 0:
        json_str += "]" * open_brackets
    if open_braces > 0:
        json_str += "}" * open_braces

    return json_str


def is_valid_json_structure(data: Any) -> bool:
    """Quick validation to check if the parsed data has the expected structure."""
    if not isinstance(data, dict):
        return False

    # Check if it has at least one of the expected fields
    expected_fields = ["claims", "initial_report", "video_analysis_summary"]
    return any(field in data for field in expected_fields)


def validate_and_normalize_json_result(
    result: Dict[str, Any], logger: logging.Logger
) -> Dict[str, Any]:
    """Validate and normalize the parsed JSON result with flexible field ordering."""
    if not isinstance(result, dict):
        logger.warning("⚠️ Result is not a dictionary, creating default structure")
        return {
            "initial_report": "Invalid result structure",
            "claims": [],
            "video_analysis_summary": "Structure validation failed",
        }

    # Ensure required fields exist (flexible about content and ordering)
    if "initial_report" not in result:
        result["initial_report"] = "No initial report provided"
        logger.info("ℹ️ Added missing initial_report field")

    if "claims" not in result:
        result["claims"] = []
        logger.warning("⚠️ No claims field found, creating empty list")
    elif not isinstance(result["claims"], list):
        logger.warning("⚠️ Claims field is not a list, converting to empty list")
        result["claims"] = []

    if "video_analysis_summary" not in result:
        result["video_analysis_summary"] = "No analysis summary provided"
        logger.info("ℹ️ Added missing video_analysis_summary field")

    # Validate and clean each claim with robust error handling
    cleaned_claims = []
    claims_list = result.get("claims", [])

    for i, claim in enumerate(claims_list):
        try:
            if isinstance(claim, dict):
                # Extract fields with multiple possible key names for flexibility
                claim_text = (
                    claim.get("claim_text")
                    or claim.get("claim")
                    or claim.get("text")
                    or f"Claim {i+1}"
                )

                timestamp = claim.get("timestamp") or claim.get("time") or "00:00"

                speaker = (
                    claim.get("speaker")
                    or claim.get("source")
                    or claim.get("who")
                    or "Unknown"
                )

                initial_assessment = (
                    claim.get("initial_assessment")
                    or claim.get("assessment")
                    or claim.get("evaluation")
                    or "No assessment"
                )

                # FIX: Strip field name prefixes that leaked into values (JSON parsing bug)
                field_prefixes = ["claim_text ", "initial_assessment ", "timestamp ", "speaker ", "source_type "]
                claim_text_str = str(claim_text)
                for prefix in field_prefixes:
                    if claim_text_str.lower().startswith(prefix.lower()):
                        claim_text_str = claim_text_str[len(prefix):].strip()
                        logger.warning(f"⚠️ Stripped leaked field name prefix '{prefix}' from claim text")
                        break
                
                # Also strip from initial_assessment if it leaked
                initial_assessment_str = str(initial_assessment)
                for prefix in field_prefixes:
                    if initial_assessment_str.lower().startswith(prefix.lower()):
                        initial_assessment_str = initial_assessment_str[len(prefix):].strip()
                        logger.warning(f"⚠️ Stripped leaked field name prefix '{prefix}' from initial_assessment")
                        break
                
                # Skip claims that are just metadata labels (not real claims)
                meta_labels = ["verifiable speaker credibility claim", "speaker credibility claim", 
                               "no assessment", "pending verification", "claim"]
                if claim_text_str.lower().strip() in meta_labels or len(claim_text_str.strip()) < 15:
                    logger.warning(f"⚠️ Skipping meta-label or too-short claim: '{claim_text_str[:50]}...'")
                    continue

                cleaned_claim = {
                    "claim_text": claim_text_str[:200],  # Enforce 200 char limit
                    "timestamp": str(timestamp),
                    "speaker": str(speaker),
                    "initial_assessment": initial_assessment_str,
                }
                cleaned_claims.append(cleaned_claim)

            else:
                logger.warning(
                    f"⚠️ Claim {i+1} is not a dictionary: {type(claim)}, skipping"
                )

        except Exception as e:
            logger.warning(f"⚠️ Error processing claim {i+1}: {e}, skipping")
            continue

    result["claims"] = cleaned_claims
    logger.info(f"✅ Validated and normalized {len(cleaned_claims)} claims")
    return result


def extract_json_fallback(json_str: str, logger: logging.Logger) -> Dict[str, Any]:
    """Advanced fallback extraction with multiple regex strategies."""
    logger.info("🔧 FALLBACK: Attempting comprehensive regex-based extraction")

    result = {
        "initial_report": "",
        "claims": [],
        "video_analysis_summary": "",
        "extraction_method": "regex_fallback",
    }

    try:
        import re

        # Strategy 1: Extract initial_report with multiple patterns
        report_patterns = [
            r'"initial_report"\s*:\s*"((?:[^"\\]|\\.)*)"',  # Handles escaped quotes
            r'"initial_report"\s*:\s*"([^"]*)"',  # Simple pattern
            r'initial_report["\s:]*([^,}\]]+)',  # Fallback without quotes
        ]

        for pattern in report_patterns:
            report_match = re.search(pattern, json_str, re.DOTALL | re.IGNORECASE)
            if report_match:
                result["initial_report"] = (
                    report_match.group(1).replace('\\"', '"').strip()
                )
                logger.info("🔧 Found initial_report")
                break

        # Strategy 2: Extract video_analysis_summary
        summary_patterns = [
            r'"video_analysis_summary"\s*:\s*"((?:[^"\\]|\\.)*)"',
            r'"video_analysis_summary"\s*:\s*"([^"]*)"',
        ]

        for pattern in summary_patterns:
            summary_match = re.search(pattern, json_str, re.DOTALL | re.IGNORECASE)
            if summary_match:
                result["video_analysis_summary"] = (
                    summary_match.group(1).replace('\\"', '"').strip()
                )
                logger.info("🔧 Found video_analysis_summary")
                break

        # Strategy 3: Extract claims with multiple approaches
        claims_patterns = [
            r'"claims"\s*:\s*\[(.*?)\]',  # Standard array
            r'claims["\s:]*\[(.*?)\]',  # Without quotes
            r'"claims"[^[]*\[(.*?)\]',  # With noise between
        ]

        claims_text = ""
        for pattern in claims_patterns:
            claims_match = re.search(pattern, json_str, re.DOTALL | re.IGNORECASE)
            if claims_match:
                claims_text = claims_match.group(1)
                logger.info("🔧 Found claims array")
                break

        if claims_text:
            # Extract individual claim objects
            claim_object_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
            claim_objects = re.findall(claim_object_pattern, claims_text)

            logger.info(f"🔧 Found {len(claim_objects)} potential claim objects")

            for i, claim_obj in enumerate(claim_objects):
                claim = {}

                # Extract fields with multiple patterns each
                field_patterns = {
                    "claim_text": [
                        r'"claim_text"\s*:\s*"((?:[^"\\]|\\.)*)"',
                        r'"claim_text"\s*:\s*"([^"]*)"',
                        r'claim_text["\s:]*([^,}\]]+)',
                    ],
                    "timestamp": [
                        r'"timestamp"\s*:\s*"([^"]*)"',
                        r'timestamp["\s:]*([^,}\]]+)',
                    ],
                    "speaker": [
                        r'"speaker"\s*:\s*"([^"]*)"',
                        r'speaker["\s:]*([^,}\]]+)',
                    ],
                    "initial_assessment": [
                        r'"initial_assessment"\s*:\s*"((?:[^"\\]|\\.)*)"',
                        r'"initial_assessment"\s*:\s*"([^"]*)"',
                        r'initial_assessment["\s:]*([^,}\]]+)',
                    ],
                }

                for field, patterns in field_patterns.items():
                    for pattern in patterns:
                        field_match = re.search(
                            pattern, claim_obj, re.DOTALL | re.IGNORECASE
                        )
                        if field_match:
                            value = (
                                field_match.group(1).replace('\\"', '"').strip(" \"'")
                            )
                            if value and len(value) > 2:  # Must have meaningful content
                                claim[field] = value
                                break

                # Only add claim if it has meaningful content
                if claim.get("claim_text") and len(claim.get("claim_text", "")) > 15:
                    # Clean and limit field lengths
                    claim["claim_text"] = claim["claim_text"][:300]
                    claim["timestamp"] = claim.get("timestamp", "Unknown")[:10]
                    claim["speaker"] = claim.get("speaker", "Unknown")[:50]
                    claim["initial_assessment"] = claim.get(
                        "initial_assessment", "No assessment"
                    )[:200]

                    result["claims"].append(claim)
                    logger.info(
                        f"🔧 Extracted claim {i+1}: {claim['claim_text'][:50]}..."
                    )

        # Strategy 4: If no claims found, try line-by-line aggressive extraction
        if not result["claims"]:
            logger.info("🔧 AGGRESSIVE: Trying line-by-line extraction")
            lines = json_str.split("\n")

            potential_claims = []
            for line in lines:
                # Look for lines that might contain claim text
                if any(
                    keyword in line.lower()
                    for keyword in ["claim", "said", "states", "according"]
                ):
                    # Try to extract meaningful text
                    cleaned = re.sub(r'[{},"\[\]:]', "", line).strip()
                    if len(cleaned) > 20 and not cleaned.startswith(
                        ("initial_report", "video_analysis")
                    ):
                        potential_claims.append(
                            {
                                "claim_text": cleaned[:200],
                                "timestamp": "Unknown",
                                "speaker": "Unknown",
                                "initial_assessment": "Extracted from malformed response",
                            }
                        )

                        if len(potential_claims) >= 30:  # Increased from 5 to 30 for better coverage
                            break

            result["claims"] = potential_claims
            logger.info(
                f"🔧 AGGRESSIVE extraction found {len(potential_claims)} potential claims"
            )

        # Ensure we have minimal required fields
        if not result["initial_report"]:
            result["initial_report"] = (
                "Initial report could not be extracted from malformed response"
            )

        if not result["video_analysis_summary"]:
            result["video_analysis_summary"] = (
                f"Extracted {len(result['claims'])} claims using fallback methods"
            )

        logger.info(
            f"🔧 COMPREHENSIVE FALLBACK extracted {len(result['claims'])} claims"
        )
        return result

    except Exception as e:
        logger.error(f"❌ COMPREHENSIVE FALLBACK extraction failed: {e}")
        return {
            "initial_report": "All extraction methods failed",
            "claims": [],
            "video_analysis_summary": "Critical parsing failure - manual review required",
        }


def fuse_segmented_json_responses(
    texts: List[str], video_id: str, logger: logging.Logger
) -> Dict[str, Any]:
    """Parse individual JSON responses from segments and fuse them into a complete structure."""
    import json
    from typing import List, Dict, Any

    logger.info(f"🔄 Fusing {len(texts)} segmented responses for video {video_id}")

    fused_claims = []
    fused_reports = []
    fused_summaries = []

    MAX_CLAIMS_PER_SEGMENT = 50  # FIX: Prevent LLM repetition bug from creating 215+ claims
    
    for i, text in enumerate(texts):
        if not text.strip():
            continue

        try:
            # Parse individual segment response
            segment_result = parse_llm_response(text, f"{video_id}_segment_{i}", logger)

            if segment_result and isinstance(segment_result, dict):
                # Extract claims
                claims = segment_result.get("claims", [])
                if isinstance(claims, list):
                    # FIX: Detect LLM repetition bug - if segment has too many claims, likely a loop
                    if len(claims) > MAX_CLAIMS_PER_SEGMENT:
                        logger.warning(
                            f"⚠️ Segment {i} has {len(claims)} claims (max={MAX_CLAIMS_PER_SEGMENT}), "
                            f"likely LLM repetition bug. Truncating and deduplicating."
                        )
                        # Deduplicate within segment first
                        segment_seen = set()
                        segment_unique = []
                        for c in claims:
                            if isinstance(c, dict):
                                ct = c.get("claim_text", "").strip().lower()
                                if ct and ct not in segment_seen:
                                    segment_seen.add(ct)
                                    segment_unique.append(c)
                        claims = segment_unique[:MAX_CLAIMS_PER_SEGMENT]
                        logger.info(f"📋 Segment {i}: reduced to {len(claims)} unique claims after dedup")
                    
                    # FIX: Detect consecutive identical claims (LLM loop pattern)
                    if len(claims) >= 3:
                        first_claim_text = claims[0].get("claim_text", "") if isinstance(claims[0], dict) else ""
                        consecutive_same = sum(
                            1 for c in claims[:10] 
                            if isinstance(c, dict) and c.get("claim_text", "") == first_claim_text
                        )
                        if consecutive_same >= 3:
                            logger.warning(
                                f"⚠️ Segment {i}: Detected {consecutive_same} consecutive identical claims, "
                                f"LLM repetition bug. Keeping only first occurrence."
                            )
                            # Keep only first instance
                            claims = [claims[0]]
                    
                    fused_claims.extend(claims)
                    logger.info(f"📋 Segment {i}: extracted {len(claims)} claims")

                # Collect reports and summaries
                if segment_result.get("initial_report"):
                    fused_reports.append(segment_result["initial_report"])
                if segment_result.get("video_analysis_summary"):
                    fused_summaries.append(segment_result["video_analysis_summary"])

        except Exception as e:
            logger.warning(f"⚠️ Failed to parse segment {i}: {e}")
            continue

    # FIX: Two-phase deduplication - exact match first (O(1)), then similarity
    # Phase 1: Exact match deduplication (fast, catches most duplicates)
    exact_seen = set()
    phase1_claims = []
    exact_duplicates = 0
    
    for claim in fused_claims:
        if isinstance(claim, dict):
            claim_text = claim.get("claim_text", "").strip().lower()
            if claim_text and claim_text not in exact_seen:
                exact_seen.add(claim_text)
                phase1_claims.append(claim)
            else:
                exact_duplicates += 1
    
    if exact_duplicates > 0:
        logger.info(f"🔄 Phase 1 dedup: Removed {exact_duplicates} exact duplicate claims")
    
    # Phase 2: Similarity-based deduplication (catches near-duplicates)
    unique_claims = []
    seen_texts = set()
    similarity_duplicates = 0

    for claim in phase1_claims:
        if isinstance(claim, dict):
            claim_text = claim.get("claim_text", "").strip().lower()
            # Simple deduplication - claims with >80% similarity are considered duplicates
            is_duplicate = False
            for seen in seen_texts:
                if claim_text and seen and len(claim_text) > 10 and len(seen) > 10:
                    # Simple overlap check
                    shorter = min(claim_text, seen, key=len)
                    longer = max(claim_text, seen, key=len)
                    if (
                        shorter in longer
                        or len(set(claim_text.split()) & set(seen.split()))
                        > len(shorter.split()) * 0.8
                    ):
                        is_duplicate = True
                        similarity_duplicates += 1
                        break

            if not is_duplicate:
                unique_claims.append(claim)
                seen_texts.add(claim_text)
    
    if similarity_duplicates > 0:
        logger.info(f"🔄 Phase 2 dedup: Removed {similarity_duplicates} similar duplicate claims")

    total_removed = exact_duplicates + similarity_duplicates
    logger.info(
        f"✅ Fused result: {len(fused_claims)} total → {len(unique_claims)} unique claims "
        f"(removed {total_removed} duplicates)"
    )

    # Create fused result
    return {
        "initial_report": (
            " | ".join(fused_reports)
            if fused_reports
            else f"Segmented analysis of video {video_id}"
        ),
        "claims": unique_claims,
        "video_analysis_summary": (
            " | ".join(fused_summaries)
            if fused_summaries
            else f"Multimodal segmented analysis complete with {len(unique_claims)} claims extracted"
        ),
    }


def parse_llm_response(
    response_content: str, video_id: str, logger: logging.Logger
) -> Dict[str, Any]:
    """Parse LLM response with hardened JSON extraction and multiple fallback strategies."""
    try:
        import re
        import json as json_lib

        # Log response info for debugging
        logger.info(f"📝 Response length: {len(response_content)} characters")
        logger.info(f"📝 Response preview: {response_content[:1000]}...")
        logger.info(f"🔍 SHERLOCK DEBUG: Full response content: {response_content}")

        # Strategy 1: Try to extract JSON from markdown code blocks
        json_str = None
        json_match = re.search(r"```json\s*\n(.*?)\n```", response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            logger.info("📝 Extracted JSON from markdown code block")

        # Strategy 2: Try to extract JSON from text code blocks
        if not json_str:
            json_match = re.search(r"```\s*\n(.*?)\n```", response_content, re.DOTALL)
            if json_match:
                potential_json = json_match.group(1).strip()
                if potential_json.startswith("{") and potential_json.endswith("}"):
                    json_str = potential_json
                    logger.info("📝 Extracted JSON from text code block")

        # Strategy 3: Try to find JSON object in the text
        if not json_str:
            json_match = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_content, re.DOTALL
            )
            if json_match:
                json_str = json_match.group(0)
                logger.info("📝 Extracted JSON using regex pattern")

        # Strategy 4: Use entire response if it looks like JSON
        if not json_str:
            if response_content.strip().startswith(
                "{"
            ) and response_content.strip().endswith("}"):
                json_str = response_content.strip()
                logger.info("📝 Using entire response as JSON")

        if not json_str:
            logger.error("❌ No JSON found in response")
            return {
                "initial_report": "Failed to extract JSON from response",
                "claims": [],
                "video_analysis_summary": "JSON extraction failed",
            }

        logger.info(f"📝 JSON string length: {len(json_str)} characters")

        # Pre-process JSON string for common issues
        json_str = preprocess_json_string(json_str, logger)

        # Strategy 5: Progressive JSON parsing with multiple attempts
        result = None
        parsing_attempts = [
            ("Direct parsing", lambda: json_lib.loads(json_str)),
            (
                "Pre-processed",
                lambda: json_lib.loads(preprocess_json_string(json_str, logger)),
            ),
            (
                "Unicode cleaned",
                lambda: json_lib.loads(
                    json_str.encode("ascii", errors="ignore").decode("ascii")
                ),
            ),
            ("Quote fixed", lambda: json_lib.loads(fix_common_json_issues(json_str))),
            (
                "Bracket balanced",
                lambda: json_lib.loads(balance_json_brackets(json_str)),
            ),
            ("Strict mode off", lambda: json_lib.loads(json_str, strict=False)),
            ("Fallback extraction", lambda: extract_json_fallback(json_str, logger)),
        ]

        for attempt_name, parse_func in parsing_attempts:
            try:
                result = parse_func()
                # Validate the structure before accepting it
                if is_valid_json_structure(result):
                    logger.info(f"✅ JSON parsing succeeded with {attempt_name}")
                    break
                else:
                    logger.warning(f"⚠️ {attempt_name} produced invalid structure")
                    result = None
                    continue
            except Exception as e:
                logger.warning(f"⚠️ {attempt_name} failed: {str(e)[:100]}...")
                continue

        if result is None:
            logger.error("❌ All JSON parsing strategies failed")
            logger.error(f"🔍 SHERLOCK DEBUG: JSON string that failed: {json_str}")
            # INSTEAD OF FALLING BACK TO BOGUS CLAIMS, FAIL CLEARLY
            return {
                "error": "CRITICAL: JSON parsing failed - cancelling verification to prevent bogus results",
                "initial_report": f"JSON parsing failed for video {video_id}. This indicates a fundamental issue with the multimodal response format.",
                "claims": [],
                "video_analysis_summary": "CANCELLED: Critical parsing failure - manual review required",
            }

        # Validate and normalize result structure
        result = validate_and_normalize_json_result(result, logger)

        if isinstance(result, dict) and "claims" in result:
            logger.info(
                f"✅ SUCCESSFUL PARSING: {len(result.get('claims', []))} claims extracted"
            )
            return result
        else:
            logger.warning("⚠️ Invalid JSON structure in response")
            return {
                "initial_report": response_content[:2000],
                "claims": [],
                "video_analysis_summary": "Invalid JSON structure",
            }

    except Exception as e:
        logger.error(f"❌ JSON PARSING FAILED: {e}")
        logger.error(f"❌ Error at line {e.lineno}, column {e.colno}: {e.msg}")

        # Log problematic JSON section for debugging
        if hasattr(e, "pos") and e.pos:
            start_pos = max(0, e.pos - 100)
            end_pos = min(len(json_str), e.pos + 100)
            problem_section = json_str[start_pos:end_pos]
            logger.error(f"❌ Problem section: ...{problem_section}...")

        # DON'T EXTRACT BOGUS CLAIMS - FAIL CLEARLY INSTEAD
        logger.error("🔍 SHERLOCK DEBUG: JSON parsing failed in exception handler")
        logger.error(
            f"🔍 SHERLOCK DEBUG: Response content: {response_content[:2000]}..."
        )
        logger.error("❌ CANCELLING VERIFICATION - refusing to generate bogus claims")

        return {
            "error": "CRITICAL: JSON parsing exception - cancelling verification to prevent bogus results",
            "initial_report": f"JSON parsing exception for video {video_id}: {str(e)}",
            "claims": [],
            "video_analysis_summary": "CANCELLED: Exception during JSON parsing - manual review required",
        }


def extract_claims(initial_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract claims from the initial analysis.

    Args:
        initial_analysis (Dict[str, Any]): Initial analysis results

    Returns:
        List[Dict[str, Any]]: List of claims
    """
    logger = logging.getLogger(__name__)

    try:
        # DEBUG: Log the entire initial_analysis structure
        print(f"==== DEBUG CLAIMS EXTRACTION ====")
        print(
            f"Initial analysis keys: {list(initial_analysis.keys()) if initial_analysis else 'None'}"
        )
        print(f"Initial analysis type: {type(initial_analysis)}")
        if initial_analysis:
            for key, value in initial_analysis.items():
                if key == "claims":
                    print(f"Claims found: {value}")
                    print(f"Claims type: {type(value)}")
                    print(
                        f"Claims length: {len(value) if isinstance(value, (list, tuple)) else 'Not a list/tuple'}"
                    )
                elif key == "initial_report":
                    print(f"Initial report length: {len(str(value)) if value else 0}")
                    print(
                        f"Initial report preview: {str(value)[:200] if value else 'None'}..."
                    )
                else:
                    print(
                        f"{key}: {type(value)} - {str(value)[:100] if value else 'None'}..."
                    )
        print(f"==== END DEBUG CLAIMS EXTRACTION ====")

        # Get claims from initial analysis
        claims = initial_analysis.get("claims", [])

        if not claims:
            logger.warning("No claims found in initial analysis")
            print(
                f"DEBUG: No claims found. Available keys: {list(initial_analysis.keys()) if initial_analysis else 'None'}"
            )
            return []

        # Format claims
        formatted_claims = []
        for i, claim in enumerate(claims, 1):
            # Handle the case where claim is a string
            if isinstance(claim, str):
                formatted_claim = {
                    "claim_id": i,
                    "claim_text": claim,
                    "timestamp": "",
                    "speaker": "Unknown",
                    "initial_assessment": "Unknown",
                    "verification_result": None,
                }
            else:
                # Handle the case where claim is a dictionary
                formatted_claim = {
                    "claim_id": i,
                    "claim_text": claim.get("claim_text", ""),
                    "timestamp": claim.get("timestamp", ""),
                    "speaker": claim.get("speaker", "Unknown"),
                    "initial_assessment": claim.get("initial_assessment", "Unknown"),
                    "verification_result": None,
                }

            # Only add claims that have actual content
            if formatted_claim["claim_text"].strip():
                formatted_claims.append(formatted_claim)

        logger.info(f"Extracted {len(formatted_claims)} claims from initial analysis")

        # Apply CRAAP analysis filtering to keep only top 5-15 claims (if needed)
        filtered_claims = apply_craap_analysis_filtering(
            formatted_claims, initial_analysis
        )
        logger.info(
            f"After quality filtering: {len(filtered_claims)} high-quality claims selected"
        )

        return filtered_claims

    except Exception as e:
        logger.error(f"Error extracting claims: {e}")
        return []


def apply_craap_analysis_filtering(
    claims: List[Dict[str, Any]],
    initial_analysis: Dict[str, Any],
    min_claims: int = 15,
    max_claims: int = 40,
) -> List[Dict[str, Any]]:
    """
    Apply CRAAP (Currency, Relevance, Authority, Accuracy, Purpose) analysis to filter claims.

    CRAAP Criteria:
    - Currency: How recent/current is the information?
    - Relevance: How relevant is the claim to the main topic?
    - Authority: Who is making the claim (credibility)?
    - Accuracy: How accurate/verifiable is the claim?
    - Purpose: What's the purpose of the claim?

    Args:
        claims (List[Dict[str, Any]]): List of extracted claims
        initial_analysis (Dict[str, Any]): Initial analysis for context
        min_claims (int): Minimum number of claims to keep
        max_claims (int): Maximum number of claims to keep

    Returns:
        List[Dict[str, Any]]: Filtered claims with highest CRAAP scores
    """
    logger = logging.getLogger(__name__)

    if len(claims) <= max_claims:
        logger.info(
            f"Number of claims ({len(claims)}) already within target range, no CRAAP filtering needed"
        )
        return claims

    # Get video context for relevance scoring
    video_title = initial_analysis.get("video_info", {}).get("title", "")
    video_description = initial_analysis.get("video_info", {}).get("description", "")

    scored_claims = []

    for claim in claims:
        claim_text = claim.get("claim_text", "")
        speaker = claim.get("speaker", "Unknown")
        timestamp = claim.get("timestamp", "")

        craap_score = calculate_craap_score(
            claim_text=claim_text,
            speaker=speaker,
            timestamp=timestamp,
            video_title=video_title,
            video_description=video_description,
        )

        # Add CRAAP score to claim for tracking
        enhanced_claim = {**claim, "craap_score": craap_score}
        scored_claims.append(enhanced_claim)

        logger.debug(f"CRAAP Score {craap_score:.2f}: {claim_text[:60]}...")

    # Sort by CRAAP score (highest first)
    scored_claims.sort(key=lambda x: x["craap_score"], reverse=True)

    # Keep top claims within the range
    num_to_keep = min(max_claims, max(min_claims, len(scored_claims)))
    filtered_claims = scored_claims[:num_to_keep]

    logger.info(f"🎯 CRAAP Analysis Results:")
    logger.info(f"   📊 Total claims analyzed: {len(claims)}")
    logger.info(f"   🏆 Top claims selected: {num_to_keep}")
    logger.info(
        f"   📈 Score range: {filtered_claims[-1]['craap_score']:.2f} - {filtered_claims[0]['craap_score']:.2f}"
    )

    # Remove craap_score from final output (keep internal)
    final_claims = []
    for claim in filtered_claims:
        clean_claim = {k: v for k, v in claim.items() if k != "craap_score"}
        final_claims.append(clean_claim)

    return final_claims


def calculate_craap_score(
    claim_text: str,
    speaker: str,
    timestamp: str,
    video_title: str,
    video_description: str,
) -> float:
    """
    Calculate CRAAP score for a single claim.

    Scoring breakdown (0-10 scale):
    - Currency (0-2): Recency and timeliness
    - Relevance (0-3): Relevance to main topic
    - Authority (0-2): Speaker credibility
    - Accuracy (0-2): Verifiability and specificity
    - Purpose (0-1): Clear informational purpose

    Returns:
        float: CRAAP score (0-10)
    """
    score = 0.0

    # 1. CURRENCY (0-2 points) - Temporal relevance
    currency_score = 0.0
    if timestamp and timestamp != "":
        currency_score += 1.0  # Has timestamp

    # Check for time-sensitive keywords
    time_keywords = [
        "today",
        "yesterday",
        "recently",
        "last week",
        "this month",
        "current",
        "latest",
        "new",
    ]
    if any(keyword in claim_text.lower() for keyword in time_keywords):
        currency_score += 0.5

    # Check for specific dates or numbers that suggest currency
    import re

    if re.search(r"\b(20\d{2}|19\d{2})\b", claim_text):  # Contains year
        currency_score += 0.5

    score += min(currency_score, 2.0)

    # 2. RELEVANCE (0-3 points) - Relevance to main video topic
    relevance_score = 0.0

    # Extract key terms from video title and description
    video_context = f"{video_title} {video_description}".lower()
    claim_lower = claim_text.lower()

    # Count overlapping significant words (3+ characters)
    video_words = set(word for word in video_context.split() if len(word) >= 3)
    claim_words = set(word for word in claim_lower.split() if len(word) >= 3)
    overlap = len(video_words.intersection(claim_words))

    if overlap >= 3:
        relevance_score += 2.0  # High relevance
    elif overlap >= 1:
        relevance_score += 1.0  # Moderate relevance

    # Boost for specific product/subject mentions
    if video_title:
        # Extract potential product names (capitalized sequences)
        import re

        product_matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", video_title)
        for product in product_matches:
            if product.lower() in claim_lower:
                relevance_score += 1.0
                break

    score += min(relevance_score, 3.0)

    # 3. AUTHORITY (0-2 points) - Speaker credibility
    authority_score = 0.0

    # Known authority indicators
    authority_titles = [
        "dr",
        "doctor",
        "phd",
        "professor",
        "researcher",
        "scientist",
        "expert",
        "specialist",
    ]
    if any(title in speaker.lower() for title in authority_titles):
        authority_score += 1.5

    # Institutional indicators
    institutions = [
        "university",
        "hospital",
        "clinic",
        "institute",
        "foundation",
        "center",
    ]
    if any(inst in speaker.lower() for inst in institutions):
        authority_score += 1.0

    # SPEAKER CREDIBILITY CLAIMS BOOST - These are crucial for truthfulness
    credibility_keywords = [
        "worked at",
        "graduated from",
        "studied at",
        "educated at",
        "affiliated with",
        "degree from",
        "trained at",
        "certified by",
        "licensed by",
        "board certified",
        "published in",
        "authored",
        "won award",
        "recognized by",
        "featured in",
        "time magazine",
        "forbes",
        "years of experience",
        "founded",
        "director of",
    ]
    if any(term in claim_lower for term in credibility_keywords):
        authority_score += 1.5  # Significant boost for speaker credibility claims

    # Specific professional indicators in claim
    professional_terms = [
        "study",
        "research",
        "clinical trial",
        "published",
        "peer reviewed",
        "journal",
    ]
    if any(term in claim_lower for term in professional_terms):
        authority_score += 0.5

    score += min(authority_score, 2.0)

    # 4. ACCURACY (0-2 points) - Verifiability and specificity
    accuracy_score = 0.0

    # Specific numbers and measurements indicate verifiability
    import re

    if re.search(
        r"\b\d+(?:\.\d+)?(?:%|percent|pounds|kg|lbs|days|weeks|months)\b", claim_text
    ):
        accuracy_score += 1.0

    # Scientific/medical terminology suggests accuracy
    scientific_terms = [
        "clinical",
        "trial",
        "study",
        "research",
        "analysis",
        "test",
        "experiment",
        "data",
    ]
    if any(term in claim_lower for term in scientific_terms):
        accuracy_score += 0.5

    # Specific claims are more verifiable than vague ones
    specific_indicators = [
        "exactly",
        "precisely",
        "specifically",
        "measured",
        "documented",
        "proven",
        "demonstrated",
    ]
    if any(indicator in claim_lower for indicator in specific_indicators):
        accuracy_score += 0.5

    # Avoid vague claims
    vague_terms = [
        "amazing",
        "incredible",
        "miracle",
        "magic",
        "revolutionary",
        "breakthrough",
        "secret",
    ]
    if any(term in claim_lower for term in vague_terms):
        accuracy_score -= 0.5

    score += min(max(accuracy_score, 0.0), 2.0)

    # 5. PURPOSE (0-1 point) - Clear informational purpose
    purpose_score = 0.0

    # Factual statement indicators
    factual_indicators = [
        "found",
        "showed",
        "demonstrated",
        "revealed",
        "indicates",
        "suggests",
        "according to",
    ]
    if any(indicator in claim_lower for indicator in factual_indicators):
        purpose_score += 0.5

    # Clear informational content
    if len(claim_text.split()) >= 8:  # Substantial content
        purpose_score += 0.5

    score += min(purpose_score, 1.0)

    # Ensure score is within bounds
    return min(max(score, 0.0), 10.0)


def build_initial_analysis_workflow() -> StateGraph:
    """
    Build the initial analysis workflow.

    Returns:
        StateGraph: The workflow graph
    """
    # Create the workflow
    workflow = StateGraph(InitialAnalysisState)

    # Define the nodes - now we only need analyze_video since it does everything
    workflow.add_node("analyze_video", analyze_video_node)

    # Define the edges - direct path from analyze_video to END
    workflow.set_entry_point("analyze_video")
    workflow.add_edge("analyze_video", END)

    return workflow


def analyze_video_node(state: InitialAnalysisState) -> InitialAnalysisState:
    """
    Node function to analyze the video.

    Args:
        state (InitialAnalysisState): Current state

    Returns:
        InitialAnalysisState: Updated state
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Analyzing video: {state.video_id}")

    # Check if we have either a video path or video URL for fallback
    if not state.video_path and not state.video_url:
        logger.error("Missing both video path and video URL - cannot proceed")
        return state

    if not state.video_path:
        logger.info(
            f"No video path available, will use YouTube URL fallback: {state.video_url}"
        )
    else:
        logger.info(f"Using downloaded video file: {state.video_path}")

    # Analyze video content
    analysis_result = analyze_video_content(state)

    # Extract the initial report text and claims from the analysis result
    if not isinstance(analysis_result, dict):
        analysis_result = {"initial_report": "", "claims": []}
    initial_report_text = analysis_result.get("initial_report", "")
    raw_claims = analysis_result.get("claims", [])

    # Format the claims properly
    formatted_claims = extract_claims(analysis_result)

    logger.info(f"Analysis completed. Found {len(formatted_claims)} claims")

    # Update state with both the initial report and the formatted claims
    return state.model_copy(
        update={
            "initial_report": analysis_result,  # Store the full dictionary
            "initial_report_text": initial_report_text,  # Store the text separately
            "claims": formatted_claims,  # Store the properly formatted claims
        }
    )


def extract_claims_node(state: InitialAnalysisState) -> InitialAnalysisState:
    """
    Node function to extract claims from the initial analysis.

    Args:
        state (InitialAnalysisState): Current state

    Returns:
        InitialAnalysisState: Updated state
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting claims for video: {state.video_id}")

    if not state.initial_report:
        logger.error("Missing initial report")
        return state

    # Extract claims from the analysis result
    claims = extract_claims(state.initial_report)

    # Update state
    return state.model_copy(update={"claims": claims})


import subprocess
import os
import tempfile


def trim_video_for_analysis(video_path: str, max_duration: int = 3600) -> str:
    """
    Trim video to extract first hour for analysis.

    Args:
        video_path: Path to the original video file
        max_duration: Maximum duration in seconds (default 3600 = 60 minutes)
                     Takes the first hour of content to avoid strange results
                     from middle extraction which may miss important context

    Returns:
        Path to the trimmed video file
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get video duration using ffprobe
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_entries",
            "format=duration",
            video_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.warning(
                f"Could not get video duration, using original file: {video_path}"
            )
            return video_path

        import json

        duration_info = json.loads(result.stdout)
        total_duration = float(duration_info["format"]["duration"])

        logger.info(f"Video duration: {total_duration:.2f} seconds")

        # If video is shorter than max_duration, return original
        if total_duration <= max_duration:
            logger.info(
                f"Video is short enough ({total_duration:.2f}s ≤ {max_duration}s), using original"
            )
            return video_path

        # Take first portion instead of middle
        start_time = 0

        # Create trimmed filename
        video_file_path = os.path.abspath(video_path)
        video_dir = os.path.dirname(os.path.abspath(video_path))
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        trimmed_path = os.path.abspath(
            os.path.join(video_dir, f"{video_name}_trimmed.mp4")
        )

        # Skip if trimmed file already exists
        if os.path.exists(trimmed_path):
            logger.info(f"Using existing trimmed video: {trimmed_path}")
            return trimmed_path

        # Trim video using ffmpeg
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-ss",
            str(start_time),
            "-t",
            str(max_duration),
            "-c",
            "copy",  # Copy without re-encoding for speed
            "-avoid_negative_ts",
            "make_zero",
            "-y",  # Overwrite output file
            trimmed_path,
        ]

        logger.info(
            f"Trimming video to first {max_duration}s ({max_duration/60:.1f} min): {start_time:.2f}s to {start_time + max_duration:.2f}s"
        )
        logger.info(f"Taking first hour to avoid context issues from middle extraction")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(trimmed_path):
            file_size_mb = os.path.getsize(trimmed_path) / (1024 * 1024)
            logger.info(
                f"✅ Video trimmed successfully: {trimmed_path} ({file_size_mb:.1f} MB)"
            )
            return trimmed_path
        else:
            logger.warning(f"Video trimming failed, using original: {result.stderr}")
            return video_path

    except Exception as e:
        logger.warning(f"Error trimming video, using original: {e}")
        return video_path


async def run_initial_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run initial video analysis using multimodal approach, preferring local .mp4 file."""
    import logging
    import os
    import base64

    logger = logging.getLogger(__name__)
    logger.info(f"🎬 Starting MULTIMODAL analysis for video: {state.get('video_url')}")

    try:
        video_url = state["video_url"]
        video_id = state["video_id"]
        out_dir_path = state["out_dir_path"]

        # ===== ALWAYS EXTRACT METADATA FIRST =====
        logger.info("📋 EXTRACTING RELIABLE METADATA AND SUBTITLES")
        print("📋 Extracting video metadata and subtitles...")

        # Extract metadata FIRST - this always runs regardless of analysis path
        metadata_result = extract_video_metadata_reliable(
            video_url, out_dir_path, logger
        )

        video_info_extracted = {}
        if metadata_result["success"]:
            logger.info(
                f"✅ METADATA EXTRACTED: {metadata_result['video_info'].get('title', 'Unknown')}"
            )
            print(
                f"✅ Video metadata extracted: {metadata_result['video_info'].get('title', 'Unknown')}"
            )

            # Store metadata info for report generation
            video_info_extracted = metadata_result["video_info"]
            info_json_path = metadata_result["info_json_path"]
            subtitle_path = metadata_result["subtitle_path"]

            logger.info(f"📄 Info JSON: {info_json_path}")
            if subtitle_path:
                logger.info(f"📝 Subtitles: {subtitle_path}")
        else:
            logger.warning(
                f"⚠️ METADATA EXTRACTION FAILED: {metadata_result.get('error', 'Unknown error')}"
            )
            video_info_extracted = {}
            info_json_path = None
            subtitle_path = None

        # ===== CHECK FOR DOWNLOADED .MP4 FILE FIRST =====
        # Check for downloaded .mp4 file from sherlock analysis or previous download
        possible_video_paths = [
            os.path.join(out_dir_path, "analysis", f"{video_id}.mp4"),
            os.path.join(out_dir_path, f"{video_id}.mp4"),
            f"sherlock_analysis_{video_id}/{video_id}.mp4",
            f"sherlock_analysis_{video_id}/vngn_reports/{video_id}/analysis/{video_id}.mp4",
        ]

        video_file_path = None
        for path in possible_video_paths:
            if os.path.exists(path):
                video_file_path = path
                logger.info(f"✅ Found existing video file: {video_file_path}")
                break

        # ===== USE LOCAL .MP4 FILE IF AVAILABLE =====
        if (
            not USE_VERTEX_YOUTUBE_URL
            and video_file_path
            and os.path.exists(video_file_path)
        ):
            logger.info(
                f"🎬 Using local video file for multimodal analysis: {video_file_path}"
            )

            # Trim video if it's too large for analysis (33 minutes max for Gemini Flash 2.0)
            trimmed_video_path = trim_video_for_analysis(
                video_file_path, max_duration=2000
            )
            if trimmed_video_path != video_file_path:
                logger.info(
                    f"🎬 Using trimmed video for analysis: {trimmed_video_path}"
                )
                video_file_path = trimmed_video_path

            # Use the working local file approach
            from langchain_google_vertexai import ChatVertexAI
            from langchain_core.messages import HumanMessage

            try:
                # 🚀 SHERLOCK: Create Gemini LLM with robust token handling
                def create_llm_with_token_limit(max_tokens: int = 32768):
                    """Create LLM with hardened JSON-specific configuration."""
                    from verityngn.utils.llm_utils import build_langchain_vertex_kwargs

                    return ChatVertexAI(
                        **build_langchain_vertex_kwargs(
                            AGENT_MODEL_NAME,
                            preferred_tokens=max_tokens,
                            temperature=0.1,
                            top_p=0.8,
                        ),
                        top_k=10,
                        verbose=True,
                        streaming=False,
                    )

                # Start with optimal token limit
                llm = create_llm_with_token_limit(32768)

                # Get video info for prompt
                if video_info_extracted:
                    video_info = video_info_extracted
                else:
                    video_info = {
                        "id": video_id,
                        "title": f"Video {video_id}",
                        "description": "",
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg",
                    }

                # Calculate target number of claims based on video duration (3 claims per minute)
                try:
                    # Get video duration from trimmed file or original
                    cmd = [
                        "ffprobe",
                        "-v",
                        "quiet",
                        "-print_format",
                        "json",
                        "-show_entries",
                        "format=duration",
                        video_file_path,
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode == 0:
                        import json

                        duration_info = json.loads(result.stdout)
                        video_duration_seconds = float(
                            duration_info["format"]["duration"]
                        )
                        video_duration_minutes = video_duration_seconds / 60
                        # For first hour analysis, cap at 60 minutes for claim calculation
                        analysis_duration_minutes = min(
                            video_duration_minutes, 60
                        )  # Max 60 min since we analyze first hour
                        target_claims = max(
                            8, min(15, int(analysis_duration_minutes * 1.8))
                        )  # 1.8 claims/min to ensure mix of speaker+content claims, 8-15 range
                        logger.info(
                            f"📊 Video duration: {video_duration_minutes:.1f} minutes, analyzing first {analysis_duration_minutes:.1f} minutes, targeting {target_claims} claims"
                        )
                    else:
                        target_claims = (
                            12  # Fallback (restored from July 20th aggressive analysis)
                        )
                        video_duration_minutes = 4.0  # Assume 4 minutes for fallback
                        logger.warning(
                            "Could not determine video duration, using fallback of 12 aggressive claims"
                        )
                except Exception as e:
                    target_claims = 12  # Fallback
                    video_duration_minutes = 4.0  # Assume 4 minutes for fallback
                    logger.warning(
                        f"Error calculating target claims: {e}, using fallback of 12 claims"
                    )

                # Create AGGRESSIVE multimodal prompt with dynamic claim count (restored from July 20th)

                prompt_text_new = f"""
🎬 AGGRESSIVE VIDEO FRAME ANALYSIS - CLAIMS EXTRACTION MISSION 🎬

CRITICAL INSTRUCTIONS FOR MULTIMODAL VIDEO ANALYSIS:
- Analyze this video with MAXIMUM detail at 1 FRAME PER SECOND sampling rate
- Extract ALL factual claims, statements, assertions from ACTUAL VIDEO CONTENT
- Focus on SPOKEN WORDS, VISUAL TEXT, ON-SCREEN GRAPHICS, and DEMONSTRATIONS
- Ignore background music, decorative elements, or irrelevant visuals
- Extract APPROXIMATELY {target_claims} specific, verifiable claims from the actual video frames and audio (targeting 3 claims per minute)

Video ID: {video_id}
Video URL: {video_url}
Video Title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}
Video Duration: {video_duration_minutes:.1f} minutes (estimated)

🎯 AGGRESSIVE MULTIMODAL REQUIREMENTS:
1. Sample video at 1 frame per second (aggressive temporal resolution)
2. Transcribe ALL spoken content with timestamps
3. Extract text from visual overlays, graphics, slides, captions
4. Identify claims from demonstrations, charts, or visual evidence
5. Note precise timestamps for each claim
6. Distinguish between speaker statements and visual text

🔍 FRAME-BY-FRAME ANALYSIS FOCUS:
- What is being SAID in the audio track?
- What TEXT appears on screen?
- What DEMONSTRATIONS or EVIDENCE is shown?
- What GRAPHICS or CHARTS contain factual information?
- What CLAIMS can be verified from external sources?
- What CREDENTIALS or BACKGROUND is mentioned about speakers?

🎯 MANDATORY CLAIM EXTRACTION MIX:
**REQUIRED SPEAKER CREDIBILITY CLAIMS (minimum 20% of total):**
- Educational background (where they studied, degrees obtained)
- Professional experience (years in field, previous positions)
- Institutional affiliations (hospitals, universities, organizations)
- Awards, recognitions, or honors received
- Publications, research, or books authored
- Professional certifications or licenses
- Leadership roles or founding positions

**CONTENT CLAIMS (remaining 80%):**
- Study results, research findings, statistics
- Product claims, effectiveness statements
- Health outcomes, treatment results
- Scientific discoveries or breakthroughs
- Specific numerical data or percentages

OUTPUT FORMAT: Provide detailed JSON with:
{{
    "initial_report": "Comprehensive analysis of video content and main themes based on frame-by-frame analysis",
    "claims": [
        {{
            "claim_text": "Specific factual claim extracted from video frames/audio",
            "timestamp": "MM:SS or time range where claim appears",
            "speaker": "Identified speaker name or 'Visual Text' or 'On-Screen Graphics'",
            "source_type": "spoken|visual_text|demonstration|graphic|chart",
            "initial_assessment": "Assessment of claim verifiability and factual nature"
        }}
    ],
    "video_analysis_summary": "Summary of video content, themes, and claim extraction process from multimodal analysis"
}}

🚨 EXTRACT CLAIMS FROM ACTUAL VIDEO FRAMES & AUDIO - NOT METADATA OR DESCRIPTIONS! 🚨
"""

                # Create the base prompt text
                prompt_text = (
                    "You are a video verification expert. Analyze this video in detail:\n\n"
                    f"Video ID: {video_id}\n\n"
                    f"Video URL: {video_url}\n\n"
                    f"Video Title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}\n\n"
                    f"Video Duration: {video_duration_minutes:.1f} minutes (estimated)\n\n"
                    f"Video Duration: {video_duration_minutes:.1f} minutes (estimated)\n\n"
                )

                ## Extract and add tags from info.json if available
                # info_json_path = os.path.join(os.path.dirname(state.video_path), f"{state.video_id}.info.json")
                # if os.path.exists(info_json_path):
                #    try:
                #        with open(info_json_path, 'r', encoding='utf-8') as f:
                #            video_info = json_lib.load(f)
                #            if 'tags' in video_info and video_info['tags']:
                #                prompt_text += (
                #                    "The video has the following tags that may indicate topics or claims to verify:\n"
                #                    f"{', '.join(video_info['tags'])}\n\n"
                #                    "Please pay special attention to these topics in your analysis and consider them when identifying claims to verify.\n\n"
                #                )
                #    except Exception as e:
                #        logger.warning(f"Error reading info.json: {e}")

                ## Add VTT transcript to the prompt
                # if state.transcription:
                #    prompt_text += (
                #        "I'm providing the VTT transcript to help with your analysis:\n\n"
                #        f"Transcript:\n{state.transcription}\n\n"
                #    )

                prompt_text += (
                    "Please provide a JSON response with the following structure:\n\n"
                    "{\n"
                    '  "initial_report": "Your detailed analysis of the video content, including visual elements, spoken claims, OCR information, and any other relevant information",\n'
                    '  "claims": [\n'
                    "    {\n"
                    '      "claim_text": "The actual claim statement",\n'
                    '      "timestamp": "MM:SS",\n'
                    '      "speaker": "Name or description of who made the claim",\n'
                    '      "initial_assessment": "Your initial assessment of this claim"\n'
                    "    }\n"
                    "  ],\n"
                    '  "video_analysis_summary": "One sentence summary of analysis process and findings"\n'
                    "}\n\n"
                    "Extract APPROXIMATELY {target_claims} specific, verifiable claims from the actual video frames and audio.\n\n"
                    "Respond with valid JSON only."
                )

                # Read video file for multimodal analysis
                logger.info(f"📖 Reading video file: {video_file_path}")
                with open(video_file_path, "rb") as f:
                    video_data = base64.b64encode(f.read()).decode("utf-8")

                # Prepare content with downloaded video for Vertex AI
                file_message = HumanMessage(
                    content=[
                        {"type": "text", "text": prompt_text},
                        {"type": "media", "data": video_data, "mime_type": "video/mp4"},
                    ]
                )

                logger.info("🎬 STARTING LOCAL VIDEO FILE ANALYSIS")

                # 🚀 SHERLOCK: Simplified, sane retry strategy
                # Attempt #1: use 32k output tokens
                response = None
                primary_tokens = 32768
                llm = create_llm_with_token_limit(primary_tokens)
                try:
                    logger.info(
                        f"🚀 Attempting analysis with {primary_tokens} max tokens (attempt 1/2)..."
                    )
                    start_time = time.time()
                    call_id = log_llm_call(
                        operation="run_initial_analysis_attempt1",
                        prompt=str(file_message.content[0]["text"]),
                        model=AGENT_MODEL_NAME,
                        video_id=video_id
                    )
                    response = await llm.ainvoke([file_message])
                    duration = time.time() - start_time
                    log_llm_response(call_id, response, duration=duration)
                    if not (
                        response and hasattr(response, "content") and response.content
                    ):
                        raise RuntimeError("Empty generation from LLM")
                except Exception as e:
                    error_msg = str(e).lower()
                    transient = any(
                        x in error_msg
                        for x in [
                            "no generations",
                            "stream",
                            "deadline",
                            "temporar",
                            "unavailable",
                            "retry",
                        ]
                    )  # transient/transport
                    logger.warning(
                        f"⚠️ First attempt failed: {e}. Retrying once with same params..."
                    )
                    # Attempt #2: same params with brief backoff (avoid reducing tokens)
                    try:
                        import asyncio

                        await asyncio.sleep(0.5)
                    except Exception:
                        pass
                    try:
                        start_time = time.time()
                        call_id = log_llm_call(
                            operation="run_initial_analysis_attempt2",
                            prompt=str(file_message.content[0]["text"]),
                            model=AGENT_MODEL_NAME,
                            video_id=video_id
                        )
                        response = await llm.ainvoke([file_message])
                        duration = time.time() - start_time
                        log_llm_response(call_id, response, duration=duration)
                        if not (
                            response
                            and hasattr(response, "content")
                            and response.content
                        ):
                            raise RuntimeError("Empty generation from LLM on retry")
                    except Exception as e2:
                        logger.error(f"❌ Second attempt failed: {e2}")
                        raise

                # Normalize response content into a single string
                content_text = ""
                try:
                    raw_content = (
                        response.content
                        if (response and hasattr(response, "content"))
                        else ""
                    )
                    if isinstance(raw_content, (list, tuple)):
                        # Join string parts; extract 'text' from dict parts if present
                        parts = []
                        for part in raw_content:
                            if isinstance(part, str):
                                parts.append(part)
                            elif isinstance(part, dict) and "text" in part:
                                parts.append(str(part.get("text") or ""))
                            else:
                                parts.append(str(part))
                        content_text = "\n".join(parts)
                    else:
                        content_text = (
                            str(raw_content) if raw_content is not None else ""
                        )
                except Exception:
                    content_text = ""

                # Save LLM response for debugging if DEBUG_OUTPUTS is enabled
                if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true":
                    import json
                    from datetime import datetime
                    from pathlib import Path

                    debug_dir = Path(f"./sherlock_analysis_{video_id}/llm_calls")
                    debug_dir.mkdir(parents=True, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_file = debug_dir / f"video_analysis_{timestamp}.json"

                    debug_data = {
                        "timestamp": datetime.now().isoformat(),
                        "video_id": video_id,
                        "llm_model": AGENT_MODEL_NAME,
                        "analysis_type": "local_video_file",
                        "prompt_text": (
                            str(file_message.content[0]["text"])
                            if file_message.content
                            else ""
                        ),
                        "prompt_length": len(
                            str(file_message.content[0]["text"])
                            if file_message.content
                            else ""
                        ),
                        "response_content": content_text,
                        "response_length": len(content_text),
                        "response_type": str(type(response)),
                        "success": bool(content_text),
                    }

                    with open(debug_file, "w") as f:
                        json.dump(debug_data, f, indent=2)
                    logger.info(f"🔍 DEBUG: Saved LLM response to {debug_file}")

                if content_text:
                    logger.info(
                        f"✅ Local file analysis completed: {len(content_text)} characters"
                    )
                    analysis_result = parse_llm_response(content_text, video_id, logger)
                else:
                    logger.warning("⚠️ Empty response from local file analysis")
                    analysis_result = {
                        "error": "Empty response from local file analysis",
                        "initial_report": "Analysis failed",
                        "claims": [],
                    }

            except Exception as e:
                logger.error(f"❌ Local file analysis failed: {e}")
                analysis_result = {
                    "error": f"Local file analysis failed: {str(e)}",
                    "initial_report": f"Failed to analyze video file {video_id}",
                    "claims": [],
                }
        else:
            # ===== FALLBACK TO YOUTUBE URL APPROACH =====
            logger.info(f"🌐 No local video file found, using YouTube URL approach")

            # Use the extracted metadata if available, otherwise get basic info
            if video_info_extracted:
                video_info = video_info_extracted
            else:
                try:
                    video_info = get_video_info(video_url)
                except Exception as e:
                    logger.warning(f"Could not get video info: {e}")
                    video_info = {
                        "id": video_id,
                        "title": f"Video {video_id}",
                        "description": "",
                        "thumbnail": f"https://img.youtube.com/vi/{video_id}/0.jpg",
                    }

            # Use YouTube URL fallback (with corrected format)
            try:
                from verityngn.config.settings import USE_VERTEX_SEGMENTED_YOUTUBE
            except Exception:
                USE_VERTEX_SEGMENTED_YOUTUBE = True
            if USE_VERTEX_SEGMENTED_YOUTUBE:
                analysis_result = await extract_claims_with_gemini_multimodal_youtube_url_segmented_vertex(
                    video_url, video_id, video_info
                )
            else:
                analysis_result = (
                    await extract_claims_with_gemini_multimodal_youtube_url(
                        video_url, video_id, video_info
                    )
                )

        # ===== PROCESS RESULTS =====
        if not isinstance(analysis_result, dict) or analysis_result.get("error"):
            logger.error(f"❌ Multimodal analysis failed: {analysis_result['error']}")
            raise ValueError(f"Multimodal analysis failed: {analysis_result['error']}")

        # Extract claims from analysis
        claims = analysis_result.get("claims", [])
        initial_report = analysis_result.get("initial_report", "")

        logger.info(f"✅ Multimodal analysis completed: {len(claims)} claims extracted")

        # CRITICAL: Validate that claims were actually extracted
        if not claims or len(claims) == 0:
            logger.error(
                "❌ MULTIMODAL_ANALYSIS_FAILED: No claims extracted from video analysis"
            )
            logger.error(
                "❌ This is a critical failure - the multimodal LLM call did not produce any claims"
            )
            logger.error(
                "❌ The program must terminate as there is no reasonable fallback without claims"
            )
            raise Exception(
                "MULTIMODAL_ANALYSIS_FAILED: No claims extracted from video analysis. This is a critical failure that requires termination."
            )

        # Create media embed with extracted or fallback info
        if video_info_extracted:
            video_info = video_info_extracted
        else:
            video_info = {}

        media_embed = {
            "title": video_info.get("title", ""),
            "video_id": video_id,
            "description": video_info.get("description", ""),
            "thumbnail_url": video_info.get("thumbnail", ""),
            "video_url": video_url,
        }

        # Return updated state as simple dict with extracted metadata
        return {
            **state,
            "video_path": None,  # No downloaded file
            "transcription": None,  # Multimodal analysis doesn't need separate transcription
            "video_info": video_info,  # Use extracted metadata
            "media_embed": media_embed,  # Use enhanced media embed
            "claims": claims,
            "initial_report": analysis_result,
            "current_claim_index": 0,
            "metadata_extraction_success": metadata_result["success"],
            "info_json_path": info_json_path if "info_json_path" in locals() else None,
            "subtitle_path": subtitle_path if "subtitle_path" in locals() else None,
        }

    except Exception as e:
        logger.error(f"❌ Multimodal analysis failed for {state.get('video_id')}: {e}")
        raise


async def run_prepare_claims(state: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare claims for verification."""
    import logging

    logger = logging.getLogger(__name__)

    claims = state.get("claims", [])
    logger.info(f"📋 Preparing {len(claims)} claims for verification")

    # CRAAP-inspired diversification: ensure we keep coverage across categories (speaker credibility, medical/science, product efficacy, mechanism, safety)
    categories = {
        "speaker_credibility": [],
        "medical_science": [],
        "product_efficacy": [],
        "mechanism": [],
        "safety": [],
        "other": [],
    }

    def classify_claim(text: str) -> str:
        t = (text or "").lower()
        if any(
            k in t
            for k in [
                "dr.",
                "doctor",
                "md",
                "phd",
                "professor",
                "endocrinologist",
                "credentials",
                "johns hopkins",
                "harvard",
            ]
        ):
            return "speaker_credibility"
        if any(
            k in t
            for k in [
                "study",
                "clinical",
                "trial",
                "randomized",
                "peer-reviewed",
                "evidence",
                "meta-analysis",
            ]
        ):
            return "medical_science"
        if any(
            k in t
            for k in [
                "works",
                "results",
                "lose",
                "pounds",
                "improves",
                "effective",
                "efficacy",
            ]
        ):
            return "product_efficacy"
        if any(
            k in t
            for k in [
                "mechanism",
                "inflammation",
                "metabolism",
                "hormone",
                "insulin",
                "glp-1",
                "mct",
            ]
        ):
            return "mechanism"
        if any(
            k in t
            for k in [
                "side effects",
                "safety",
                "danger",
                "unsafe",
                "contraindicated",
                "fda warning",
            ]
        ):
            return "safety"
        return "other"

    for c in claims:
        text = (
            c.get("claim_text", "")
            if isinstance(c, dict)
            else getattr(c, "claim_text", "")
        )
        categories[classify_claim(text)].append(c)

    # Selection: aim for 20 claims with at least 3 per primary category when available
    target_total = 20
    min_per_cat = {
        "speaker_credibility": 3,
        "medical_science": 3,
        "product_efficacy": 3,
        "mechanism": 3,
        "safety": 2,
    }
    selected = []

    # First satisfy minimums
    for cat, minimum in min_per_cat.items():
        selected.extend(categories[cat][:minimum])

    # Fill remaining slots round-robin across categories to diversify
    cats_order = [
        "speaker_credibility",
        "medical_science",
        "product_efficacy",
        "mechanism",
        "safety",
        "other",
    ]
    idx_map = {k: min_per_cat.get(k, 0) for k in cats_order}
    while len(selected) < min(target_total, len(claims)):
        progressed = False
        for cat in cats_order:
            arr = categories[cat]
            i = idx_map[cat]
            if i < len(arr):
                selected.append(arr[i])
                idx_map[cat] += 1
                progressed = True
                if len(selected) >= target_total:
                    break
        if not progressed:
            break

    # Deduplicate while preserving order
    seen_ids = set()
    deduped = []
    for c in selected:
        cid = c.get("claim_id") if isinstance(c, dict) else getattr(c, "claim_id", None)
        key = cid or (
            c.get("claim_text") if isinstance(c, dict) else getattr(c, "claim_text", "")
        )
        if key not in seen_ids:
            seen_ids.add(key)
            deduped.append(c)

    logger.info(f"✅ Selected {len(deduped)} diversified claims for verification")
    return {**state, "claims": deduped, "aggregated_evidence": []}


async def extract_claims_with_llm(
    transcription: str, video_info: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Extract claims from transcription using LLM."""
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.prompts import ChatPromptTemplate
    import logging

    logger = logging.getLogger(__name__)
    logger.info("🤖 Using Gemini LLM to extract claims from transcription")

    try:
        llm = ChatVertexAI(
            model_name=AGENT_MODEL_NAME,
            max_output_tokens=MAX_OUTPUT_TOKENS_2_5_FLASH,  # Increased for Gemini 2.5 Flash (supports up to 65K)
            temperature=0.2,  # Lower temperature for more factual responses
            top_p=0.95,
            top_k=40,
            verbose=True,  # Help with debugging
            streaming=False,  # Disable streaming to prevent "No generations found in stream" errors
        )

        prompt = ChatPromptTemplate.from_template(
            """
        Analyze this video transcription and extract specific, verifiable claims made by the speaker.
        
        Video Title: {title}
        Transcription: {transcription}
        
        Extract claims that are:
        1. Factual statements that can be verified
        2. Specific enough to research
        3. Important to the video's main message
        
        For each claim, provide:
        - claim_text: The exact claim
        - timestamp: Best estimate of when it was said
        - speaker: Who made the claim
        - importance: Why this claim matters
        
        Return as JSON array of claim objects.
        """
        )

        start_time = time.time()
        call_id = log_llm_call(
            operation="extract_claims_with_llm",
            prompt=prompt.format(
                title=video_info.get("title", "Unknown"),
                transcription=transcription[:10000],
            ),
            model=AGENT_MODEL_NAME,
            video_id=video_info.get("id")
        )

        response = await llm.ainvoke(
            prompt.format_messages(
                title=video_info.get("title", "Unknown"),
                transcription=transcription[:10000],  # Limit length
            )
        )
        duration = time.time() - start_time
        log_llm_response(call_id, response, duration=duration)

        # Save LLM response for debugging if DEBUG_OUTPUTS is enabled
        if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true":
            import json
            from datetime import datetime
            from pathlib import Path

            # Use a generic debug directory since video_id might not be available
            debug_dir = Path("./sherlock_llm_debug")
            debug_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = debug_dir / f"transcription_analysis_{timestamp}.json"

            debug_data = {
                "timestamp": datetime.now().isoformat(),
                "video_title": video_info.get("title", "Unknown"),
                "llm_model": AGENT_MODEL_NAME,
                "analysis_type": "transcription_claims",
                "transcription_length": len(transcription),
                "prompt_text": prompt.format(
                    title=video_info.get("title", "Unknown"),
                    transcription=transcription[:10000],
                ),
                "response_content": (
                    response.content
                    if response and hasattr(response, "content")
                    else None
                ),
                "response_length": (
                    len(response.content)
                    if response and hasattr(response, "content") and response.content
                    else 0
                ),
                "response_type": str(type(response)),
                "success": bool(
                    response and hasattr(response, "content") and response.content
                ),
            }

            with open(debug_file, "w") as f:
                json.dump(debug_data, f, indent=2)
            logger.info(f"🔍 DEBUG: Saved transcription LLM response to {debug_file}")

        # Parse response and format claims
        import json

        try:
            claims_data = json.loads(response.content)
            if not isinstance(claims_data, list):
                claims_data = []
        except:
            claims_data = []

        # Format claims consistently
        claims = []
        for i, claim in enumerate(claims_data):
            if isinstance(claim, dict):
                formatted_claim = {
                    "claim_id": i + 1,
                    "claim_text": claim.get("claim_text", ""),
                    "timestamp": claim.get("timestamp", "00:00"),
                    "speaker": claim.get("speaker", "Speaker"),
                    "importance": claim.get("importance", ""),
                    "initial_assessment": "Pending verification",
                }
                claims.append(formatted_claim)

        logger.info(f"✅ Successfully extracted {len(claims)} claims")
        return claims

    except Exception as e:
        logger.error(f"❌ LLM claim extraction failed: {e}")
        return []


async def extract_claims_with_gemini_multimodal_youtube_url(
    video_url: str, video_id: str, video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract claims using Gemini multimodal analysis with YouTube URL (fallback approach)."""
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.messages import HumanMessage

    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"🌐 Starting Gemini YouTube URL analysis for video {video_id}")

    try:
        # Create Gemini LLM
        llm = ChatVertexAI(
            model_name=AGENT_MODEL_NAME,
            max_output_tokens=MAX_OUTPUT_TOKENS_2_5_FLASH,  # Increased for Gemini 2.5 Flash (supports up to 65K)
            temperature=0.2,  # Lower temperature for more factual responses
            top_p=0.95,
            top_k=40,
            verbose=True,  # Help with debugging
            streaming=False,  # Disable streaming to prevent "No generations found in stream" errors
        )

        # Create AGGRESSIVE multimodal prompt (restored from July 20th)
        prompt_text = f"""
🎬 AGGRESSIVE VIDEO FRAME ANALYSIS - CLAIMS EXTRACTION MISSION 🎬

CRITICAL INSTRUCTIONS FOR MULTIMODAL VIDEO ANALYSIS:
- Analyze this video with MAXIMUM detail at 1 FRAME PER SECOND sampling rate
- Extract ALL factual claims, statements, assertions from ACTUAL VIDEO CONTENT
- Focus on SPOKEN WORDS, VISUAL TEXT, ON-SCREEN GRAPHICS, and DEMONSTRATIONS
- Ignore background music, decorative elements, or irrelevant visuals
- Extract EXACTLY 5-15 specific, verifiable claims from the actual video frames and audio (targeting 3 claims per minute)

Video ID: {video_id}
Video URL: {video_url}
Video Title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}

🎯 AGGRESSIVE MULTIMODAL REQUIREMENTS:
1. Sample video at 1 frame per second (aggressive temporal resolution)
2. Transcribe ALL spoken content with timestamps
3. Extract text from visual overlays, graphics, slides, captions
4. Identify claims from demonstrations, charts, or visual evidence
5. Note precise timestamps for each claim
6. Distinguish between speaker statements and visual text

🔍 FRAME-BY-FRAME ANALYSIS FOCUS:
- What is being SAID in the audio track?
- What TEXT appears on screen?
- What DEMONSTRATIONS or EVIDENCE is shown?
- What GRAPHICS or CHARTS contain factual information?
- What CLAIMS can be verified from external sources?
- What CREDENTIALS or BACKGROUND is mentioned about speakers?

🎯 MANDATORY CLAIM EXTRACTION MIX:
**REQUIRED SPEAKER CREDIBILITY CLAIMS (minimum 20% of total):**
- Educational background (where they studied, degrees obtained)
- Professional experience (years in field, previous positions)
- Institutional affiliations (hospitals, universities, organizations)
- Awards, recognitions, or honors received
- Publications, research, or books authored
- Professional certifications or licenses
- Leadership roles or founding positions

**CONTENT CLAIMS (remaining 80%):**
- Study results, research findings, statistics
- Product claims, effectiveness statements
- Health outcomes, treatment results
- Scientific discoveries or breakthroughs
- Specific numerical data or percentages

OUTPUT FORMAT: Provide detailed JSON with:
{{
    "initial_report": "Comprehensive analysis of video content and main themes based on frame-by-frame analysis",
    "claims": [
        {{
            "claim_text": "Specific factual claim extracted from video frames/audio",
            "timestamp": "MM:SS or time range where claim appears",
            "speaker": "Identified speaker name or 'Visual Text' or 'On-Screen Graphics'",
            "source_type": "spoken|visual_text|demonstration|graphic|chart",
            "initial_assessment": "Assessment of claim verifiability and factual nature"
        }}
    ],
    "video_analysis_summary": "Summary of video content, themes, and claim extraction process from multimodal analysis"
}}

🚨 EXTRACT CLAIMS FROM ACTUAL VIDEO FRAMES & AUDIO - NOT METADATA OR DESCRIPTIONS! 🚨
        """

        # Create message with YouTube URL (using correct 'url' format)
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "media", "file_uri": video_url, "mime_type": "video/*"},
            ]
        )

        # Get response from Gemini
        logger.info("🚀 Invoking Gemini YouTube URL analysis...")
        start_time = time.time()
        call_id = log_llm_call(
            operation="extract_claims_with_gemini_multimodal_youtube_url",
            prompt=prompt_text,
            model=AGENT_MODEL_NAME,
            video_id=video_id
        )

        response = await llm.ainvoke([message])
        duration = time.time() - start_time
        log_llm_response(call_id, response, duration=duration)

        # Save LLM response for debugging if DEBUG_OUTPUTS is enabled
        if os.getenv("DEBUG_OUTPUTS", "False").lower() == "true":
            import json
            from datetime import datetime
            from pathlib import Path

            debug_dir = Path(f"./sherlock_analysis_{video_id}/llm_calls")
            debug_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = debug_dir / f"youtube_url_analysis_{timestamp}.json"

            debug_data = {
                "timestamp": datetime.now().isoformat(),
                "video_id": video_id,
                "llm_model": AGENT_MODEL_NAME,
                "analysis_type": "youtube_url",
                "prompt_text": (
                    str(message.content[0]["text"]) if message.content else ""
                ),
                "prompt_length": len(
                    str(message.content[0]["text"]) if message.content else ""
                ),
                "response_content": (
                    response.content
                    if response and hasattr(response, "content")
                    else None
                ),
                "response_length": (
                    len(response.content)
                    if response and hasattr(response, "content") and response.content
                    else 0
                ),
                "response_type": str(type(response)),
                "success": bool(
                    response and hasattr(response, "content") and response.content
                ),
            }

            with open(debug_file, "w") as f:
                json.dump(debug_data, f, indent=2)
            logger.info(f"🔍 DEBUG: Saved LLM response to {debug_file}")

        if response and hasattr(response, "content") and response.content:
            logger.info(
                f"✅ YouTube URL analysis completed: {len(response.content)} characters"
            )
            return parse_llm_response(response.content, video_id, logger)
        else:
            logger.warning("⚠️ Empty response from YouTube URL analysis")
            return {
                "error": "Empty response from Gemini YouTube URL analysis",
                "initial_report": "Analysis failed",
                "claims": [],
            }

    except Exception as e:
        logger.error(f"❌ Gemini YouTube URL analysis failed: {e}")
        return {
            "error": f"YouTube URL analysis failed: {str(e)}",
            "initial_report": f"Failed to analyze YouTube video {video_id}",
            "claims": [],
        }


async def extract_claims_with_gemini_multimodal_youtube_url_segmented_genai(
    video_url: str, video_id: str, video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Segmented YouTube URL analysis using Google AI (GenAI) API with videoMetadata clipping and fps.
    Reference: https://ai.google.dev/gemini-api/docs/video-understanding
    """
    import logging
    from typing import Any, Dict, List
    from google import genai
    from google.genai import types
    from verityngn.config.settings import (
        SEGMENTED_URL_ANALYSIS,
        SEGMENT_DURATION_SECONDS,
        SEGMENT_FPS,
        GENAI_VIDEO_MAX_OUTPUT_TOKENS,
        THINKING_BUDGET,
    )

    logger = logging.getLogger(__name__)
    logger.info(
        f"🌐 [GENAI] Segmented YouTube URL analysis for {video_id} | segments={SEGMENTED_URL_ANALYSIS}"
    )

    # Initialize GenAI client explicitly with API key to avoid missing key error
    import os

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_STUDIO_KEY")
    client = genai.Client(api_key=api_key) if api_key else genai.Client()

    # Prompt and thinking budget hint
    duration_sec = int(video_info.get("duration", 0) or 0)
    duration_min = max(1, duration_sec // 60 or 1)
    target_claims = max(
        8, min(20, int(duration_min * 3))
    )  # encourage more claims initially
    prompt_text = (
        f"Extract {target_claims} high-quality, verifiable claims. Prioritize scientific/verifiable claims (70%+), "
        "only 10% speaker-credibility if clearly stated. Focus on claims throughout video timeline. "
        "Prioritize CRAAP; avoid micro-claims. Output compact JSON list."
    )
    thinking_hint = "Minimize hidden thinking; be concise."

    def call_segment(start_s: int = None, end_s: int = None) -> str:
        parts = [
            types.Part(
                file_data=types.FileData(file_uri=video_url),
                video_metadata=types.VideoMetadata(
                    **({"start_offset": f"{start_s}s"} if start_s is not None else {}),
                    **({"end_offset": f"{end_s}s"} if end_s is not None else {}),
                    **({"fps": SEGMENT_FPS} if SEGMENT_FPS else {}),
                ),
            ),
            types.Part(text=f"{prompt_text}\n{thinking_hint}"),
        ]
        contents = types.Content(parts=parts)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=GENAI_VIDEO_MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
            ),
        )
        txt = getattr(resp, "text", None) or ""
        logger.info(f"[GENAI] segment=({start_s},{end_s}) len={len(txt)}")
        return txt

    texts: List[str] = []
    if not SEGMENTED_URL_ANALYSIS or duration_sec <= 0:
        texts.append(call_segment())
    else:
        start = 0
        while start < duration_sec:
            end = min(start + SEGMENT_DURATION_SECONDS, duration_sec)
            texts.append(call_segment(start, end))
            start = end

    # Parse each segment response as JSON and fuse claims together
    # Check for video unavailability markers first
    for t in texts:
        if t and t.startswith("__VIDEO_UNAVAILABLE__:"):
            error_detail = t.replace("__VIDEO_UNAVAILABLE__:", "")
            logger.error(f"❌ Video is unavailable or inaccessible: {error_detail}")
            return {
                "error": f"YouTube video is unavailable, private, deleted, or not accessible. The video cannot be analyzed. Details: {error_detail}",
                "initial_report": "",
                "claims": [],
            }
    
    if not texts or not any(t.strip() for t in texts):
        return {
            "error": "Empty response from segmented GenAI YouTube analysis - the video may be unavailable or too short",
            "initial_report": "",
            "claims": [],
        }

    try:
        return fuse_segmented_json_responses(
            texts, video_id, logging.getLogger(__name__)
        )
    except Exception as e:
        logger.error(f"Failed to fuse segmented outputs: {e}")
        return {
            "error": "Failed to parse segmented output",
            "initial_report": "",
            "claims": [],
        }


async def extract_claims_with_gemini_multimodal_youtube_url_segmented_vertex(
    video_url: str, video_id: str, video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhanced segmented YouTube URL analysis using latest Vertex SDK patterns.

    Now uses intelligent segmentation based on model context windows to minimize API calls
    while maximizing context utilization.

    Note: Updated to use latest Vertex AI Python SDK patterns to avoid deprecation warnings.
    The Vertex Python SDK does not expose video_metadata on Part in all versions; this method
    attempts to pass a dict with video_metadata where supported. If unsupported, it falls back to whole-video calls per segment indices as prompt hints.
    """
    import logging
    from typing import Any, Dict, List
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
    from verityngn.config.settings import (
        PROJECT_ID,
        LOCATION,
        VERTEX_MODEL_NAME,
        SEGMENTED_URL_ANALYSIS,
        SEGMENT_FPS,
        MAX_OUTPUT_TOKENS_2_5_FLASH,
        THINKING_BUDGET,
        DEFAULT_SEGMENTED_DURATION_SEC,
    )
    from verityngn.config.video_segmentation import (
        get_segmentation_for_video,
        log_segmentation_plan,
        get_segment_duration_from_env_or_optimal
    )

    logger = logging.getLogger(__name__)
    logger.info(
        f"🌐 [VERTEX] Intelligent segmented YouTube URL analysis for {video_id}"
    )

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = GenerativeModel(VERTEX_MODEL_NAME)

    # Guard: video_info may be None
    if not video_info:
        video_info = {}
    duration_sec = int(
        (video_info.get("duration", 0) if isinstance(video_info, dict) else 0) or 0
    )
    if duration_sec <= 0:
        # For TL video, we know it's ~30 minutes = 1800 seconds
        duration_sec = 1800  # Use known duration for TL video when metadata fails
        logger.warning(
            f"⚠️ Using fallback duration of {duration_sec}s for segmentation since metadata failed"
        )
    
    # Calculate optimal segment duration based on model context window
    SEGMENT_DURATION_SECONDS = get_segment_duration_from_env_or_optimal(
        video_duration_seconds=duration_sec,
        model_name=VERTEX_MODEL_NAME
    )
    
    # Log intelligent segmentation plan
    log_segmentation_plan(duration_sec, VERTEX_MODEL_NAME, SEGMENT_FPS)
    duration_min = max(1, duration_sec // 60 or 1)
    # Aim for rich coverage: ~3 claims/minute; keep within 45–90
    target_claims = min(90, max(45, int(duration_min * 3)))

    #   base_prompt = (
    #         f"Extract {target_claims} high-quality, verifiable claims from the video content (audio+visual). "
    #         "Ensure at least 20% are speaker-credibility claims; the rest are content claims. "
    #         "Apply CRAAP; avoid micro-claims; prioritize variety and importance. "
    #         "OUTPUT STRICTLY JSON ONLY (no prose, no markdown, no code fences):\n"
    #         "Insure each claim in the claims list has the following JSON template filled in, oncluding claim_text, timestamp, speaker, and source_type."
    #         "{\n"
    #         "  \"initial_report\": \"<brief 1-2 sentences>\",\n"
    #         "  \"claims\": [\n"
    #         "    {\n"
    #         "      \"claim_text\": \"<concise claim>\",\n"
    #         "      \"timestamp\": \"MM:SS or range\",\n"
    #         "      \"speaker\": \"<name or Visual Text>\",\n"
    #         "      \"source_type\": \"spoken|visual_text|demonstration|graphic|chart\"\n"
    #         "    }\n"
    #         "  ]\n"
    #         "}"
    #     )
    #

    # Create AGGRESSIVE multimodal prompt (restored from July 20th)

    base_prompt = f"""
🎬 ENHANCED VIDEO FRAME ANALYSIS - HIGH-QUALITY CLAIMS EXTRACTION 🎬
- Extract {target_claims} SUBSTANTIAL, high-quality, verifiable claims from the video content (audio+visual)
- Ensure at least 20% are speaker-credibility claims; the rest are content claims
- Apply CRAAP criteria (Currency, Relevance, Authority, Accuracy, Purpose)
- AVOID micro-claims and overly fine-grained statements
- Prioritize VERIFIABLE facts over vague assertions
- Focus on claims that substantially impact truthfulness assessment
 
CRITICAL INSTRUCTIONS FOR MULTIMODAL VIDEO ANALYSIS:
- Analyze this video with MAXIMUM detail at 1 FRAME PER SECOND sampling rate
- Extract SUBSTANTIAL factual claims, statements, assertions from ACTUAL VIDEO CONTENT
- Focus on SPOKEN WORDS, VISUAL TEXT, ON-SCREEN GRAPHICS, and DEMONSTRATIONS
- Ignore background music, decorative elements, or irrelevant visuals
- Extract APPROXIMATELY {target_claims} specific, MEANINGFUL claims from the actual video frames and audio

Video ID: {video_id}
Video URL: {video_url}
Video Title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}

🎯 ENHANCED MULTIMODAL REQUIREMENTS:
1. Sample video at 1 frame per second (aggressive temporal resolution)
2. Transcribe ALL spoken content with precise timestamps
3. Extract text from visual overlays, graphics, slides, captions
4. Identify claims from demonstrations, charts, or visual evidence
5. Note precise timestamps for each claim
6. Distinguish between speaker statements and visual text
7. PRIORITIZE claims that can be fact-checked against external sources

🔍 FRAME-BY-FRAME ANALYSIS FOCUS (CRAAP CRITERIA):
- CURRENCY: What recent studies, dates, or current information is mentioned?
- RELEVANCE: What claims are central to the video's main message?
- AUTHORITY: What CREDENTIALS, institutional affiliations, or expertise is claimed?
- ACCURACY: What specific facts, statistics, or verifiable data is presented?
- PURPOSE: What persuasive claims or promotional statements are made?

🎯 MANDATORY HIGH-QUALITY CLAIM EXTRACTION MIX:
**PRIORITY: SCIENTIFIC & VERIFIABLE CLAIMS (minimum 70% - CRUCIAL for truthfulness):**
- Specific study results: "[Institution] study found [specific quantified outcome]"
- Research findings: "Research published in [journal] shows [specific data]"
- Statistical claims: "[X]% of [specific population] experienced [measurable outcome]"
- Product effectiveness: "[Product] caused [specific measurable effect] in [timeframe]"
- Health outcomes: "[Treatment] resulted in [specific health improvement] in [study size]"
- Scientific discoveries: "[Researcher] discovered [specific finding] published in [year]"
- Comparative claims: "[X] is [quantifiably] better than [Y] based on [specific metric]"

**SECONDARY: SPEAKER CREDIBILITY CLAIMS (minimum 10% only if clearly stated):**
- Educational background: "Dr. X studied/graduated from [specific institution]"
- Professional experience: "Dr. X has [X] years of experience in [specific field]"
- Institutional affiliations: "Dr. X works at/is affiliated with [specific organization]"
- Awards/recognitions: "Dr. X received [specific award] from [organization]"
- Publications: "Dr. X authored [specific publication/book title]"
- Professional certifications: "Dr. X is board-certified/licensed by [organization]"

**OTHER VERIFIABLE CLAIMS (remaining 20%):**
- Specific study results: "[Institution] study found [specific quantified outcome]"
- Research findings: "Research published in [journal] shows [specific data]"
- Statistical claims: "[X]% of [specific population] experienced [measurable outcome]"
- Product effectiveness: "[Product] caused [specific measurable effect] in [timeframe]"
- Health outcomes: "[Treatment] resulted in [specific health improvement] in [study size]"
- Scientific discoveries: "[Researcher] discovered [specific finding] published in [year]"
- Comparative claims: "[X] is [quantifiably] better than [Y] based on [specific metric]"

🚫 AVOID LOW-QUALITY/MICRO-CLAIMS:
- Vague motivational statements
- General health advice without specifics
- Obvious facts that don't need verification
- Claims too granular to be meaningful for truthfulness assessment
- Subjective opinions without factual basis

OUTPUT FORMAT: Provide detailed JSON with:
{{
    "initial_report": "Comprehensive analysis of video content and main themes based on frame-by-frame analysis",
    "claims": [
        {{
            "claim_text": "Specific, SUBSTANTIAL factual claim extracted from video (avoid micro-claims)",
            "timestamp": "MM:SS or time range where claim appears",
            "speaker": "Identified speaker name or 'Visual Text' or 'On-Screen Graphics'",
            "source_type": "spoken|visual_text|demonstration|graphic|chart",
            "initial_assessment": "CRAAP-based assessment of claim verifiability, importance, and factual nature"
        }}
    ],
    "video_analysis_summary": "Summary of video content, themes, and claim extraction process from multimodal analysis"
}}

🚨 EXTRACT HIGH-QUALITY CLAIMS FROM ACTUAL VIDEO FRAMES & AUDIO - NOT METADATA OR DESCRIPTIONS! 🚨
"""

    thinking_hint = "NO THINKING TOKENS! Extract claims immediately without internal reasoning. Direct JSON output only."

    gen_cfg = GenerationConfig(
        max_output_tokens=min(32768, MAX_OUTPUT_TOKENS_2_5_FLASH),
        temperature=0.25,
        top_p=0.95,
        top_k=40,
    )

    def build_part_with_metadata(start: int = None, end: int = None, fps: float = None):
        # Use simple URI part; rely on textual segment hints to avoid API 400s
        return Part.from_uri(video_url, mime_type="video/youtube")

    def call_segment(start_s: int = None, end_s: int = None) -> str:
        video_part = build_part_with_metadata(
            start_s, end_s, SEGMENT_FPS if SEGMENTED_URL_ANALYSIS else None
        )
        # Add explicit segment hint in text in case metadata is not honored
        segment_hint = (
            f"Analyze only segment {start_s}s..{end_s}s of the video. "
            if (start_s is not None and end_s is not None)
            else ""
        )
        # Place video content first, followed by the instruction text to improve response stability
        contents = [video_part, f"{segment_hint}{base_prompt}\n{thinking_hint}"]
        start_time = time.time()
        call_id = log_llm_call(
            operation="extract_claims_segmented_vertex",
            prompt=f"{segment_hint}{base_prompt}\n{thinking_hint}",
            model=VERTEX_MODEL_NAME,
            video_id=video_id,
            metadata={"start_s": start_s, "end_s": end_s}
        )

        # Primary attempt
        try:
            resp = model.generate_content(
                contents=contents,
                generation_config=gen_cfg,
                stream=False,
            )
            duration = time.time() - start_time
            log_llm_response(call_id, resp, duration=duration)
        except Exception as e:
            # Implement exponential backoff for 503 and other transient errors
            error_msg = str(e).lower()
            original_error = str(e)
            
            # Detect video unavailability errors (non-retryable)
            is_video_unavailable = any(
                x in error_msg
                for x in [
                    "not owned by the user",
                    "video unavailable",
                    "video not found",
                    "private video",
                    "deleted video",
                    "age-restricted",
                    "403",
                ]
            )
            
            if is_video_unavailable:
                logger.error(f"❌ [VERTEX] Video unavailable error (non-retryable): {original_error}")
                # Return special marker that will be caught later
                return f"__VIDEO_UNAVAILABLE__:{original_error}"
            
            is_503_or_transient = any(
                x in error_msg
                for x in [
                    "503",
                    "unavailable",
                    "overloaded",
                    "timeout",
                    "deadline",
                    "rate limit",
                ]
            )

            if is_503_or_transient:
                # Exponential backoff with jitter for 503/transient errors
                base_delay = 2.0
                jitter = random.uniform(0.5, 1.5)
                backoff_delay = base_delay * jitter
                logger.warning(
                    f"[VERTEX] 503/Transient error detected: {e}. Waiting {backoff_delay:.1f}s before retry..."
                )
                time.sleep(backoff_delay)
            else:
                logger.warning(
                    f"[VERTEX] Primary generate_content failed: {e}. Retrying with relaxed config..."
                )

            try:
                relaxed_cfg = GenerationConfig(
                    max_output_tokens=min(32768, MAX_OUTPUT_TOKENS_2_5_FLASH),
                    temperature=0.25,
                    top_p=0.95,
                    top_k=40,
                )
                resp = model.generate_content(
                    contents=contents,
                    generation_config=relaxed_cfg,
                    stream=False,
                )
            except Exception as e2:
                error2_msg = str(e2).lower()
                # Check again for video unavailability in retry
                is_video_unavailable_retry = any(
                    x in error2_msg
                    for x in [
                        "not owned by the user",
                        "video unavailable",
                        "video not found",
                        "private video",
                        "deleted video",
                        "age-restricted",
                        "403",
                    ]
                )
                if is_video_unavailable_retry:
                    logger.error(f"❌ [VERTEX] Video unavailable error (non-retryable): {e2}")
                    return f"__VIDEO_UNAVAILABLE__:{e2}"
                    
                logger.error(
                    f"[VERTEX] Relaxed config failed: {e2}. No further model fallback will be attempted."
                )
                return ""

        # ============================================================
        # DIAGNOSTIC LOGGING: Deep inspection of response structure
        # ============================================================
        logger.info("[VERTEX DIAGNOSTIC] ========== RESPONSE OBJECT INSPECTION ==========")
        logger.info(f"[VERTEX DIAGNOSTIC] Response type: {type(resp)}")
        logger.info(f"[VERTEX DIAGNOSTIC] Response dir: {[x for x in dir(resp) if not x.startswith('_')]}")
        
        # Check for internal/raw response attributes
        if hasattr(resp, '_raw_response'):
            logger.info(f"[VERTEX DIAGNOSTIC] Has _raw_response: {type(resp._raw_response)}")
        if hasattr(resp, '_pb'):
            logger.info(f"[VERTEX DIAGNOSTIC] Has _pb: {type(resp._pb)}")
            try:
                pb_text = resp._pb.candidates[0].content.parts[0].text if resp._pb.candidates else "N/A"
                logger.info(f"[VERTEX DIAGNOSTIC] _pb text length: {len(pb_text) if pb_text else 0}")
                logger.info(f"[VERTEX DIAGNOSTIC] _pb text preview: {pb_text[:200] if pb_text else 'EMPTY'}")
            except Exception as pb_ex:
                logger.info(f"[VERTEX DIAGNOSTIC] _pb access failed: {pb_ex}")
        
        # Inspect candidates
        if hasattr(resp, "candidates") and resp.candidates:
            logger.info(f"[VERTEX DIAGNOSTIC] Candidates count: {len(resp.candidates)}")
            cand = resp.candidates[0]
            logger.info(f"[VERTEX DIAGNOSTIC] Candidate type: {type(cand)}")
            logger.info(f"[VERTEX DIAGNOSTIC] Candidate dir: {[x for x in dir(cand) if not x.startswith('_')]}")
            
            # Inspect content
            if hasattr(cand, "content"):
                content = cand.content
                logger.info(f"[VERTEX DIAGNOSTIC] Content type: {type(content)}")
                logger.info(f"[VERTEX DIAGNOSTIC] Content dir: {[x for x in dir(content) if not x.startswith('_')]}")
                
                # Inspect parts
                if hasattr(content, "parts"):
                    logger.info(f"[VERTEX DIAGNOSTIC] Parts count: {len(content.parts)}")
                    for i, part in enumerate(content.parts):
                        logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] type: {type(part)}")
                        logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] dir: {[x for x in dir(part) if not x.startswith('_')]}")
                        logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] is dict: {isinstance(part, dict)}")
                        
                        # Try different access methods
                        logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] hasattr 'text': {hasattr(part, 'text')}")
                        if hasattr(part, 'text'):
                            text_val = getattr(part, 'text', None)
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] .text value: {text_val}")
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] .text type: {type(text_val)}")
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] .text length: {len(text_val) if text_val else 0}")
                            if text_val:
                                logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] .text preview: {text_val[:200]}")
                        
                        # Try direct attribute access
                        try:
                            direct_text = part.text
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] direct .text: {len(direct_text) if direct_text else 0} chars")
                        except Exception as direct_ex:
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] direct .text failed: {direct_ex}")
                        
                        # Try dict access
                        if isinstance(part, dict):
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] dict keys: {list(part.keys())}")
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] dict['text']: {part.get('text', 'N/A')}")
                        
                        # Check for _pb on part
                        if hasattr(part, '_pb'):
                            logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] has _pb: {type(part._pb)}")
                            try:
                                pb_part_text = part._pb.text if hasattr(part._pb, 'text') else "N/A"
                                logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] _pb.text: {len(pb_part_text) if pb_part_text else 0} chars")
                            except Exception as pb_part_ex:
                                logger.info(f"[VERTEX DIAGNOSTIC] Part[{i}] _pb.text failed: {pb_part_ex}")
        
        logger.info("[VERTEX DIAGNOSTIC] ========== END INSPECTION ==========")
        
        # ============================================================
        # TEXT EXTRACTION: Try multiple approaches
        # ============================================================
        text = ""
        
        # Approach 1: Standard .text attribute
        try:
            text = getattr(resp, "text", None) or ""
            if text:
                logger.info(f"[VERTEX] ✅ Approach 1 (resp.text): Extracted {len(text)} chars")
        except ValueError as e:
            logger.warning(f"[VERTEX] ❌ Approach 1 (resp.text): {e}")
        
        # Approach 2: Extract from candidates[0].content.parts via protobuf
        if not text and hasattr(resp, '_pb'):
            try:
                if resp._pb.candidates and resp._pb.candidates[0].content.parts:
                    pb_parts = resp._pb.candidates[0].content.parts
                    pb_texts = [p.text for p in pb_parts if hasattr(p, 'text') and p.text]
                    if pb_texts:
                        text = '\n'.join(pb_texts) if len(pb_texts) > 1 else pb_texts[0]
                        logger.info(f"[VERTEX] ✅ Approach 2 (_pb protobuf): Extracted {len(text)} chars from {len(pb_texts)} part(s)")
            except Exception as pb_ex:
                logger.warning(f"[VERTEX] ❌ Approach 2 (_pb protobuf): {pb_ex}")
        
        # Approach 3: Extract from candidates[0].content.parts via getattr
        if not text and hasattr(resp, "candidates") and resp.candidates:
            try:
                cand = resp.candidates[0]
                parts = getattr(cand, "content", None)
                if parts and hasattr(parts, "parts"):
                    part_texts = []
                    for p in parts.parts:
                        # Try multiple ways to get text
                        p_text = None
                        
                        # Method A: getattr
                        p_text = getattr(p, "text", None)
                        
                        # Method B: direct access if getattr failed
                        if not p_text and hasattr(p, "text"):
                            try:
                                p_text = p.text
                            except:
                                pass
                        
                        # Method C: _pb access if still no text
                        if not p_text and hasattr(p, "_pb") and hasattr(p._pb, "text"):
                            try:
                                p_text = p._pb.text
                            except:
                                pass
                        
                        if p_text:
                            part_texts.append(p_text)
                    
                    if part_texts:
                        # Deduplicate identical parts (common with Gemini 2.5 Flash)
                        unique_parts = list(set(part_texts))
                        if len(unique_parts) == 1:
                            # All parts are identical - use just one copy
                            text = unique_parts[0]
                            logger.info(f"[VERTEX] ✅ Approach 3 (candidates.parts multi-method): Extracted {len(text)} chars from {len(part_texts)} duplicate part(s)")
                        else:
                            # Parts are different - try to merge intelligently
                            # For JSON responses, take the longest/most complete one
                            text = max(unique_parts, key=len)
                            logger.info(f"[VERTEX] ✅ Approach 3 (candidates.parts multi-method): Extracted {len(text)} chars from {len(unique_parts)} unique part(s) out of {len(part_texts)} total")
            except Exception as ex:
                logger.warning(f"[VERTEX] ❌ Approach 3 (candidates.parts): {ex}")
        
        # Approach 4: Check if response is iterable (streaming)
        if not text:
            try:
                if hasattr(resp, '__iter__'):
                    chunks = list(resp)
                    if chunks:
                        chunk_texts = [getattr(c, 'text', '') for c in chunks if hasattr(c, 'text')]
                        if chunk_texts:
                            text = ''.join(chunk_texts)
                            logger.info(f"[VERTEX] ✅ Approach 4 (iterator/streaming): Extracted {len(text)} chars from {len(chunks)} chunk(s)")
            except Exception as iter_ex:
                logger.warning(f"[VERTEX] ❌ Approach 4 (iterator): {iter_ex}")
        
        if not text:
            logger.error("[VERTEX] ❌ ALL TEXT EXTRACTION APPROACHES FAILED - Response generated tokens but no text accessible!")
        usage = getattr(resp, "usage_metadata", None)
        finish = None
        try:
            if hasattr(resp, "candidates") and resp.candidates:
                finish = getattr(resp.candidates[0], "finish_reason", None)
        except Exception:
            pass
        # Log safety blocks if present for diagnostics
        try:
            if hasattr(resp, "candidates") and resp.candidates:
                safety = getattr(resp.candidates[0], "safety_ratings", None)
                if safety:
                    logger.info(f"[VERTEX] segment=({start_s},{end_s}) safety={safety}")
        except Exception:
            pass

        logger.info(
            f"[VERTEX] segment=({start_s},{end_s}) finish={finish} usage={usage} len={len(text)}"
        )
        return text

    texts: List[str] = []
    if not SEGMENTED_URL_ANALYSIS or duration_sec <= 0:
        texts.append(call_segment())
    else:
        import time
        import os

        # Get rate limiting configuration
        rate_limit_enabled = os.getenv(
            "SEGMENT_RATE_LIMIT_ENABLED", "false"
        ).lower() in ("true", "1", "t")
        segment_delay = (
            float(os.getenv("SEGMENT_PROCESSING_DELAY", "2.0"))
            if rate_limit_enabled
            else 0.0
        )

        start = 0
        segment_count = 0
        total_segments = max(1, (duration_sec + SEGMENT_DURATION_SECONDS - 1) // SEGMENT_DURATION_SECONDS)
        
        logger.info(f"🎬 [VERTEX] Segmentation plan: {duration_sec}s video → {total_segments} segment(s) of {SEGMENT_DURATION_SECONDS}s each")
        logger.info(f"   Expected time: ~{total_segments * 8}-{total_segments * 12} minutes total")
        logger.info("")
        
        while start < duration_sec:
            end = min(start + SEGMENT_DURATION_SECONDS, duration_sec)
            segment_duration_min = (end - start) / 60

            # Add delay between segments to prevent 503 errors (only if rate limiting is enabled)
            if segment_count > 0 and rate_limit_enabled and segment_delay > 0:
                logger.info(
                    f"⏱️ Rate limiting: waiting {segment_delay}s before processing segment {segment_count}"
                )
                time.sleep(segment_delay)
            elif segment_count > 0:
                logger.info("")
                logger.info(
                    f"🚀 Processing segment {segment_count} (rate limiting disabled)"
                )

            # ALWAYS log segment start for visibility
            logger.info(f"🎬 [VERTEX] Segment {segment_count + 1}/{total_segments}: Processing {start}s → {end}s ({segment_duration_min:.1f} minutes)")
            logger.info(f"   ⏱️  Expected processing time: 8-12 minutes for this segment")
            logger.info(f"   📊 Progress: {((segment_count) / total_segments * 100):.0f}% complete")
            logger.info(f"   ⏳ Please wait... (this is NORMAL, not hung)")
            
            texts.append(call_segment(start, end))
            start = end
            segment_count += 1

    # Parse each segment response as JSON and fuse claims together
    # Check for video unavailability markers first
    for t in texts:
        if t and t.startswith("__VIDEO_UNAVAILABLE__:"):
            error_detail = t.replace("__VIDEO_UNAVAILABLE__:", "")
            logger.error(f"❌ Video is unavailable or inaccessible: {error_detail}")
            return {
                "error": f"YouTube video is unavailable, private, deleted, or not accessible. The video cannot be analyzed. Details: {error_detail}",
                "initial_report": "",
                "claims": [],
            }
    
    if not texts or not any(t.strip() for t in texts):
        return {
            "error": "Empty response from segmented Vertex YouTube analysis - the video may be unavailable or too short",
            "initial_report": "",
            "claims": [],
        }

    try:
        return fuse_segmented_json_responses(
            texts, video_id, logging.getLogger(__name__)
        )
    except Exception as e:
        logger.error(f"Failed to fuse segmented outputs: {e}")
        return {
            "error": "Failed to parse segmented output",
            "initial_report": "",
            "claims": [],
        }


async def extract_claims_with_gemini_multimodal(
    video_url: str, video_id: str, video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract claims using Gemini multimodal analysis with downloaded video file."""
    from langchain_google_vertexai import ChatVertexAI
    from langchain_core.messages import HumanMessage

    from verityngn.services.storage.gcs_storage import upload_to_gcs
    import logging
    import tempfile
    import os

    logger = logging.getLogger(__name__)
    logger.info(f"🤖 Starting Gemini multimodal analysis for video {video_id}")

    try:
        # Calculate target claims based on video duration (3 claims per minute)
        video_duration = video_info.get("duration", 0) if video_info else 0
        if video_duration > 0:
            video_duration_minutes = video_duration / 60
            # For first hour analysis, cap at 60 minutes for claim calculation
            analysis_duration_minutes = min(
                video_duration_minutes, 60
            )  # Max 60 min since we analyze first hour
            target_claims = max(
                8, min(15, int(analysis_duration_minutes * 1.8))
            )  # 1.8 claims/min to ensure mix of speaker+content claims, 8-15 range
            logger.info(
                f"📊 Video duration: {video_duration_minutes:.1f} minutes, analyzing first {analysis_duration_minutes:.1f} minutes, targeting {target_claims} claims"
            )
        else:
            target_claims = 12  # Fallback when duration unknown
            video_duration_minutes = 4.0  # Assume 4 minutes
            logger.warning("Video duration unknown, using fallback of 12 claims")

        # Download and trim video for multimodal analysis
        logger.info("🎥 Downloading and trimming video for multimodal analysis...")
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download original video using robust download function
            download_result = download_video_robust_cloud_config(
                video_url, temp_dir, logger
            )
            video_path = (
                download_result.get("video_path")
                if download_result.get("success")
                else None
            )

            # Check if we have video file OR metadata files (from fallback)
            has_video = video_path and os.path.exists(video_path)
            has_metadata = download_result.get("analysis_files", {}).get("info_json")

            if not has_video and not has_metadata:
                logger.error(
                    "Failed to download video or extract metadata for multimodal analysis"
                )
                # Fall back to text-only analysis
                return await extract_claims_fallback_text_only(
                    video_url, video_id, video_info, logger
                )
            elif not has_video:
                logger.info(
                    "📄 No video file but metadata available - using YouTube URL analysis with genai client"
                )
                # Skip video processing and go directly to YouTube URL analysis
            else:
                # We have video - process it normally
                # Trim video to optimize for Gemini analysis (5 minutes max)
                trimmed_video_path = trim_video_for_analysis(
                    video_path, max_duration=300
                )  # 5 minutes for Cloud Run
                if not trimmed_video_path or not os.path.exists(trimmed_video_path):
                    logger.error("Failed to trim video for multimodal analysis")
                    return await extract_claims_fallback_text_only(
                        video_url, video_id, video_info, logger
                    )

                # Upload trimmed video to GCS
                gcs_path = f"tmp/analysis/{video_id}/trimmed_video.mp4"
                try:
                    gcs_uri = upload_to_gcs(trimmed_video_path, gcs_path)
                    logger.info(f"✅ Video uploaded to GCS: {gcs_uri}")
                except Exception as e:
                    logger.error(f"Failed to upload video to GCS: {e}")
                    return await extract_claims_fallback_text_only(
                        video_url, video_id, video_info, logger
                    )

                # Create multimodal prompt with dynamic claim count
                prompt_text = f"""
                Analyze this YouTube video and extract specific, verifiable claims made in the content.
                
                Video ID: {video_id}
                Video URL: {video_url}
                Video Title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}
                Video Duration: {video_duration_minutes:.1f} minutes (estimated)
                
                Instructions:
                1. Watch/analyze the video content carefully
                2. Extract the {target_claims} MOST IMPORTANT and verifiable claims, MANDATORY MIX:
                   
                   **REQUIRED SPEAKER CREDIBILITY CLAIMS (minimum 2-3 claims):**
                   - Dr. Julian Ross worked at/studied at [institution]
                   - Dr. Julian Ross has [years] of experience in [field]
                   - Dr. Julian Ross received award/recognition from [organization]
                   - Dr. Julian Ross authored/published [research/book]
                   - Dr. Julian Ross founded/directed [organization/clinic]
                   
                   **CONTENT CLAIMS (remaining claims):**
                   - Study results, product claims, statistics, outcomes
                
                3. Focus on claims that can be verified through external sources
                4. Include timestamps where possible
                5. Speaker credibility claims are ESSENTIAL for truthfulness analysis - without them, content claims are meaningless
                
                Return as JSON:
                {{
                    "initial_report": "Brief summary of video content and analysis approach",
                    "claims": [
                        {{
                            "claim_text": "Specific claim extracted from video",
                            "timestamp": "MM:SS or time range", 
                            "speaker": "Who made the claim",
                            "initial_assessment": "Brief assessment of claim"
                        }}
                    ]
                }}
                """

                # Vertex-only mode: skip AI Studio genai video path
                logger.info(
                    "🎯 Skipping AI Studio genai uploaded-video path (Vertex-only)"
                )

            # If we reach here, either we don't have video OR the video analysis failed
            # Use YouTube URL analysis with genai client
            logger.info(f"🎯 Using YouTube URL analysis with genai client")

            # Create multimodal prompt for YouTube URL analysis
            prompt_text = f"""
            Analyze this YouTube video and extract specific, verifiable claims made in the content.
            
            Video ID: {video_id}
            Video URL: {video_url}
            Video Title: {video_info.get('title', 'Unknown') if video_info else 'Unknown'}
            Video Duration: {video_duration_minutes:.1f} minutes (estimated)
            
            Instructions:
            1. Watch/analyze the video content carefully
            2. Extract EXACTLY {target_claims} factual claims made by speakers or shown visually (targeting 3 claims per minute)
            3. Focus on claims that can be verified through external sources
            4. Include timestamps where possible
            5. Prioritize the most significant and verifiable claims
            
            Return as JSON:
            {{
                "initial_report": "Brief summary of video content and analysis approach",
                "claims": [
                    {{
                        "claim_text": "Specific claim extracted from video",
                        "timestamp": "MM:SS or time range", 
                        "speaker": "Who made the claim",
                        "initial_assessment": "Brief assessment of claim"
                    }}
                ]
            }}
            """

            # GenAI YouTube URL analysis path removed; Vertex-only flow proceeds via fallback paths

    except Exception as e:
        logger.error(f"❌ Gemini multimodal analysis failed: {e}")
        # Fall back to text-only analysis
        return await extract_claims_fallback_text_only(
            video_url, video_id, video_info, logger
        )


async def extract_claims_fallback_text_only(
    video_url: str, video_id: str, video_info: Dict[str, Any], logger
) -> Dict[str, Any]:
    """Fallback to text-only analysis when multimodal analysis fails."""
    logger.info(f"🔄 Falling back to text-only analysis for video {video_id}")

    try:
        from langchain_google_vertexai import ChatVertexAI

        # Create Gemini LLM
        llm = ChatVertexAI(
            model_name=AGENT_MODEL_NAME,
            max_output_tokens=MAX_OUTPUT_TOKENS_2_5_FLASH,  # Increased for Gemini 2.5 Flash (supports up to 65K)
            temperature=0.2,  # Lower temperature for more factual responses
            top_p=0.95,
            top_k=40,
            verbose=True,  # Help with debugging
            streaming=False,  # Disable streaming to prevent "No generations found in stream" errors
        )

        # Get video metadata and transcript if available
        video_title = video_info.get("title", "Unknown") if video_info else "Unknown"
        video_description = video_info.get("description", "") if video_info else ""

        # Calculate target claims
        video_duration = video_info.get("duration", 0) if video_info else 0
        if video_duration > 0:
            video_duration_minutes = video_duration / 60
            target_claims = max(5, min(25, int(video_duration_minutes * 3)))
        else:
            target_claims = 12
            video_duration_minutes = 4.0

        # Create text-only prompt
        prompt_text = f"""
        Analyze this YouTube video based on metadata and extract verifiable claims.
        
        Video ID: {video_id}
        Video URL: {video_url}
        Video Title: {video_title}
        Video Description: {video_description[:1000]}...
        Video Duration: {video_duration_minutes:.1f} minutes
        
        Based on the title and description, infer likely claims that would be made in this video.
        Extract EXACTLY {target_claims} potential factual claims.
        
        Return as JSON:
        {{
            "initial_report": "Analysis based on video metadata and description",
            "claims": [
                {{
                    "claim_text": "Inferred claim from title/description",
                    "timestamp": "N/A (metadata-based)", 
                    "speaker": "Video presenter",
                    "initial_assessment": "Claim inferred from metadata"
                }}
            ]
        }}
        """

        response = await llm.ainvoke([{"type": "text", "text": prompt_text}])

        if response and hasattr(response, "content") and response.content:
            logger.info(
                f"✅ Text-only fallback analysis completed: {len(response.content)} characters"
            )
            return parse_llm_response(response.content, video_id, logger)
        else:
            logger.error("⚠️ Even text-only analysis failed")
            return {
                "error": "All analysis methods failed",
                "initial_report": f"Failed to analyze video {video_id}",
                "claims": [],
            }

    except Exception as e:
        logger.error(f"❌ Text-only fallback analysis failed: {e}")
        return {
            "error": f"Text-only analysis failed: {str(e)}",
            "initial_report": f"Failed to analyze video {video_id}",
            "claims": [],
        }


def extract_claims_with_gemini_multimodal_sync(
    video_url: str, logger: logging.Logger
) -> List[str]:
    """
    Sync wrapper for Gemini multimodal claim extraction.
    Gets video info and calls the async function properly.
    """
    import asyncio
    from verityngn.utils.file_utils import extract_video_id

    try:
        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            logger.error("Could not extract video ID from URL")
            return []

        # Get basic video info for the analysis
        try:
            import yt_dlp

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "ignoreerrors": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(video_url, download=False)

            if not video_info:
                video_info = {
                    "title": f"Video {video_id}",
                    "description": "",
                    "duration": 0,
                    "uploader": "Unknown",
                }
        except Exception as e:
            logger.warning(f"Could not get video info: {e}")
            video_info = {
                "title": f"Video {video_id}",
                "description": "",
                "duration": 0,
                "uploader": "Unknown",
            }

        # Call the async function properly
        logger.info(f"🚀 Calling async Gemini multimodal analysis for {video_id}")

        # Create and run the async function
        async def run_analysis():
            return await extract_claims_with_gemini_multimodal(
                video_url, video_id, video_info
            )

        # Run the async function
        result = asyncio.run(run_analysis())

        # Extract claims from result
        if result and not result.get("error"):
            claims = result.get("claims", [])
            # Convert claim objects to simple strings for compatibility
            claim_texts = []
            for claim in claims:
                if isinstance(claim, dict):
                    claim_texts.append(claim.get("claim_text", str(claim)))
                else:
                    claim_texts.append(str(claim))

            logger.info(f"✅ Extracted {len(claim_texts)} claims via Gemini multimodal")
            return claim_texts
        else:
            error = result.get("error", "Unknown error") if result else "No result"
            logger.error(f"❌ Gemini multimodal analysis failed: {error}")
            return []

    except Exception as e:
        logger.error(f"❌ Sync wrapper failed: {e}")
        return []
