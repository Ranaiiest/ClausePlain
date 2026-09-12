"""Groq / OpenAI-compatible engine unit tests (no live API)."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.llm.engine import LLMEngineError, LLMResponse, OpenAIEngine, build_llm_engine
from src.utils.config import LLMConfig


def test_build_llm_engine_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported"):
        build_llm_engine(LLMConfig(provider="ollama"))


def test_engine_requires_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(LLMEngineError, match="Missing API key"):
        OpenAIEngine(LLMConfig())


def test_engine_json_mode_uses_prompt_not_groq_schema(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"clause_found": false}'))]
    )
    with patch("src.llm.engine.OpenAI", return_value=mock_client):
        engine = OpenAIEngine(LLMConfig())
        result = engine.generate("prompt", json_mode=True)

    assert isinstance(result, LLMResponse)
    assert "clause_found" in result.text
    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "response_format" not in kwargs
    assert kwargs["reasoning_effort"] == "low"
    assert kwargs["temperature"] == 1
    assert kwargs["max_completion_tokens"] == 1024
    assert kwargs["model"] == "openai/gpt-oss-20b"


def test_engine_respects_max_tokens_override(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok": true}'))]
    )
    with patch("src.llm.engine.OpenAI", return_value=mock_client):
        engine = OpenAIEngine(LLMConfig())
        engine.generate("prompt", json_mode=True, max_tokens=4096)

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert kwargs["max_completion_tokens"] == 4096


def test_engine_summary_is_plain_text(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="A short summary."))]
    )
    with patch("src.llm.engine.OpenAI", return_value=mock_client):
        engine = OpenAIEngine(LLMConfig())
        result = engine.generate("summarize", json_mode=False)

    kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "response_format" not in kwargs
    assert result.text == "A short summary."
