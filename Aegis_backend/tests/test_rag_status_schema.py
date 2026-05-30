from app.schemas.rag import RagStatus


def test_rag_status_is_supabase_only():
    status = RagStatus(
        knowledge_base_dir="./kb",
        vector_store="supabase_pgvector",
        llm_provider="openai_compatible",
        embedding_model="BAAI/bge-m3",
        indexed_files=1,
        indexed_chunks=3,
        runner={"connected": False},
    )

    payload = status.model_dump()

    assert payload == {
        "knowledge_base_dir": "./kb",
        "vector_store": "supabase_pgvector",
        "llm_provider": "openai_compatible",
        "embedding_model": "BAAI/bge-m3",
        "indexed_files": 1,
        "indexed_chunks": 3,
        "last_ingested_at": None,
        "runner": {"connected": False},
    }
