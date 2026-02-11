"""
Centralised configuration loaded from environment variables.

Uses pydantic-settings for validation, defaults, and type coercion.
Every module imports `settings` from here instead of calling os.getenv directly.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings with sensible defaults for local dev."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── AI Provider ─────────────────────────────────────────────
    ai_provider: str = "openai"  # openai | xai | google
    openai_api_key: str = ""
    xai_api_key: str = ""
    google_api_key: str = ""

    # ── Bhashini (Indian Govt STT/TTS) ──────────────────────────
    bhashini_user_id: str = ""
    bhashini_api_key: str = ""
    bhashini_pipeline_url: str = (
        "https://dhruva-api.bhashini.gov.in/services/inference"
    )

    # ── Database ────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./sampark.db"

    # ── JWT Auth ────────────────────────────────────────────────
    jwt_secret: str = "change-this-to-a-random-secret-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # ── Server ──────────────────────────────────────────────────
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    cors_origins: str = '["http://localhost:8501","http://localhost:3000"]'
    backend_url: str = "http://localhost:8000"

    # ── Notifications ───────────────────────────────────────────
    twilio_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    # ── Monitoring ──────────────────────────────────────────────
    sentry_dsn: str = ""
    log_level: str = "INFO"

    # ── Feature Flags ───────────────────────────────────────────
    enable_screen_guide: bool = True
    enable_rag: bool = True
    enable_auth: bool = False
    enable_notifications: bool = False

    # ── Derived helpers ─────────────────────────────────────────

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.cors_origins)
        except (json.JSONDecodeError, TypeError):
            return ["*"]

    def get_ai_api_key(self) -> str:
        """Return the API key for the active provider."""
        mapping = {
            "openai": self.openai_api_key,
            "xai": self.xai_api_key,
            "google": self.google_api_key,
        }
        return mapping.get(self.ai_provider, self.openai_api_key)

    def get_ai_base_url(self) -> str | None:
        """Return the base URL override for xAI; None for others."""
        if self.ai_provider == "xai":
            return "https://api.x.ai/v1"
        return None

    def get_model_name(self, vision: bool = False) -> str:
        """Return the model name for the active provider."""
        if self.ai_provider == "xai":
            return "grok-2-vision-1212" if vision else "grok-2-1212"
        if self.ai_provider == "google":
            return "gemini-1.5-flash"
        return "gpt-4o"


@lru_cache()
def get_settings() -> Settings:
    """Singleton accessor — cached after first call."""
    return Settings()
