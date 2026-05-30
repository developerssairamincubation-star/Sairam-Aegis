import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import get_current_user


def make_settings() -> Settings:
    return Settings(
        app_name="Aegis API",
        app_env="test",
        frontend_origin="http://localhost:3000",
        llm_provider="openai_compatible",
        local_llm_base_url="http://localhost:11434/v1",
        local_llm_model="test-model",
        local_llm_api_key="test-key",
        runner_request_timeout_seconds=30,
        embedding_model="BAAI/bge-m3",
        embedding_dimension=1024,
        rag_ingest_on_startup=True,
        knowledge_base_dir="./Sairam knowledge base",
        ingestion_manifest_path="./storage/ingestion_manifest.json",
        supabase_url="https://example.supabase.co",
        supabase_publishable_key="sb_publishable_test",
        supabase_secret_key="sb_secret_test",
    )


@pytest.mark.asyncio
async def test_missing_session_is_rejected():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None, make_settings())

    assert exc.value.status_code == 401
