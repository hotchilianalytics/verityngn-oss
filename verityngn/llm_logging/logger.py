"""
LLM Transparency Logger

Captures complete LLM interaction data for research reproducibility.

Every LLM call is logged with:
- Full prompt text (including system messages)
- Complete response text
- Token counts (input, output, total)
- Timing metrics (latency, TTFT)
- Model name and version
- All parameters (temperature, max_tokens, etc.)
- Context (video_id, claim_id, operation)
- Errors and retries

This enables:
- Research reproducibility
- Cost analysis
- Performance optimization
- Error debugging
- Bias detection
"""

import logging
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, List
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class LLMLogger:
    """
    Logger for capturing all LLM interactions with full transparency.
    
    Logs are saved as JSON files in the configured output directory.
    Each call gets a unique ID for tracking across request/response.
    
    Example:
        >>> from verityngn.llm_logging import LLMLogger
        >>> llm_logger = LLMLogger(output_dir='./llm_logs')
        >>> 
        >>> # Before LLM call
        >>> call_id = llm_logger.start_call(
        ...     operation='initial_analysis',
        ...     video_id='abc123',
        ...     prompt='Analyze this video...',
        ...     model='gemini-2.5-flash',
        ...     parameters={'temperature': 0.1, 'max_tokens': 65536}
        ... )
        >>> 
        >>> # After LLM call
        >>> llm_logger.log_response(
        ...     call_id=call_id,
        ...     response_text='...',
        ...     token_counts={'input': 1000, 'output': 2000},
        ...     duration=15.3
        ... )
        >>> 
        >>> # Save complete call
        >>> llm_logger.save_call(call_id)
    """
    
    def __init__(self, output_dir: Optional[str] = None, enabled: bool = True):
        """
        Initialize LLM logger.
        
        Args:
            output_dir: Directory for log files (default: ./llm_logs)
            enabled: Enable/disable logging (default: True)
        """
        self.enabled = enabled
        self.output_dir = Path(output_dir or './llm_logs')
        self.calls = {}  # In-memory storage for active calls
        
        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📝 LLM logging enabled: {self.output_dir}")
        else:
            logger.info("📝 LLM logging disabled")
    
    def start_call(
        self,
        operation: str,
        prompt: str,
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        video_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start logging an LLM call.
        
        Args:
            operation: Operation name (e.g., 'initial_analysis', 'claim_verification')
            prompt: Full prompt text
            model: Model name
            parameters: Model parameters (temperature, max_tokens, etc.)
            video_id: Optional video identifier
            claim_id: Optional claim identifier
            metadata: Optional additional metadata
            
        Returns:
            Unique call ID for tracking
        """
        if not self.enabled:
            return str(uuid.uuid4())
        
        call_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        call_data = {
            'call_id': call_id,
            'operation': operation,
            'timestamp_start': timestamp,
            'video_id': video_id,
            'claim_id': claim_id,
            'request': {
                'prompt': prompt,
                'model': model,
                'parameters': parameters or {},
                'prompt_length': len(prompt),
                'prompt_lines': prompt.count('\n') + 1
            },
            'metadata': metadata or {},
            'status': 'pending'
        }
        
        self.calls[call_id] = call_data
        
        logger.debug(f"🔵 LLM call started: {call_id} ({operation})")
        
        return call_id
    
    def log_response(
        self,
        call_id: str,
        response_text: str,
        token_counts: Optional[Dict[str, int]] = None,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Log LLM response.
        
        Args:
            call_id: Call identifier from start_call()
            response_text: Complete response text
            token_counts: Token usage (input, output, total)
            duration: Response duration in seconds
            error: Error message if call failed
        """
        if not self.enabled or call_id not in self.calls:
            return
        
        call_data = self.calls[call_id]
        timestamp = datetime.now().isoformat()
        
        call_data['timestamp_end'] = timestamp
        call_data['response'] = {
            'text': response_text,
            'length': len(response_text),
            'lines': response_text.count('\n') + 1
        }
        
        if token_counts:
            call_data['tokens'] = {
                'input': token_counts.get('input', 0),
                'output': token_counts.get('output', 0),
                'total': token_counts.get('total', 0)
            }
        
        if duration is not None:
            call_data['timing'] = {
                'duration_seconds': duration,
                'tokens_per_second': (
                    call_data.get('tokens', {}).get('output', 0) / duration
                    if duration > 0 else 0
                )
            }
        
        if error:
            call_data['error'] = error
            call_data['status'] = 'failed'
            logger.warning(f"🔴 LLM call failed: {call_id} - {error}")
        else:
            call_data['status'] = 'completed'
            logger.debug(f"🟢 LLM call completed: {call_id}")
    
    def save_call(self, call_id: str) -> Optional[str]:
        """
        Save call data to JSON file.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Path to saved file or None if disabled/not found
        """
        if not self.enabled or call_id not in self.calls:
            return None
        
        call_data = self.calls[call_id]
        
        # Create filename with operation and timestamp
        operation = call_data.get('operation', 'unknown')
        timestamp = call_data.get('timestamp_start', '').replace(':', '-').replace('.', '-')
        filename = f"{operation}_{call_id[:8]}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(call_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 LLM call saved: {filepath}")
            
            # Remove from memory to save space
            del self.calls[call_id]
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save LLM call {call_id}: {e}")
            return None
    
    def log_complete_call(
        self,
        operation: str,
        prompt: str,
        response: str,
        model: str,
        parameters: Optional[Dict[str, Any]] = None,
        token_counts: Optional[Dict[str, int]] = None,
        duration: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Log a complete LLM call in one step (convenience method).
        
        Args:
            operation: Operation name
            prompt: Full prompt text
            response: Full response text
            model: Model name
            parameters: Model parameters
            token_counts: Token usage
            duration: Response duration
            **kwargs: Additional metadata (video_id, claim_id, etc.)
            
        Returns:
            Call ID
        """
        call_id = self.start_call(
            operation=operation,
            prompt=prompt,
            model=model,
            parameters=parameters,
            video_id=kwargs.get('video_id'),
            claim_id=kwargs.get('claim_id'),
            metadata={k: v for k, v in kwargs.items() if k not in ['video_id', 'claim_id']}
        )
        
        self.log_response(
            call_id=call_id,
            response_text=response,
            token_counts=token_counts,
            duration=duration
        )
        
        self.save_call(call_id)
        
        return call_id
    
    def get_call_data(self, call_id: str) -> Optional[Dict[str, Any]]:
        """
        Get call data by ID.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Call data dictionary or None
        """
        return self.calls.get(call_id)
    
    def list_calls(self, operation: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all logged calls from disk.
        
        Args:
            operation: Optional filter by operation name
            
        Returns:
            List of call data dictionaries
        """
        if not self.enabled:
            return []
        
        calls = []
        
        for filepath in self.output_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    call_data = json.load(f)
                    
                if operation is None or call_data.get('operation') == operation:
                    calls.append(call_data)
                    
            except Exception as e:
                logger.warning(f"Failed to read call file {filepath}: {e}")
        
        return sorted(calls, key=lambda x: x.get('timestamp_start', ''), reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get logging statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.enabled:
            return {'enabled': False}
        
        calls = self.list_calls()
        
        total_tokens = sum(c.get('tokens', {}).get('total', 0) for c in calls)
        total_duration = sum(c.get('timing', {}).get('duration_seconds', 0) for c in calls)
        
        operations = {}
        for call in calls:
            op = call.get('operation', 'unknown')
            if op not in operations:
                operations[op] = {'count': 0, 'tokens': 0, 'duration': 0}
            operations[op]['count'] += 1
            operations[op]['tokens'] += call.get('tokens', {}).get('total', 0)
            operations[op]['duration'] += call.get('timing', {}).get('duration_seconds', 0)
        
        return {
            'enabled': True,
            'output_dir': str(self.output_dir),
            'total_calls': len(calls),
            'total_tokens': total_tokens,
            'total_duration_seconds': total_duration,
            'operations': operations,
            'average_tokens_per_call': total_tokens / len(calls) if calls else 0,
            'average_duration_per_call': total_duration / len(calls) if calls else 0
        }


# Global logger instance
_global_logger = None


def get_logger(config: Optional[Dict[str, Any]] = None) -> LLMLogger:
    """
    Get global LLM logger instance (singleton).
    
    Args:
        config: Optional configuration dict with:
            - output_dir: Log directory
            - enabled: Enable/disable logging
            
    Returns:
        LLMLogger instance
    """
    global _global_logger
    
    if _global_logger is None:
        if config is None:
            # Try to load from config system
            try:
                from verityngn.config.config_loader import get_config
                app_config = get_config()
                llm_config = app_config.get_section('llm_logging')
                config = {
                    'output_dir': llm_config.get('output_dir', './llm_logs'),
                    'enabled': llm_config.get('enabled', True)
                }
            except Exception:
                config = {'output_dir': './llm_logs', 'enabled': True}
        
        _global_logger = LLMLogger(
            output_dir=config.get('output_dir', './llm_logs'),
            enabled=config.get('enabled', True)
        )
    
    return _global_logger


# Convenience functions for direct logging

def log_llm_call(
    operation: str,
    prompt: str,
    model: str,
    video_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convenience function to start logging an LLM call.
    
    Args:
        operation: Operation name
        prompt: Full prompt text
        model: Model name
        video_id: Optional video identifier
        **kwargs: Additional parameters
        
    Returns:
        Call ID for tracking
    """
    logger_instance = get_logger()
    return logger_instance.start_call(
        operation=operation,
        prompt=prompt,
        model=model,
        video_id=video_id,
        parameters=kwargs.get('parameters'),
        claim_id=kwargs.get('claim_id'),
        metadata=kwargs.get('metadata')
    )


def log_llm_response(
    call_id: str,
    response: Any,
    duration: Optional[float] = None
) -> None:
    """
    Convenience function to log an LLM response.
    
    Args:
        call_id: Call identifier from log_llm_call()
        response: Response object (will extract text and tokens)
        duration: Optional response duration in seconds
    """
    logger_instance = get_logger()
    
    # Extract response text
    if hasattr(response, 'content'):
        response_text = response.content
    elif hasattr(response, 'text'):
        try:
            response_text = response.text
        except Exception:
            response_text = str(response)
    elif isinstance(response, dict):
        response_text = response.get('content', response.get('text', str(response)))
    else:
        response_text = str(response)
    
    # Extract token counts if available
    token_counts = None
    if hasattr(response, 'usage'):
        usage = response.usage
        token_counts = {
            'input': getattr(usage, 'prompt_tokens', getattr(usage, 'input_tokens', 0)),
            'output': getattr(usage, 'completion_tokens', getattr(usage, 'output_tokens', 0)),
            'total': getattr(usage, 'total_tokens', 0)
        }
    elif hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        # UsageMetadata is often an object, not a dict
        if hasattr(usage, 'input_tokens') or hasattr(usage, 'prompt_tokens'):
            token_counts = {
                'input': getattr(usage, 'input_tokens', getattr(usage, 'prompt_tokens', 0)),
                'output': getattr(usage, 'output_tokens', getattr(usage, 'completion_tokens', 0)),
                'total': getattr(usage, 'total_tokens', 0)
            }
        elif isinstance(usage, dict):
            token_counts = {
                'input': usage.get('input_tokens', usage.get('prompt_tokens', 0)),
                'output': usage.get('output_tokens', usage.get('completion_tokens', 0)),
                'total': usage.get('total_tokens', 0)
            }
    elif isinstance(response, dict) and 'usage' in response:
        usage = response['usage']
        token_counts = {
            'input': usage.get('prompt_tokens', 0),
            'output': usage.get('completion_tokens', 0),
            'total': usage.get('total_tokens', 0)
        }
    
    logger_instance.log_response(
        call_id=call_id,
        response_text=response_text,
        token_counts=token_counts,
        duration=duration
    )
    
    logger_instance.save_call(call_id)


