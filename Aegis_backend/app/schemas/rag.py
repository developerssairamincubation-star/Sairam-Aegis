from pydantic import BaseModel


class RagStatus(BaseModel):
    knowledge_base_dir: str
    embedding_model: str
    persist_dir: str
    indexed_files: int
    indexed_chunks: int
    last_ingested_at: str | None = None
