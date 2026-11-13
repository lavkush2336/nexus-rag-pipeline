from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    app_name: str = "Nexus Closed-Loop RAG Pipeline"
    environment: str = Field(default="production", validation_alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    port: int = Field(default=8000, validation_alias=AliasChoices("PORT", "APP_PORT"))
    cors_origins: str = Field(default="*", validation_alias="CORS_ORIGINS")

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.5-flash", validation_alias="GEMINI_MODEL")
    gemini_evaluation_model: str | None = Field(default=None, validation_alias="GEMINI_EVALUATION_MODEL")
    gemini_embedding_model: str = Field(default="gemini-embedding-2", validation_alias="GEMINI_EMBEDDING_MODEL")
    gemini_temperature: float = Field(default=0.2, ge=0.0, le=2.0, validation_alias="GEMINI_TEMPERATURE")
    gemini_max_retries: int = Field(default=3, ge=1, le=6, validation_alias="GEMINI_MAX_RETRIES")
    gemini_retry_backoff_seconds: float = Field(
        default=0.8,
        ge=0.1,
        le=10.0,
        validation_alias="GEMINI_RETRY_BACKOFF_SECONDS",
    )

    elasticsearch_url: str = Field(default="", validation_alias="ELASTICSEARCH_URL")
    elasticsearch_api_key: str = Field(default="", validation_alias="ELASTICSEARCH_API_KEY")
    elasticsearch_index: str = Field(default="nexus-rag-documents", validation_alias="ELASTICSEARCH_INDEX")

    retrieve_k: int = Field(default=5, ge=1, le=20, validation_alias="RETRIEVE_K")
    max_rag_rounds: int = Field(default=3, ge=1, le=3, validation_alias="MAX_RAG_ROUNDS")
    request_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0, validation_alias="REQUEST_TIMEOUT_SECONDS")
    chunk_size_chars: int = Field(default=1600, ge=500, le=8000, validation_alias="CHUNK_SIZE_CHARS")
    chunk_overlap_chars: int = Field(default=200, ge=0, le=2000, validation_alias="CHUNK_OVERLAP_CHARS")

    static_dir: Path = Field(default=Path("frontend"), validation_alias="STATIC_DIR")

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key.strip())

    @property
    def elasticsearch_configured(self) -> bool:
        return bool(self.elasticsearch_url.strip() and self.elasticsearch_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()

