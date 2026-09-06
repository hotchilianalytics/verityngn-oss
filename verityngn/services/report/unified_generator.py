#!/usr/bin/env python3
"""
Unified Report Generation System
===============================

This module provides a single, unified system for generating all types of reports
in VerityNgn. It consolidates the different report generation approaches into
one consistent system.

Key Features:
- Single source of truth for report generation
- Consistent API endpoint usage for all links
- Comprehensive logging and tracking
- Support for all report formats (JSON, Markdown, HTML)
- Claim source file generation with proper links
- Timestamped storage with completion markers
"""

import logging
import json
import os
import shutil
import copy
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from langchain_google_vertexai import ChatVertexAI
from langchain_core.prompts import ChatPromptTemplate

from verityngn.config.settings import AGENT_MODEL_NAME, MAX_OUTPUT_TOKENS_2_0_FLASH, PROJECT_ID, VERTEX_LOCATION
from verityngn.models.report import VerityReport
from verityngn.services.report.markdown_generator import generate_markdown_report
from verityngn.services.report.html_generator import generate_html_report
from verityngn.services.report.fast_html_generator import generate_fast_html_report
from verityngn.utils.llm_utils import invoke_text_prompt_with_fallback
from verityngn.services.storage.timestamped_storage import timestamped_storage
from verityngn.utils.html_to_pdf import async_convert_html_content_to_pdf
from verityngn.services.report.evidence_utils import (
    enhance_source_credibility,
    search_youtube_counter_intelligence,
    analyze_youtube_evidence_content,
    generate_press_release_sources_file,
    generate_youtube_sources_file,
)
from verityngn.services.report.report_sanitize import (
    apply_audit_and_sanitize,
    report_to_persisted_dict,
)
from verityngn.services.storage.yt_artefact_cleanup import (
    capture_info_audit,
    cleanup_yt_api_artefacts,
)

logger = logging.getLogger(__name__)

# System tracking
REPORT_SYSTEMS = {
    "unified_generator": "✅ ACTIVE: Unified report generation system (single source of truth)",
    "run_generate_report": "✅ ACTIVE: Main workflow report generation (uses unified system)",
    "write_all_reports": "❌ REMOVED: Legacy report generation (redundant - replaced by unified system)", 
    "vi_agent_full": "⚠️ ISOLATED: Old agentic system (separate workflow - no claim source files)",
    "test_report": "✅ ACTIVE: Test report generation (uses unified system)"
}

def log_report_system_usage(system_name: str, video_id: str, function_name: str):
    """Log which report generation system is being used."""
    system_desc = REPORT_SYSTEMS.get(system_name, "Unknown system")
    logger.info(f"🔍 [UNIFIED REPORT SYSTEM] Using {system_name}: {system_desc}")
    logger.info(f"🔍 [UNIFIED REPORT SYSTEM] Video: {video_id}, Function: {function_name}")
    
    # Also log to a dedicated file for tracking
    tracking_logger = logging.getLogger("unified_report_tracking")
    tracking_logger.info(f"{datetime.now().isoformat()} | {system_name} | {video_id} | {function_name} | {system_desc}")

