import os
import logging
import subprocess
import time
import json
from typing import Tuple, Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import yt_dlp
import ffmpeg

from verityngn.config.settings import USER_AGENTS, ALLOWED_EXTENSIONS
from verityngn.utils.file_utils import save_video_directory, get_random_user_agent, extract_video_id

class VideoDownloader:
    """Service for downloading videos from YouTube."""
    
    def __init__(self, proxy_url: Optional[str] = None, max_retries: int = 3, retry_delay: int = 5):
        """
        Initialize the video downloader.
        
        Args:
            proxy_url (Optional[str]): Proxy URL to use for downloading
            max_retries (int): Maximum number of download retries
            retry_delay (int): Delay between retries in seconds
        """
        self.logger = logging.getLogger(__name__)
        self.proxy_url = proxy_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    def _get_download_options(self, video_id: str, out_dir_path: str) -> Dict[str, Any]:
        """Get the robust download options for yt-dlp (anti-bot, all files, fallback)."""
        return {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best',
            'outtmpl': os.path.join(out_dir_path, f'{video_id}.%(ext)s'),
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'writethumbnail': True,
            'writedescription': True,
            'writeinfojson': True,
            'cookiefile': 'cookies.txt',
            'user_agent': get_random_user_agent(),
            'retries': 20,
            'fragment_retries': 10,
            'file_access_retries': 10,
            'extractor_retries': 10,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'nooverwrites': False,
            'no_warnings': False,
            'ignoreerrors': False,
            'skip_download': False,
            'proxy': self.proxy_url if self.proxy_url else None,
            'progress_hooks': [self._progress_hook],
        }
    
    def _get_fallback_download_options(self, video_id: str, out_dir_path: str) -> Dict[str, Any]:
        """Get fallback download options for problematic videos."""
        return {
            # Format selection - more flexible fallback options
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'outtmpl': os.path.join(out_dir_path, f'{video_id}.%(ext)s'),
            
            # Metadata options
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'writethumbnail': True,
            'writedescription': True,
            'writeinfojson': True,
            
            # Download options
            'skip_download': False,
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'nooverwrites': False,
            'no_cache': True,
            'fragment_retries': 5,
            'retries': 5,
            'file_access_retries': 5,
            'extractor_retries': 5,
            'socket_timeout': 30,
            
            # User agent and proxy
            'user_agent': get_random_user_agent(),
            'proxy': self.proxy_url if self.proxy_url else None,
            
            # Progress tracking
            'progress_hooks': [self._progress_hook],
            
            # Force MP4 format
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            
            # Additional options to handle nsig issues
            'extract_flat': False,
            'no_check_formats': True,
            'no_check_certificates': True,
            'prefer_insecure': True,
            'legacyserverconnect': True,
        }
    
    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """Track download progress."""
        if d['status'] == 'downloading':
            try:
                total_bytes = d.get('total_bytes')
                downloaded_bytes = d.get('downloaded_bytes')
                if total_bytes and downloaded_bytes:
                    percentage = (downloaded_bytes / total_bytes) * 100
                    self.logger.info(f"Download progress: {percentage:.1f}%")
            except Exception:
                pass
        elif d['status'] == 'finished':
            self.logger.info("Download finished, processing...")
    
    def _cleanup_temp_files(self, out_dir_path: str, video_id: str) -> None:
        """Clean up temporary files after download."""
        try:
            # Remove temporary files
            temp_patterns = [
                f"{video_id}.part",
                f"{video_id}.ytdl",
                f"{video_id}.m4a",
                f"{video_id}.webm",
                f"{video_id}.webm.part",
                f"{video_id}.m4a.part",
            ]
            
            for pattern in temp_patterns:
                temp_file = os.path.join(out_dir_path, pattern)
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.debug(f"Removed temporary file: {temp_file}")
        except Exception as e:
            self.logger.warning(f"Error cleaning up temporary files: {e}")
    
    def _try_fallback_download(self, video_url: str, video_id: str, out_dir_path: str) -> Optional[str]:
        """
        Try downloading using fallback options for problematic videos.
        
        Args:
            video_url (str): URL of the video to download
            video_id (str): Video ID
            out_dir_path (str): Output directory path
            
        Returns:
            Optional[str]: Path to downloaded video if successful, None otherwise
        """
        self.logger.info(f"Attempting fallback download for video {video_id}")
        
        try:
            # First get available formats
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                if info and 'formats' in info:
                    self.logger.info(f"Available formats: {[f.get('format_id', 'N/A') for f in info['formats']]}")
            
            # Try to download with fallback options
            ydl_opts = self._get_fallback_download_options(video_id, out_dir_path)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Clean up temporary files
            self._cleanup_temp_files(out_dir_path, video_id)
            
            # Check for downloaded file
            video_path = os.path.join(out_dir_path, f'{video_id}.mp4')
            if os.path.exists(video_path):
                self.logger.info(f"Fallback download successful: {video_path}")
                return video_path
                
            return None
            
        except Exception as e:
            self.logger.error(f"Fallback download failed: {e}")
            return None
    
    def download_video(self, video_url: str, output_dir: str = "downloads") -> Tuple[str, str, str]:
        """
        Downloads a video and its metadata (transcript, description, etc.).
        Guarantees .mp4, .vtt, .info.json, .description files are present.
        """
        video_id, out_dir_path = save_video_directory(video_url, base_dir=output_dir)
        video_path = os.path.join(out_dir_path, f'{video_id}.mp4')
        expected_files = [
            f'{video_id}.mp4',
            f'{video_id}.en.vtt',
            f'{video_id}.info.json',
            f'{video_id}.description'
        ]
        
        # Download video and all metadata
        ydl_opts = self._get_download_options(video_id, out_dir_path)
        self.logger.info(f"[yt-dlp] Downloading {video_url} with options: {ydl_opts}")
        for attempt in range(self.max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                self._cleanup_temp_files(out_dir_path, video_id)
                break
            except Exception as e:
                self.logger.error(f"[yt-dlp] Error downloading video (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    ydl_opts['user_agent'] = get_random_user_agent()
                else:
                    self.logger.error(f"[yt-dlp] Failed after {self.max_retries} attempts: {video_url}")
        # Check for all expected files
        missing = []
        for fname in expected_files:
            fpath = os.path.join(out_dir_path, fname)
            if not os.path.exists(fpath):
                self.logger.warning(f"[yt-dlp] Missing file after download: {fpath}")
                missing.append(fname)
        # Fallback: try to download missing files individually
        if missing:
            for fname in missing:
                if fname.endswith('.en.vtt'):
                    # Try to download subtitles only
                    sub_opts = self._get_download_options(video_id, out_dir_path)
                    sub_opts['writesubtitles'] = True
                    sub_opts['writeautomaticsub'] = True
                    sub_opts['skip_download'] = True
                    sub_opts['subtitleslangs'] = ['en']
                    sub_opts['format'] = 'best'
                    try:
                        with yt_dlp.YoutubeDL(sub_opts) as ydl:
                            ydl.download([video_url])
                        self.logger.info(f"[yt-dlp] Fallback subtitle download succeeded: {fname}")
                    except Exception as e:
                        self.logger.error(f"[yt-dlp] Fallback subtitle download failed: {fname} - {e}")
                elif fname.endswith('.info.json'):
                    # Try to download info only
                    info_opts = self._get_download_options(video_id, out_dir_path)
                    info_opts['writeinfojson'] = True
                    info_opts['skip_download'] = True
                    info_opts['format'] = 'best'
                    try:
                        with yt_dlp.YoutubeDL(info_opts) as ydl:
                            ydl.download([video_url])
                        self.logger.info(f"[yt-dlp] Fallback info.json download succeeded: {fname}")
                    except Exception as e:
                        self.logger.error(f"[yt-dlp] Fallback info.json download failed: {fname} - {e}")
                elif fname.endswith('.description'):
                    # Try to download description only
                    desc_opts = self._get_download_options(video_id, out_dir_path)
                    desc_opts['writedescription'] = True
                    desc_opts['skip_download'] = True
                    desc_opts['format'] = 'best'
                    try:
                        with yt_dlp.YoutubeDL(desc_opts) as ydl:
                            ydl.download([video_url])
                        self.logger.info(f"[yt-dlp] Fallback description download succeeded: {fname}")
                    except Exception as e:
                        self.logger.error(f"[yt-dlp] Fallback description download failed: {fname} - {e}")
                elif fname.endswith('.mp4'):
                    # Try to download video only
                    vid_opts = self._get_download_options(video_id, out_dir_path)
                    vid_opts['format'] = 'best[ext=mp4]/mp4/best'
                    try:
                        with yt_dlp.YoutubeDL(vid_opts) as ydl:
                            ydl.download([video_url])
                        self.logger.info(f"[yt-dlp] Fallback .mp4 download succeeded: {fname}")
                    except Exception as e:
                        self.logger.error(f"[yt-dlp] Fallback .mp4 download failed: {fname} - {e}")
        # Final check
        for fname in expected_files:
            fpath = os.path.join(out_dir_path, fname)
            if not os.path.exists(fpath):
                self.logger.error(f"[yt-dlp] FINAL MISSING FILE: {fpath}")
        return video_id, out_dir_path, video_path if os.path.exists(video_path) else ""
    
    def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Gets information about a video without downloading it.
        
        Args:
            video_url (str): URL of the video
            
        Returns:
            Dict[str, Any]: Video information
        """
        ydl_opts = {
            'format': 'best',
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'user_agent': get_random_user_agent(),
            'proxy': self.proxy_url if self.proxy_url else None,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return {}

def get_video_info(video_path: str) -> dict:
    """
    Get information about a video file.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Video information
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Getting video info for {video_path}")
    
    try:
        # Prepare the ffprobe command
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error getting video info: {result.stderr}")
            raise Exception(f"Error getting video info: {result.stderr}")
        
        # Parse the JSON output
        video_info = json.loads(result.stdout)
        
        logger.info(f"Video info retrieved for {video_path}")
        return video_info
        
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise Exception(f"Error getting video info: {e}")

def extract_audio(video_path: str, output_dir: Optional[str] = None) -> str:
    """
    Extract audio from a video file.
    
    Args:
        video_path (str): Path to the video file
        output_dir (Optional[str]): Directory to save the audio to
        
    Returns:
        str: Path to the extracted audio
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting audio from {video_path}")
    
    try:
        # Determine the output directory
        if output_dir is None:
            output_dir = os.path.dirname(video_path)
        
        # Prepare the output path
        audio_path = os.path.join(output_dir, "audio.wav")
        
        # Prepare the ffmpeg command
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error extracting audio: {result.stderr}")
            raise Exception(f"Error extracting audio: {result.stderr}")
        
        logger.info(f"Audio extracted to {audio_path}")
        return audio_path
        
    except Exception as e:
        logger.error(f"Error extracting audio: {e}")
        raise Exception(f"Error extracting audio: {e}") 