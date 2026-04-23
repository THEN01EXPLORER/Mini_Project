"""
Configuration management using pydantic-settings.

Why pydantic-settings instead of raw os.environ?
- Type validation at startup (fail fast, not at runtime)
- IDE autocomplete for config values
- Automatic .env file loading without python-dotenv boilerplate
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via .env file or environment variables.
    Environment variables take precedence over .env file values.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Don't crash on unknown env vars
    )
    
    # API Keys
    gemini_api_key: Annotated[
        str,
        Field(description="Google Gemini API key from AI Studio")
    ]
    
    # Storage
    chroma_persist_dir: Annotated[
        Path,
        Field(
            default=Path("./chroma_db"),
            description="Directory for ChromaDB persistent storage"
        )
    ]
    
    # Rate Limiting - Keep it reasonable to prevent abuse
    rate_limit_per_minute: Annotated[
        int,
        Field(
            default=10,
            ge=1,
            le=100,
            description="Max API requests per minute per IP"
        )
    ]
    
    # Embedding Model
    embedding_model: Annotated[
        str,
        Field(
            default="sentence-transformers/all-MiniLM-L6-v2",
            description="HuggingFace model ID for embeddings"
        )
    ]
    
    # Logging
    log_level: Annotated[
        str,
        Field(
            default="INFO",
            pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
            description="Logging verbosity level"
        )
    ]
    
    # Gemini Model - 2.0 Flash is fast and widely available
    gemini_model: Annotated[
        str,
        Field(
            default="gemini-2.0-flash",
            description="Gemini model to use for text extraction"
        )
    ]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.
    
    Using lru_cache here because settings should be loaded once at startup,
    not re-parsed on every request. This is a common pattern in FastAPI apps.
    """
    return Settings()
