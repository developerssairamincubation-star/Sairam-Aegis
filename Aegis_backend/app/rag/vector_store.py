from typing import Any

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.db.supabase import SupabaseRepository


class SupabaseVectorCollection:
    def __init__(self, repository: SupabaseRepository) -> None:
        self.repository = repository

    def delete(self, where: dict[str, Any]) -> None:
        source = where.get("source")
        if source:
            self.repository.delete_rag_source(source)

    def count(self) -> int:
        _, chunks = self.repository.rag_counts()
        return chunks


class SupabaseVectorStore:
    def __init__(
        self,
        repository: SupabaseRepository,
        embeddings: HuggingFaceEmbeddings,
    ) -> None:
        self.repository = repository
        self.embeddings = embeddings
        self._collection = SupabaseVectorCollection(repository)

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        source = docs[0].metadata.get("source")
        title = docs[0].metadata.get("title")
        sha256 = docs[0].metadata.get("sha256")
        document = self.repository.upsert_rag_document(source=source, title=title, sha256=sha256)
        embeddings = self.embeddings.embed_documents([doc.page_content for doc in docs])
        chunks = [
            {
                "chunk_index": index,
                "content": doc.page_content,
                "metadata": doc.metadata,
                "embedding": embedding,
            }
            for index, (doc, embedding) in enumerate(zip(docs, embeddings, strict=True))
        ]
        self.repository.replace_rag_chunks(document["id"], chunks)

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        query_embedding = self.embeddings.embed_query(query)
        matches = self.repository.match_rag_chunks(query_embedding=query_embedding, match_count=k)
        documents: list[Document] = []
        for match in matches:
            metadata = match.get("metadata") or {}
            metadata.update(
                {
                    "source": match.get("source"),
                    "title": match.get("title"),
                    "chunk_id": match.get("chunk_id"),
                    "score": match.get("similarity"),
                }
            )
            documents.append(Document(page_content=match["content"], metadata=metadata))
        return documents
