"""
Hosted LLM inference via Groq (OpenAI-compatible Chat Completions).

Default model is `openai/gpt-oss-20b` on Groq's free developer plan.
Llama 3.3 70B is enterprise-only and returns 404 for free API keys.
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from openai import APIError, APITimeoutError, BadRequestError, NotFoundError, OpenAI, RateLimitError

from src.utils.config import LLMConfig, resolve_secret
from src.utils.logger import get_logger

logger = get_logger(__name__)

_JSON_SYSTEM = (
    "You analyze legal documents. Reply with a single JSON object only. "
    "Never invent wording that is not in the provided excerpts."
)

# Prefer models available on Groq's free/developer plan. Llama 3.3 70B is
# enterprise-only and 404s for personal keys.
_GROQ_CHAT_FALLBACKS = (
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
)


class LLMEngineError(Exception):
    """Raised when the LLM backend fails after exhausting retries."""


@dataclass
class LLMResponse:
    """Result of a single LLM completion call."""

    text: str
    latency_seconds: float
    model_name: str


class LLMEngine(ABC):
    """Abstract interface for a hosted LLM completion backend."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a completion for the given prompt."""
        raise NotImplementedError


def _is_model_missing(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "model_not_found" in text or "does not exist" in text or "do not have access" in text


class OpenAIEngine(LLMEngine):
    """Calls Groq or any OpenAI-compatible `base_url` with retries."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._model = config.model_name
        api_key = resolve_secret(config.api_key_env)
        if not api_key:
            raise LLMEngineError(
                f"Missing API key. Set {config.api_key_env} in .env or Streamlit secrets."
            )
        kwargs: dict = {
            "api_key": api_key,
            "timeout": config.request_timeout_seconds,
        }
        if config.base_url:
            kwargs["base_url"] = config.base_url.rstrip("/")
        self._client = OpenAI(**kwargs)
        self._tried_models: set[str] = {config.model_name}

    def _apply_model_kwargs(self, kwargs: dict) -> None:
        kwargs["model"] = self._model
        if "gpt-oss" in self._model:
            kwargs["temperature"] = 1
            if self.config.reasoning_effort:
                kwargs["reasoning_effort"] = self.config.reasoning_effort
        else:
            kwargs["temperature"] = self.config.temperature
            kwargs.pop("reasoning_effort", None)

    def _next_fallback_model(self) -> str | None:
        for name in _GROQ_CHAT_FALLBACKS:
            if name not in self._tried_models:
                return name
        return None

    def _switch_model(self, nxt: str, kwargs: dict) -> None:
        logger.warning("Switching Groq model '{}' → '{}'.", self._model, nxt)
        self._model = nxt
        self._tried_models.add(nxt)
        self._apply_model_kwargs(kwargs)

    def generate(
        self,
        prompt: str,
        *,
        json_mode: bool = False,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        if json_mode:
            messages.insert(0, {"role": "system", "content": _JSON_SYSTEM})

        token_budget = max_tokens if max_tokens is not None else self.config.max_tokens
        enforce_json = json_mode and self.config.use_json_response_format
        kwargs: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_completion_tokens": token_budget,
        }
        if "gpt-oss" in self._model:
            # GPT-OSS on Groq is a reasoning model; temp 0 + json_object often
            # yields empty failed_generation. Keep sampling default and low reasoning.
            kwargs["temperature"] = 1
            if self.config.reasoning_effort:
                kwargs["reasoning_effort"] = self.config.reasoning_effort
        if enforce_json:
            kwargs["response_format"] = {"type": "json_object"}

        last_error: Exception | None = None
        for attempt in range(1, self.config.max_retries + 1):
            self._apply_model_kwargs(kwargs)
            start = time.perf_counter()
            try:
                completion = self._client.chat.completions.create(**kwargs)
                elapsed = time.perf_counter() - start
                choice = completion.choices[0].message.content or ""
                if not choice.strip():
                    extra = getattr(completion.choices[0].message, "reasoning", None)
                    if extra:
                        choice = str(extra)
                return LLMResponse(
                    text=choice,
                    latency_seconds=round(elapsed, 4),
                    model_name=self._model,
                )
            except BadRequestError as exc:
                last_error = exc
                if enforce_json and "response_format" in kwargs:
                    logger.warning("JSON mode rejected by API; retrying as plain text: {}", exc)
                    kwargs.pop("response_format")
                    enforce_json = False
                    continue
                logger.warning(
                    "LLM call failed (attempt {}/{}): {}",
                    attempt,
                    self.config.max_retries,
                    exc,
                )
                if attempt < self.config.max_retries:
                    time.sleep(min(2 ** attempt, 8))
            except RateLimitError as exc:
                last_error = exc
                nxt = self._next_fallback_model()
                if nxt:
                    logger.warning("Groq rate limit on '{}'.", self._model)
                    self._switch_model(nxt, kwargs)
                    continue
                raise LLMEngineError(
                    "Groq daily token quota is exhausted for every fallback model. "
                    f"Wait and retry later. Last error: {exc}"
                ) from exc
            except (NotFoundError, APIError, APITimeoutError, OSError) as exc:
                last_error = exc
                if _is_model_missing(exc):
                    nxt = self._next_fallback_model()
                    if nxt:
                        self._switch_model(nxt, kwargs)
                        continue
                    raise LLMEngineError(
                        f"No Groq chat model available for this API key. Last error: {exc}"
                    ) from exc
                logger.warning(
                    "LLM call failed (attempt {}/{}): {}",
                    attempt,
                    self.config.max_retries,
                    exc,
                )
                if attempt < self.config.max_retries:
                    time.sleep(min(2 ** attempt, 8))

        raise LLMEngineError(
            f"LLM generation failed after {self.config.max_retries} attempts: {last_error}"
        )


def build_llm_engine(config: LLMConfig) -> LLMEngine:
    """Factory: groq / openai / openai_compatible all use the OpenAI SDK."""
    if config.provider in ("groq", "openai", "openai_compatible"):
        return OpenAIEngine(config)
    raise ValueError(f"Unsupported LLM provider: '{config.provider}'")
