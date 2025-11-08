"""
API Routes for video verification workflows.

This module provides FastAPI endpoints to trigger and monitor
video verification tasks.
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory task storage (replace with Redis/DB for production)
tasks: Dict[str, Dict[str, Any]] = {}


class VerificationRequest(BaseModel):
    """Request model for video verification."""
    video_url: HttpUrl
    config: Optional[Dict[str, Any]] = None


class VerificationResponse(BaseModel):
    """Response model for verification submission."""
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    """Status model for verification task."""
    task_id: str
    status: str
    progress: float
    message: str
    video_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


async def run_verification_task(task_id: str, video_url: str, config: Dict[str, Any]):
    """
    Run the verification workflow in the background.
    
    Args:
        task_id: Unique task identifier
        video_url: YouTube video URL
        config: Configuration parameters
    """
    try:
        # Update task status
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["progress"] = 0.1
        tasks[task_id]["message"] = "Starting verification workflow..."
        tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Task {task_id}: Starting verification for {video_url}")
        
        # Import workflow here to avoid circular imports
        from verityngn.workflows.pipeline import run_verification
        
        # Update progress
        tasks[task_id]["progress"] = 0.2
        tasks[task_id]["message"] = "Downloading video..."
        tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"[WORKFLOW] Task {task_id}: Downloading video from {video_url}")
        
        # Run the actual verification workflow
        logger.info(f"[WORKFLOW] Task {task_id}: Running verification pipeline...")
        result = await asyncio.to_thread(
            run_verification,
            video_url=video_url
        )
        
        # Extract video_id from result
        video_id = result.get("video_id") if result else None
        logger.info(f"[WORKFLOW] Task {task_id}: Pipeline complete. Video ID: {video_id}")
        
        # Mark as complete
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 1.0
        tasks[task_id]["message"] = "Verification complete!"
        tasks[task_id]["video_id"] = video_id
        tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()
        tasks[task_id]["result"] = result
        
        logger.info(f"[WORKFLOW] Task {task_id}: ✅ Verification completed successfully for video {video_id}")
        
    except Exception as e:
        logger.error(f"[WORKFLOW] Task {task_id}: ❌ Failed with error: {str(e)}", exc_info=True)
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["progress"] = 0.0
        tasks[task_id]["error_message"] = str(e)
        tasks[task_id]["message"] = f"Verification failed: {str(e)}"
        tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()


@router.post("/verify", response_model=VerificationResponse)
async def submit_verification(
    request: VerificationRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a video verification task.
    
    Args:
        request: Verification request with video URL and config
        background_tasks: FastAPI background tasks manager
    
    Returns:
        Task ID and status information
    """
    try:
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Create task entry
        now = datetime.utcnow().isoformat()
        tasks[task_id] = {
            "task_id": task_id,
            "video_url": str(request.video_url),
            "config": request.config or {},
            "status": "pending",
            "progress": 0.0,
            "message": "Task submitted, waiting to start...",
            "video_id": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }
        
        # Start background task
        background_tasks.add_task(
            run_verification_task,
            task_id,
            str(request.video_url),
            request.config or {}
        )
        
        logger.info(f"[WORKFLOW] 🚀 New verification task submitted: {task_id} for {request.video_url}")
        
        return VerificationResponse(
            task_id=task_id,
            status="pending",
            message="Verification task submitted successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to submit verification: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Get the status of a verification task.
    
    Args:
        task_id: Unique task identifier
    
    Returns:
        Current task status and progress
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    task = tasks[task_id]
    
    return TaskStatus(
        task_id=task["task_id"],
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        video_id=task.get("video_id"),
        error_message=task.get("error_message"),
        created_at=task["created_at"],
        updated_at=task["updated_at"]
    )


@router.get("/tasks")
async def list_tasks():
    """
    List all verification tasks.
    
    Returns:
        List of all tasks with their statuses
    """
    return {
        "tasks": list(tasks.values()),
        "count": len(tasks)
    }

