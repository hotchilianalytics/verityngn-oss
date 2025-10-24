import os
import logging
import math
from typing import List, Optional
from moviepy.editor import VideoFileClip

class VideoProcessor:
    """Service for processing videos, including chunking."""
    
    def __init__(self):
        """Initialize the video processor."""
        self.logger = logging.getLogger(__name__)
    
    def split_video_into_chunks(
        self, 
        video_path: str, 
        chunk_duration_minutes: int, 
        output_dir: str,
        video_id: str
    ) -> List[str]:
        """
        Splits a video into chunks of specified duration with overlap.
        
        Args:
            video_path (str): Path to the video file
            chunk_duration_minutes (int): Duration of each chunk in minutes
            output_dir (str): Directory to save the chunks to
            video_id (str): ID of the video
            
        Returns:
            List[str]: List of paths to the chunk files
        """
        if not os.path.exists(video_path):
            self.logger.error(f"Video file not found: {video_path}")
            return []
        
        try:
            video = VideoFileClip(video_path)
            duration = video.duration
            chunk_duration_seconds = chunk_duration_minutes * 60
            overlap_seconds = 10  # 10 seconds overlap between chunks
            
            # If video is shorter than chunk duration, return the original video
            if duration <= chunk_duration_seconds:
                self.logger.info(f"Video is shorter than chunk duration, skipping chunking: {video_path}")
                return [video_path]
            
            # Calculate number of chunks
            num_chunks = math.ceil(duration / (chunk_duration_seconds - overlap_seconds))
            self.logger.info(f"Splitting video into {num_chunks} chunks of {chunk_duration_minutes} minutes each with {overlap_seconds}s overlap")
            
            chunk_files = []
            for i in range(num_chunks):
                start_time = max(0, i * (chunk_duration_seconds - overlap_seconds))
                end_time = min(start_time + chunk_duration_seconds, duration)
                
                chunk_file = os.path.join(output_dir, f"{video_id}_chunk_{i+1:03d}.mp4")
                
                # Skip if chunk already exists
                if os.path.exists(chunk_file):
                    self.logger.info(f"Chunk already exists: {chunk_file}")
                    chunk_files.append(chunk_file)
                    continue
                
                # Extract chunk
                chunk = video.subclip(start_time, end_time)
                chunk.write_videofile(
                    chunk_file,
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile=os.path.join(output_dir, f"temp_audio_{i}.m4a"),
                    remove_temp=True,
                    threads=4,
                    preset="ultrafast"
                )
                
                chunk_files.append(chunk_file)
                self.logger.info(f"Created chunk {i+1}/{num_chunks}: {chunk_file} ({start_time:.2f}s to {end_time:.2f}s)")
            
            video.close()
            return chunk_files
            
        except Exception as e:
            self.logger.error(f"Error splitting video into chunks: {e}")
            return []
    
    def extract_audio(self, video_path: str, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Extracts audio from a video file.
        
        Args:
            video_path (str): Path to the video file
            output_dir (Optional[str]): Directory to save the audio file to
            
        Returns:
            Optional[str]: Path to the audio file, or None if extraction failed
        """
        if not os.path.exists(video_path):
            self.logger.error(f"Video file not found: {video_path}")
            return None
        
        try:
            video = VideoFileClip(video_path)
            
            # Determine output directory
            if output_dir is None:
                output_dir = os.path.dirname(video_path)
            
            # Create output filename
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(output_dir, f"{base_name}.mp3")
            
            # Skip if audio file already exists
            if os.path.exists(audio_path):
                self.logger.info(f"Audio file already exists: {audio_path}")
                return audio_path
            
            # Extract audio
            video.audio.write_audiofile(audio_path, codec="mp3")
            video.close()
            
            self.logger.info(f"Extracted audio to: {audio_path}")
            return audio_path
            
        except Exception as e:
            self.logger.error(f"Error extracting audio: {e}")
            return None 