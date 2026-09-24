import json
import logging
import os
import re
from typing import Optional, Dict, Any, List, Tuple


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
    from verityngn.config.settings import PROJECT_ID, VERTEX_LOCATION

    kwargs: Dict[str, Any] = {
        "model_name": model_name,
        "project": PROJECT_ID,
        "location": VERTEX_LOCATION or "global",
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


def _fallback_logger(logger: Optional[logging.Logger] = None) -> logging.Logger:
    return logger or logging.getLogger(__name__)


def get_vertex_fallback_matrix(primary_model: str) -> List[Dict[str, Any]]:
    """
    Ordered fallback plan for Gemini calls.

    Default policy:
    1. primary model on Vertex global
    2. configured fallback models on Vertex global
    3. configured fallback models on Vertex us-central1
    4. primary + fallback models on Developer API
    """
    primary = (primary_model or "").strip() or "gemini-3.8-flash"
    vertex_locations = [
        s.strip() for s in os.getenv("VERTEX_FALLBACK_LOCATIONS", "global,us-central1").split(",") if s.strip()
    ]
    fallback_models = [
        s.strip()
        for s in os.getenv("VERTEX_FALLBACK_MODELS", "gemini-3.6-flash,gemini-2.5-flash").split(",")
        if s.strip()
    ]
    developer_fallback = os.getenv("ALLOW_DEVELOPER_API_FALLBACK", "true").lower() in ("1", "true", "yes", "t")
    api_key = (
        os.getenv("VERITY_GEMINI_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_AI_STUDIO_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    ).strip()

    matrix: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str, str]] = set()

    def _add(backend: str, model: str, location: str = "") -> None:
        key = (backend, model, location)
        if not model or key in seen:
            return
        seen.add(key)
        matrix.append(
            {
                "backend": backend,
                "model": model,
                "location": location,
                "api_key": api_key if backend == "developer" else "",
            }
        )

    if vertex_locations:
        _add("vertex", primary, vertex_locations[0])
    for loc in vertex_locations:
        for model in fallback_models:
            _add("vertex", model, loc)
    if developer_fallback and api_key:
        _add("developer", primary)
        for model in fallback_models:
            _add("developer", model)
    return matrix


def is_retryable_model_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    needles = (
        "404",
        "not found",
        "invalid model",
        "unsupported",
        "permission",
        "location",
        "publisher model",
        "operation not permitted",
        "reauthentication is needed",
        "refresherror",
        "resource exhausted",
        "temporarily unavailable",
        "service unavailable",
        "503",
    )
    return any(n in msg for n in needles)


def generate_content_with_fallback(
    *,
    primary_model: str,
    contents: Any,
    config: Any,
    project_id: str,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """Run google.genai generate_content with Vertex/developer fallback."""
    log = _fallback_logger(logger)
    from google import genai  # type: ignore

    last_exc: Optional[Exception] = None
    hops: List[str] = []
    for idx, step in enumerate(get_vertex_fallback_matrix(primary_model), start=1):
        backend = step["backend"]
        model = step["model"]
        location = step.get("location") or ""
        meta = {
            "backend_selected": backend,
            "model_selected": model,
            "location_selected": location or "developer-api",
            "fallback_hops": idx - 1,
        }
        try:
            if backend == "vertex":
                client = genai.Client(vertexai=True, project=project_id, location=location)
            else:
                client = genai.Client(api_key=step.get("api_key") or None)
            log.info(
                "llm_fallback attempting backend=%s model=%s location=%s hop=%d",
                backend,
                model,
                location or "developer-api",
                idx - 1,
            )
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            log.info(
                "llm_fallback success backend=%s model=%s location=%s hops=%d",
                backend,
                model,
                location or "developer-api",
                idx - 1,
            )
            return response, meta
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            hops.append(f"{backend}:{model}:{location or 'developer'}")
            log.warning(
                "llm_fallback miss backend=%s model=%s location=%s err=%s",
                backend,
                model,
                location or "developer-api",
                exc,
            )
            if not is_retryable_model_error(exc):
                raise
    raise RuntimeError(
        f"All fallback attempts failed for {primary_model}: {last_exc} via {hops}"
    )


def invoke_json_prompt_with_fallback(
    *,
    primary_model: str,
    prompt: str,
    project_id: str,
    preferred_tokens: int = 2048,
    temperature: float = 0.2,
    tools: Optional[List[Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Dict[str, Any], str, Dict[str, Any], Any]:
    """Generate JSON text with fallback and parse it best-effort."""
    from google.genai import types  # type: ignore

    cfg_kwargs: Dict[str, Any] = {
        "response_mime_type": "application/json",
        "temperature": temperature,
        "max_output_tokens": get_preferred_output_tokens(primary_model, preferred_tokens),
    }
    if tools:
        cfg_kwargs["tools"] = tools
    response, meta = generate_content_with_fallback(
        primary_model=primary_model,
        contents=prompt,
        config=types.GenerateContentConfig(**cfg_kwargs),
        project_id=project_id,
        logger=logger,
    )
    text = (getattr(response, "text", None) or "").strip()
    parsed: Dict[str, Any] = {}
    if text:
        cleaned = re.sub(r"^```(?:json)?\s*", "", text)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            obj = json.loads(cleaned)
            if isinstance(obj, dict):
                parsed = obj
        except Exception:
            parsed = {}
    return parsed, text, meta, response


def invoke_text_prompt_with_fallback(
    *,
    primary_model: str,
    prompt: str,
    project_id: str,
    preferred_tokens: int = 2048,
    temperature: float = 0.2,
    logger: Optional[logging.Logger] = None,
) -> Tuple[str, Dict[str, Any], Any]:
    """Generate plain text with the shared fallback router."""
    from google.genai import types  # type: ignore

    response, meta = generate_content_with_fallback(
        primary_model=primary_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=get_preferred_output_tokens(primary_model, preferred_tokens),
            temperature=temperature,
        ),
        project_id=project_id,
        logger=logger,
    )
    return (getattr(response, "text", None) or "").strip(), meta, response


