import logging
from typing import Dict, Any, Optional
import yt_dlp

logger = logging.getLogger(__name__)

def get_video_info(video_url: str) -> Optional[Dict[str, Any]]:
    """
    Get video information from YouTube.
    
    Args:
        video_url (str): URL of the video
        
    Returns:
        Optional[Dict[str, Any]]: Video information including title, description, etc.
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            if info:
                return {
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),
                    'view_count': info.get('view_count'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                }
            
            logger.warning(f"Could not extract info for video: {video_url}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return None 