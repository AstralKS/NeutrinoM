"""Settings configuration with environment validation.

This module provides centralized configuration management with:
- Environment variable loading and validation
- Fail-fast behavior for missing required variables
- OpenRouter API key rotation support
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All secrets are loaded at runtime and never stored or logged.
    Missing required variables cause immediate startup failure.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Supabase Configuration
    supabase_url: str = Field(
        ...,
        description="Supabase project URL",
    )
    supabase_service_role_key: str = Field(
        ...,
        description="Supabase service role key (backend only)",
    )
    supabase_jwt_secret: str = Field(
        ...,
        description="Supabase JWT secret for token verification",
    )

    # OpenRouter API Keys (multiple for rotation/fallback)
    openrouter_api_key_1: str = Field(
        ...,
        description="Primary OpenRouter API key",
    )
    openrouter_api_key_2: str | None = Field(
        default=None,
        description="Secondary OpenRouter API key",
    )
    openrouter_api_key_3: str | None = Field(
        default=None,
        description="Tertiary OpenRouter API key",
    )
    openrouter_api_key_4: str | None = Field(
        default=None,
        description="Quaternary OpenRouter API key",
    )

    # OpenRouter Configuration
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )

    # Serper API Configuration (for web search)
    serper_api_key: str | None = Field(
        default=None,
        description="Serper API key for web search in trend analysis",
    )

    # Application Configuration
    app_name: str = Field(
        default="AI Development Advisor",
        description="Application name for logging and reports",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v: str) -> str:
        """Ensure Supabase URL is properly formatted."""
        if not v or not v.startswith("https://"):
            raise ValueError("SUPABASE_URL must be a valid HTTPS URL")
        return v.rstrip("/")

    @field_validator("supabase_service_role_key", "openrouter_api_key_1")
    @classmethod
    def validate_required_keys(cls, v: str) -> str:
        """Ensure required API keys are not empty."""
        if not v or len(v.strip()) < 10:
            raise ValueError("Required API key is missing or too short")
        return v.strip()

    @property
    def openrouter_api_keys(self) -> list[str]:
        """Get list of all available OpenRouter API keys.

        Returns:
            List of non-None API keys for rotation/fallback.
        """
        keys = [
            self.openrouter_api_key_1,
            self.openrouter_api_key_2,
            self.openrouter_api_key_3,
            self.openrouter_api_key_4,
        ]
        return [k for k in keys if k is not None]

    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return Path(__file__).parent.parent.parent.parent


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are loaded once and cached for the application lifetime.
    Call this function to access configuration throughout the app.

    Returns:
        Settings instance with validated configuration.

    Raises:
        ValidationError: If required environment variables are missing.
    """
    return Settings()
