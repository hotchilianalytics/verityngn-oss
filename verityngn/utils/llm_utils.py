import re
from typing import Optional, Dict, Any


def _normalize_model_name(model_name: str) -> str:
    name = (model_name or "").lower()
    # Common aliases
    name = name.replace("chat-", "").replace("vertex-", "")
    return name


def get_model_max_tokens(model_name: str) -> int:
    """Return the known max output tokens for a Gemini model family.

    Defaults to 8192 if unknown.
    """
    name = _normalize_model_name(model_name)
    # Gemini 2.5 families (Flash/Pro) - use 8k for Cloud Run compatibility
    if re.search(r"gemini[-_]?2\.5", name):
        return 8192
    # Gemini 2.0 Flash families commonly allow up to ~8k
    if re.search(r"gemini[-_]?2\.0", name) or "flash" in name:
        return 8192
    # Fallback conservative default
    return 8192


def get_preferred_output_tokens(model_name: str, preferred_tokens: int = 32768) -> int:
    """Return the preferred max_output_tokens bounded by the model's maximum.

    - Prefer 32k by default
    - If the model supports less (e.g., 8k), cap to its max
    - If the model supports more (e.g., 64k for 2.5), keep preferred unless caller wants otherwise
    """
    return min(preferred_tokens, get_model_max_tokens(model_name))


def build_langchain_vertex_kwargs(model_name: str, *, preferred_tokens: int = 32768, temperature: Optional[float] = None, top_p: Optional[float] = None) -> Dict[str, Any]:
    """Return keyword args for ChatVertexAI/VertexAI constructors with sane token limits."""
    kwargs: Dict[str, Any] = {
        "model_name": model_name,
        "max_output_tokens": get_preferred_output_tokens(model_name, preferred_tokens),
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    if top_p is not None:
        kwargs["top_p"] = top_p
    return kwargs


def build_genai_config(model_name: str, *, preferred_tokens: int = 32768, response_mime_type: str = "application/json") -> Dict[str, Any]:
    """Return config for google.genai Client.models.generate_content()."""
    return {
        "response_mime_type": response_mime_type,
        "max_output_tokens": get_preferred_output_tokens(model_name, preferred_tokens),
    }


