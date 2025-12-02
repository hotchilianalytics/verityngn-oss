"""
Video Service Module

This module provides a centralized interface for video operations.
"""
import logging
import os
import json
import tempfile
from typing import Dict, Any, Optional, Tuple
from verityngn.utils.file_utils import extract_video_id, ensure_directory_exists
import yt_dlp
from yt_dlp.utils import DownloadError
from verityngn.config.settings import DOWNLOADS_DIR, USER_AGENTS, GCS_BUCKET_NAME
from verityngn.services.video.downloader import VideoDownloader
from google.cloud import storage
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import functions from individual services
try:
    from verityngn.services.video.info import get_video_info
    from verityngn.services.video.download_video import download_video as new_download_video
    from verityngn.services.video.transcription import get_video_transcript
except ImportError as e:
    logger.error(f"Error importing video services: {e}")
    
    # Define fallback functions if imports fail
    def get_video_info(video_id_or_url: str) -> Optional[Dict[str, Any]]:
        """Get video information from YouTube."""
        logger = logging.getLogger(__name__)
        logger.info(f"Getting video info for: {video_id_or_url}")
        
        # Try different URL formats
        url_formats = [
            video_id_or_url,  # Try original input first
            f"https://youtu.be/{video_id_or_url}",  # Short URL format
            f"https://www.youtube.com/watch?v={video_id_or_url}"  # Standard URL format
        ]
        
        for url in url_formats:
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        logger.info(f"Successfully retrieved video info using URL: {url}")
                        return {
                            'title': info.get('title'),
                            'description': info.get('description'),
                            'duration': info.get('duration'),
                            'view_count': info.get('view_count'),
                            'uploader': info.get('uploader'),
                            'upload_date': info.get('upload_date'),
                        }
            except Exception as e:
                logger.warning(f"Error getting video info with URL {url}: {e}")
                continue
        
        # If all attempts fail, try reading from info.json
        try:
            video_id = video_id_or_url.split('/')[-1].split('?')[0]  # Extract video ID
            info_json_path = os.path.join(DOWNLOADS_DIR, video_id, f"{video_id}.info.json")
            if os.path.exists(info_json_path):
                with open(info_json_path, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    logger.info(f"Retrieved video info from info.json: {info_json_path}")
                    return {
                        'title': info.get('title'),
                        'description': info.get('description'),
                        'duration': info.get('duration'),
                        'view_count': info.get('view_count'),
                        'uploader': info.get('uploader'),
                        'upload_date': info.get('upload_date'),
                    }
        except Exception as e:
            logger.warning(f"Error reading info.json: {e}")
        
        # If all attempts fail, return None instead of fallback values
        logger.error(f"Could not retrieve video info for: {video_id_or_url}")
        return None
        
    def get_video_transcript(*args, **kwargs):
        """Fallback function for get_video_transcript."""
        logger.error("Video transcription service not available. This is a fallback function.")
        return []

# Create a singleton instance of the VideoDownloader
_video_downloader = None

def get_video_downloader(proxy_url: Optional[str] = None) -> VideoDownloader:
    """
    Get or create a VideoDownloader instance.
    
    Args:
        proxy_url (Optional[str]): Proxy URL to use for downloading
        
    Returns:
        VideoDownloader: The video downloader instance
    """
    global _video_downloader
    if _video_downloader is None:
        _video_downloader = VideoDownloader(proxy_url=proxy_url)
    return _video_downloader

def download_video(video_url: str, output_dir: str = "downloads") -> Tuple[str, Dict[str, Any]]:
    """Download a video from YouTube."""
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading video from: {video_url}")
    
    try:
        # Extract video ID first
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {video_url}")
            
        logger.info(f"Extracted video ID: {video_id}")
        
        # Create video-specific output directory
        video_output_dir = os.path.join(output_dir, video_id)
        os.makedirs(video_output_dir, exist_ok=True)
        logger.info(f"Created output directory: {video_output_dir}")
        
        # Configure yt-dlp options with all metadata and ULTRA-ADVANCED bot bypass
        ydl_opts = {
            'format': 'best[ext=mp4]/mp4/best',  # Fallback strategy
            'outtmpl': os.path.join(video_output_dir, '%(id)s.%(ext)s'),
            
            # Subtitle and caption options
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'allsubtitles': False,
            
            # Metadata options - CRITICAL for transcript extraction
            'writeinfojson': True,
            'writethumbnail': True,
            'writedescription': True,
            
            # Network and retry options
            'verbose': True,
            'logger': logger,
            # Use absolute path for cookies.txt (in container it's at /app/cookies.txt)
            'cookiefile': os.path.join(os.getcwd(), 'cookies.txt') if os.path.exists(os.path.join(os.getcwd(), 'cookies.txt')) else (os.path.join('/app', 'cookies.txt') if os.path.exists('/app/cookies.txt') else None),
            'retries': 20,
            'fragment_retries': 20,
            'socket_timeout': 90,
            
            # ULTRA-ADVANCED Anti-bot detection measures
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'sleep_interval': 10,
            'max_sleep_interval': 25,
            'sleep_requests': 2,
            
            # Enhanced HTTP headers to perfectly mimic Chrome browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Cache-Control': 'max-age=0',
            },
            
            # Advanced extractor arguments with multiple client fallbacks
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'web', 'android', 'ios', 'tv_embedded'],
                    'player_skip': ['configs', 'webpage'],
                    'skip': ['hls', 'dash'],
                    'comment_sort': ['top'],
                    'max_comments': ['100'],
                    'innertube_host': ['www.youtube.com'],
                    # innertube_key removed for security - yt-dlp will extract automatically if needed
                    'lang': ['en'],
                    'region': ['US'],
                }
            },
            
            # Advanced retry configuration
            'retry_sleep_functions': {
                'http': lambda n: min(6 * (1.8 ** n), 200),
                'fragment': lambda n: min(6 * (1.8 ** n), 200),
                'extractor': lambda n: min(6 * (2.5 ** n), 200),
            },
            
            # Force IPv4 to avoid IPv6 issues
            'force_ipv4': True,
            
            # Bypass geo-blocking
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            
            # Additional anti-detection measures
            'no_check_certificate': True,
            'prefer_insecure': False,
            'call_home': False,
            'no_color': True,
        }
        
        logger.debug(f"yt-dlp options: {ydl_opts}")
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting video download...")
            try:
                info = ydl.extract_info(video_url, download=True)
                logger.info("Video download completed")
                
                # Log available subtitle formats
                if 'subtitles' in info:
                    logger.info(f"Available subtitle formats: {list(info['subtitles'].keys())}")
                if 'automatic_captions' in info:
                    logger.info(f"Available automatic caption formats: {list(info['automatic_captions'].keys())}")
                
                # Get video path - now in the video-specific directory
                video_path = os.path.join(video_output_dir, f"{video_id}.{info['ext']}")
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"Video file not found at expected path: {video_path}")
                    
                logger.info(f"Video saved to: {video_path}")
                
                # Check for metadata files and log their presence
                info_json_path = os.path.join(video_output_dir, f"{video_id}.info.json")
                vtt_path = os.path.join(video_output_dir, f"{video_id}.en.vtt")
                
                if os.path.exists(info_json_path):
                    logger.info(f"Metadata file saved: {info_json_path}")
                else:
                    logger.warning(f"Metadata file not found: {info_json_path}")
                    
                if os.path.exists(vtt_path):
                    logger.info(f"VTT subtitle file saved: {vtt_path}")
                else:
                    logger.warning(f"VTT subtitle file not found: {vtt_path}")
                
                return video_path, info
                
            except yt_dlp.utils.DownloadError as e:
                logger.warning(f"Error during download: {e}")
                if "Did not get any data blocks" in str(e):
                    logger.info("Retrying without subtitle download...")
                    ydl_opts['writesubtitles'] = False
                    ydl_opts['writeautomaticsub'] = False
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_no_subs:
                        info = ydl_no_subs.extract_info(video_url, download=True)
                        logger.info("Successfully downloaded video without subtitles")
                        video_path = os.path.join(video_output_dir, f"{video_id}.{info['ext']}")
                        
                        # Even without subtitles, we should still have metadata
                        info_json_path = os.path.join(video_output_dir, f"{video_id}.info.json")
                        if os.path.exists(info_json_path):
                            logger.info(f"Metadata file saved (no subtitles): {info_json_path}")
                        
                        return video_path, info
                raise
            
    except Exception as e:
        logger.error(f"Error downloading video: {e}", exc_info=True)
        raise

