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

_PROMPTS_DIR = Path(__file__).parent / "prompts"


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
    grounding_uris: List[str] = field(default_factory=list)

    @property
    def output_bytes(self) -> int:
        return len((self.markdown or "").encode("utf-8"))


def _prompt_path(version: Optional[str] = None) -> Path:
    ver = (version or DEEP_RESEARCH_PROMPT_VERSION or "dr_prompt_v2").strip()
    # Accept bare ids like dr_prompt_v2 or filenames
    name = ver if ver.endswith(".md") else f"{ver}.md"
    path = _PROMPTS_DIR / name
    if not path.is_file():
        fallback = _PROMPTS_DIR / "dr_prompt_v1.md"
        logger.warning(
            "[deep-research] prompt %s missing; falling back to %s", path.name, fallback.name
        )
        return fallback
    return path


def _load_prompt(version: Optional[str] = None) -> Tuple[str, str]:
    """Return (system_instruction, user_prompt_prefix) from the versioned prompt file."""
    prompt_file = _prompt_path(version)
    text = prompt_file.read_text(encoding="utf-8")
    system_marker = "## SYSTEM_INSTRUCTION"
    user_marker = "## USER_PROMPT_PREFIX"
    if system_marker not in text or user_marker not in text:
        raise DeepResearchConfigError(
            f"Prompt file {prompt_file} missing required headers"
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


def _extract_grounding(response: Any) -> Tuple[str, List[str], List[str]]:
    """Pull grounding metadata string, search queries, and grounding URIs."""
    grounding_str = "No grounding metadata returned."
    queries: List[str] = []
    uris: List[str] = []
    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            gm = getattr(candidates[0], "grounding_metadata", None)
            if gm is not None:
                grounding_str = str(gm)
                wq = getattr(gm, "web_search_queries", None)
                if isinstance(wq, (list, tuple)):
                    queries = [str(q) for q in wq]
                chunks = getattr(gm, "grounding_chunks", None) or []
                for ch in chunks:
                    web = getattr(ch, "web", None)
                    if web is None and isinstance(ch, dict):
                        web = ch.get("web")
                    if web is None:
                        continue
                    uri = getattr(web, "uri", None)
                    if uri is None and isinstance(web, dict):
                        uri = web.get("uri") or web.get("url")
                    if uri:
                        uris.append(str(uri))
                # de-dupe preserving order
                seen = set()
                uniq = []
                for u in uris:
                    if u not in seen:
                        seen.add(u)
                        uniq.append(u)
                uris = uniq
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[deep-research] grounding metadata extraction failed: %s", exc)
    return grounding_str, queries, uris


def run_deep_research(sanitized_data: Dict[str, Any]) -> DeepResearchResult:
    """
    Run the Gemini Deep Research generation over already-sanitized report data.

    Mirrors the vetted pipeline: low temperature, native google_search grounding,
    strict-citation system instruction. Retries once with the fallback model on
    a model-availability error.
    """
    from google.genai import types  # type: ignore

    system_instruction, user_prefix = _load_prompt()
    # Reinforce current date so Search tool queries use the correct year (Gemini 3 guidance).
    try:
        from verityngn.utils.date_utils import get_current_date_context

        pack_hint = (
            "Prefer DATA.primary_pack / DATA.primary_urls when present "
            "(domain-class official hosts)."
            if (sanitized_data.get("primary_pack") or sanitized_data.get("legislature_primary_pack"))
            else "Prefer official agency / primary sources matching the claim domain."
        )
        system_instruction = (
            f"{system_instruction}\n\nFor time-sensitive research, today's date is "
            f"{get_current_date_context()}. {pack_hint}"
        )
    except Exception:
        pass

    client = _build_client()

    prompt = f"{user_prefix}\n\nDATA:\n{json.dumps(sanitized_data, indent=2)}"

    models_to_try = [DEEP_RESEARCH_MODEL]
    if DEEP_RESEARCH_FALLBACK_MODEL and DEEP_RESEARCH_FALLBACK_MODEL != DEEP_RESEARCH_MODEL:
        models_to_try.append(DEEP_RESEARCH_FALLBACK_MODEL)

    last_exc: Optional[Exception] = None
    for model_id in models_to_try:
        try:
            logger.info("[deep-research] dispatching to model=%s", model_id)
            # Gemini 3.8+: prefer thinking_level; avoid deprecated temperature on 3.8-only paths.
            cfg_kwargs: Dict[str, Any] = {
                "tools": [{"google_search": {}}],
                "system_instruction": system_instruction,
            }
            if "3.8" in (model_id or ""):
                try:
                    cfg_kwargs["thinking_config"] = types.ThinkingConfig(
                        thinking_level="MEDIUM"
                    )
                except Exception:
                    cfg_kwargs["temperature"] = DEEP_RESEARCH_TEMPERATURE
            else:
                cfg_kwargs["temperature"] = DEEP_RESEARCH_TEMPERATURE
            config = types.GenerateContentConfig(**cfg_kwargs)
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            markdown = getattr(response, "text", "") or ""
            grounding_str, queries, uris = _extract_grounding(response)
            return DeepResearchResult(
                markdown=markdown,
                grounding_metadata=grounding_str,
                model_id=model_id,
                prompt_version=DEEP_RESEARCH_PROMPT_VERSION,
                queries=queries,
                grounding_uris=uris,
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
