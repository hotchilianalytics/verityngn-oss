import json
import re
from typing import Optional, Dict, Any

def clean_gemini_json(content: str) -> str:
    """
    Clean and fix common JSON issues from Gemini/LLM outputs:
    - Code block markers (``````)
    - Unescaped quotes within string values
    - Excessive repetition (model getting stuck)
    - Incomplete JSON structures
    - Trailing commas
    """
    
    # Step 1: Remove markdown code blocks
    content = content.strip()
    if content.startswith('```json'):
        content = content[7:]
    elif content.startswith('```'):
        content = content[3:]
    if content.endswith('```'):
        content = content[:-3]
    content = content.strip()
    
    # Step 2: Fix excessive repetition (major LLM failure mode)
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if not line.strip():
            cleaned_lines.append(line)
            continue
            
        words = line.split()
        if len(words) > 15:  # Only process long lines
            # Detect repetitive patterns
            cleaned_words = []
            i = 0
            while i < len(words):
                word = words[i]
                
                # Count consecutive repetitions
                repeat_count = 1
                while (i + repeat_count < len(words) and 
                       words[i + repeat_count] == word):
                    repeat_count += 1
                
                # If word repeats more than 3 times, it's likely a generation error
                if repeat_count > 3:
                    # Keep only first instance and maybe one more for context
                    cleaned_words.append(word)
                    if 'bot' in word.lower() or 'leverage' in word.lower():
                        cleaned_words.append(word)  # Keep technical terms
                    i += repeat_count
                    
                    # Check if rest of line is just repetition - if so, stop
                    remaining = words[i:]
                    if len(remaining) > 5:
                        unique_remaining = len(set(remaining))
                        if unique_remaining < len(remaining) * 0.2:  # Less than 20% unique
                            break
                else:
                    cleaned_words.append(word)
                    i += 1
            
            line = ' '.join(cleaned_words)
        
        cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    # Step 3: Fix unescaped quotes in JSON string values
    def escape_internal_quotes(text: str) -> str:
        result = []
        in_string = False
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Skip escaped characters
            if i > 0 and text[i-1] == '\\':
                result.append(char)
                i += 1
                continue
            
            if char == '"':
                if not in_string:
                    # Starting a JSON string
                    result.append(char)
                    in_string = True
                else:
                    # Ending a string or internal quote?
                    # Look ahead to determine context
                    lookahead = text[i+1:i+15].strip()
                    
                    # These patterns indicate end of JSON string value
                    if (lookahead.startswith(',') or 
                        lookahead.startswith('}') or 
                        lookahead.startswith(']') or 
                        lookahead.startswith('\n') or
                        lookahead == ''):
                        result.append(char)
                        in_string = False
                    else:
                        # Internal quote - escape it
                        result.append('\\"')
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result)
    
    content = escape_internal_quotes(content)
    
    # Step 4: Complete incomplete JSON structures
    # Count unmatched braces/brackets
    open_braces = content.count('{') - content.count('}')
    open_brackets = content.count('[') - content.count(']')
    
    # Add missing closers
    content += ']' * max(0, open_brackets)
    content += '}' * max(0, open_braces)
    
    # Step 5: Remove trailing commas before closing braces/brackets
    content = re.sub(r',(\s*[}$$])', r'\1', content)
    
    # Step 6: Fix common quote patterns
    # Handle contractions and possessives that got mangled
    content = re.sub(r"(\w)'(\w)", r"\1'\2", content)  # Fix contractions
    
    return content

def parse_gemini_json(raw_response: str) -> Optional[Dict[Any, Any]]:
    """
    Parse JSON from Gemini response with automatic error correction.
    
    Args:
        raw_response: Raw text output from Gemini
        
    Returns:
        Parsed JSON dict or None if unfixable
        
    Raises:
        ValueError: If JSON cannot be parsed even after cleaning
    """
    # First try parsing as-is
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass
    
    # Apply cleaning and retry
    try:
        cleaned = clean_gemini_json(raw_response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # For debugging - show what we tried to parse
        print(f"JSON parsing failed even after cleaning: {e}")
        print("Attempted to parse:")
        print(cleaned[:300] + "..." if len(cleaned) > 300 else cleaned)
        raise ValueError(f"Could not parse JSON: {e}")

# Utility function for your specific use case
def safe_gemini_json_parse(response_content: str) -> Dict[Any, Any]:
    """
    Safe wrapper that always returns a dict, even if parsing fails.
    """
    try:
        return parse_gemini_json(response_content)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Warning: Could not parse Gemini JSON output: {e}")
        return {
            "error": "JSON parsing failed",
            "raw_content": response_content[:500],  # First 500 chars for debugging
            "error_message": str(e)
        }


