"""
Configuration-driven design layer.

Loads `configs/config.yaml` into strongly-typed Pydantic models so the
rest of the codebase never touches raw dicts or magic strings. This is
the single source of truth for paths, model names, chunking thresholds,
retrieval parameters, etc.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


class PathsConfig(BaseModel):
    processed_dir: str = "data/processed"
    vectordb_dir: str = "data/processed/chroma"
    log_dir: str = "logs"


class ChunkingConfig(BaseModel):
    small_doc_word_threshold: int = 1500
    chunk_size_tokens: int = 500
    chunk_overlap_tokens: int = 75
    separators: list[str] = Field(
        default_factory=lambda: ["\n\n", "\n", ". ", " ", ""]
    )


class EmbeddingConfig(BaseModel):
    model_name: str = "BAAI/bge-small-en-v1.5"
    device: str = "cpu"
    normalize_embeddings: bool = True
    batch_size: int = 32


class VectorDBConfig(BaseModel):
    collection_name: str = "user_document_chunks"
    persist_directory: str = "data/processed/chroma"
    distance_metric: str = "cosine"


class UploadConfig(BaseModel):
    max_file_mb: float = 10
    max_pages: int = 40
    max_words: int = 25000


class RetrievalConfig(BaseModel):
    top_k: int = 5
    score_threshold: float = 0.0


class LLMConfig(BaseModel):
    provider: str = "groq"
    model_name: str = "openai/gpt-oss-20b"
    api_key_env: str = "GROQ_API_KEY"
    base_url: str = "https://api.groq.com/openai/v1"
    temperature: float = 0.0
    max_tokens: int = 1024
    analysis_max_tokens: int = 6144
    chat_max_tokens: int = 1024
    request_timeout_seconds: int = 120
    max_retries: int = 4
    # Groq GPT-OSS fails `response_format=json_object` (empty failed_generation).
    # Prompt + parser already require JSON.
    use_json_response_format: bool = False
    reasoning_effort: str = "low"


class AppConfig(BaseModel):
    """Root configuration object composing every subsystem's config."""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vectordb: VectorDBConfig = Field(default_factory=VectorDBConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    upload: UploadConfig = Field(default_factory=UploadConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    log_level: str = "INFO"


_CACHED_CONFIG: Optional[AppConfig] = None


def resolve_secret(name: str) -> str:
    """Read a secret from the environment, then Streamlit secrets if present."""
    value = (os.getenv(name) or "").strip()
    if value:
        return value
    try:
        import streamlit as st

        secret = st.secrets.get(name)
        if secret:
            text = str(secret).strip()
            os.environ[name] = text
            return text
    except Exception:
        return ""
    return ""


def apply_env_overrides(raw: dict[str, Any]) -> dict[str, Any]:
    """Override model / endpoint from env. The API key stays in .env only."""
    data = dict(raw)
    llm = dict(data.get("llm") or {})
    if os.getenv("GROQ_MODEL"):
        llm["model_name"] = os.environ["GROQ_MODEL"]
    if os.getenv("GROQ_BASE_URL"):
        llm["base_url"] = os.environ["GROQ_BASE_URL"].rstrip("/")
    data["llm"] = llm
    return data


def load_config(config_path: str = "configs/config.yaml", force_reload: bool = False) -> AppConfig:
    """Load and cache the application configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file relative to the project root.
        force_reload: If True, bypass the in-memory cache and re-read the file.

    Returns:
        A validated `AppConfig` instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
    """
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None and not force_reload:
        return _CACHED_CONFIG

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at '{config_path}'."
        )

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    _CACHED_CONFIG = AppConfig(**apply_env_overrides(raw))
    return _CACHED_CONFIG
