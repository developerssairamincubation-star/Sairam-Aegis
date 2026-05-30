from functools import lru_cache
import logging
import time
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import Settings, get_settings
from app.db.supabase import get_repository
from app.rag.ingestion import IngestionResult, MarkdownIngestor
from app.rag.llm import LLMClient, build_llm_client
from app.rag.runner_manager import runner_manager
from app.rag.vector_store import SupabaseVectorStore

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Aegis, a model developed by Sairam Innovation lab.
Answer using the provided knowledge-base context whenever it is relevant.
If the context does not contain enough information, say that clearly and provide the best helpful next step.
Keep responses clear, grounded, and concise."""

GREETING_RESPONSE = "Hi I am Aegis! A Model developed by Sairam innovation lab. How can i help you today?"


def _is_greeting(question: str) -> bool:
    normalized = " ".join(question.lower().strip().split())
    return normalized in {
        "hi",
        "hello",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
    }


class RagService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        self.vector_store = SupabaseVectorStore(repository=get_repository(), embeddings=self.embeddings)
        self.llm: LLMClient = build_llm_client(settings, runner_manager)
        self.last_ingestion: IngestionResult | None = None

    def ingest_on_startup(self) -> IngestionResult:
        if self.settings.ingestion_manifest_path is None:
            raise RuntimeError("INGESTION_MANIFEST_PATH is required for startup ingestion.")

        ingestor = MarkdownIngestor(
            knowledge_base_dir=self.settings.knowledge_base_dir,
            manifest_path=self.settings.ingestion_manifest_path,
        )
        self.last_ingestion = ingestor.ingest(self.vector_store)
        logger.info(
            "Ingestion completed indexed_files=%s indexed_chunks=%s changed_files=%s",
            self.last_ingestion.indexed_files,
            self.last_ingestion.indexed_chunks,
            self.last_ingestion.changed_files,
        )
        return self.last_ingestion

    def status(self) -> dict[str, Any]:
        manifest_path = self.settings.ingestion_manifest_path
        last_ingested_at = None
        if manifest_path and manifest_path.exists():
            import json

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            last_ingested_at = manifest.get("last_ingested_at")

        indexed_files_from_store, chunk_count = get_repository().rag_counts()

        return {
            "knowledge_base_dir": str(self.settings.knowledge_base_dir),
            "vector_store": "supabase_pgvector",
            "llm_provider": self.settings.llm_provider,
            "embedding_model": self.settings.embedding_model,
            "indexed_files": indexed_files_from_store,
            "indexed_chunks": chunk_count,
            "last_ingested_at": last_ingested_at,
            "runner": runner_manager.status(),
        }

    def retrieve(self, question: str, k: int = 5) -> tuple[str, list[dict[str, Any]]]:
        started_at = time.perf_counter()
        docs = self.vector_store.similarity_search(question, k=k)
        logger.info(
            "Retrieved context provider=supabase_pgvector k=%s hits=%s latency_ms=%s",
            k,
            len(docs),
            round((time.perf_counter() - started_at) * 1000),
        )
        context_parts: list[str] = []
        sources: list[dict[str, Any]] = []
        for doc in docs:
            source = {
                "source": doc.metadata.get("source"),
                "title": doc.metadata.get("title"),
                "chunk_id": doc.metadata.get("chunk_id"),
            }
            sources.append(source)
            context_parts.append(
                f"Source: {source.get('source')}\n{doc.page_content}"
            )
        return "\n\n---\n\n".join(context_parts), sources

    async def stream_answer(self, question: str):
        logger.info("Stream answer start")
        if _is_greeting(question):
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": GREETING_RESPONSE}
            logger.info("Stream answer done")
            return
        context, sources = self.retrieve(question)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Knowledge-base context:\n"
                    f"{context or 'No relevant context was found.'}\n\n"
                    f"User question:\n{question}"
                ),
            },
        ]

        yield {"type": "sources", "data": sources}
        async for token in self.llm.stream_chat(messages):
            if token:
                yield {"type": "token", "data": token}
        logger.info("Stream answer done")


@lru_cache
def get_rag_service() -> RagService:
    return RagService(get_settings())
