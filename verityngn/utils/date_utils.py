"""
Date utilities for VerityNgn.

Provides consistent date formatting for LLM context injection to prevent
knowledge cutoff date issues where the model incorrectly treats current
dates as "future dates."
"""

from datetime import datetime


def get_current_date_context() -> str:
    """
    Get current date formatted for LLM context injection.
    
    This function provides a human-readable date string that can be injected
    into LLM prompts to inform the model about the actual current date,
    preventing it from incorrectly treating recent sources as "future-dated"
    due to training data cutoff limitations.
    
    Returns:
        str: Current date in format "December 20, 2025"
    """
    now = datetime.now()
    return now.strftime("%B %d, %Y")


def get_current_year() -> int:
    """
    Get the current year as an integer.
    
    Returns:
        int: Current year (e.g., 2025)
    """
    return datetime.now().year


def get_current_date_iso() -> str:
    """
    Get current date in ISO format for logging and metadata.
    
    Returns:
        str: Current date in format "2025-12-20"
    """
    return datetime.now().strftime("%Y-%m-%d")


def get_date_context_prompt_section() -> str:
    """
    Get a complete prompt section about date context for LLM injection.
    
    This provides a standardized block of text that can be inserted into
    any LLM prompt to establish proper date awareness.
    
    Returns:
        str: Multi-line prompt section about current date context
    """
    current_date = get_current_date_context()
    current_year = get_current_year()
    
    return f"""IMPORTANT DATE CONTEXT:
Today's date is {current_date}. When evaluating evidence sources:
- Sources dated on or before {current_date} are valid current sources
- {current_year} is the current year - sources from {current_year} are NOT future-dated
- Do not discount sources simply because they are from {current_year}
- A source from earlier this year (e.g., January {current_year}) is approximately 12 months old at most"""