def upload_to_gcs(local_path: str, gcs_path: str) -> str:
    """
    Upload a file to Google Cloud Storage and generate a signed URL.
    
    Args:
        local_path (str): Path to the local file
        gcs_path (str): Path in GCS where the file should be uploaded
        
    Returns:
        str: Signed URL for accessing the uploaded file
    """
    try:
        # Initialize GCS client
        client = storage.Client()
        
        # Get the bucket
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Create a blob
        blob = bucket.blob(gcs_path)
        
        # Upload the file
        blob.upload_from_filename(local_path)
        
        # Generate a signed URL that expires in 7 days
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=7),
            method="GET"
        )
        
        logger.info(f"File uploaded to GCS with signed URL: {signed_url}")
        return signed_url
        
    except Exception as e:
        logger.error(f"Error uploading to GCS: {e}")
        raise

def get_video_info(video_url: str) -> Optional[dict]:
    """
    Get video information without downloading.
    
    Args:
        video_url (str): URL of the video
        
    Returns:
        Optional[dict]: Video information
    """
    try:
        # Find cookies.txt in common locations
        cookies_path = None
        for path in [os.path.join(os.getcwd(), 'cookies.txt'), '/app/cookies.txt', 'cookies.txt']:
            if os.path.exists(path):
                cookies_path = path
                break
        
        ydl_opts = {
            'quiet': False,  # Enable verbose for debugging
            'no_warnings': False,
            'cookiefile': cookies_path if cookies_path else None,
            
            # ULTRA-ADVANCED anti-bot detection measures
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'sleep_interval': 12,
            'max_sleep_interval': 30,
            'sleep_requests': 3,
            
            # Enhanced HTTP headers to perfectly mimic Chrome browser
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Cache-Control': 'max-age=0',
            },
            
            # Advanced extractor arguments with multiple client fallbacks
            'extractor_args': {
                'youtube': {
                    'player_client': ['mweb', 'web', 'android', 'ios', 'tv_embedded'],
                    'player_skip': ['configs', 'webpage'],
                    'skip': ['hls', 'dash'],
                    'lang': ['en'],
                    'region': ['US'],
                }
            },
            
            # Network options
            'socket_timeout': 120,
            'retries': 30,
            'retry_sleep_functions': {
                'http': lambda n: min(8 * (2 ** n), 300),
                'extractor': lambda n: min(8 * (3 ** n), 300),
            },
            
            # Force IPv4 to avoid IPv6 issues
            'force_ipv4': True,
            
            # Bypass geo-blocking
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            
            # Additional anti-detection measures
            'no_check_certificate': True,
            'prefer_insecure': False,
            'call_home': False,
            'no_color': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None 

