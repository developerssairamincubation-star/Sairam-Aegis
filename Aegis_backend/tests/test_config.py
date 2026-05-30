import pytest
from pydantic import ValidationError

from app.core.config import Settings


def base_settings(**overrides):
    values = {
        "app_name": "Aegis API",
        "app_env": "test",
        "frontend_origin": "http://localhost:3000",
        "supabase_url": "https://example.supabase.co",
        "supabase_publishable_key": "sb_publishable_test",
        "supabase_secret_key": "sb_secret_test",
        "llm_provider": "openai_compatible",
        "local_llm_base_url": "http://localhost:11434/v1",
        "local_llm_model": "llama3.1:8b",
        "local_llm_api_key": "ollama",
        "rag_ingest_on_startup": True,
        "knowledge_base_dir": "./Sairam_knowledge_base",
        "ingestion_manifest_path": "./storage/ingestion_manifest.json",
        "embedding_model": "BAAI/bge-m3",
        "embedding_dimension": 1024,
        "runner_request_timeout_seconds": 180,
    }
    values.update(overrides)
    return Settings(**values)


def test_settings_load_with_supabase_vector_config():
    settings = base_settings()

    assert settings.supabase_publishable_key == "sb_publishable_test"
    assert settings.supabase_secret_key == "sb_secret_test"
    assert settings.local_llm_model == "llama3.1:8b"


def test_missing_supabase_secret_key_fails_clearly():
    with pytest.raises(ValidationError):
        base_settings(supabase_secret_key=None)


def test_runner_secret_required_only_for_runner_provider():
    base_settings(llm_provider="openai_compatible", runner_shared_secret=None)

    with pytest.raises(ValidationError, match="RUNNER_SHARED_SECRET"):
        base_settings(llm_provider="runner", runner_shared_secret=None)


def test_ingestion_manifest_required_only_when_startup_ingestion_enabled():
    base_settings(rag_ingest_on_startup=False, ingestion_manifest_path=None)

    with pytest.raises(ValidationError, match="INGESTION_MANIFEST_PATH"):
        base_settings(rag_ingest_on_startup=True, ingestion_manifest_path=None)
