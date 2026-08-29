"""
Deep Research — grounded forensic pass over a standard VerityNgn report.

Takes ``{video_id}_report.json`` as input and produces:

    {video_id}_deep_private_report.md
    {video_id}_deep_private_report.html
    {video_id}_deep_private_report.pdf
    {video_id}_deep_private_report.grounding.json

The Gemini call lives in ``client.py``; orchestration in ``pipeline.py``.
Available in OSS via ``verityngn analyze --deep`` (requires Gemini/Vertex credentials).
"""
from __future__ import annotations

from verityngn.services.deepresearch.client import DeepResearchResult, run_deep_research
from verityngn.services.deepresearch.pipeline import generate_deep_research_report
from verityngn.services.deepresearch.sanitize import count_claims, sanitize_report_data

__all__ = [
    "DeepResearchResult",
    "run_deep_research",
    "generate_deep_research_report",
    "sanitize_report_data",
    "count_claims",
]
