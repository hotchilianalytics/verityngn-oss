"""
Gemini Deep Research client (isolated drop-in for the vetted Colab logic).

Uses the unified ``google-genai`` SDK with the native ``google_search`` grounding
tool, exactly as in the vetted ``platinum_pipeline.py``. Credentials resolve to a
Gemini Developer API key by default, or Vertex AI (project+location/ADC) when
``DEEP_RESEARCH_USE_VERTEX`` is set.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from verityngn.config.settings import (
    DEEP_RESEARCH_API_KEY,
    DEEP_RESEARCH_FALLBACK_MODEL,
    DEEP_RESEARCH_MODEL,
    DEEP_RESEARCH_PROMPT_VERSION,
    DEEP_RESEARCH_TEMPERATURE,
    DEEP_RESEARCH_USE_VERTEX,
    PROJECT_ID,
    VERTEX_LOCATION,
)

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "dr_prompt_v1.md"


class DeepResearchConfigError(RuntimeError):
    """Raised when the Deep Research client cannot be configured (missing key/SDK)."""


@dataclass
class DeepResearchResult:
    """Result of a single Deep Research generation."""

    markdown: str
    grounding_metadata: str
    model_id: str
    prompt_version: str
    queries: List[str] = field(default_factory=list)

    @property
    def output_bytes(self) -> int:
        return len((self.markdown or "").encode("utf-8"))


def _load_prompt() -> Tuple[str, str]:
    """Return (system_instruction, user_prompt_prefix) from the versioned prompt file."""
    text = _PROMPT_PATH.read_text(encoding="utf-8")
    system_marker = "## SYSTEM_INSTRUCTION"
    user_marker = "## USER_PROMPT_PREFIX"
    if system_marker not in text or user_marker not in text:
        raise DeepResearchConfigError(
            f"Prompt file {_PROMPT_PATH} missing required headers"
        )
    after_system = text.split(system_marker, 1)[1]
    system_part, user_part = after_system.split(user_marker, 1)
    return system_part.strip(), user_part.strip()


def _build_client():
    """Construct a google-genai client for API-key or Vertex mode."""
    try:
        from google import genai  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise DeepResearchConfigError(
            "google-genai SDK not installed. Add 'google-genai' to requirements.txt "
            "(pip install google-genai)."
        ) from exc

    if DEEP_RESEARCH_USE_VERTEX:
        logger.info(
            "[deep-research] using Vertex AI (project=%s location=%s)",
            PROJECT_ID,
            VERTEX_LOCATION,
        )
        return genai.Client(vertexai=True, project=PROJECT_ID, location=VERTEX_LOCATION)

    if not DEEP_RESEARCH_API_KEY:
        raise DeepResearchConfigError(
            "No Deep Research API key. Set VERITY_GEMINI_KEY / GEMINI_API_KEY / "
            "GOOGLE_API_KEY, or set DEEP_RESEARCH_USE_VERTEX=true to use Vertex/ADC."
        )
    return genai.Client(api_key=DEEP_RESEARCH_API_KEY)


def _extract_grounding(response: Any) -> Tuple[str, List[str]]:
    """Pull grounding metadata string + best-effort search queries from a response."""
    grounding_str = "No grounding metadata returned."
    queries: List[str] = []
    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            gm = getattr(candidates[0], "grounding_metadata", None)
            if gm is not None:
                grounding_str = str(gm)
                wq = getattr(gm, "web_search_queries", None)
                if isinstance(wq, (list, tuple)):
                    queries = [str(q) for q in wq]
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[deep-research] grounding metadata extraction failed: %s", exc)
    return grounding_str, queries


def run_deep_research(sanitized_data: Dict[str, Any]) -> DeepResearchResult:
    """
    Run the Gemini Deep Research generation over already-sanitized report data.

    Mirrors the vetted pipeline: low temperature, native google_search grounding,
    strict-citation system instruction. Retries once with the fallback model on
    a model-availability error.
    """
    from google.genai import types  # type: ignore

    system_instruction, user_prefix = _load_prompt()
    client = _build_client()

    config = types.GenerateContentConfig(
        temperature=DEEP_RESEARCH_TEMPERATURE,
        tools=[{"google_search": {}}],
        system_instruction=system_instruction,
    )
    prompt = f"{user_prefix}\n\nDATA:\n{json.dumps(sanitized_data, indent=2)}"

    models_to_try = [DEEP_RESEARCH_MODEL]
    if DEEP_RESEARCH_FALLBACK_MODEL and DEEP_RESEARCH_FALLBACK_MODEL != DEEP_RESEARCH_MODEL:
        models_to_try.append(DEEP_RESEARCH_FALLBACK_MODEL)

    last_exc: Optional[Exception] = None
    for model_id in models_to_try:
        try:
            logger.info("[deep-research] dispatching to model=%s", model_id)
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            markdown = getattr(response, "text", "") or ""
            grounding_str, queries = _extract_grounding(response)
            return DeepResearchResult(
                markdown=markdown,
                grounding_metadata=grounding_str,
                model_id=model_id,
                prompt_version=DEEP_RESEARCH_PROMPT_VERSION,
                queries=queries,
            )
        except Exception as exc:  # noqa: BLE001 - fall through to fallback model
            last_exc = exc
            msg = str(exc).lower()
            if any(s in msg for s in ("not found", "404", "permission", "unsupported", "invalid model")):
                logger.warning("[deep-research] model %s unavailable (%s); trying next", model_id, exc)
                continue
            raise

    raise DeepResearchConfigError(
        f"Deep Research generation failed for all models {models_to_try}: {last_exc}"
    )
