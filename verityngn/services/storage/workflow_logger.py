import logging
import json
import time
import os
import threading
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

from verityngn.config.settings import GCS_BUCKET_NAME, STORAGE_BACKEND, StorageBackend
from verityngn.services.storage.gcs import GCSStorageService


@dataclass
class WorkflowLogEntry:
    """Single workflow log entry."""
    timestamp: str
    video_id: str
    step_name: str
    step_type: str  # "llm_call", "state_transition", "error", "info"
    duration_ms: Optional[int] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    model_name: Optional[str] = None
    status: str = "unknown"  # "started", "completed", "failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class WorkflowLogger:
    """
    Comprehensive workflow logger for VerityNgn.
    
    Captures all important events during video processing workflow:
    - LLM calls (input, output, duration, tokens)
    - State transitions
    - Errors and exceptions
    - Performance metrics
    
    Provides both real-time logging and GCS storage for post-facto analysis.
    """
    
    def __init__(self, video_id: str, enable_gcs: bool = True):
        self.video_id = video_id
        self.enable_gcs = enable_gcs
        self.logger = logging.getLogger(__name__)
        
        # Initialize log storage
        self.log_entries: List[WorkflowLogEntry] = []
        self.current_step_start_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # Create local log directory
        self.local_log_dir = Path(f"/tmp/workflow_logs/{video_id}")
        self.local_log_dir.mkdir(parents=True, exist_ok=True)
        self.local_log_file = self.local_log_dir / f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        # Initialize GCS if enabled
        self.gcs_service = None
        if self.enable_gcs and STORAGE_BACKEND == StorageBackend.GCS:
            try:
                self.gcs_service = GCSStorageService(GCS_BUCKET_NAME)
                self.logger.info(f"WorkflowLogger initialized with GCS for video {video_id}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize GCS for workflow logging: {e}")
                self.enable_gcs = False
        
        # Start workflow
        self._log_event("workflow_start", "info", {"video_id": video_id})
    
    def _log_event(self, step_name: str, step_type: str, data: Optional[Dict[str, Any]] = None, 
                   error: Optional[str] = None, duration_ms: Optional[int] = None,
                   token_usage: Optional[Dict[str, int]] = None, model_name: Optional[str] = None,
                   status: str = "completed"):
        """Internal method to log an event."""
        with self._lock:
            entry = WorkflowLogEntry(
                timestamp=datetime.now().isoformat(),
                video_id=self.video_id,
                step_name=step_name,
                step_type=step_type,
                duration_ms=duration_ms,
                input_data=data.get("input") if data else None,
                output_data=data.get("output") if data else None,
                error_message=error,
                token_usage=token_usage,
                model_name=model_name,
                status=status
            )
            
            self.log_entries.append(entry)
            
            # Write to local file immediately
            try:
                with open(self.local_log_file, 'a') as f:
                    f.write(json.dumps(entry.to_dict()) + '\n')
            except Exception as e:
                self.logger.error(f"Failed to write to local log file: {e}")
            
            # Log to standard logger
            if step_type == "error":
                self.logger.error(f"[{self.video_id}] {step_name}: {error}")
            else:
                self.logger.info(f"[{self.video_id}] {step_name} ({step_type}) - {status}")
    
    def start_step(self, step_name: str) -> None:
        """Mark the start of a workflow step."""
        self.current_step_start_times[step_name] = time.time()
        self._log_event(step_name, "state_transition", status="started")
    
    def complete_step(self, step_name: str, output_data: Optional[Dict[str, Any]] = None) -> None:
        """Mark the completion of a workflow step."""
        duration_ms = None
        if step_name in self.current_step_start_times:
            duration_ms = int((time.time() - self.current_step_start_times[step_name]) * 1000)
            del self.current_step_start_times[step_name]
        
        self._log_event(step_name, "state_transition", 
                       data={"output": output_data} if output_data else None,
                       duration_ms=duration_ms, status="completed")
    
    def log_llm_call(self, step_name: str, model_name: str, input_data: Dict[str, Any], 
                     output_data: Optional[Dict[str, Any]] = None, 
                     duration_ms: Optional[int] = None,
                     token_usage: Optional[Dict[str, int]] = None,
                     error: Optional[str] = None) -> None:
        """Log an LLM API call with full details."""
        status = "failed" if error else "completed"
        
        # Truncate large content for readability
        safe_input = self._truncate_content(input_data)
        safe_output = self._truncate_content(output_data) if output_data else None
        
        self._log_event(
            step_name=f"llm_{step_name}",
            step_type="llm_call",
            data={"input": safe_input, "output": safe_output},
            error=error,
            duration_ms=duration_ms,
            token_usage=token_usage,
            model_name=model_name,
            status=status
        )
    
    def log_error(self, step_name: str, error: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context."""
        self._log_event(step_name, "error", data=context, error=error, status="failed")
    
    def log_info(self, step_name: str, info: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log general information."""
        self._log_event(step_name, "info", data=data or {"message": info})
    
    def _truncate_content(self, content: Any, max_length: int = 1000) -> Any:
        """Truncate large content to keep logs manageable."""
        if isinstance(content, str):
            return content[:max_length] + "..." if len(content) > max_length else content
        elif isinstance(content, dict):
            truncated = {}
            for key, value in content.items():
                if isinstance(value, str) and len(value) > max_length:
                    truncated[key] = value[:max_length] + "..."
                else:
                    truncated[key] = value
            return truncated
        return content
    
    def upload_to_gcs(self) -> Optional[str]:
        """Upload workflow logs to GCS and return the GCS path."""
        if not self.enable_gcs or not self.gcs_service:
            self.logger.warning("GCS upload disabled or not available")
            return None
        
        try:
            # Create summary log
            summary = self._create_workflow_summary()
            
            # Upload detailed log
            gcs_log_path = f"workflow_logs/{self.video_id}/detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            success, _ = self.gcs_service.upload_file(str(self.local_log_file), gcs_log_path)
            
            if success:
                # Upload summary
                summary_file = self.local_log_dir / "summary.json"
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                
                gcs_summary_path = f"workflow_logs/{self.video_id}/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.gcs_service.upload_file(str(summary_file), gcs_summary_path)
                
                self.logger.info(f"Workflow logs uploaded to GCS: gs://{GCS_BUCKET_NAME}/{gcs_log_path}")
                return f"gs://{GCS_BUCKET_NAME}/{gcs_log_path}"
            else:
                self.logger.error("Failed to upload workflow logs to GCS")
                return None
                
        except Exception as e:
            self.logger.error(f"Error uploading workflow logs to GCS: {e}")
            return None
    
    def _create_workflow_summary(self) -> Dict[str, Any]:
        """Create a workflow execution summary."""
        summary = {
            "video_id": self.video_id,
            "start_time": self.log_entries[0].timestamp if self.log_entries else None,
            "end_time": self.log_entries[-1].timestamp if self.log_entries else None,
            "total_events": len(self.log_entries),
            "steps": {},
            "llm_calls": [],
            "errors": [],
            "token_usage_total": {"input_tokens": 0, "output_tokens": 0}
        }
        
        # Analyze log entries
        for entry in self.log_entries:
            # Track steps
            if entry.step_type == "state_transition":
                if entry.step_name not in summary["steps"]:
                    summary["steps"][entry.step_name] = {"status": "unknown", "duration_ms": 0}
                
                if entry.status in ["completed", "failed"]:
                    summary["steps"][entry.step_name]["status"] = entry.status
                    if entry.duration_ms:
                        summary["steps"][entry.step_name]["duration_ms"] = entry.duration_ms
            
            # Track LLM calls
            elif entry.step_type == "llm_call":
                llm_call = {
                    "step_name": entry.step_name,
                    "model_name": entry.model_name,
                    "duration_ms": entry.duration_ms,
                    "status": entry.status,
                    "token_usage": entry.token_usage
                }
                summary["llm_calls"].append(llm_call)
                
                # Aggregate token usage
                if entry.token_usage:
                    summary["token_usage_total"]["input_tokens"] += entry.token_usage.get("input_tokens", 0)
                    summary["token_usage_total"]["output_tokens"] += entry.token_usage.get("output_tokens", 0)
            
            # Track errors
            elif entry.step_type == "error":
                summary["errors"].append({
                    "step_name": entry.step_name,
                    "error_message": entry.error_message,
                    "timestamp": entry.timestamp
                })
        
        return summary
    
    def finalize(self) -> Optional[str]:
        """Finalize the workflow logging and upload to GCS."""
        self._log_event("workflow_end", "info", {
            "total_events": len(self.log_entries),
            "final_status": "completed" if not any(e.step_type == "error" for e in self.log_entries) else "failed"
        })
        
        # Upload to GCS
        gcs_path = self.upload_to_gcs()
        
        # Clean up local files (optional)
        try:
            # Keep the summary but remove detailed log to save space
            os.remove(self.local_log_file)
        except Exception as e:
            self.logger.warning(f"Failed to clean up local log file: {e}")
        
        return gcs_path


# Global logger instances
_workflow_loggers: Dict[str, WorkflowLogger] = {}
_logger_lock = threading.Lock()


def get_workflow_logger(video_id: str) -> WorkflowLogger:
    """Get or create a workflow logger for a video."""
    with _logger_lock:
        if video_id not in _workflow_loggers:
            _workflow_loggers[video_id] = WorkflowLogger(video_id)
        return _workflow_loggers[video_id]


def finalize_workflow_logger(video_id: str) -> Optional[str]:
    """Finalize and clean up a workflow logger."""
    with _logger_lock:
        if video_id in _workflow_loggers:
            logger = _workflow_loggers[video_id]
            gcs_path = logger.finalize()
            del _workflow_loggers[video_id]
            return gcs_path
    return None 