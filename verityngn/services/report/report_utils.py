from pathlib import Path
import logging
from typing import Optional
from markdown_it import MarkdownIt

def generate_html_from_markdown(markdown_content: str, template_path: Optional[Path] = None) -> str:
    """
    Convert markdown content to HTML using MarkdownIt.
    
    Args:
        markdown_content: The markdown content to convert
        template_path: Optional path to HTML template file
        
    Returns:
        str: Generated HTML content
    """
    if not template_path:
        template_path = Path(__file__).parent.parent.parent / "template.html"
    
    try:
        # Read template
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()
            
        # Initialize MarkdownIt with basic options
        md = MarkdownIt("gfm-like", {
            "html": True,
            "linkify": True,
            "typographer": True,
            "breaks": True
        })
        
        # Convert markdown to HTML
        html_content = md.render(markdown_content)
        
        # Replace content placeholder in template
        return template_content.replace("{{content}}", html_content)
        
    except Exception as e:
        logging.error(f"Error generating HTML: {e}")
        raise 