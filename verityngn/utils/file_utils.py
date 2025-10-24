import logging
import os
import re
import random
from typing import Tuple, Optional
from urllib.parse import urlparse, parse_qs

from verityngn.config.settings import USER_AGENTS

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): Filename to sanitize
        
    Returns:
        str: Sanitized filename
    """
    # Replace invalid characters with underscores
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def save_video_directory(video_url: str, base_dir: str) -> Tuple[str, str]:
    """
    Parse a YouTube link, extract the video ID, and create a directory for saving the video.
    
    Args:
        video_url (str): URL of the video
        base_dir (str): Base directory for saving videos
        
    Returns:
        Tuple[str, str]: Video ID and output directory path
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Creating directory for video: {video_url}")
    
    try:
        # Extract video ID from URL
        video_id = extract_video_id(video_url)
        
        if not video_id:
            logger.error(f"Could not extract video ID from URL: {video_url}")
            raise ValueError(f"Could not extract video ID from URL: {video_url}")
            
        # Create output directory
        out_dir_path = os.path.join(base_dir, video_id)
        ensure_directory_exists(out_dir_path)
        
        logger.info(f"Video directory created: {out_dir_path}")
        return video_id, out_dir_path
        
    except Exception as e:
        logger.error(f"Error creating video directory: {e}")
        raise Exception(f"Error creating video directory: {e}")

def extract_video_id(video_url: str) -> Optional[str]:
    """
    Extract the video ID from a YouTube URL.
    
    Args:
        video_url (str): URL of the video
        
    Returns:
        Optional[str]: Video ID or None if not found
    """
    try:
        # Parse the URL
        parsed_url = urlparse(video_url)
        
        # YouTube video URLs can be in different formats
        if parsed_url.netloc == 'youtu.be':
            # Short URL format: https://youtu.be/VIDEO_ID
            return parsed_url.path.lstrip('/')
            
        elif parsed_url.netloc in ('www.youtube.com', 'youtube.com'):
            # Standard URL format: https://www.youtube.com/watch?v=VIDEO_ID
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
                    
            # Embed URL format: https://www.youtube.com/embed/VIDEO_ID
            elif parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
                
            # Shortened URL format: https://www.youtube.com/v/VIDEO_ID
            elif parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
                
        # If we couldn't extract the video ID, return None
        return None
        
    except Exception:
        return None

def get_random_user_agent() -> str:
    """
    Get a random user agent from the list of user agents.
    
    Returns:
        str: Random user agent
    """
    return random.choice(USER_AGENTS)

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path (str): Path to the directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)

def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: File extension
    """
    return os.path.splitext(file_path)[1].lower()

def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(file_path)

def list_files(directory_path: str, extension: Optional[str] = None) -> list:
    """
    List files in a directory, optionally filtered by extension.
    
    Args:
        directory_path (str): Path to the directory
        extension (Optional[str]): File extension to filter by
        
    Returns:
        list: List of file paths
    """
    if not os.path.exists(directory_path):
        return []
        
    files = []
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        if os.path.isfile(file_path):
            if extension is None or file.endswith(extension):
                files.append(file_path)
                
    return files 