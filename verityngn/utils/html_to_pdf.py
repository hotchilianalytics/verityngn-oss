"""
HTML to PDF Conversion using Playwright (Headless Chrome)
=========================================================

This module provides high-quality HTML to PDF conversion using Playwright,
which uses a real Chrome browser engine to render HTML exactly as it appears
in a browser, then exports to PDF.

This replaces the previous markdown-pdf based approach which produced
low-quality output due to loss of CSS styling.

Usage:
    from verityngn.utils.html_to_pdf import convert_html_file_to_pdf, convert_html_content_to_pdf
    
    # Convert an HTML file to PDF (sync)
    convert_html_file_to_pdf("report.html", "report.pdf")
    
    # Convert HTML content string to PDF (async)
    await async_convert_html_content_to_pdf("<html>...</html>", "report.pdf")

Requirements:
    pip install playwright
    playwright install chromium
"""

import os
import logging
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

_PLAYWRIGHT_CHANNEL_FALLBACKS = ("chrome", "msedge")

# CSS injected to optimize for print (accordions are opened via JS)
PRINT_OPTIMIZATION_CSS = """
/* Style for expanded accordions */
details {
    display: block !important;
    border: 1px solid #e1e4e8 !important;
    border-radius: 6px !important;
    margin-bottom: 16px !important;
    page-break-inside: avoid;
}
details[open] {
    display: block !important;
}
details > summary {
    display: block !important;
    padding: 12px 16px !important;
    background-color: #f6f8fa !important;
    border-radius: 6px 6px 0 0 !important;
    font-weight: 600 !important;
    list-style: none !important;
    cursor: default !important;
}
details > summary::marker,
details > summary::-webkit-details-marker {
    display: none !important;
}
details > div {
    display: block !important;
    padding: 16px !important;
    border-radius: 0 0 6px 6px !important;
}

/* Ensure links are visible and styled */
a {
    color: #0366d6 !important;
    text-decoration: underline !important;
}
ul li a {
    word-break: break-all;
}

/* Page break control */
h1, h2, h3, h4 {
    page-break-after: avoid;
}
table {
    page-break-inside: avoid;
}
.claim-section, .source-section {
    page-break-inside: avoid;
}

/* Ensure backgrounds print */
* {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}
"""

# JavaScript to expand all accordions before PDF generation
EXPAND_ACCORDIONS_JS = """
() => {
    // Open all details elements
    document.querySelectorAll('details').forEach(details => {
        details.setAttribute('open', 'true');
    });
    // Return count for logging
    return document.querySelectorAll('details[open]').length;
}
"""

# Default PDF margins
DEFAULT_MARGIN = {
    "top": "0.5in",
    "bottom": "0.5in",
    "left": "0.5in",
    "right": "0.5in"
}


def _is_missing_browser_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "executable doesn't exist" in msg or "browserType.launch" in msg


async def _launch_async_browser_with_fallback(playwright_obj: Any):
    """Prefer bundled Chromium, then fall back to installed browser channels."""
    try:
        return await playwright_obj.chromium.launch(headless=True)
    except Exception as exc:
        if not _is_missing_browser_error(exc):
            raise
        logger.warning(
            "Playwright bundled Chromium unavailable; trying local browser channels: %s",
            ", ".join(_PLAYWRIGHT_CHANNEL_FALLBACKS),
        )
        for channel in _PLAYWRIGHT_CHANNEL_FALLBACKS:
            try:
                browser = await playwright_obj.chromium.launch(headless=True, channel=channel)
                logger.info("Using Playwright channel fallback: %s", channel)
                return browser
            except Exception as channel_exc:
                logger.warning("Playwright channel %s unavailable: %s", channel, channel_exc)
        raise


def _launch_sync_browser_with_fallback(playwright_obj: Any):
    """Prefer bundled Chromium, then fall back to installed browser channels."""
    try:
        return playwright_obj.chromium.launch(headless=True)
    except Exception as exc:
        if not _is_missing_browser_error(exc):
            raise
        logger.warning(
            "Playwright bundled Chromium unavailable; trying local browser channels: %s",
            ", ".join(_PLAYWRIGHT_CHANNEL_FALLBACKS),
        )
        for channel in _PLAYWRIGHT_CHANNEL_FALLBACKS:
            try:
                browser = playwright_obj.chromium.launch(headless=True, channel=channel)
                logger.info("Using Playwright channel fallback: %s", channel)
                return browser
            except Exception as channel_exc:
                logger.warning("Playwright channel %s unavailable: %s", channel, channel_exc)
        raise


