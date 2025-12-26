"""
Clip Generator Service for Tutorial Video Creation.

This service takes Sherlock analysis results and generates tutorial videos
composed of claim clips with text overlays and explanations.
"""

import os
import re
import json
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

try:
    from moviepy.editor import (
        VideoFileClip,
        TextClip,
        CompositeVideoClip,
        concatenate_videoclips,
        ColorClip,
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from verityngn.utils.file_utils import extract_video_id

logger = logging.getLogger(__name__)

# GCS imports - optional, only needed for --from-gcs
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False


class VerdictType(Enum):
    """Verdict types for claims."""
    TRUE = "TRUE"
    LIKELY_TRUE = "LIKELY_TRUE"
    UNCERTAIN = "UNCERTAIN"
    LIKELY_FALSE = "LIKELY_FALSE"
    FALSE = "FALSE"


@dataclass
class ClipConfig:
    """Configuration for clip generation."""
    clip_duration: float = 12.0  # seconds
    padding_before: float = 2.0  # seconds before timestamp
    padding_after: float = 10.0  # seconds after timestamp
    overlay_font_size: int = 24
    overlay_font: str = "Arial-Bold"
    overlay_color: str = "white"
    overlay_bg_opacity: float = 0.7
    transition_duration: float = 0.5
    intro_duration: float = 5.0
    output_fps: int = 24
    output_codec: str = "libx264"
    output_audio_codec: str = "aac"


@dataclass 
class ClaimClip:
    """Represents an extracted claim clip with metadata."""
    claim_id: int
    claim_text: str
    timestamp_str: str
    start_seconds: float
    end_seconds: float
    speaker: str
    verdict: str
    false_probability: float
    clip_path: Optional[str] = None


class ClipGenerator:
    """
    Service for generating tutorial videos from Sherlock analysis results.
    
    Features:
    - Locate or download source videos
    - Parse various timestamp formats
    - Rank claims by severity (FALSE probability)
    - Extract individual claim clips
    - Add text overlays with claim and verdict
    - Compose tutorial videos with transitions
    """
    
    def __init__(self, config: Optional[ClipConfig] = None):
        """Initialize the ClipGenerator with optional configuration."""
        self.config = config or ClipConfig()
        self.logger = logging.getLogger(__name__)
        
        if not MOVIEPY_AVAILABLE:
            self.logger.warning(
                "moviepy not available. Install with: pip install moviepy"
            )
    
    # =========================================================================
    # Video Locator
    # =========================================================================
    
    def locate_video(self, video_id: str, base_dirs: Optional[List[str]] = None) -> Optional[str]:
        """
        Locate an existing video file by video ID.
        
        Args:
            video_id: YouTube video ID
            base_dirs: Optional list of base directories to search
            
        Returns:
            Path to video file if found, None otherwise
        """
        if base_dirs is None:
            base_dirs = [
                ".",
                "downloads",
                "outputs",
                f"sherlock_analysis_{video_id}",
            ]
        
        # Common video file patterns
        patterns = [
            f"{video_id}.mp4",
            f"{video_id}.webm",
            f"{video_id}.mkv",
            f"analysis/{video_id}.mp4",
            f"{video_id}/analysis/{video_id}.mp4",
            f"vngn_reports/{video_id}/analysis/{video_id}.mp4",
        ]
        
        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                continue
                
            for pattern in patterns:
                path = os.path.join(base_dir, pattern)
                if os.path.exists(path):
                    self.logger.info(f"Found video at: {path}")
                    return path
                    
            # Also search recursively for the video file
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.startswith(video_id) and file.endswith(('.mp4', '.webm', '.mkv')):
                        path = os.path.join(root, file)
                        self.logger.info(f"Found video at: {path}")
                        return path
        
        self.logger.warning(f"Video not found for ID: {video_id}")
        return None
    
    def download_video(self, video_url: str, output_dir: str = "downloads") -> Optional[str]:
        """
        Download a video using yt-dlp.
        
        Args:
            video_url: YouTube video URL
            output_dir: Directory to save the video
            
        Returns:
            Path to downloaded video file
        """
        try:
            import yt_dlp
            
            video_id = extract_video_id(video_url)
            if not video_id:
                self.logger.error(f"Could not extract video ID from URL: {video_url}")
                return None
            
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{video_id}.mp4")
            
            if os.path.exists(output_path):
                self.logger.info(f"Video already exists: {output_path}")
                return output_path
            
            ydl_opts = {
                # More flexible format selection that works with most videos
                'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                'outtmpl': os.path.join(output_dir, f'{video_id}.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': True,
                'ignoreerrors': False,
                'retries': 3,
                'fragment_retries': 3,
            }
            
            self.logger.info(f"Downloading video: {video_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            if os.path.exists(output_path):
                self.logger.info(f"Video downloaded to: {output_path}")
                return output_path
            
            # Check for other extensions
            for ext in ['webm', 'mkv']:
                alt_path = os.path.join(output_dir, f"{video_id}.{ext}")
                if os.path.exists(alt_path):
                    return alt_path
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading video: {e}")
            return None
    
    def locate_or_download_video(
        self, 
        video_id: str, 
        video_url: Optional[str] = None,
        download_dir: str = "downloads"
    ) -> Optional[str]:
        """
        Locate an existing video or download it if not found.
        
        Args:
            video_id: YouTube video ID
            video_url: Optional YouTube URL for downloading
            download_dir: Directory for downloads
            
        Returns:
            Path to video file
        """
        # First try to locate existing video
        video_path = self.locate_video(video_id)
        if video_path:
            return video_path
        
        # If not found and URL provided, download it
        if video_url:
            return self.download_video(video_url, download_dir)
        
        # Try constructing URL from video ID
        default_url = f"https://www.youtube.com/watch?v={video_id}"
        return self.download_video(default_url, download_dir)
    
    # =========================================================================
    # Timestamp Parser
    # =========================================================================
    
    def parse_timestamp(self, timestamp_str: str) -> Tuple[float, Optional[float]]:
        """
        Parse various timestamp formats into seconds.
        
        Handles formats like:
        - "00:25" -> (25.0, None)
        - "1:35" -> (95.0, None)
        - "00:25-00:35" -> (25.0, 35.0)
        - "01:35-01:4" -> (95.0, 100.0) [truncated format]
        - "01:35-01:45" -> (95.0, 105.0)
        
        Args:
            timestamp_str: Timestamp string in various formats
            
        Returns:
            Tuple of (start_seconds, end_seconds) where end may be None
        """
        if not timestamp_str:
            return (0.0, None)
        
        # Clean up the string
        timestamp_str = timestamp_str.strip()
        
        def parse_single_timestamp(ts: str) -> float:
            """Parse a single MM:SS or HH:MM:SS timestamp."""
            ts = ts.strip()
            parts = ts.split(':')
            
            try:
                if len(parts) == 1:
                    # Just seconds
                    return float(parts[0])
                elif len(parts) == 2:
                    # MM:SS
                    minutes = int(parts[0])
                    # Handle truncated seconds like "4" instead of "45"
                    seconds_str = parts[1]
                    if len(seconds_str) == 1:
                        # Truncated - assume it's the first digit of seconds
                        seconds = int(seconds_str) * 10
                    else:
                        seconds = float(seconds_str)
                    return minutes * 60 + seconds
                elif len(parts) == 3:
                    # HH:MM:SS
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    return hours * 3600 + minutes * 60 + seconds
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Could not parse timestamp '{ts}': {e}")
            
            return 0.0
        
        # Check for range format (start-end)
        if '-' in timestamp_str:
            parts = timestamp_str.split('-')
            if len(parts) == 2:
                start = parse_single_timestamp(parts[0])
                end = parse_single_timestamp(parts[1])
                return (start, end if end > start else None)
        
        # Single timestamp
        return (parse_single_timestamp(timestamp_str), None)
    
    # =========================================================================
    # Claim Ranker
    # =========================================================================
    
    def get_false_probability(self, claim: Dict[str, Any]) -> float:
        """
        Extract the FALSE probability from a claim.
        
        Args:
            claim: Claim dictionary with verification results
            
        Returns:
            FALSE probability (0.0 to 1.0)
        """
        # Check nested verification_result first
        verification_result = claim.get('verification_result', {})
        if isinstance(verification_result, dict):
            prob_dist = verification_result.get('probability_distribution', {})
            if prob_dist:
                return prob_dist.get('FALSE', 0.0)
        
        # Check top-level probability_distribution
        prob_dist = claim.get('probability_distribution', {})
        if prob_dist:
            return prob_dist.get('FALSE', 0.0)
        
        # Fallback: infer from result string
        result = None
        if isinstance(verification_result, dict):
            result = verification_result.get('result', '')
        elif isinstance(verification_result, str):
            result = verification_result
        
        result = result or claim.get('initial_assessment', '')
        result = result.upper()
        
        if 'FALSE' in result and 'LIKELY' not in result:
            return 0.9
        elif 'LIKELY_FALSE' in result or 'LIKELY FALSE' in result:
            return 0.7
        elif 'UNCERTAIN' in result:
            return 0.5
        elif 'LIKELY_TRUE' in result or 'LIKELY TRUE' in result:
            return 0.3
        elif 'TRUE' in result:
            return 0.1
        
        return 0.5  # Default uncertain
    
    def get_verdict(self, claim: Dict[str, Any]) -> str:
        """
        Extract the verdict string from a claim.
        
        Args:
            claim: Claim dictionary
            
        Returns:
            Verdict string
        """
        verification_result = claim.get('verification_result', {})
        if isinstance(verification_result, dict):
            result = verification_result.get('result', '')
            if result:
                return result
        
        return claim.get('initial_assessment', 'UNCERTAIN')
    
    def rank_claims_by_severity(
        self, 
        claims: List[Dict[str, Any]], 
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Rank claims by their FALSE probability (severity).
        
        Args:
            claims: List of claim dictionaries
            ascending: If True, sort least false first (for "best" claims)
            
        Returns:
            Sorted list of claims
        """
        ranked = sorted(
            claims,
            key=lambda c: self.get_false_probability(c),
            reverse=not ascending
        )
        
        self.logger.info(
            f"Ranked {len(ranked)} claims by severity "
            f"({'ascending' if ascending else 'descending'})"
        )
        
        return ranked
    
    def select_claims_for_tutorial(
        self,
        claims: List[Dict[str, Any]],
        top_n_worst: int = 5,
        top_n_best: int = 0,
        include_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Select claims for the tutorial based on criteria.
        
        Args:
            claims: All claims from analysis
            top_n_worst: Number of worst (most false) claims to include
            top_n_best: Number of best (most true) claims to include
            include_all: If True, include all claims
            
        Returns:
            Selected claims in order for tutorial
        """
        if include_all:
            return claims
        
        selected = []
        
        # Get worst claims (highest FALSE probability)
        if top_n_worst > 0:
            worst = self.rank_claims_by_severity(claims, ascending=False)[:top_n_worst]
            selected.extend(worst)
        
        # Get best claims (lowest FALSE probability)
        if top_n_best > 0:
            best = self.rank_claims_by_severity(claims, ascending=True)[:top_n_best]
            # Add only if not already in selected
            for claim in best:
                if claim not in selected:
                    selected.append(claim)
        
        self.logger.info(
            f"Selected {len(selected)} claims for tutorial "
            f"(worst: {top_n_worst}, best: {top_n_best})"
        )
        
        return selected
    
    # =========================================================================
    # Clip Extractor
    # =========================================================================
    
    def extract_claim_clip_ffmpeg(
        self,
        video_path: str,
        claim: Dict[str, Any],
        output_dir: str,
        claim_index: int
    ) -> Optional[ClaimClip]:
        """
        Extract a clip for a single claim using ffmpeg (fast, no re-encoding).
        
        Args:
            video_path: Path to source video
            claim: Claim dictionary
            output_dir: Directory for output clips
            claim_index: Index of claim for naming
            
        Returns:
            ClaimClip object with clip metadata
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Parse timestamp
        timestamp_str = claim.get('timestamp', '00:00')
        start_ts, end_ts = self.parse_timestamp(timestamp_str)
        
        # Calculate clip boundaries with padding
        clip_start = max(0, start_ts - self.config.padding_before)
        
        if end_ts:
            clip_end = end_ts + self.config.padding_after
        else:
            clip_end = start_ts + self.config.clip_duration
        
        clip_duration = clip_end - clip_start
        
        # Generate output filename
        video_id = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{video_id}_claim_{claim_index:02d}.mp4")
        
        # Extract clip using ffmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-ss", str(clip_start),
            "-i", video_path,
            "-t", str(clip_duration),
            "-c", "copy",  # Copy without re-encoding for speed
            "-avoid_negative_ts", "make_zero",
            output_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"ffmpeg error: {result.stderr}")
                return None
            
            if not os.path.exists(output_path):
                self.logger.error(f"Output clip not created: {output_path}")
                return None
            
            self.logger.info(
                f"Extracted clip {claim_index}: {clip_start:.1f}s - {clip_end:.1f}s -> {output_path}"
            )
            
            return ClaimClip(
                claim_id=claim.get('claim_id', claim_index),
                claim_text=claim.get('claim_text', ''),
                timestamp_str=timestamp_str,
                start_seconds=clip_start,
                end_seconds=clip_end,
                speaker=claim.get('speaker', 'Unknown'),
                verdict=self.get_verdict(claim),
                false_probability=self.get_false_probability(claim),
                clip_path=output_path
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting clip: {e}")
            return None
    
    def extract_all_claim_clips(
        self,
        video_path: str,
        claims: List[Dict[str, Any]],
        output_dir: str
    ) -> List[ClaimClip]:
        """
        Extract clips for all selected claims.
        
        Args:
            video_path: Path to source video
            claims: List of claims to extract
            output_dir: Directory for output clips
            
        Returns:
            List of ClaimClip objects
        """
        clips = []
        
        for i, claim in enumerate(claims):
            clip = self.extract_claim_clip_ffmpeg(video_path, claim, output_dir, i)
            if clip:
                clips.append(clip)
        
        self.logger.info(f"Extracted {len(clips)} claim clips")
        return clips
    
    # =========================================================================
    # Overlay Generator
    # =========================================================================
    
    def get_verdict_color(self, verdict: str) -> str:
        """Get color for verdict badge."""
        verdict_upper = verdict.upper().replace(' ', '_')
        
        if 'FALSE' in verdict_upper and 'LIKELY' not in verdict_upper:
            return '#e74c3c'  # Red
        elif 'LIKELY_FALSE' in verdict_upper or 'LIKELY FALSE' in verdict_upper:
            return '#e67e22'  # Orange
        elif 'UNCERTAIN' in verdict_upper:
            return '#f1c40f'  # Yellow
        elif 'LIKELY_TRUE' in verdict_upper or 'LIKELY TRUE' in verdict_upper:
            return '#2ecc71'  # Light green
        elif 'TRUE' in verdict_upper:
            return '#27ae60'  # Green
        
        return '#95a5a6'  # Gray default
    
    def add_text_overlay_to_clip(
        self,
        clip_path: str,
        claim_text: str,
        verdict: str,
        output_path: str
    ) -> Optional[str]:
        """
        Add text overlay with claim and verdict to a clip.
        
        The claim text appears in the middle 50% of the clip (starts at 25%, ends at 75%).
        The verdict badge appears for the full duration.
        
        Args:
            clip_path: Path to input clip
            claim_text: Claim text to display
            verdict: Verdict to display
            output_path: Path for output clip with overlay
            
        Returns:
            Path to output clip
        """
        if not MOVIEPY_AVAILABLE:
            self.logger.warning("moviepy not available, skipping overlay")
            return clip_path
        
        try:
            video = VideoFileClip(clip_path)
            
            # Calculate middle 50% timing
            # Overlay appears at 25% and disappears at 75% of clip duration
            overlay_start = video.duration * 0.25
            overlay_duration = video.duration * 0.50
            
            # Truncate claim text if too long
            display_text = claim_text[:120] + "..." if len(claim_text) > 120 else claim_text
            
            # Create semi-transparent background for better readability
            # Position it at the bottom portion of the screen - larger for bigger text
            bg_height = 160
            claim_bg = ColorClip(
                size=(video.w, bg_height),
                color=(0, 0, 0)
            ).set_opacity(0.75).set_position(('center', video.h - bg_height)).set_start(overlay_start).set_duration(overlay_duration)
            
            # Create claim text overlay - LARGER font for clarity in tutorials
            # Appears in middle 50% of clip
            claim_fontsize = 36  # Larger for quick info clips
            claim_txt = TextClip(
                f'"{display_text}"',
                fontsize=claim_fontsize,
                color=self.config.overlay_color,
                font=self.config.overlay_font,
                method='caption',
                size=(video.w - 80, None),
                align='center'
            ).set_position(('center', video.h - bg_height + 20)).set_start(overlay_start).set_duration(overlay_duration)
            
            # Create verdict badge - LARGER and positioned down-right for clarity
            # Moved from (20, 20) to (80, 60) and larger font
            verdict_color = self.get_verdict_color(verdict)
            verdict_fontsize = 42  # Larger for visibility
            verdict_txt = TextClip(
                f"  {verdict.replace('_', ' ')}  ",
                fontsize=verdict_fontsize,
                color='white',
                font=self.config.overlay_font,
                bg_color=verdict_color,
            ).set_position((80, 60)).set_duration(video.duration)
            
            # Composite all layers
            final = CompositeVideoClip([video, verdict_txt, claim_bg, claim_txt])
            
            final.write_videofile(
                output_path,
                codec=self.config.output_codec,
                audio_codec=self.config.output_audio_codec,
                fps=self.config.output_fps,
                preset="medium",
                threads=4
            )
            
            video.close()
            final.close()
            
            self.logger.info(f"Added overlay to clip: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error adding overlay: {e}")
            return clip_path
    
    def add_overlays_to_clips(
        self,
        clips: List[ClaimClip],
        output_dir: str
    ) -> List[ClaimClip]:
        """
        Add overlays to all clips.
        
        Args:
            clips: List of ClaimClip objects
            output_dir: Directory for output clips
            
        Returns:
            Updated list of ClaimClip objects with overlay paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        updated_clips = []
        for clip in clips:
            if not clip.clip_path:
                continue
            
            base_name = os.path.basename(clip.clip_path)
            name, ext = os.path.splitext(base_name)
            output_path = os.path.join(output_dir, f"{name}_overlay{ext}")
            
            result_path = self.add_text_overlay_to_clip(
                clip.clip_path,
                clip.claim_text,
                clip.verdict,
                output_path
            )
            
            if result_path:
                clip.clip_path = result_path
            
            updated_clips.append(clip)
        
        return updated_clips
    
    # =========================================================================
    # Tutorial Composer
    # =========================================================================
    
    def create_intro_card(
        self,
        title: str,
        subtitle: str,
        duration: float,
        size: Tuple[int, int] = (1920, 1080)
    ) -> Optional[Any]:
        """
        Create an intro card clip.
        
        Args:
            title: Main title text
            subtitle: Subtitle text
            duration: Duration in seconds
            size: Video size (width, height)
            
        Returns:
            VideoClip for intro
        """
        if not MOVIEPY_AVAILABLE:
            return None
        
        try:
            # Background
            bg = ColorClip(size=size, color=(26, 26, 26)).set_duration(duration)
            
            # Title
            title_txt = TextClip(
                title,
                fontsize=48,
                color='white',
                font=self.config.overlay_font,
                method='caption',
                size=(size[0] - 100, None),
                align='center'
            ).set_position('center').set_duration(duration)
            
            # Subtitle
            subtitle_txt = TextClip(
                subtitle,
                fontsize=28,
                color='#cccccc',
                font="Arial",
                method='caption',
                size=(size[0] - 100, None),
                align='center'
            ).set_position(('center', size[1] * 0.65)).set_duration(duration)
            
            intro = CompositeVideoClip([bg, title_txt, subtitle_txt])
            return intro
            
        except Exception as e:
            self.logger.error(f"Error creating intro card: {e}")
            return None
    
    def create_claim_transition_card(
        self,
        clip: 'ClaimClip',
        claim_number: int,
        total_claims: int,
        video_id: str,
        video_title: Optional[str],
        duration: float = 3.0,
        size: Tuple[int, int] = (1920, 1080)
    ) -> Optional[Any]:
        """
        Create a transition card before a claim clip with full metadata.
        
        Displays:
        - Video ID/Title
        - Claim number (e.g., "CLAIM 2 of 5")
        - Timestamp
        - Claim text
        - Verdict with color
        - FALSE probability percentage
        
        Args:
            clip: ClaimClip object with metadata
            claim_number: Current claim number (1-indexed)
            total_claims: Total number of claims
            video_id: YouTube video ID
            video_title: Optional video title
            duration: Duration of transition card
            size: Video size (width, height)
            
        Returns:
            VideoClip for transition card
        """
        if not MOVIEPY_AVAILABLE:
            return None
        
        try:
            # Dark background
            bg = ColorClip(size=size, color=(20, 20, 25)).set_duration(duration)
            
            layers = [bg]
            
            # Video ID bar at top
            video_label = f"Video: {video_id}"
            if video_title:
                # Truncate title if too long
                display_title = video_title[:60] + "..." if len(video_title) > 60 else video_title
                video_label = f"{display_title}\n({video_id})"
            
            video_txt = TextClip(
                video_label,
                fontsize=22,
                color='#888888',
                font="Arial",
                method='caption',
                size=(size[0] - 100, None),
                align='center'
            ).set_position(('center', 30)).set_duration(duration)
            layers.append(video_txt)
            
            # Claim number header - large and prominent
            claim_header = f"CLAIM {claim_number} of {total_claims}"
            header_txt = TextClip(
                claim_header,
                fontsize=56,
                color='white',
                font=self.config.overlay_font,
            ).set_position(('center', size[1] * 0.15)).set_duration(duration)
            layers.append(header_txt)
            
            # Timestamp
            timestamp_txt = TextClip(
                f"⏱  {clip.timestamp_str}",
                fontsize=32,
                color='#aaaaaa',
                font="Arial",
            ).set_position(('center', size[1] * 0.28)).set_duration(duration)
            layers.append(timestamp_txt)
            
            # Claim text - centered, wrapped
            display_claim = clip.claim_text[:200] + "..." if len(clip.claim_text) > 200 else clip.claim_text
            claim_txt = TextClip(
                f'"{display_claim}"',
                fontsize=30,
                color='white',
                font="Arial",
                method='caption',
                size=(size[0] - 200, None),
                align='center'
            ).set_position(('center', size[1] * 0.40)).set_duration(duration)
            layers.append(claim_txt)
            
            # Verdict with colored background
            verdict_color = self.get_verdict_color(clip.verdict)
            verdict_display = clip.verdict.replace('_', ' ')
            verdict_txt = TextClip(
                f"  {verdict_display}  ",
                fontsize=36,
                color='white',
                font=self.config.overlay_font,
                bg_color=verdict_color,
            ).set_position(('center', size[1] * 0.65)).set_duration(duration)
            layers.append(verdict_txt)
            
            # FALSE probability percentage
            false_pct = clip.false_probability * 100
            pct_txt = TextClip(
                f"FALSE Probability: {false_pct:.1f}%",
                fontsize=28,
                color='#ff6b6b' if false_pct > 50 else '#aaaaaa',
                font="Arial",
            ).set_position(('center', size[1] * 0.75)).set_duration(duration)
            layers.append(pct_txt)
            
            # Separator line visual (using a thin colored bar)
            separator = ColorClip(
                size=(size[0] - 400, 2), 
                color=(80, 80, 80)
            ).set_position(('center', size[1] * 0.85)).set_duration(duration)
            layers.append(separator)
            
            # "Playing clip..." indicator at bottom
            play_txt = TextClip(
                "▶  Playing clip...",
                fontsize=20,
                color='#666666',
                font="Arial",
            ).set_position(('center', size[1] * 0.90)).set_duration(duration)
            layers.append(play_txt)
            
            transition = CompositeVideoClip(layers)
            return transition
            
        except Exception as e:
            self.logger.error(f"Error creating claim transition card: {e}")
            return None
    
    def compose_tutorial(
        self,
        clips: List[ClaimClip],
        output_path: str,
        title: str = "Video Fact-Check Tutorial",
        subtitle: str = "Claims Analysis by VerityNgn",
        video_id: Optional[str] = None,
        video_title: Optional[str] = None,
        transition_duration: float = 3.0
    ) -> Optional[str]:
        """
        Compose a tutorial video from clips with transition cards.
        
        Each claim is preceded by a transition card showing:
        - Video ID/Title
        - Claim number
        - Timestamp
        - Claim text
        - Verdict
        - FALSE %
        
        Args:
            clips: List of ClaimClip objects
            output_path: Path for output tutorial video
            title: Tutorial title for intro
            subtitle: Tutorial subtitle
            video_id: Video ID for transition cards
            video_title: Video title for transition cards
            transition_duration: Duration of each transition card
            
        Returns:
            Path to composed tutorial video
        """
        if not MOVIEPY_AVAILABLE:
            self.logger.error("moviepy required for tutorial composition")
            return None
        
        if not clips:
            self.logger.error("No clips to compose")
            return None
        
        try:
            video_clips = []
            
            # Load first clip to get dimensions
            first_clip = VideoFileClip(clips[0].clip_path)
            size = (first_clip.w, first_clip.h)
            first_clip.close()
            
            # Create intro
            intro = self.create_intro_card(title, subtitle, self.config.intro_duration, size)
            if intro:
                video_clips.append(intro)
            
            # Load and add claim clips with transition cards
            total_claims = len(clips)
            for i, clip in enumerate(clips):
                if clip.clip_path and os.path.exists(clip.clip_path):
                    # Create transition card before each clip
                    transition = self.create_claim_transition_card(
                        clip=clip,
                        claim_number=i + 1,
                        total_claims=total_claims,
                        video_id=video_id or "Unknown",
                        video_title=video_title,
                        duration=transition_duration,
                        size=size
                    )
                    if transition:
                        video_clips.append(transition)
                    
                    # Add the actual clip
                    video = VideoFileClip(clip.clip_path)
                    video_clips.append(video)
            
            if len(video_clips) <= 1:  # Only intro or nothing
                self.logger.error("No valid clips to compose")
                return None
            
            # Concatenate all clips
            self.logger.info(f"Concatenating {len(video_clips)} segments (intro + {total_claims} transitions + {total_claims} clips)")
            final = concatenate_videoclips(
                video_clips, 
                method="compose",
                transition=None
            )
            
            # Write output
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            final.write_videofile(
                output_path,
                codec=self.config.output_codec,
                audio_codec=self.config.output_audio_codec,
                fps=self.config.output_fps,
                preset="medium",
                threads=4
            )
            
            # Cleanup
            for clip in video_clips:
                clip.close()
            final.close()
            
            self.logger.info(f"Tutorial composed: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error composing tutorial: {e}")
            return None
    
    # =========================================================================
    # Main Pipeline
    # =========================================================================
    
    def generate_tutorial(
        self,
        video_id: str,
        claims: List[Dict[str, Any]],
        output_dir: str,
        video_url: Optional[str] = None,
        title: Optional[str] = None,
        top_n_worst: int = 5,
        top_n_best: int = 0,
        include_all: bool = False,
        add_overlays: bool = True,
        save_individual_clips: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a complete tutorial video from Sherlock analysis.
        
        Args:
            video_id: YouTube video ID
            claims: List of claims from analysis
            output_dir: Directory for all outputs
            video_url: Optional video URL for downloading
            title: Optional video title for intro
            top_n_worst: Number of worst claims to include
            top_n_best: Number of best claims to include
            include_all: Include all claims
            add_overlays: Add text overlays to clips
            save_individual_clips: Save individual claim clips
            
        Returns:
            Dictionary with paths and metadata
        """
        result = {
            "success": False,
            "video_id": video_id,
            "tutorial_path": None,
            "clip_paths": [],
            "metadata": {},
            "error": None
        }
        
        try:
            # Step 1: Locate or download video
            self.logger.info(f"🎬 Locating video: {video_id}")
            video_path = self.locate_or_download_video(video_id, video_url)
            
            if not video_path:
                result["error"] = f"Could not find or download video: {video_id}"
                return result
            
            self.logger.info(f"✅ Video found: {video_path}")
            
            # Step 2: Select claims
            self.logger.info(f"📋 Selecting claims from {len(claims)} total")
            selected_claims = self.select_claims_for_tutorial(
                claims, top_n_worst, top_n_best, include_all
            )
            
            if not selected_claims:
                result["error"] = "No claims selected for tutorial"
                return result
            
            # Step 3: Extract clips
            clips_dir = os.path.join(output_dir, "clips")
            self.logger.info(f"✂️ Extracting {len(selected_claims)} clips")
            clips = self.extract_all_claim_clips(video_path, selected_claims, clips_dir)
            
            if not clips:
                result["error"] = "Failed to extract clips"
                return result
            
            # Step 4: Add overlays (optional)
            if add_overlays and MOVIEPY_AVAILABLE:
                overlays_dir = os.path.join(output_dir, "clips_with_overlays")
                self.logger.info("🎨 Adding text overlays")
                clips = self.add_overlays_to_clips(clips, overlays_dir)
            
            # Step 5: Compose tutorial with transition cards
            tutorial_title = title or f"Fact-Check: Video {video_id}"
            tutorial_path = os.path.join(output_dir, f"{video_id}_tutorial.mp4")
            
            self.logger.info("🎬 Composing tutorial video with transition cards")
            tutorial_result = self.compose_tutorial(
                clips,
                tutorial_path,
                title=tutorial_title,
                subtitle=f"Analysis of {len(clips)} claims",
                video_id=video_id,
                video_title=title,
                transition_duration=3.0
            )
            
            # Step 6: Save metadata
            metadata = {
                "video_id": video_id,
                "source_video": video_path,
                "total_claims": len(claims),
                "selected_claims": len(selected_claims),
                "clips_generated": len(clips),
                "clips": [
                    {
                        "claim_id": c.claim_id,
                        "claim_text": c.claim_text,
                        "timestamp": c.timestamp_str,
                        "verdict": c.verdict,
                        "false_probability": c.false_probability,
                        "clip_path": c.clip_path
                    }
                    for c in clips
                ]
            }
            
            metadata_path = os.path.join(output_dir, f"{video_id}_tutorial_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Build result
            result["success"] = True
            result["tutorial_path"] = tutorial_result
            result["clip_paths"] = [c.clip_path for c in clips if c.clip_path]
            result["metadata"] = metadata
            result["metadata_path"] = metadata_path
            
            self.logger.info(f"✅ Tutorial generation complete: {tutorial_result}")
            
        except Exception as e:
            self.logger.error(f"Error generating tutorial: {e}")
            result["error"] = str(e)
        
        return result
    
    # =========================================================================
    # GCS Report Fetching
    # =========================================================================
    
    @staticmethod
    def fetch_report_from_gcs(
        video_id: str,
        output_dir: str = "downloads",
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Fetch the latest report JSON from GCS for a given video ID.
        
        Searches for reports in:
        - vngn_reports/{video_id}/ (timestamped directories)
        - reports/{video_id}/
        
        Args:
            video_id: YouTube video ID
            output_dir: Local directory to save the downloaded report
            bucket_name: GCS bucket name (defaults to env var GCS_BUCKET_NAME)
            project_id: GCP project ID (defaults to env var PROJECT_ID)
            
        Returns:
            Path to downloaded report file, or None if not found
        """
        if not GCS_AVAILABLE:
            logger.error("google-cloud-storage not available. Install with: pip install google-cloud-storage")
            return None
        
        # Get defaults from environment
        bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME", "verityindex_bucket")
        project_id = project_id or os.environ.get("PROJECT_ID", "verityindex-0-0-1")
        
        logger.info(f"🔍 Searching for report in GCS bucket: {bucket_name}")
        
        try:
            client = storage.Client(project=project_id)
            bucket = client.bucket(bucket_name)
            
            # Search patterns in order of preference (newest first)
            search_prefixes = [
                f"vngn_reports/{video_id}/",  # Timestamped storage (newer)
                f"reports/{video_id}/",        # Legacy storage
            ]
            
            report_blob = None
            latest_time = None
            
            for prefix in search_prefixes:
                logger.info(f"  Checking prefix: {prefix}")
                blobs = list(bucket.list_blobs(prefix=prefix))
                
                # Find report JSON files
                for blob in blobs:
                    if blob.name.endswith("_report.json"):
                        # Check if this is more recent
                        if latest_time is None or blob.updated > latest_time:
                            latest_time = blob.updated
                            report_blob = blob
                            logger.info(f"  Found report: {blob.name} (updated: {blob.updated})")
            
            if not report_blob:
                logger.warning(f"No report found in GCS for video ID: {video_id}")
                return None
            
            # Download the report
            os.makedirs(output_dir, exist_ok=True)
            local_path = os.path.join(output_dir, f"{video_id}_report.json")
            
            logger.info(f"📥 Downloading: gs://{bucket_name}/{report_blob.name}")
            report_blob.download_to_filename(local_path)
            
            logger.info(f"✅ Report downloaded to: {local_path}")
            return local_path
            
        except Exception as e:
            logger.error(f"Error fetching report from GCS: {e}")
            return None
    
    @staticmethod
    def list_gcs_reports(
        video_id: Optional[str] = None,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List available reports in GCS.
        
        Args:
            video_id: Optional video ID to filter by
            bucket_name: GCS bucket name
            project_id: GCP project ID
            limit: Maximum number of reports to return
            
        Returns:
            List of report metadata dictionaries
        """
        if not GCS_AVAILABLE:
            logger.error("google-cloud-storage not available")
            return []
        
        bucket_name = bucket_name or os.environ.get("GCS_BUCKET_NAME", "verityindex_bucket")
        project_id = project_id or os.environ.get("PROJECT_ID", "verityindex-0-0-1")
        
        try:
            client = storage.Client(project=project_id)
            bucket = client.bucket(bucket_name)
            
            # Determine prefix
            if video_id:
                prefixes = [f"vngn_reports/{video_id}/", f"reports/{video_id}/"]
            else:
                prefixes = ["vngn_reports/", "reports/"]
            
            reports = []
            
            for prefix in prefixes:
                blobs = bucket.list_blobs(prefix=prefix)
                
                for blob in blobs:
                    if blob.name.endswith("_report.json"):
                        # Extract video ID from path
                        parts = blob.name.split("/")
                        vid = parts[1] if len(parts) > 1 else "unknown"
                        
                        reports.append({
                            "video_id": vid,
                            "path": blob.name,
                            "gcs_uri": f"gs://{bucket_name}/{blob.name}",
                            "updated": blob.updated.isoformat() if blob.updated else None,
                            "size_bytes": blob.size,
                        })
                        
                        if len(reports) >= limit:
                            break
                
                if len(reports) >= limit:
                    break
            
            # Sort by updated time (newest first)
            reports.sort(key=lambda x: x.get("updated", ""), reverse=True)
            
            return reports[:limit]
            
        except Exception as e:
            logger.error(f"Error listing GCS reports: {e}")
            return []
    
    # =========================================================================
    # Utility: Load Claims from File
    # =========================================================================
    
    @staticmethod
    def load_claims_from_file(claims_path: str) -> List[Dict[str, Any]]:
        """
        Load claims from a JSON file.
        
        Args:
            claims_path: Path to claims JSON file
            
        Returns:
            List of claim dictionaries
        """
        with open(claims_path, 'r') as f:
            data = json.load(f)
        
        # Handle different formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if 'claims' in data:
                return data['claims']
            elif 'claims_breakdown' in data:
                return data['claims_breakdown']
            elif 'final_claims' in data:
                return data['final_claims']
        
        return []
    
    @staticmethod
    def find_claims_file(video_id: str, base_dirs: Optional[List[str]] = None) -> Optional[str]:
        """
        Find a claims file for a given video ID.
        
        Args:
            video_id: YouTube video ID
            base_dirs: Optional directories to search
            
        Returns:
            Path to claims file if found
        """
        if base_dirs is None:
            base_dirs = [
                ".",
                "outputs",
                f"outputs/{video_id}",
                f"sherlock_analysis_{video_id}",
            ]
        
        patterns = [
            f"{video_id}_claims_detailed.json",
            f"{video_id}_final_claims.json",
            f"{video_id}_report.json",
            f"{video_id}_claim_processing_report.json",
        ]
        
        for base_dir in base_dirs:
            if not os.path.exists(base_dir):
                continue
            
            for pattern in patterns:
                path = os.path.join(base_dir, pattern)
                if os.path.exists(path):
                    return path
            
            # Search recursively
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file in patterns or (video_id in file and file.endswith('.json')):
                        return os.path.join(root, file)
        
        return None

