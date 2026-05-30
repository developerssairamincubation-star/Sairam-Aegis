from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

import bcrypt
from fastapi import HTTPException, status
from supabase import Client, create_client

from app.core.config import get_settings


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


class SupabaseRepository:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.db_configured:
            self.client: Client | None = None
            return

        self.client = create_client(settings.supabase_url, settings.supabase_secret_key)

    def _table(self, table: str):
        if self.client is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase database is not configured.",
            )
        return self.client.table(table)

    def list_projects(self, user_id: str) -> list[dict[str, Any]]:
        return (
            self._table("projects")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
            .data
            or []
        )

    def create_project(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = {"user_id": user_id, **data}
        return self._table("projects").insert(payload).execute().data[0]

    def update_project(self, user_id: str, project_id: str, data: dict[str, Any]) -> dict[str, Any]:
        payload = {key: value for key, value in data.items() if value is not None}
        result = (
            self._table("projects")
            .update(payload)
            .eq("id", project_id)
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        return result[0]

    def delete_project(self, user_id: str, project_id: str) -> None:
        self._table("projects").delete().eq("id", project_id).eq("user_id", user_id).execute()

    def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        return (
            self._table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
            .data
            or []
        )

    def create_conversation(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        title = data.get("title") or "New chat"
        payload = {"user_id": user_id, "title": title, "project_id": data.get("project_id")}
        return self._table("conversations").insert(payload).execute().data[0]

    def get_conversation(self, user_id: str, conversation_id: str) -> dict[str, Any]:
        result = (
            self._table("conversations")
            .select("*")
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        return result[0]

    def update_conversation_title(self, user_id: str, conversation_id: str, title: str) -> None:
        self._table("conversations").update({"title": title}).eq("id", conversation_id).eq(
            "user_id", user_id
        ).execute()

    def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        result = (
            self._table("conversations")
            .delete()
            .eq("id", conversation_id)
            .eq("user_id", user_id)
            .execute()
            .data
            or []
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    def list_messages(self, user_id: str, conversation_id: str) -> list[dict[str, Any]]:
        self.get_conversation(user_id, conversation_id)
        return (
            self._table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
            .data
            or []
        )

    def create_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        sources: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.get_conversation(user_id, conversation_id)
        payload = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "sources": sources or [],
        }
        result = self._table("messages").insert(payload).execute().data[0]
        self._table("conversations").update(
            {"updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", conversation_id).eq("user_id", user_id).execute()
        return result

    def record_ingestion_run(self, indexed_files: int, indexed_chunks: int, status_value: str) -> None:
        if self.client is None:
            return
        self._table("rag_ingestion_runs").insert(
            {
                "indexed_files": indexed_files,
                "indexed_chunks": indexed_chunks,
                "status": status_value,
            }
        ).execute()

    def delete_rag_source(self, source: str) -> None:
        documents = (
            self._table("rag_documents")
            .select("id")
            .eq("source", source)
            .execute()
            .data
            or []
        )
        for document in documents:
            self._table("rag_chunks").delete().eq("document_id", document["id"]).execute()
        self._table("rag_documents").delete().eq("source", source).execute()

    def upsert_rag_document(self, source: str, title: str | None, sha256: str | None) -> dict[str, Any]:
        payload = {
            "source": source,
            "title": title,
            "sha256": sha256,
        }
        result = (
            self._table("rag_documents")
            .upsert(payload, on_conflict="source")
            .execute()
            .data
            or []
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to upsert RAG document.",
            )
        return result[0]

    def replace_rag_chunks(self, document_id: str, chunks: list[dict[str, Any]]) -> int:
        self._table("rag_chunks").delete().eq("document_id", document_id).execute()
        if not chunks:
            return 0
        payload = [
            {
                "document_id": document_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "metadata": chunk.get("metadata") or {},
                "embedding": _vector_literal(chunk["embedding"]),
            }
            for chunk in chunks
        ]
        self._table("rag_chunks").insert(payload).execute()
        return len(payload)

    def match_rag_chunks(
        self,
        query_embedding: list[float],
        match_count: int,
    ) -> list[dict[str, Any]]:
        if self.client is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase database is not configured.",
            )
        return (
            self.client.rpc(
                "match_rag_chunks",
                {
                    "query_embedding": _vector_literal(query_embedding),
                    "match_count": match_count,
                },
            )
            .execute()
            .data
            or []
        )

    def rag_counts(self) -> tuple[int, int]:
        documents = self._table("rag_documents").select("id", count="exact").execute()
        chunks = self._table("rag_chunks").select("id", count="exact").execute()
        return documents.count or 0, chunks.count or 0

    def create_local_user(self, email: str, password: str) -> dict[str, Any]:
        existing = (
            self._table("local_users").select("id").eq("email", email).limit(1).execute().data
            or []
        )
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        return (
            self._table("local_users")
            .insert({"email": email, "password_hash": password_hash})
            .execute()
            .data[0]
        )

    def verify_local_user(self, email: str, password: str) -> dict[str, Any]:
        result = (
            self._table("local_users")
            .select("id, email, password_hash")
            .eq("email", email)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
            )
        user = result[0]
        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
            )
        return user


@lru_cache
def get_repository() -> SupabaseRepository:
    return SupabaseRepository()
