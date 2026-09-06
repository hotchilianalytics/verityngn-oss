from __future__ import annotations

from verityngn.utils.llm_utils import (
    get_vertex_fallback_matrix,
    is_retryable_model_error,
)


def test_vertex_fallback_matrix_default_order(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.delenv("VERTEX_FALLBACK_MODELS", raising=False)
    monkeypatch.delenv("VERTEX_FALLBACK_LOCATIONS", raising=False)
    matrix = get_vertex_fallback_matrix("gemini-3.8-flash")

    assert matrix[0]["backend"] == "vertex"
    assert matrix[0]["model"] == "gemini-3.8-flash"
    assert matrix[0]["location"] == "global"

    pairs = [(m["backend"], m["model"], m["location"]) for m in matrix]
    assert ("vertex", "gemini-3.6-flash", "global") in pairs
    assert ("vertex", "gemini-2.5-flash", "us-central1") in pairs
    assert ("developer", "gemini-3.8-flash", "") in pairs
    assert ("developer", "gemini-2.5-flash", "") in pairs


def test_vertex_fallback_matrix_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_STUDIO_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("VERITY_GEMINI_KEY", raising=False)
    matrix = get_vertex_fallback_matrix("gemini-3.8-flash")
    assert all(m["backend"] == "vertex" for m in matrix)


def test_retryable_model_error_signatures():
    assert is_retryable_model_error(RuntimeError("404 model not found"))
    assert is_retryable_model_error(RuntimeError("Publisher model was not found in us-central1"))
    assert is_retryable_model_error(RuntimeError("503 service unavailable"))
    assert not is_retryable_model_error(RuntimeError("JSON parse failure"))