class UnifiedReportGenerator:
    """
    Unified report generator that consolidates all report generation approaches.
    
    This is the single source of truth for report generation in VerityNgn.
    All other report generation systems should eventually be replaced by this.
    """
    
    def __init__(self, video_id: str, out_dir_path: str, user_id: Optional[str] = None):
        self.video_id = video_id
        self.out_dir_path = out_dir_path
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        
        # Create timestamped directory for this report generation (user-scoped when user_id + commercial bucket)
        self.timestamped_dir = timestamped_storage.create_timestamped_directory(video_id, user_id=user_id)
        
        # Ensure output directory exists (for local storage)
        os.makedirs(out_dir_path, exist_ok=True)
        
        log_report_system_usage("unified_generator", video_id, "__init__")
        self.logger.info(f"🕐 [TIMESTAMPED] Using timestamped directory: {self.timestamped_dir}")
    
    async def generate_description_review(self, description: str) -> str:
        """
        Generate a ~200 word review of the video description using VertexAI.
        """
        if not description:
            return "No description available to review."
            
        try:
            prompt = """
            You are VerityNgn, a video verification AI.
            Review the following YouTube video description.
            Write a concise (~200 words) assessment of the description's claims, tone, and potential flags.
            Focus on whether it makes sensational claims, provides sources, or uses manipulative language.

            Description:
            {description}
            """

            text, meta, _response = invoke_text_prompt_with_fallback(
                primary_model=AGENT_MODEL_NAME,
                prompt=prompt.format(description=description[:5000]),
                project_id=PROJECT_ID,
                preferred_tokens=MAX_OUTPUT_TOKENS_2_0_FLASH,
                temperature=0.3,
                logger=self.logger,
            )
            return text
        except Exception as e:
            self.logger.error(f"Error generating description review: {e}")
            return "Review generation failed."

    async def generate_all_reports(self, report: VerityReport) -> Dict[str, str]:
        """
        Generate all report formats using the unified system with timestamped storage.
        
        Args:
            report: The VerityReport object containing all data
            
        Returns:
            Dict containing paths to all generated files
        """
        self.logger.info(f"🚀 [UNIFIED] Generating all reports for {self.video_id}")
        
        try:
            # Coerce dict input into VerityReport to tolerate upstream variations
            if isinstance(report, dict):
                try:
                    from verityngn.models.report import VerityReport as _VerityReport
                    report = _VerityReport(**report)
                except Exception as coerce_err:
                    self.logger.warning(f"[UNIFIED] Coercion of dict->VerityReport failed, normalizing: {coerce_err}")
                    try:
                        # Minimal normalization for common mismatches
                        overall = report.get('overall_assessment')
                        if isinstance(overall, list) and len(overall) == 2:
                            report['overall_assessment'] = (overall[0], overall[1])
                        claims = report.get('claims_breakdown') or []
                        for c in claims:
                            cid = c.get('claim_id')
                            if isinstance(cid, str) and cid.startswith('claim_'):
                                try:
                                    c['claim_id'] = int(cid.split('_')[-1])
                                except Exception:
                                    c['claim_id'] = 0
                            if 'initial_assessment' not in c:
                                vr = c.get('verification_result') or {}
                                c['initial_assessment'] = vr.get('result', 'UNVERIFIED')
                        if not report.get('evidence_summary'):
                            report['evidence_summary'] = []
                        if not report.get('media_embed'):
                            report['media_embed'] = {
                                'video_id': self.video_id,
                            }
                        from verityngn.models.report import VerityReport as _VR2
                        report = _VR2(**report)
                    except Exception as normalize_err:
                        self.logger.error(f"[UNIFIED] Normalization failed: {normalize_err}")
                        raise

            # Collect press release and YouTube evidence from all claims
            all_press_release_sources = []
            all_youtube_evidence = {'counter_evidence': [], 'confirming_evidence': [], 'total_videos_analyzed': 0}
            
            if hasattr(report, 'claims_breakdown') and report.claims_breakdown:
                for claim in report.claims_breakdown:
                    sources_to_process = []
                    if claim.verification_result and isinstance(claim.verification_result, dict):
                        sources_from_verification = claim.verification_result.get("sources", [])
                        sources_to_process.extend(sources_from_verification)
                    
                    if hasattr(claim, 'evidence_sources') and claim.evidence_sources:
                        sources_to_process.extend(claim.evidence_sources)
                    
                    # Process sources for press releases and YouTube evidence
                    for source in sources_to_process:
                        source_dict = source if isinstance(source, dict) else {'url': str(source)}
                        source_type = source_dict.get('source_type', '').lower()
                        url = source_dict.get('url', '')
                        
                        # Check for press release sources
                        if source_type == 'press release' or any(domain in url for domain in [
                            'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'prweb.com',
                            'marketwatch.com', 'newswire.com', 'einnews.com', 'pressrelease.com'
                        ]):
                            all_press_release_sources.append(source_dict)
                        
                        # Check for YouTube counter-evidence
                        if source_type == 'youtube counter-evidence' or source_dict.get('stance') == 'counter':
                            all_youtube_evidence['counter_evidence'].append(source_dict)
                        elif source_type == 'youtube response' or 'youtube.com' in url:
                            all_youtube_evidence['total_videos_analyzed'] += 1
                            if source_dict.get('stance') == 'confirming':
                                all_youtube_evidence['confirming_evidence'].append(source_dict)
            
            # Generate press release and YouTube source reference files
            pr_files = None
            yt_files = None
            
            if all_press_release_sources:
                try:
                    pr_files = generate_press_release_sources_file(self.video_id, all_press_release_sources, self.out_dir_path)
                    self.logger.info(f"Generated press release source files: {pr_files}")
                except Exception as e:
                    self.logger.error(f"Error generating press release source files: {e}")
            
            if (all_youtube_evidence['counter_evidence'] or all_youtube_evidence['confirming_evidence']):
                try:
                    yt_files = generate_youtube_sources_file(self.video_id, all_youtube_evidence, self.out_dir_path)
                    self.logger.info(f"Generated YouTube source files: {yt_files}")
                except Exception as e:
                    self.logger.error(f"Error generating YouTube source files: {e}")
            
            # --- Set press_release_count and youtube_response_count on the report object ---
            press_release_count = len(all_press_release_sources)
            youtube_response_count = len(all_youtube_evidence['counter_evidence']) + len(all_youtube_evidence['confirming_evidence'])
            
            # Set counts on report object
            report.press_release_count = press_release_count
            report.youtube_response_count = youtube_response_count
            
            # Store reference file paths for use in report generation
            if hasattr(report, 'metadata'):
                if not report.metadata:
                    report.metadata = {}
            else:
                report.metadata = {}
                
            if pr_files:
                report.metadata['press_release_files'] = {
                    'markdown': pr_files[0],
                    'html': pr_files[1]
                }
            
            if yt_files:
                report.metadata['youtube_files'] = {
                    'markdown': yt_files[0], 
                    'html': yt_files[1]
                }
            
            # In-RAM description for LLM review only (not persisted in report JSON)
            description_for_review = ""
            if report.media_embed:
                description_for_review = report.media_embed.description or ""

            report_original = copy.deepcopy(report)

            audit = capture_info_audit(self.out_dir_path, self.video_id)
            review_text = await self.generate_description_review(description_for_review)

            apply_audit_and_sanitize(
                report,
                source_info_hash=audit.get("source_info_hash"),
                info_ingested_at=audit.get("info_ingested_at"),
            )
            if not report.metadata:
                report.metadata = {}
            report.metadata["description_review"] = review_text

            # Report families (second _-delimited segment after video_id):
            #   _report.*           — user-controlled original (pre-sanitize snapshot)
            #   _private_report.*   — YouTube-compliant public gallery
            #   _fast_report.html   — compliant CRAAP teaser
            original_markdown_content, _, _ = generate_markdown_report(report_original, tier="original")
            original_html_content = generate_html_report(report_original, tier="original")
            compliant_markdown_content, _, _ = generate_markdown_report(report, tier="public")
            compliant_html_content = generate_html_report(report, tier="public")
            fast_html_content = generate_fast_html_report(report, review_text)

            self.logger.info(
                f"📊 [UNIFIED] Generated content: original(MD={len(original_markdown_content)}, HTML={len(original_html_content)}), "
                f"compliant(MD={len(compliant_markdown_content)}, HTML={len(compliant_html_content)}), "
                f"FastHTML={len(fast_html_content)} chars"
            )

            for _label, _content in (
                ("original Markdown", original_markdown_content),
                ("original HTML", original_html_content),
                ("compliant Markdown", compliant_markdown_content),
                ("compliant HTML", compliant_html_content),
                ("Fast HTML", fast_html_content),
            ):
                if not _content.strip():
                    self.logger.warning(f"⚠️ [UNIFIED] Generated {_label} content is empty")

            # Set up file paths in timestamped directory (local uses os.path.join; GCS uses "/")
            def _report_path(name: str) -> str:
                if timestamped_storage.storage_backend.value == "local":
                    return os.path.join(self.timestamped_dir, name)
                return f"{self.timestamped_dir}/{name}"

            json_path = _report_path(f"{self.video_id}_report.json")
            markdown_path = _report_path(f"{self.video_id}_report.md")
            html_path = _report_path(f"{self.video_id}_report.html")
            fast_html_path = _report_path(f"{self.video_id}_fast_report.html")
            private_markdown_path = _report_path(f"{self.video_id}_private_report.md")
            private_html_path = _report_path(f"{self.video_id}_private_report.html")
            
            # Write JSON report (editorial-only; no YouTube API statistics at rest)
            persisted = report_to_persisted_dict(report)
            self._write_file(
                json_path,
                json.dumps(persisted, indent=2, cls=CustomJsonEncoder),
            )
            self.logger.info(f"✅ [UNIFIED] Wrote JSON report: {json_path}")

            # Original user-controlled reports (_report.md/.html/.pdf)
            self._write_file(markdown_path, original_markdown_content)
            self.logger.info(f"✅ [UNIFIED] Wrote original Markdown report: {markdown_path}")
            self._write_file(html_path, original_html_content)
            self.logger.info(f"✅ [UNIFIED] Wrote original HTML report: {html_path}")
            self._write_file(fast_html_path, fast_html_content)
            self.logger.info(f"✅ [UNIFIED] Wrote Fast HTML report: {fast_html_path}")

            # Gallery-compliant reports (_private_report.md/.html/.pdf)
            self._write_file(private_markdown_path, compliant_markdown_content)
            self.logger.info(f"✅ [UNIFIED] Wrote gallery-compliant Markdown report: {private_markdown_path}")
            self._write_file(private_html_path, compliant_html_content)
            self.logger.info(f"✅ [UNIFIED] Wrote gallery-compliant HTML report: {private_html_path}")

            # 5. Generate PDF reports from HTML (high-quality using Playwright) for both tiers
            async def _render_pdf(html_for_pdf: str, target_path: str, label: str) -> None:
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                        tmp_pdf_path = tmp_pdf.name
                    result_pdf = await async_convert_html_content_to_pdf(html_for_pdf, tmp_pdf_path)
                    if result_pdf:
                        if timestamped_storage.storage_backend.value == "local":
                            shutil.move(tmp_pdf_path, target_path)
                            self.logger.info(f"✅ [UNIFIED] Generated {label} PDF report: {target_path}")
                        else:
                            success, _ = timestamped_storage.upload_file(tmp_pdf_path, target_path)
                            if success:
                                self.logger.info(f"✅ [UNIFIED] Uploaded {label} PDF report to GCS: {target_path}")
                            else:
                                self.logger.warning(f"⚠️ [UNIFIED] Failed to upload {label} PDF report to GCS")
                            os.unlink(tmp_pdf_path)
                    else:
                        self.logger.warning(
                            f"⚠️ [UNIFIED] {label} PDF generation returned no result. "
                            "If running in Batch, ensure the image has Chromium installed: "
                            "playwright install chromium (and Chromium runtime deps) in Dockerfile.batch."
                        )
                except Exception as pdf_error:
                    self.logger.error(
                        f"⚠️ [UNIFIED] {label} PDF generation failed: {pdf_error}. "
                        "If running in Batch, ensure the image has Chromium: "
                        "playwright install chromium and Chromium runtime deps in Dockerfile.batch."
                    )

            pdf_path = _report_path(f"{self.video_id}_report.pdf")
            private_pdf_path = _report_path(f"{self.video_id}_private_report.pdf")
            await _render_pdf(original_html_content, pdf_path, "original")
            await _render_pdf(compliant_html_content, private_pdf_path, "gallery-compliant")
            
            # No separate claim files to write now (embedded)
            claim_files = [] 
            
            # No separate CI files to write now (embedded)
            ci_files = []
            
            # 🎯 SHERLOCK ENHANCED: Generate DEMO-style counter-intelligence reference files (Keep these for now or remove?)
            # The plan says "This ensures the "Full Report" (final_report.html) works as a single file."
            # I will keep generating them as separate files just in case, but they are not linked in the main report anymore.
            # Actually, the plan says "embed... instead of links to external files".
            # So I should probably skip generating separate claim/CI files if they are not used.
            # The code above already skips generating them because `generate_markdown_report` returns empty dicts.
            
            demo_ci_files = []
            
            # ... (Skipping generation of demo CI files logic if it relies on returning them, but let's check)
            # The previous code generated them based on `youtube_counter_intel` directly from report, so it might still run.
            # I'll keep the demo files generation as they are useful standalone artifacts, even if not linked.
            
            # Generate YouTube counter-intelligence file (DEMO style)
            youtube_counter_intel = getattr(report, 'youtube_counter_intelligence', [])
            if youtube_counter_intel:
                try:
                    from verityngn.services.report.evidence_utils import generate_youtube_counter_intelligence_file
                    yt_md_path, yt_html_path = generate_youtube_counter_intelligence_file(
                        self.video_id, youtube_counter_intel, self.timestamped_dir
                    )
                    demo_ci_files.extend([yt_md_path, yt_html_path])
                    self.logger.info(f"✅ [SHERLOCK DEMO] Generated YouTube counter-intelligence files: {yt_md_path}, {yt_html_path}")
                except Exception as e:
                    self.logger.error(f"❌ Error generating YouTube counter-intelligence files: {e}")
            
            # Generate Press Release counter-intelligence file (DEMO style)
            press_release_counter = getattr(report, 'press_release_counter_intelligence', [])
            if press_release_counter:
                try:
                    from verityngn.services.report.evidence_utils import generate_press_release_counter_intelligence_file
                    pr_md_path, pr_html_path = generate_press_release_counter_intelligence_file(
                        self.video_id, press_release_counter, self.timestamped_dir
                    )
                    demo_ci_files.extend([pr_md_path, pr_html_path])
                    self.logger.info(f"✅ [SHERLOCK DEMO] Generated Press Release counter-intelligence files: {pr_md_path}, {pr_html_path}")
                except Exception as e:
                    self.logger.error(f"❌ Error generating Press Release counter-intelligence files: {e}")
            
            self.logger.info(f"✅ [UNIFIED] Generated {len(claim_files)} claim source files (0 expected)")
            
            # Mark generation as complete (including DEMO CI files)
            all_ci_files = ci_files + demo_ci_files if demo_ci_files else ci_files
            report_metadata = {
                "video_id": self.video_id,
                "claims_count": len(report.claims_breakdown),
                "report_files": [
                    f"{self.video_id}_report.json",
                    f"{self.video_id}_report.md", 
                    f"{self.video_id}_report.html",
                    f"{self.video_id}_fast_report.html",
                    f"{self.video_id}_report.pdf",
                    f"{self.video_id}_private_report.md",
                    f"{self.video_id}_private_report.html",
                    f"{self.video_id}_private_report.pdf"
                ],
                "claim_source_files": [],
                "counter_intelligence_files": [os.path.basename(f) for f in all_ci_files],
                "youtube_counter_intel_files": [os.path.basename(f) for f in demo_ci_files if "youtube_counter_intel" in f],
                "press_release_counter_intel_files": [os.path.basename(f) for f in demo_ci_files if "press_release_counter_intel" in f]
            }
            
            success = timestamped_storage.mark_generation_complete(
                self.timestamped_dir, 
                self.video_id, 
                report_metadata
            )
            
            if success:
                self.logger.info(f"✅ [TIMESTAMPED] Marked report generation complete")
                
                # Clean up old versions (keep last 5)
                timestamped_storage.cleanup_old_versions(self.video_id, keep_count=5)
            else:
                self.logger.warning(f"⚠️ [TIMESTAMPED] Failed to mark generation complete")

            try:
                cleanup_yt_api_artefacts(self.out_dir_path, self.video_id)
            except Exception as cleanup_exc:
                self.logger.warning("YT artefact cleanup after report write: %s", cleanup_exc)
            
            return {
                "json_path": json_path,
                "markdown_path": markdown_path,
                "html_path": html_path,
                "fast_html_path": fast_html_path,
                "private_markdown_path": private_markdown_path,
                "private_html_path": private_html_path,
                "private_pdf_path": private_pdf_path,
                "pdf_path": pdf_path,
                "claim_files": claim_files,
                "timestamped_dir": self.timestamped_dir
            }
            
        except Exception as e:
            self.logger.error(f"❌ [UNIFIED] Report generation failed: {e}")
            raise
    
    def _write_file(self, file_path: str, content: str):
        """Write content to a file, handling both local and GCS storage."""
        if timestamped_storage.storage_backend.value == "local":
            # For local storage, write directly
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            # For GCS, upload the file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                success, _ = timestamped_storage.upload_file(temp_file_path, file_path)
                if not success:
                    raise Exception(f"Failed to upload {file_path} to GCS")
            finally:
                os.unlink(temp_file_path)
    
    def _generate_claim_source_html(self, claim_id: str, source_content: str):
        """Generate HTML version of claim source file with proper API links."""
        try:
            from markdown_it import MarkdownIt
            md_parser = MarkdownIt("gfm-like", {"html": True, "linkify": True, "typographer": True})
            html_body = md_parser.render(source_content)
            
            # Create HTML wrapper with proper API links
            html_source_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sources for {claim_id.replace('_', ' ').title()} - {self.video_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 1.5em;
        }}
        h1 {{
            font-size: 2em;
            border-bottom: 2px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding-left: 16px;
            margin-left: 0;
            background-color: #f6f8fa;
            padding: 10px 16px;
            border-radius: 3px;
        }}
        .back-link {{
            margin-bottom: 20px;
            display: inline-block;
            background-color: #0366d6;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
        }}
        .back-link:hover {{
            background-color: #0256cc;
            color: white;
        }}
    </style>
