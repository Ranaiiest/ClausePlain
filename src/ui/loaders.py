"""Lightweight status helpers for the Streamlit app."""
from __future__ import annotations

from pathlib import Path

import yaml

from src.utils.config import apply_env_overrides, resolve_secret

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "config.yaml"


def load_config_dict() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return apply_env_overrides(raw)


def llm_status() -> tuple[bool, str]:
    import src.utils.config  # noqa: F401  # loads .env

    key = resolve_secret("GROQ_API_KEY")
    if not key:
        return False, "Add GROQ_API_KEY in .env or Streamlit secrets"
    if not key.startswith("gsk_"):
        return False, "GROQ_API_KEY should start with gsk_"
    model = resolve_secret("GROQ_MODEL") or "openai/gpt-oss-20b"
    return True, f"Groq ready · {model}"