# Simple metadata/subtitle fetch using yt-dlp without complex headers/cookies
def fetch_youtube_info_and_subs_simple(video_url: str, out_dir: str, logger_in: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """Fetch info.json and English auto-captions (.vtt) using yt_dlp with minimal config.
    Returns dict: { 'info_json_path': str|None, 'subtitle_path': str|None, 'info': dict }
    """
    log = logger_in or logging.getLogger(__name__)
    try:
        os.makedirs(out_dir, exist_ok=True)
        ydl_opts = {
            'skip_download': True,
            'writeinfojson': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'outtmpl': os.path.join(out_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'force_ipv4': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # ensure writing
            ydl.process_info(info)
            vid = info.get('id') or extract_video_id(video_url)
            info_path = os.path.join(out_dir, f"{vid}.info.json") if vid else None
            vtt_path = os.path.join(out_dir, f"{vid}.en.vtt") if vid else None
            parsed = {}
            if info_path and os.path.exists(info_path):
                with open(info_path, 'r', encoding='utf-8') as f:
                    parsed = json.load(f)
            log.info(f"[yt-dlp simple] info_json={bool(info_path and os.path.exists(info_path))} subs={bool(vtt_path and os.path.exists(vtt_path))}")
            return {
                'info_json_path': info_path if (info_path and os.path.exists(info_path)) else None,
                'subtitle_path': vtt_path if (vtt_path and os.path.exists(vtt_path)) else None,
                'info': parsed or {},
            }
    except Exception as e:
        log.warning(f"[yt-dlp simple] Failed to fetch info/subs: {e}")
        return {'info_json_path': None, 'subtitle_path': None, 'info': {}}