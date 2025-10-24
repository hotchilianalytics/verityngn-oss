import logging
import os
import json
import re
from typing import Optional, Dict, Any, List
import yt_dlp

from verityngn.services.video.downloader import extract_audio
from verityngn.config.settings import DEFAULT_CHUNK_DURATION

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    
    try:
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        log_file = os.path.join(log_dir, 'transcription.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        # If we can't create the log file, continue without file logging
        pass
    
    # Always add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def get_video_transcript(video_path: str, chunk_duration: int = DEFAULT_CHUNK_DURATION) -> str:
    """
    Get the transcript of a video from YouTube metadata.
    
    Args:
        video_path (str): Path to the video file
        chunk_duration (int): Duration of each chunk in seconds
        
    Returns:
        str: Transcript of the video
    """
    logger.info(f"Getting transcript for video: {video_path}")
    
    try:
        # Extract video ID from the path
        video_id_match = re.search(r'([a-zA-Z0-9_-]{11})\.mp4$', video_path)
        if not video_id_match:
            logger.error(f"Could not extract video ID from path: {video_path}")
            return ""
            
        video_id = video_id_match.group(1)
        
        # Get the directory containing the video
        video_dir = os.path.dirname(video_path)
        
        # Check if transcript JSON file exists
        transcript_file_path = os.path.join(video_dir, f"{video_id}.transcript.json")

        # Check if transcript en.vtt file exists
        vtt_file_path = os.path.join(video_dir, f"{video_id}.en.vtt")
        
        if os.path.exists(vtt_file_path):
            logger.info(f"Found vtt file: {vtt_file_path}")
            try:
                with open(vtt_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove VTT header and timestamps
                    lines = content.split('\n')
                    text_lines = []
                    skip_next = False
                    for line in lines:
                        if skip_next:
                            skip_next = False
                            continue
                        if '-->' in line:
                            skip_next = True
                            continue
                        if line.strip() and not line.startswith('WEBVTT'):
                            text_lines.append(line.strip())

                    return ' '.join(text_lines)
            except Exception as e:
                logger.error(f"Error reading VTT file: {e}")
        else:
            logger.warning(f"No vtt file found at: {vtt_file_path}")

        # Try youtube djson file of all transcripts.
        if os.path.exists(transcript_file_path):
            logger.info(f"Found transcript file: {transcript_file_path}")
            return extract_transcript_from_json(transcript_file_path)
        else:
            logger.warning(f"No transcript file found at: {transcript_file_path}")
            
            # Try to download transcript directly
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            logger.info(f"Attempting to download transcript for: {video_url}")
            
            transcript_data = download_transcript(video_url, video_dir, video_id)
            if transcript_data:
                return extract_transcript_from_json(transcript_file_path)
        
        logger.error("Failed to get transcript")
        return ""
        
    except Exception as e:
      logger.error(f"Error getting video transcript: {e}")
    return ""

def download_transcript(video_url: str, output_dir: str, video_id: str) -> Dict:
    """
    Download transcript data for a YouTube video.
    
    Args:
        video_url (str): YouTube video URL
        output_dir (str): Directory to save the transcript
        video_id (str): YouTube video ID
        
    Returns:
        Dict: Transcript data
    """
    logger.info(f"Downloading transcript for video: {video_url}")
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'subtitleslangs': ['en'],
        'writeautomaticsub': True,
        'allsubtitles': False,
        'outtmpl': os.path.join(output_dir, f'{video_id}.%(ext)s'),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=False)
            
            transcript_data = {}
            if 'subtitles' in info_dict and info_dict['subtitles']:
                transcript_data['subtitles'] = info_dict['subtitles']
            if 'automatic_captions' in info_dict and info_dict['automatic_captions']:
                transcript_data['automatic_captions'] = info_dict['automatic_captions']
            
            if transcript_data:
                transcript_file_path = os.path.join(output_dir, f"{video_id}.transcript.json")
                with open(transcript_file_path, "w", encoding="utf-8") as f:
                    json.dump(transcript_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Transcript data saved to: {transcript_file_path}")
                return transcript_data
            else:
                logger.warning("No transcript data found")
                return {}
    
    except Exception as e:
        logger.error(f"Error downloading transcript: {e}")
        return {}

def extract_transcript_from_json(transcript_file_path: str) -> str:
    """
    Extract transcript text from the JSON file.
    
    Args:
        transcript_file_path (str): Path to the transcript JSON file
        
    Returns:
        str: Extracted transcript text
    """
    logger.info(f"Extracting transcript from: {transcript_file_path}")
    
    try:
        with open(transcript_file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # First try to get manual subtitles
        if 'subtitles' in transcript_data and transcript_data['subtitles'] and 'en' in transcript_data['subtitles']:
            logger.info("Found English subtitles in transcript data")
            subtitle_data = transcript_data['subtitles']['en']
            return extract_text_from_subtitle_data(subtitle_data)
        
        # Fall back to automatic captions
        if 'automatic_captions' in transcript_data and transcript_data['automatic_captions'] and 'en' in transcript_data['automatic_captions']:
            logger.info("Found English automatic captions in transcript data")
            subtitle_data = transcript_data['automatic_captions']['en']
            return extract_text_from_subtitle_data(subtitle_data)
        
        logger.warning("No English subtitles or captions found in transcript data")
        return "No transcript available."
    
    except Exception as e:
        logger.error(f"Error extracting transcript from JSON: {e}")
        return "Error extracting transcript."

def extract_text_from_subtitle_data(subtitle_data: List) -> str:
    """
    Extract text from subtitle data.
    
    Args:
        subtitle_data (List): List of subtitle entries
        
    Returns:
        str: Concatenated transcript text
    """
    try:   
        # Find the most complete format (usually vtt or json3)
        for format_name in ['vtt', 'json3', 'srv1', 'ttml', 'srv2', 'srv3']:
            for item in subtitle_data:
                if item.get('ext') == format_name:
                    # For vtt format, we can read the file directly
                    if format_name == 'vtt' and 'filepath' in item:
                        try:
                            with open(item['filepath'], 'r', encoding='utf-8') as f:
                                content = f.read()
                                # Remove VTT header and timestamps
                                lines = content.split('\n')
                                text_lines = []
                                skip_next = False
                                for line in lines:
                                    if skip_next:
                                        skip_next = False
                                        continue
                                    if '-->' in line:
                                        skip_next = True
                                        continue
                                    if line.strip() and not line.startswith('WEBVTT'):
                                        text_lines.append(line.strip())
                                return ' '.join(text_lines)
                        except Exception as e:
                            logger.error(f"Error reading VTT file: {e}")
                            continue
                    
                    # For other formats, we need to download and parse the subtitle file
                    # This would require additional implementation
                    logger.info(f"Found {format_name} format, but parsing not implemented yet")
                    return f"Transcript available in {format_name} format. Parsing not implemented yet."
        
        # If we can't find a preferred format, just return a placeholder
        return "Transcript available but format not recognized."
    
    except Exception as e:
        logger.error(f"Error extracting text from subtitle data: {e}")
        return ""

def chunk_transcript(transcript: str, chunk_duration: int = DEFAULT_CHUNK_DURATION,
                    timestamps: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Chunk a transcript into smaller pieces.
    
    Args:
        transcript (str): Transcript to chunk
        chunk_duration (int): Duration of each chunk in minutes
        timestamps (Optional[List[Dict[str, Any]]]): Timestamps for the transcript
        
    Returns:
        List[Dict[str, Any]]: Chunked transcript
    """
    logger.info(f"Chunking transcript with chunk duration: {chunk_duration}")
    
    try:
        if not transcript:
            return []
            
        # If no timestamps, split by words
        if not timestamps:
            words = transcript.split()
            total_words = len(words)
            
            # Estimate 150 words per minute for speech
            words_per_chunk = 150 * chunk_duration
            
            num_chunks = max(1, (total_words + words_per_chunk - 1) // words_per_chunk)
            
            chunks = []
            for i in range(num_chunks):
                start_idx = i * words_per_chunk
                end_idx = min(start_idx + words_per_chunk, total_words)
                
                chunk_text = " ".join(words[start_idx:end_idx])
                chunks.append({
                    "text": chunk_text,
                    "start": i * chunk_duration * 60,  # Convert to seconds
                    "end": min((i + 1) * chunk_duration * 60, chunk_duration * num_chunks * 60)  # Convert to seconds
                })
                
            logger.info(f"Transcript chunked into {len(chunks)} chunks")
            return chunks
            
        # If timestamps are provided, use them for chunking
        else:
            chunk_duration_seconds = chunk_duration * 60
            chunks = []
            current_chunk = {"text": "", "start": 0, "end": 0}
            
            for item in timestamps:
                if not current_chunk["text"]:
                    current_chunk["start"] = item["start"]
                    
                current_chunk["text"] += " " + item["text"]
                current_chunk["end"] = item["end"]
                
                if item["end"] - current_chunk["start"] >= chunk_duration_seconds:
                    chunks.append(current_chunk)
                    current_chunk = {"text": "", "start": 0, "end": 0}
                    
            # Add the last chunk if it has content
            if current_chunk["text"]:
                chunks.append(current_chunk)
                
            logger.info(f"Transcript chunked into {len(chunks)} chunks")
            return chunks
            
    except Exception as e:
        logger.error(f"Error chunking transcript: {e}")
        return [{"text": transcript, "start": 0, "end": 0}] 