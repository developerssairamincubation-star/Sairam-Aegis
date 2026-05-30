from pydantic import BaseModel


class RagStatus(BaseModel):
    knowledge_base_dir: str
    vector_store: str
    llm_provider: str
    embedding_model: str
    indexed_files: int
    indexed_chunks: int
    last_ingested_at: str | None = None
    runner: dict