async def async_convert_html_file_to_pdf(
    html_path: str,
    output_path: str,
    format: str = "A4",
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None,
    landscape: bool = False
) -> Optional[str]:
    """
    Convert an HTML file to PDF using Playwright Async API.
    
    Args:
        html_path: Path to the HTML file to convert
        output_path: Path where the PDF will be saved
        format: Paper format - "A4", "Letter", "Legal", etc.
        print_background: Whether to print background colors/images
        margin: Dict with top, bottom, left, right margins
        landscape: Whether to use landscape orientation
        
    Returns:
        Path to the generated PDF, or None if conversion failed
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None
    
    margin = margin or DEFAULT_MARGIN
    html_path = os.path.abspath(html_path)
    
    if not os.path.exists(html_path):
        logger.error(f"HTML file not found: {html_path}")
        return None
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Converting HTML to PDF (Async): {html_path} -> {output_path}")
        
        async with async_playwright() as p:
            # Launch headless Chrome
            browser = await _launch_async_browser_with_fallback(p)
            page = await browser.new_page()
            
            # Navigate to the HTML file
            await page.goto(f"file://{html_path}", wait_until="networkidle")
            
            # Expand all accordion (details) elements via JavaScript
            accordions_opened = await page.evaluate(EXPAND_ACCORDIONS_JS)
            logger.info(f"Expanded {accordions_opened} accordion elements")
            
            # Inject CSS to optimize for print
            await page.add_style_tag(content=PRINT_OPTIMIZATION_CSS)
            
            # Small delay to ensure styles and JS changes are applied
            await asyncio.sleep(0.5)
            
            # Generate PDF
            await page.pdf(
                path=output_path,
                format=format,
                print_background=print_background,
                margin=margin,
                landscape=landscape
            )
            
            await browser.close()
        
        logger.info(f"✅ PDF generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ PDF conversion failed: {e}")
        return None


async def async_convert_html_content_to_pdf(
    html_content: str,
    output_path: str,
    format: str = "A4",
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None,
    landscape: bool = False
) -> Optional[str]:
    """
    Convert HTML content string to PDF using Playwright Async API.
    """
    # Write HTML content to a temporary file
    with tempfile.NamedTemporaryFile(
        suffix=".html",
        delete=False,
        mode="w",
        encoding="utf-8"
    ) as f:
        f.write(html_content)
        temp_path = f.name
    
    try:
        return await async_convert_html_file_to_pdf(
            html_path=temp_path,
            output_path=output_path,
            format=format,
            print_background=print_background,
            margin=margin,
            landscape=landscape
        )
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def convert_html_file_to_pdf(
    html_path: str,
    output_path: str,
    format: str = "A4",
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None,
    landscape: bool = False
) -> Optional[str]:
    """
    Convert an HTML file to PDF using Playwright Sync API.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed.")
        return None
    
    margin = margin or DEFAULT_MARGIN
    html_path = os.path.abspath(html_path)
    
    if not os.path.exists(html_path):
        logger.error(f"HTML file not found: {html_path}")
        return None
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Converting HTML to PDF (Sync): {html_path} -> {output_path}")
        
        with sync_playwright() as p:
            browser = _launch_sync_browser_with_fallback(p)
            page = browser.new_page()
            page.goto(f"file://{html_path}", wait_until="networkidle")
            page.evaluate(EXPAND_ACCORDIONS_JS)
            page.add_style_tag(content=PRINT_OPTIMIZATION_CSS)
            import time
            time.sleep(0.5)
            page.pdf(
                path=output_path,
                format=format,
                print_background=print_background,
                margin=margin,
                landscape=landscape
            )
            browser.close()
        
        logger.info(f"✅ PDF generated successfully: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"❌ PDF conversion failed: {e}")
        return None


def convert_html_content_to_pdf(
    html_content: str,
    output_path: str,
    format: str = "A4",
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None,
    landscape: bool = False
) -> Optional[str]:
    """
    Convert HTML content string to PDF using Playwright Sync API.
    """
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html_content)
        temp_path = f.name
    try:
        return convert_html_file_to_pdf(temp_path, output_path, format, print_background, margin, landscape)
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def batch_convert_html_to_pdf(
    input_dir: str,
    output_dir: str,
    format: str = "A4",
    print_background: bool = True,
    margin: Optional[Dict[str, str]] = None
) -> List[str]:
    """
    Convert all HTML files in a directory to PDF (Sync).
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return []
    
    output_path.mkdir(parents=True, exist_ok=True)
    html_files = list(input_path.glob("*.html"))
    logger.info(f"Found {len(html_files)} HTML files to convert")
    
    successful = []
    for i, html_file in enumerate(html_files, 1):
        pdf_name = html_file.stem + ".pdf"
        pdf_path = output_path / pdf_name
        logger.info(f"[{i}/{len(html_files)}] Converting {html_file.name}...")
        result = convert_html_file_to_pdf(str(html_file), str(pdf_path), format, print_background, margin)
        if result:
            successful.append(result)
    
    logger.info(f"✅ Batch conversion complete: {len(successful)}/{len(html_files)} successful")
    return successful


# Convenience aliases
convert_html_to_pdf = convert_html_file_to_pdf
async_convert_html_to_pdf = async_convert_html_file_to_pdf
