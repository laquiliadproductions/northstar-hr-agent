"""Environment-based application settings."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)

class Settings:
    openai_api_key: str
    openai_base_url: str | None
    openai_model: str | None
    embedding_model: str | None

def get_settings() -> Settings:

    """Load application settings without hard-coding secrets."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not api_key or api_key == "replace_with_your_api_key":
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to the local .env file."
        )

    return Settings(
        openai_api_key=api_key,
        openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
        openai_model=os.getenv("OPENAI_MODEL") or None,
        embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL") or None,
    )
