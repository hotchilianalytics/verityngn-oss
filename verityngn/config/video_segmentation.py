"""
Intelligent video segmentation based on LLM context windows.

This module calculates optimal segment sizes for video analysis based on:
1. Model context window size
2. Expected output token budget
3. Video tokenization rates (frames + audio)
4. Safety margins for overhead
"""

import os
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


# Token consumption rates (empirical data from Google Gemini docs)
TOKENS_PER_FRAME = 258  # Average tokens per video frame
TOKENS_PER_SECOND_AUDIO = 32  # Average tokens per second of audio
PROMPT_OVERHEAD_TOKENS = 5000  # System prompt + instructions
SAFETY_MARGIN_PERCENT = 10  # Reserve 10% for variability


# Model specifications
MODEL_SPECS = {
    "gemini-2.5-flash": {
        "context_window": 1_000_000,  # 1M tokens
        "max_output_tokens": 65_536,   # 64K tokens
        "recommended_fps": 1.0,         # Frames per second
    },
    "gemini-2.0-flash": {
        "context_window": 1_000_000,
        "max_output_tokens": 8_192,
        "recommended_fps": 1.0,
    },
    "gemini-1.5-pro": {
        "context_window": 2_000_000,   # 2M tokens!
        "max_output_tokens": 8_192,
        "recommended_fps": 1.0,
    },
    "gemini-1.5-flash": {
        "context_window": 1_000_000,
        "max_output_tokens": 8_192,
        "recommended_fps": 1.0,
    },
}


def calculate_tokens_per_second(fps: float = 1.0) -> float:
    """
    Calculate token consumption rate per second of video.
    
    Args:
        fps: Frames per second to sample
        
    Returns:
        Tokens per second (video frames + audio)
    """
    video_tokens = TOKENS_PER_FRAME * fps
    audio_tokens = TOKENS_PER_SECOND_AUDIO
    return video_tokens + audio_tokens


def calculate_optimal_segment_duration(
    model_name: str = "gemini-2.5-flash",
    fps: float = 1.0,
    custom_context_window: int = None,
    custom_output_tokens: int = None
) -> Dict[str, any]:
    """
    Calculate optimal segment duration for video analysis.
    
    Args:
        model_name: LLM model name
        fps: Frames per second for video sampling
        custom_context_window: Override context window size
        custom_output_tokens: Override output token budget
        
    Returns:
        Dictionary with segmentation parameters
    """
    # Get model specs or use defaults
    if model_name in MODEL_SPECS:
        specs = MODEL_SPECS[model_name]
    else:
        logger.warning(f"Unknown model {model_name}, using gemini-2.5-flash defaults")
        specs = MODEL_SPECS["gemini-2.5-flash"]
    
    # Apply overrides if provided
    context_window = custom_context_window or specs["context_window"]
    max_output_tokens = custom_output_tokens or specs["max_output_tokens"]
    
    # Calculate available tokens for input
    safety_margin_tokens = int(context_window * (SAFETY_MARGIN_PERCENT / 100))
    available_input_tokens = (
        context_window 
        - max_output_tokens 
        - PROMPT_OVERHEAD_TOKENS 
        - safety_margin_tokens
    )
    
    # Calculate token consumption rate
    tokens_per_second = calculate_tokens_per_second(fps)
    
    # Calculate max segment duration
    max_segment_seconds = int(available_input_tokens / tokens_per_second)
    max_segment_minutes = max_segment_seconds / 60
    
    # Calculate segments needed for different video lengths
    common_durations = [600, 1200, 1800, 3600, 7200]  # 10min, 20min, 30min, 60min, 120min
    segments_needed = {
        f"{d//60}min": (d + max_segment_seconds - 1) // max_segment_seconds
        for d in common_durations
    }
    
    result = {
        "model_name": model_name,
        "context_window": context_window,
        "max_output_tokens": max_output_tokens,
        "fps": fps,
        "tokens_per_second": tokens_per_second,
        "available_input_tokens": available_input_tokens,
        "max_segment_seconds": max_segment_seconds,
        "max_segment_minutes": max_segment_minutes,
        "prompt_overhead": PROMPT_OVERHEAD_TOKENS,
        "safety_margin_tokens": safety_margin_tokens,
        "segments_for_common_videos": segments_needed,
        "recommendation": {
            "segment_duration_seconds": max_segment_seconds,
            "use_case": "Maximize context utilization, minimize API calls",
            "tradeoff": "Longer processing time per segment, but fewer segments overall"
        }
    }
    
    return result


