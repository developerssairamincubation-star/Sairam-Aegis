from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Aegis API"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:3000"

    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "qwen3.5-4b"
    lm_studio_api_key: str = "lm-studio"

    embedding_model: str = "BAAI/bge-m3"
    knowledge_base_dir: Path = Field(default=Path("./Sairam knowledge base"))
    chroma_persist_dir: Path = Field(default=Path("./storage/chroma"))
    ingestion_manifest_path: Path = Field(default=Path("./storage/ingestion_manifest.json"))

    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_secret: str | None = None

    @property
    def auth_configured(self) -> bool:
        return bool(self.supabase_url and (self.supabase_jwt_secret or self.supabase_anon_key))

    @property
    def db_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