</head>
<body>
    <a href="../report.html" class="back-link">← Back to Main Report</a>
    {html_body}
</body>
</html>"""
            
            # Write HTML version
            if timestamped_storage.storage_backend.value == "local":
                html_source_file_path = os.path.join(self.timestamped_dir, f"{self.video_id}_{claim_id}_sources.html")
            else:
                html_source_file_path = f"{self.timestamped_dir}/{self.video_id}_{claim_id}_sources.html"
            
            self._write_file(html_source_file_path, html_source_content)
            self.logger.info(f"✅ [UNIFIED] Wrote HTML claim source: {html_source_file_path}")
            
        except Exception as e:
            self.logger.error(f"❌ [UNIFIED] Error generating HTML claim source for {claim_id}: {e}")
    
    def _generate_counter_intel_html(self, ci_id: str, ci_content: str):
        """🚀 SHERLOCK: Generate HTML version of counter-intelligence file."""
        try:
            # Convert markdown to HTML body
            import markdown
            md = markdown.Markdown(extensions=['tables', 'fenced_code'])
            html_body = md.convert(ci_content)
            
            # Wrap in HTML document
            html_ci_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Counter-Intelligence Analysis - {ci_id}</title>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            line-height: 1.6; 
        }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            background-color: #007cba;
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            text-decoration: none;
        }}
        .back-link:hover {{
            background-color: #0256cc;
            color: white;
        }}
        .ci-header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <a href="../report.html" class="back-link">← Back to Main Report</a>
    <div class="ci-header">
        <h1>🕵️ Counter-Intelligence Analysis</h1>
        <p>Detailed counter-intelligence findings for this specific claim</p>
    </div>
    {html_body}
</body>
</html>"""
            
            # Write HTML version
            if timestamped_storage.storage_backend.value == "local":
                html_ci_file_path = os.path.join(self.timestamped_dir, f"{self.video_id}_{ci_id}.html")
            else:
                html_ci_file_path = f"{self.timestamped_dir}/{self.video_id}_{ci_id}.html"
            
            self._write_file(html_ci_file_path, html_ci_content)
            self.logger.info(f"✅ [SHERLOCK] Wrote HTML counter-intel file: {html_ci_file_path}")
            
        except Exception as e:
            self.logger.error(f"❌ [SHERLOCK] Error generating HTML counter-intel for {ci_id}: {e}")

# Custom JSON encoder for datetime and other objects
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Path):
            return str(o)
        # Fix for Pydantic v2 - use model_dump instead of __pydantic_serializer__
        if hasattr(o, 'model_dump'):
            return o.model_dump()
        if hasattr(o, '__pydantic_serializer__'):
            # For Pydantic v2, use model_dump() method instead
            if hasattr(o, 'model_dump'):
                return o.model_dump()
            else:
                return str(o)
        return super().default(o)

def create_unified_generator(video_id: str, out_dir_path: str, user_id: Optional[str] = None) -> UnifiedReportGenerator:
    """Factory function to create a unified report generator."""
    return UnifiedReportGenerator(video_id, out_dir_path, user_id=user_id)

# Convenience function for backward compatibility
def generate_unified_reports(report: VerityReport, video_id: str, out_dir_path: str, user_id: Optional[str] = None) -> Dict[str, str]:
    """Generate all reports using the unified system."""
    generator = create_unified_generator(video_id, out_dir_path, user_id=user_id)
    return generator.generate_all_reports(report) 