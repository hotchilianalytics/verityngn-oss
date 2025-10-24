import os
import logging
import json
import urllib.request
import urllib.error
from typing import Optional, Tuple, Dict
import yt_dlp
from pathlib import Path
import subprocess
import random

# Configure logging
logger = logging.getLogger(__name__)

# List of user agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
]

def get_random_headers():
    """Return a dictionary of headers with a random user agent."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

def download_vtt_fallback(info_json_path: str, vtt_output_path: str):
    """Attempt to download VTT from URL found in .info.json."""
    logger.info(f"Attempting VTT fallback using {info_json_path}")
    try:
        with open(info_json_path, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
        
        sub_url = None
        # Check both automatic and manual subtitles for English VTT
        caption_sources = [info_data.get('automatic_captions', {}), info_data.get('subtitles', {})]
        
        for source in caption_sources:
            if 'en' in source:
                for format_info in source['en']:
                    logger.debug(f"Found subtitle format: {format_info}")
                    if format_info.get('ext') == 'vtt' and 'url' in format_info:
                        sub_url = format_info['url']
                        logger.info(f"Found VTT URL in info.json: {sub_url[:80]}...")
                        break # Found it
                if sub_url: break # Found it in this source
        
        if not sub_url:
            logger.warning("Could not find English VTT URL in .info.json")
            return False

        # Download the VTT content with headers
        logger.info(f"Downloading VTT from URL...")
        try:
            req = urllib.request.Request(sub_url, headers=get_random_headers())
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    vtt_content = response.read().decode('utf-8')
                    with open(vtt_output_path, 'w', encoding='utf-8') as f:
                        f.write(vtt_content)
                    logger.info(f"Successfully downloaded VTT to {vtt_output_path}")
                    return True
                else:
                    logger.error(f"Failed to download VTT: HTTP status {response.getcode()}")
                    return False
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            logger.error(f"Error downloading VTT: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error in VTT fallback: {e}")
        return False

def download_video(video_url: str, output_dir: str) -> Tuple[str, Dict]:
    """
    Download video and metadata using yt-dlp, prioritizing the best available 
    format up to 720p.
    
    Args:
        video_url: URL of the video to download
        output_dir: Base directory (e.g., 'verityngn')
        
    Returns:
        Tuple of (video_path, metadata)
    """
    try:
        # Extract video ID first to create the directory
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl_check:
            info_dict = ydl_check.extract_info(video_url, download=False)
            video_id = info_dict['id']
        
        # Corrected directory structure: output_dir/video_id
        # Assumes output_dir passed in is the base (e.g., "downloads")
        download_dir = os.path.join(output_dir, video_id)
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"Ensured download directory exists: {download_dir}")
        
        # --- Use the simplified and successful format options --- 
        ydl_opts = {
            # Select best H.264 (avc) video up to 720p + best audio (m4a preferred), 
            # with fallbacks to mp4 container or general best.
            'format': 'bestvideo[height<=720][vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720][vcodec^=avc1][ext=mp4]/best[height<=720][ext=mp4]/best', 
            
            # Output template using the created download_dir
            'outtmpl': os.path.join(download_dir, '%(id)s.%(ext)s'),
            
            # Metadata and subtitles
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'writethumbnail': True,
            'writeinfojson': True,
            
            # Other options
            'noplaylist': True,
            'verbose': False,
            'quiet': False,
            'no_warnings': False,
            'force-overwrites': True,
            'no-check-certificates': True,
            'cookiesfrombrowser': ('chrome', None),
            
            # Add custom headers
            'http_headers': get_random_headers(),
            
            # Retry options
            'retries': 10,
            'fragment_retries': 10,
            'file_access_retries': 10,
            'retry_sleep_functions': {
                'http': lambda n: 5 * (1.5 ** n),
                'fragment': lambda n: 5 * (1.5 ** n),
                'file_access': lambda n: 5 * (1.5 ** n)
            }
        }
        
        logger.info(f"Starting download for video {video_id} with options:")
        logger.info(f"  Format: {ydl_opts['format']}")
        logger.info(f"  Output: {ydl_opts['outtmpl']}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info *and* download
            info = ydl.extract_info(video_url, download=True) 
            # prepare_filename needs the info dict from the *download* call
            video_path = ydl.prepare_filename(info)
            # Ensure the path exists after download attempt
            if not os.path.exists(video_path):
                 # Sometimes prepare_filename gives the template before extension is known
                 # We need to find the actual downloaded file
                 possible_files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if f.startswith(video_id) and not f.endswith(('.vtt', '.json', '.webp', '.jpg', '.description', '.part'))]
                 if possible_files:
                     video_path = possible_files[0]
                     logger.info(f"Confirmed video file exists: {video_path}")
                 else:
                    raise FileNotFoundError(f"Video file for {video_id} not found in {download_dir} after download attempt.")
            else:
                logger.info(f"Video download appears successful: {video_path}")

        # VTT Fallback (can be kept as it relies on info.json)
        info_json_path = os.path.join(download_dir, f"{video_id}.info.json")
        vtt_path = os.path.join(download_dir, f"{video_id}.en.vtt")
        if not os.path.exists(vtt_path) and os.path.exists(info_json_path):
            logger.warning(f"Primary VTT download failed or missing for {video_id}. Attempting fallback.")
            download_vtt_fallback(info_json_path, vtt_path)
        elif not os.path.exists(info_json_path):
             logger.warning(f"Cannot attempt VTT fallback for {video_id} because info.json is missing.")
             
        logger.info(f"Download process complete for video {video_id}.")
        return video_path, info
        
    except yt_dlp.utils.DownloadError as dl_err:
        logger.error(f"yt-dlp specific download error for {video_url}: {dl_err}", exc_info=True)
        raise # Re-raise the specific error
    except Exception as e:
        logger.error(f"Unexpected error downloading video {video_url}: {str(e)}", exc_info=True)
        raise # Re-raise other exceptions

def download_video_by_id(video_id: str, output_dir: str = "downloads") -> Optional[str]:
    """
    Download a video and metadata from YouTube using its ID.
    Args: video_id, output_dir
    Returns: Path to video file or None.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return download_video(video_url, output_dir) 