def get_segmentation_for_video(
    video_duration_seconds: int,
    model_name: str = "gemini-2.5-flash",
    fps: float = 1.0,
    prefer_fewer_segments: bool = True
) -> Tuple[int, int]:
    """
    Get optimal segment duration and count for a specific video.
    
    Args:
        video_duration_seconds: Video length in seconds
        model_name: LLM model to use
        fps: Frame sampling rate
        prefer_fewer_segments: If True, use maximum segment size; 
                              If False, use balanced segment sizes
        
    Returns:
        Tuple of (segment_duration_seconds, total_segments)
    """
    optimal = calculate_optimal_segment_duration(model_name, fps)
    max_segment = optimal["max_segment_seconds"]
    
    if prefer_fewer_segments:
        # Use maximum possible segment size (minimize API calls)
        segment_duration = max_segment
    else:
        # Balance segment sizes for better progress feedback
        # Target: 3-5 segments for hour-long videos
        target_segments = max(1, min(5, video_duration_seconds // 600))  # ~10 min segments
        segment_duration = (video_duration_seconds + target_segments - 1) // target_segments
        
        # But don't exceed max segment size
        segment_duration = min(segment_duration, max_segment)
    
    # Calculate actual number of segments
    total_segments = (video_duration_seconds + segment_duration - 1) // segment_duration
    
    return segment_duration, total_segments


def log_segmentation_plan(
    video_duration_seconds: int,
    model_name: str = "gemini-2.5-flash",
    fps: float = 1.0
):
    """
    Log detailed segmentation plan for a video.
    """
    optimal = calculate_optimal_segment_duration(model_name, fps)
    segment_duration, total_segments = get_segmentation_for_video(
        video_duration_seconds, model_name, fps, prefer_fewer_segments=True
    )
    
    logger.info("="*80)
    logger.info("📊 INTELLIGENT SEGMENTATION PLAN")
    logger.info("="*80)
    logger.info(f"Model: {model_name}")
    logger.info(f"Context Window: {optimal['context_window']:,} tokens")
    logger.info(f"Max Output: {optimal['max_output_tokens']:,} tokens")
    logger.info(f"FPS Sampling: {fps}")
    logger.info(f"Token Rate: {optimal['tokens_per_second']:.0f} tokens/second")
    logger.info("")
    logger.info(f"Video Duration: {video_duration_seconds}s ({video_duration_seconds/60:.1f} minutes)")
    logger.info(f"Optimal Segment Size: {segment_duration}s ({segment_duration/60:.1f} minutes)")
    logger.info(f"Total Segments: {total_segments}")
    logger.info(f"Tokens per Segment: ~{int(optimal['tokens_per_second'] * segment_duration):,}")
    logger.info(f"Context Utilization: ~{(optimal['tokens_per_second'] * segment_duration / optimal['context_window'] * 100):.1f}%")
    logger.info("")
    logger.info(f"Expected Time: {total_segments * 8}-{total_segments * 12} minutes")
    logger.info("="*80)


# Allow override via environment variables
def get_segment_duration_from_env_or_optimal(
    video_duration_seconds: int = 3600,
    model_name: str = None
) -> int:
    """
    Get segment duration from environment or calculate optimal.
    
    Priority:
    1. SEGMENT_DURATION_SECONDS env var (user override)
    2. Calculated optimal based on model
    """
    # Check environment variable first
    env_duration = os.getenv("SEGMENT_DURATION_SECONDS")
    if env_duration:
        try:
            duration = int(env_duration)
            logger.info(f"Using SEGMENT_DURATION_SECONDS from environment: {duration}s")
            return duration
        except ValueError:
            logger.warning(f"Invalid SEGMENT_DURATION_SECONDS: {env_duration}, calculating optimal")
    
    # Calculate optimal
    if not model_name:
        model_name = os.getenv("VERTEX_MODEL_NAME", "gemini-2.5-flash")
    
    fps = float(os.getenv("SEGMENT_FPS", "1.0"))
    segment_duration, _ = get_segmentation_for_video(
        video_duration_seconds, model_name, fps, prefer_fewer_segments=True
    )
    
    logger.info(f"Calculated optimal segment duration: {segment_duration}s ({segment_duration/60:.1f} min)")
    return segment_duration


if __name__ == "__main__":
    # Test with different scenarios
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    print("OPTIMAL SEGMENTATION ANALYSIS")
    print("="*80 + "\n")
    
    # Test different models
    for model in ["gemini-2.5-flash", "gemini-1.5-pro"]:
        print(f"\n{model.upper()}")
        print("-"*80)
        result = calculate_optimal_segment_duration(model, fps=1.0)
        print(f"Context Window: {result['context_window']:,} tokens")
        print(f"Max Segment: {result['max_segment_minutes']:.1f} minutes ({result['max_segment_seconds']}s)")
        print(f"Token Rate: {result['tokens_per_second']:.0f} tokens/sec")
        print(f"\nSegments needed for common videos:")
        for duration, segments in result['segments_for_common_videos'].items():
            print(f"  {duration}: {segments} segment(s)")
    
    # Test with specific video (33-minute LIPOZEM video)
    print("\n" + "="*80)
    print("LIPOZEM VIDEO (33 minutes / 1998 seconds)")
    print("="*80)
    segment_dur, total_segs = get_segmentation_for_video(1998, "gemini-2.5-flash", 1.0)
    print(f"Optimal: {total_segs} segment(s) of {segment_dur/60:.1f} minutes each")
    print(f"Expected time: {total_segs * 8}-{total_segs * 12} minutes")


