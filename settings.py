"""Environment-based application settings."""

from __future__ import annotations
from dataclasses import dataclass

import os

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    """Configuration for an OpenAI-compatible language model provider."""

    llm_provider: str
    llm_api_key: str
    llm_base_url: str | None
    llm_model: str

def get_settings() -> Settings:
    """Load language-model settings without hard-coding secrets."""

    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    if not api_key or api_key == "replace_with_your_api_key":
        raise RuntimeError(
            "LLM_API_KEY is missing. Add it to the local .env file."
        )

    if not model:
        raise RuntimeError(
            "LLM_MODEL is missing. Add it to the local .env file."
        )

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai-compatible").strip(),
        llm_api_key=api_key,
        llm_base_url=os.getenv("LLM_BASE_URL", "").strip() or None,
        llm_model=model,
    )
