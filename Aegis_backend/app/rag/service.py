from functools import lru_cache
import logging
from typing import Any

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings
from app.rag.ingestion import IngestionResult, MarkdownIngestor

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
        settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = Chroma(
            collection_name="sairam_knowledge_base",
            embedding_function=self.embeddings,
            persist_directory=str(settings.chroma_persist_dir),
        )
        self.llm = ChatOpenAI(
            model=settings.lm_studio_model,
            api_key=settings.lm_studio_api_key,
            base_url=settings.lm_studio_base_url,
            temperature=0.2,
            streaming=True,
        )
        self.last_ingestion: IngestionResult | None = None

    def ingest_on_startup(self) -> IngestionResult:
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
        indexed_files = 0
        last_ingested_at = None
        if manifest_path.exists():
            import json

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            indexed_files = len(manifest.get("files", {}))
            last_ingested_at = manifest.get("last_ingested_at")

        chunk_count = 0
        if hasattr(self.vector_store, "_collection"):
            chunk_count = self.vector_store._collection.count()

        return {
            "knowledge_base_dir": str(self.settings.knowledge_base_dir),
            "embedding_model": self.settings.embedding_model,
            "persist_dir": str(self.settings.chroma_persist_dir),
            "indexed_files": indexed_files,
            "indexed_chunks": chunk_count,
            "last_ingested_at": last_ingested_at,
        }

    def retrieve(self, question: str, k: int = 5) -> tuple[str, list[dict[str, Any]]]:
        docs = self.vector_store.similarity_search(question, k=k)
        logger.info("Retrieved context k=%s hits=%s", k, len(docs))
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
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Knowledge-base context:\n"
                    f"{context or 'No relevant context was found.'}\n\n"
                    f"User question:\n{question}"
                )
            ),
        ]

        yield {"type": "sources", "data": sources}
        async for chunk in self.llm.astream(messages):
            token = chunk.content or ""
            if token:
                yield {"type": "token", "data": token}
        logger.info("Stream answer done")


@lru_cache
def get_rag_service() -> RagService:
    return RagService(get_settings())
