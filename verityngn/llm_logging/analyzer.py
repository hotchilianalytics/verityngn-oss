"""
LLM Log Analyzer

Analyzes logged LLM calls for insights:
- Cost analysis and token usage
- Performance metrics (latency, throughput)
- Error rates and patterns
- Model comparison
- Prompt optimization suggestions

This enables researchers to:
- Understand system behavior
- Optimize prompts and parameters
- Debug issues
- Compare model performance
- Track costs
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class LLMLogAnalyzer:
    """
    Analyze LLM logs for insights and optimization.
    
    Example:
        >>> from verityngn.llm_logging.analyzer import LLMLogAnalyzer
        >>> analyzer = LLMLogAnalyzer('./llm_logs')
        >>> stats = analyzer.get_statistics()
        >>> print(f"Total cost: ${stats['total_cost']:.2f}")
        >>> print(f"Average latency: {stats['average_latency']:.2f}s")
    """
    
    # Token pricing (per 1K tokens) - Update as needed
    TOKEN_PRICING = {
        'gemini-2.5-flash': {
            'input': 0.0001,   # $0.10 per 1M tokens
            'output': 0.0004   # $0.40 per 1M tokens
        },
        'gemini-2.0-flash': {
            'input': 0.00015,
            'output': 0.0006
        },
        'gemini-pro': {
            'input': 0.0005,
            'output': 0.0015
        }
    }
    
    def __init__(self, log_dir: str = './llm_logs'):
        """
        Initialize log analyzer.
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
        self.logs = []
        self._load_logs()
    
    def _load_logs(self):
        """Load all log files from directory."""
        if not self.log_dir.exists():
            logger.warning(f"Log directory not found: {self.log_dir}")
            return
        
        for filepath in self.log_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    self.logs.append(log_data)
            except Exception as e:
                logger.warning(f"Failed to load log file {filepath}: {e}")
        
        logger.info(f"📊 Loaded {len(self.logs)} log files")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics from all logs.
        
        Returns:
            Dictionary with statistics
        """
        if not self.logs:
            return {'error': 'No logs found'}
        
        # Aggregate metrics
        total_calls = len(self.logs)
        total_tokens_input = sum(log.get('tokens', {}).get('input', 0) for log in self.logs)
        total_tokens_output = sum(log.get('tokens', {}).get('output', 0) for log in self.logs)
        total_tokens = total_tokens_input + total_tokens_output
        
        # Calculate costs
        total_cost = self._calculate_total_cost()
        
        # Timing metrics
        durations = [
            log.get('timing', {}).get('duration_seconds', 0) 
            for log in self.logs 
            if log.get('timing')
        ]
        
        # Success/failure rates
        successful = sum(1 for log in self.logs if log.get('status') == 'completed')
        failed = sum(1 for log in self.logs if log.get('status') == 'failed')
        
        # Operation breakdown
        operations = self._group_by_operation()
        
        # Model usage
        models = self._group_by_model()
        
        return {
            'summary': {
                'total_calls': total_calls,
                'successful_calls': successful,
                'failed_calls': failed,
                'success_rate': successful / total_calls if total_calls > 0 else 0
            },
            'tokens': {
                'total_input': total_tokens_input,
                'total_output': total_tokens_output,
                'total': total_tokens,
                'average_per_call': total_tokens / total_calls if total_calls > 0 else 0
            },
            'costs': {
                'total_cost_usd': total_cost,
                'average_cost_per_call': total_cost / total_calls if total_calls > 0 else 0,
                'input_cost': self._calculate_token_cost(total_tokens_input, 'input'),
                'output_cost': self._calculate_token_cost(total_tokens_output, 'output')
            },
            'timing': {
                'total_duration_seconds': sum(durations),
                'average_duration_seconds': statistics.mean(durations) if durations else 0,
                'median_duration_seconds': statistics.median(durations) if durations else 0,
                'min_duration_seconds': min(durations) if durations else 0,
                'max_duration_seconds': max(durations) if durations else 0
            },
            'operations': operations,
            'models': models
        }
    
    def _calculate_total_cost(self) -> float:
        """Calculate total cost of all LLM calls."""
        total_cost = 0.0
        
        for log in self.logs:
            model = log.get('request', {}).get('model', 'gemini-2.5-flash')
            tokens = log.get('tokens', {})
            
            input_tokens = tokens.get('input', 0)
            output_tokens = tokens.get('output', 0)
            
            pricing = self.TOKEN_PRICING.get(model, self.TOKEN_PRICING['gemini-2.5-flash'])
            
            input_cost = (input_tokens / 1000) * pricing['input']
            output_cost = (output_tokens / 1000) * pricing['output']
            
            total_cost += input_cost + output_cost
        
        return total_cost
    
    def _calculate_token_cost(self, tokens: int, token_type: str) -> float:
        """Calculate cost for specific token count."""
        # Use average pricing across models
        avg_price = statistics.mean([
            pricing[token_type] 
            for pricing in self.TOKEN_PRICING.values()
        ])
        return (tokens / 1000) * avg_price
    
    def _group_by_operation(self) -> Dict[str, Dict[str, Any]]:
        """Group statistics by operation type."""
        ops = defaultdict(lambda: {
            'count': 0,
            'tokens_input': 0,
            'tokens_output': 0,
            'total_duration': 0.0,
            'successful': 0,
            'failed': 0
        })
        
        for log in self.logs:
            op = log.get('operation', 'unknown')
            ops[op]['count'] += 1
            ops[op]['tokens_input'] += log.get('tokens', {}).get('input', 0)
            ops[op]['tokens_output'] += log.get('tokens', {}).get('output', 0)
            ops[op]['total_duration'] += log.get('timing', {}).get('duration_seconds', 0)
            
            if log.get('status') == 'completed':
                ops[op]['successful'] += 1
            elif log.get('status') == 'failed':
                ops[op]['failed'] += 1
        
        return dict(ops)
    
    def _group_by_model(self) -> Dict[str, Dict[str, Any]]:
        """Group statistics by model."""
        models = defaultdict(lambda: {
            'count': 0,
            'tokens': 0,
            'cost': 0.0
        })
        
        for log in self.logs:
            model = log.get('request', {}).get('model', 'unknown')
            tokens = log.get('tokens', {})
            
            models[model]['count'] += 1
            models[model]['tokens'] += tokens.get('total', 0)
            
            # Calculate cost for this call
            pricing = self.TOKEN_PRICING.get(model, self.TOKEN_PRICING['gemini-2.5-flash'])
            input_cost = (tokens.get('input', 0) / 1000) * pricing['input']
            output_cost = (tokens.get('output', 0) / 1000) * pricing['output']
            models[model]['cost'] += input_cost + output_cost
        
        return dict(models)
    
    def get_slowest_calls(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the N slowest LLM calls.
        
        Args:
            n: Number of calls to return
            
        Returns:
            List of log entries sorted by duration
        """
        calls_with_timing = [
            log for log in self.logs 
            if log.get('timing', {}).get('duration_seconds')
        ]
        
        sorted_calls = sorted(
            calls_with_timing,
            key=lambda x: x.get('timing', {}).get('duration_seconds', 0),
            reverse=True
        )
        
        return sorted_calls[:n]
    
    def get_most_expensive_calls(self, n: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """
        Get the N most expensive LLM calls.
        
        Args:
            n: Number of calls to return
            
        Returns:
            List of (log_entry, cost) tuples sorted by cost
        """
        calls_with_cost = []
        
        for log in self.logs:
            model = log.get('request', {}).get('model', 'gemini-2.5-flash')
            tokens = log.get('tokens', {})
            
            pricing = self.TOKEN_PRICING.get(model, self.TOKEN_PRICING['gemini-2.5-flash'])
            
            input_cost = (tokens.get('input', 0) / 1000) * pricing['input']
            output_cost = (tokens.get('output', 0) / 1000) * pricing['output']
            total_cost = input_cost + output_cost
            
            calls_with_cost.append((log, total_cost))
        
        sorted_calls = sorted(calls_with_cost, key=lambda x: x[1], reverse=True)
        
        return sorted_calls[:n]
    
    def get_failed_calls(self) -> List[Dict[str, Any]]:
        """
        Get all failed LLM calls.
        
        Returns:
            List of failed call logs
        """
        return [log for log in self.logs if log.get('status') == 'failed']
    
    def get_calls_by_video(self, video_id: str) -> List[Dict[str, Any]]:
        """
        Get all LLM calls for a specific video.
        
        Args:
            video_id: Video identifier
            
        Returns:
            List of log entries for the video
        """
        return [log for log in self.logs if log.get('video_id') == video_id]
    
    def analyze_prompt_patterns(self) -> Dict[str, Any]:
        """
        Analyze prompt patterns for optimization suggestions.
        
        Returns:
            Dictionary with prompt analysis
        """
        prompt_lengths = []
        prompt_lines = []
        
        for log in self.logs:
            request = log.get('request', {})
            prompt_lengths.append(request.get('prompt_length', 0))
            prompt_lines.append(request.get('prompt_lines', 0))
        
        if not prompt_lengths:
            return {}
        
        return {
            'average_prompt_length': statistics.mean(prompt_lengths),
            'median_prompt_length': statistics.median(prompt_lengths),
            'max_prompt_length': max(prompt_lengths),
            'average_prompt_lines': statistics.mean(prompt_lines),
            'suggestions': self._generate_prompt_suggestions(prompt_lengths)
        }
    
    def _generate_prompt_suggestions(self, prompt_lengths: List[int]) -> List[str]:
        """Generate optimization suggestions based on prompt analysis."""
        suggestions = []
        
        avg_length = statistics.mean(prompt_lengths)
        
        if avg_length > 5000:
            suggestions.append("Consider shortening prompts - average length is high")
        
        if max(prompt_lengths) > 10000:
            suggestions.append("Some prompts are very long - review for redundancy")
        
        return suggestions
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate comprehensive analysis report.
        
        Args:
            output_file: Optional file path to save report
            
        Returns:
            Report as markdown string
        """
        stats = self.get_statistics()
        prompt_analysis = self.analyze_prompt_patterns()
        slowest = self.get_slowest_calls(5)
        expensive = self.get_most_expensive_calls(5)
        failed = self.get_failed_calls()
        
        report = f"""# LLM Logging Analysis Report

Generated: {datetime.now().isoformat()}

## Summary

- **Total Calls**: {stats['summary']['total_calls']}
- **Success Rate**: {stats['summary']['success_rate']:.1%}
- **Failed Calls**: {stats['summary']['failed_calls']}

## Token Usage

- **Total Tokens**: {stats['tokens']['total']:,}
  - Input: {stats['tokens']['total_input']:,}
  - Output: {stats['tokens']['total_output']:,}
- **Average per Call**: {stats['tokens']['average_per_call']:,.0f}

## Cost Analysis

- **Total Cost**: ${stats['costs']['total_cost_usd']:.4f}
- **Average per Call**: ${stats['costs']['average_cost_per_call']:.4f}
- **Input Cost**: ${stats['costs']['input_cost']:.4f}
- **Output Cost**: ${stats['costs']['output_cost']:.4f}

## Performance Metrics

- **Total Duration**: {stats['timing']['total_duration_seconds']:.1f} seconds
- **Average Duration**: {stats['timing']['average_duration_seconds']:.2f} seconds
- **Median Duration**: {stats['timing']['median_duration_seconds']:.2f} seconds
- **Min/Max**: {stats['timing']['min_duration_seconds']:.2f}s / {stats['timing']['max_duration_seconds']:.2f}s

## Operations Breakdown

"""
        
        for op, op_stats in stats['operations'].items():
            report += f"""
### {op}

- Calls: {op_stats['count']}
- Tokens: {op_stats['tokens_input'] + op_stats['tokens_output']:,}
- Duration: {op_stats['total_duration']:.1f}s
- Success: {op_stats['successful']}/{op_stats['count']}
"""
        
        report += "\n## Model Usage\n\n"
        for model, model_stats in stats['models'].items():
            report += f"""
### {model}

- Calls: {model_stats['count']}
- Tokens: {model_stats['tokens']:,}
- Cost: ${model_stats['cost']:.4f}
"""
        
        if slowest:
            report += "\n## Slowest Calls\n\n"
            for i, call in enumerate(slowest, 1):
                duration = call.get('timing', {}).get('duration_seconds', 0)
                operation = call.get('operation', 'unknown')
                report += f"{i}. {operation}: {duration:.2f}s\n"
        
        if expensive:
            report += "\n## Most Expensive Calls\n\n"
            for i, (call, cost) in enumerate(expensive, 1):
                operation = call.get('operation', 'unknown')
                report += f"{i}. {operation}: ${cost:.4f}\n"
        
        if failed:
            report += f"\n## Failed Calls ({len(failed)})\n\n"
            for call in failed[:10]:  # Show first 10
                operation = call.get('operation', 'unknown')
                error = call.get('error', 'Unknown error')
                report += f"- {operation}: {error}\n"
        
        if prompt_analysis.get('suggestions'):
            report += "\n## Optimization Suggestions\n\n"
            for suggestion in prompt_analysis['suggestions']:
                report += f"- {suggestion}\n"
        
        report += "\n---\n\n*Generated by VerityNgn LLM Log Analyzer*\n"
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"📄 Report saved to: {output_file}")
        
        return report


def analyze_logs(log_dir: str = './llm_logs') -> LLMLogAnalyzer:
    """
    Convenience function to create analyzer and load logs.
    
    Args:
        log_dir: Directory containing log files
        
    Returns:
        LLMLogAnalyzer instance
    """
    return LLMLogAnalyzer(log_dir)


