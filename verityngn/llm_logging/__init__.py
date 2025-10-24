"""
VerityNgn LLM Transparency Logging

Captures all LLM interactions for research reproducibility and transparency.

This module logs every LLM request and response with full details:
- Complete prompts (including system messages)
- Full responses
- Token counts and costs
- Timing/latency metrics
- Model versions
- All parameters

Example:
    >>> from verityngn.llm_logging import get_logger
    >>> 
    >>> logger = get_logger()
    >>> call_id = logger.start_call('initial_analysis', prompt="...", model="gemini-2.5-flash")
    >>> # ... make LLM call ...
    >>> logger.log_response(call_id, response)
    >>> logger.save_call(call_id)
    
Analyze logs:
    >>> from verityngn.llm_logging import analyze_logs
    >>> analyzer = analyze_logs('./llm_logs')
    >>> stats = analyzer.get_statistics()
    >>> print(f"Total cost: ${stats['costs']['total_cost_usd']:.2f}")
"""

from .logger import LLMLogger, get_logger, log_llm_call, log_llm_response
from .analyzer import LLMLogAnalyzer, analyze_logs

__all__ = [
    'LLMLogger', 
    'get_logger', 
    'log_llm_call', 
    'log_llm_response',
    'LLMLogAnalyzer',
    'analyze_logs'
]

