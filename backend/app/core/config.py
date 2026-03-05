"""Application settings loaded from environment and .env file."""

from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration from env vars and .env. See .env.example for required keys."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/carousel"
    S3_ENDPOINT: str = ""
    S3_BUCKET: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: SecretStr = SecretStr("")
    S3_PUBLIC_BASE_URL: str = ""
    LLM_API_KEY: SecretStr = SecretStr("")
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""

    PREVIEW_BASE_URL: str = "http://localhost:8000"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Optional API key; when set, all /api/v1/* (except health) require X-API-Key or api_key query
    API_KEY: SecretStr = SecretStr("")

    @model_validator(mode="after")
    def validate_critical_settings(self) -> "Settings":
        if self.S3_BUCKET and (not self.S3_ACCESS_KEY or not self.S3_SECRET_KEY.get_secret_value()):
            raise ValueError(
                "S3_BUCKET is set but S3_ACCESS_KEY or S3_SECRET_KEY is empty"
            )
        if self.LLM_BASE_URL and (
            not self.LLM_API_KEY.get_secret_value() or not self.LLM_MODEL
        ):
            raise ValueError(
                "LLM_BASE_URL is set but LLM_API_KEY or LLM_MODEL is empty"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Dependency-friendly access to settings (cached singleton)."""
    return Settings()
