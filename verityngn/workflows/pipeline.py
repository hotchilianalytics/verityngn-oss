"""
VerityNgn Core Verification Pipeline

This module implements the main verification workflow that processes YouTube videos
and generates truthfulness reports. It uses LangGraph for orchestration.

Workflow stages:
1. Initial Analysis: Download video and perform multimodal LLM analysis
2. Counter Intelligence: Search for contradictory evidence on YouTube
3. Prepare Claims: Extract and filter claims from analysis
4. Claim Verification: Verify each claim using web search
5. Generate Report: Create comprehensive truthfulness report
6. Save Report: Save report in multiple formats (JSON, MD, HTML)

Execution Mode: Local-first (runs on user's machine)
Optional: Can submit to Google Batch for scalability (see advanced docs)
"""

import logging
import json
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple, TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Configure console logging for visibility
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

# Import workflow stages
from .analysis import run_initial_analysis, run_prepare_claims
from .verification import run_claim_verification
from .reporting import run_generate_report, run_upload_report
from .counter_intel import run_counter_intel_once


# Custom JSON encoder for datetime and Path objects
class CustomJsonEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and Path objects."""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Path):
            return str(o)
        if hasattr(o, '__pydantic_serializer__'):
            return o.__pydantic_serializer__()
        return super().default(o)


# Workflow state definition
class VerificationState(TypedDict, total=False):
    """State dictionary for the verification workflow."""
    # Video information
    video_url: str
    video_id: str
    video_path: Optional[str]
    video_info: Optional[Dict[str, Any]]
    
    # Processing paths
    out_dir_path: str
    chunk_file_name: Optional[str]
    
    # Analysis results
    initial_report: Optional[Dict[str, Any]]
    transcription: Optional[str]
    
    # Claims processing
    claims: List[Dict[str, Any]]
    current_claim_index: int
    aggregated_evidence: List[Dict[str, Any]]
    
    # Counter intelligence
    ci_once: List[Dict[str, Any]]
    
    # Report generation
    markdown_report_content: Optional[str]
    claim_source_markdown_content: Optional[Dict[str, Any]]
    html_report_content: Optional[str]
    final_report: Optional[Dict[str, Any]]
    
    # Output paths
    html_path: Optional[str]
    json_path: Optional[str]
    markdown_path: Optional[str]
    media_embed: Optional[Dict[str, Any]]
    
    # Storage (optional - for GCS uploads)
    gcs_base_uri: Optional[str]
    gcs_uri: Optional[str]
    
    # Messages (for LangGraph message passing)
    messages: List[BaseMessage]


def create_workflow() -> StateGraph:
    """
    Create the main verification workflow graph.
    
    Returns:
        StateGraph: Compiled LangGraph workflow
    """
    logger.info("📊 Creating verification workflow graph")
    
    # Create workflow graph with state schema
    workflow = StateGraph(VerificationState)
    
    # Add workflow nodes (stages)
    workflow.add_node("initial_analysis", run_initial_analysis)
    workflow.add_node("counter_intel_once", run_counter_intel_once)
    workflow.add_node("prepare_claims", run_prepare_claims)
    workflow.add_node("claim_verification", run_claim_verification)
    workflow.add_node("generate_report", run_generate_report)
    workflow.add_node("upload_report", run_upload_report)
    
    # Define workflow edges (stage transitions)
    workflow.add_edge(START, "initial_analysis")
    workflow.add_edge("initial_analysis", "counter_intel_once")
    workflow.add_edge("counter_intel_once", "prepare_claims")
    workflow.add_edge("prepare_claims", "claim_verification")
    workflow.add_edge("claim_verification", "generate_report")
    workflow.add_edge("generate_report", "upload_report")
    workflow.add_edge("upload_report", END)
    
    logger.info("✅ Workflow graph created successfully")
    return workflow


def run_verification(
    video_url: str, 
    out_dir_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Run the complete verification workflow for a YouTube video.
    
    This is the main entry point for processing videos. It:
    1. Downloads the video
    2. Performs multimodal analysis
    3. Extracts and verifies claims
    4. Generates comprehensive reports
    5. Saves results locally (or optionally to GCS)
    
    Args:
        video_url: YouTube video URL (e.g., 'https://www.youtube.com/watch?v=...')
        out_dir_path: Output directory path (defaults to temp directory)
        config: Optional configuration overrides (dict from config.yaml)
        
    Returns:
        Tuple containing:
        - final_state (Dict): Complete workflow state with all results
        - out_dir_path (str): Path to output directory with reports
        
    Raises:
        ValueError: If video URL is invalid or video ID cannot be extracted
        Exception: For any processing errors during the workflow
        
    Example:
        >>> from verityngn.workflows.pipeline import run_verification
        >>> final_state, output_dir = run_verification(
        ...     "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        ... )
        >>> print(f"Report saved to: {output_dir}")
        >>> print(f"Truthfulness score: {final_state['final_report']['truthfulness_score']}")
    """
    logger.info(f"🚀 Starting verification workflow for: {video_url}")
    
    try:
        # Extract video ID from URL
        from verityngn.utils.file_utils import extract_video_id
        video_id = extract_video_id(video_url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL. Please provide a valid YouTube URL.")
            
        logger.info(f"📹 Video ID: {video_id}")
        
        # Set up output directory
        if not out_dir_path:
            # Default to local outputs directory
            from verityngn.config.settings import OUTPUTS_DIR
            out_dir_path = os.path.join(str(OUTPUTS_DIR), video_id)
        
        os.makedirs(out_dir_path, exist_ok=True)
        logger.info(f"📁 Output directory: {out_dir_path}")
        
        # Create initial workflow state
        initial_state = {
            "video_url": video_url,
            "video_id": video_id,
            "out_dir_path": out_dir_path,
            "claims": [],
            "current_claim_index": 0,
            "aggregated_evidence": [],
            "messages": [],
            "ci_once": []
        }
        
        # Add config overrides if provided
        if config:
            initial_state["config_overrides"] = config
        
        # Create and compile workflow
        logger.info("🔧 Compiling workflow graph...")
        workflow = create_workflow()
        compiled_workflow = workflow.compile()
        
        # Run workflow (using asyncio for LangGraph)
        logger.info("▶️  Executing workflow stages...")
        logger.info("    Stage 1: Initial Analysis (download + multimodal LLM)")
        logger.info("    Stage 2: Counter Intelligence (YouTube search)")
        logger.info("    Stage 3: Prepare Claims (extract + filter)")
        logger.info("    Stage 4: Claim Verification (web search + evidence)")
        logger.info("    Stage 5: Generate Report (truthfulness scoring)")
        logger.info("    Stage 6: Save Report (JSON + MD + HTML)")
        
        # Set up workflow log file handler - save to outputs directory
        os.makedirs(out_dir_path, exist_ok=True)
        log_file_path = os.path.join(out_dir_path, f"{video_id}_workflow.log")
        
        # Create file handler for workflow logs
        file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s:%(lineno)d] %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Add file handler to root logger to capture all workflow logs
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        
        # Also add to workflow-specific loggers
        workflow_loggers = [
            logging.getLogger('verityngn.workflows'),
            logging.getLogger('verityngn.workflows.pipeline'),
            logging.getLogger('verityngn.workflows.analysis'),
            logging.getLogger('verityngn.workflows.verification'),
            logging.getLogger('verityngn.workflows.reporting'),
        ]
        for wf_logger in workflow_loggers:
            wf_logger.addHandler(file_handler)
            wf_logger.setLevel(logging.DEBUG)
        
        try:
            import asyncio
            final_state = asyncio.run(compiled_workflow.ainvoke(initial_state))
            
            logger.info("✅ Workflow completed successfully!")
            logger.info(f"📊 Claims processed: {len(final_state.get('claims', []))}")
            logger.info(f"📄 Reports saved to: {out_dir_path}")
            logger.info(f"📝 Workflow log saved to: {log_file_path}")
        finally:
            # Remove file handler after workflow completes
            root_logger.removeHandler(file_handler)
            for wf_logger in workflow_loggers:
                wf_logger.removeHandler(file_handler)
            file_handler.close()
        
        # Return dict for API compatibility (not tuple)
        return {
            "video_id": video_id,
            "output_dir": str(out_dir_path),
            "claims_count": len(final_state.get('claims', [])),
            "state": final_state
        }
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}", exc_info=True)
        
        # Save error state for debugging
        try:
            error_state = {
                "video_url": video_url,
                "video_id": video_id if 'video_id' in locals() else "unknown",
                "out_dir_path": out_dir_path or "",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
            
            if out_dir_path:
                os.makedirs(out_dir_path, exist_ok=True)
                error_file = os.path.join(out_dir_path, "error_state.json")
                with open(error_file, "w") as f:
                    json.dump(error_state, f, indent=2, cls=CustomJsonEncoder)
                logger.info(f"💾 Error state saved to: {error_file}")
        except Exception as save_error:
            logger.error(f"Failed to save error state: {save_error}")
        
        # Re-raise the original exception so callers know it failed
        raise


# Backward compatibility aliases
build_main_workflow = create_workflow

