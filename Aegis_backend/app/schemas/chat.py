from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str | None = None
    project_id: str | None = None


class ConversationOut(BaseModel):
    id: str
    user_id: str
    project_id: str | None = None
    title: str
    created_at: str | None = None
    updated_at: str | None = None


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None


class ChatMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class Source(BaseModel):
    source: str | None = None
    title: str | None = None
    chunk_id: str | None = None
    score: float | None = None
