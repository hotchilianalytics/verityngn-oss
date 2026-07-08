import os
import logging
import re
from typing import Optional
from markdown_pdf import MarkdownPdf, Section

logger = logging.getLogger(__name__)

def expand_accordions(text: str) -> str:
    """
    Convert HTML5 <details>/<summary> tags to standard Markdown headers and dividers.
    This ensures that collapsible content is fully visible in static PDF exports.
    Handles attributes in tags and nested structures gracefully.
    """
    # 1. Convert <details ...><summary ...>Title</summary> to ### Title
    # Using re.DOTALL and handling potential attributes in the tags
    text = re.sub(r'<details[^>]*>\s*<summary[^>]*>(.*?)</summary>', r'\n### \1\n\n', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Replace </details> with a horizontal divider to separate sections
    # Using case-insensitive replacement for safety
    text = re.sub(r'</details>', '\n---\n', text, flags=re.IGNORECASE)
    
    return text

def simplify_tables(text: str) -> str:
    """
    Convert Markdown tables to a list-like format.
    Complex tables often cause hangs or layout issues in PDF generation.
    """
    lines = text.split('\n')
    new_lines = []
    table_headers = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and stripped.endswith('|'):
            # It's a table line
            parts = [p.strip() for p in stripped.split('|')[1:-1]]
            
            if not in_table:
                # First line of table - assume headers
                table_headers = parts
                in_table = True
                new_lines.append('\n---')
            elif all(re.match(r'^[:\-\s]+$', p) for p in parts):
                # Divider line (---)
                continue
            else:
                # Data row
                for i, part in enumerate(parts):
                    header = table_headers[i] if i < len(table_headers) else f"Column {i+1}"
                    if part:
                        new_lines.append(f"**{header}**: {part}")
                new_lines.append('---\n')
        else:
            if in_table:
                in_table = False
            new_lines.append(line)
            
    return '\n'.join(new_lines)

def convert_markdown_to_pdf(md_content: str, output_path: str, title: str = "VerityNgn Report") -> Optional[str]:
    """
    Convert Markdown content to a high-quality PDF file using markdown-pdf.
    Automatically expands <details>/<summary> accordions for static PDF viewing.
    """
    try:
        print(f"Starting professional PDF conversion for {output_path}...", flush=True)
        
        # 1. Expand accordions (<details>/<summary>) for PDF
        expanded_md = expand_accordions(md_content)
        
        # 2. Simplify tables to prevent hangs and layout issues
        print("Simplifying tables for PDF layout...", flush=True)
        simplified_md = simplify_tables(expanded_md)
        
        # 3. Clean up any other HTML that might break rendering or cause hangs
        # We strip common container tags and images (remote images can cause hangs)
        # We also strip potentially dangerous or irrelevant tags like script, style, etc.
        # Note: we specifically target tags with attributes as well
        print("Cleaning HTML tags and anchors...", flush=True)
        problematic_tags = r'div|span|p|br|table|tr|td|th|img|iframe|script|style|link|meta|base'
        clean_md = re.sub(f'<(?:{problematic_tags})[^>]*>', '', simplified_md, flags=re.IGNORECASE)
        clean_md = re.sub(f'</(?:{problematic_tags})>', '', clean_md, flags=re.IGNORECASE)
        
        # Remove markdown anchor links that point to internal destinations we might have stripped
        # e.g., [text](#anchor) -> text
        clean_md = re.sub(r'\[([^\]]+)\]\(#[^\)]+\)', r'\1', clean_md)
        
        # 4. Initialize markdown-pdf with professional TOC settings
        # toc_level=2 ensures headers up to level 2 are in the table of contents
        # Note: level 3 (accordions) might cause PyMuPDF "bad hierarchy level" if level 2 is missing
        pdf = MarkdownPdf(toc_level=2)
        
        # 5. Add content as a section
        # We wrap the content with the document title
        print("Adding content to PDF section...", flush=True)
        pdf.add_section(Section(f"# {title}\n\n" + clean_md, toc=True))
        
        # 6. Ensure output directory exists (if one is specified)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        
        # 7. Save the PDF
        print(f"Saving PDF to disk: {output_path}...", flush=True)
        pdf.save(output_path)
        print("PDF save complete.", flush=True)
        
        logger.info(f"✅ Professional PDF generated at {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ PDF conversion failed: {e}")
        # Fallback to extremely basic version using fitz if markdown-pdf fails
        try:
            print("Trying fallback PDF conversion...", flush=True)
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            # Simple text insertion - not pretty but ensures an artifact is produced
            page.insert_text((50, 50), f"PDF GENERATION ERROR: Falling back to plain text.\n\nDOCUMENT: {title}\n\n" + md_content[:10000], fontsize=10)
            doc.save(output_path)
            doc.close()
            return output_path
        except Exception as e2:
            logger.error(f"❌ Fallback PDF conversion also failed: {e2}")
            return None
