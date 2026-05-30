from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str
    app_env: str
    frontend_origin: str

    llm_provider: Literal["openai_compatible", "runner"]

    local_llm_base_url: str
    local_llm_model: str
    local_llm_api_key: str

    runner_shared_secret: str | None = None
    runner_request_timeout_seconds: int

    embedding_model: str
    embedding_dimension: int
    rag_ingest_on_startup: bool
    knowledge_base_dir: Path
    ingestion_manifest_path: Path | None = None

    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str

    @model_validator(mode="after")
    def validate_provider_config(self) -> "Settings":
        if self.llm_provider == "runner" and not self.runner_shared_secret:
            raise ValueError("RUNNER_SHARED_SECRET is required when LLM_PROVIDER=runner.")
        if self.rag_ingest_on_startup and self.ingestion_manifest_path is None:
            raise ValueError(
                "INGESTION_MANIFEST_PATH is required when RAG_INGEST_ON_STARTUP=true."
            )
        return self

    @property
    def auth_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_publishable_key)

    @property
    def db_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
