import json
import logging

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from app.api.deps import Rag, Repository, UserId
from app.schemas.chat import ChatMessageRequest, ConversationCreate, ConversationOut, MessageOut

router = APIRouter(prefix="/chats", tags=["chats"])
logger = logging.getLogger(__name__)


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _title_from_content(content: str) -> str:
    title = " ".join(content.strip().split())
    return title[:48] + ("..." if len(title) > 48 else "")


@router.get("", response_model=list[ConversationOut])
def list_chats(user_id: UserId, repo: Repository):
    return repo.list_conversations(user_id)


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_chat(payload: ConversationCreate, user_id: UserId, repo: Repository):
    return repo.create_conversation(user_id, payload.model_dump())


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: str, user_id: UserId, repo: Repository):
    logger.info("List messages user_id=%s conversation_id=%s", user_id, conversation_id)
    return repo.list_messages(user_id, conversation_id)


@router.post("/{conversation_id}/messages/stream")
async def stream_message(
    conversation_id: str,
    payload: ChatMessageRequest,
    user_id: UserId,
    repo: Repository,
    rag: Rag,
):
    logger.info("Stream message start user_id=%s conversation_id=%s", user_id, conversation_id)
    conversation = repo.get_conversation(user_id, conversation_id)
    repo.create_message(user_id, conversation_id, "user", payload.content)
    logger.info("User message stored user_id=%s conversation_id=%s", user_id, conversation_id)
    if conversation.get("title") == "New chat":
        repo.update_conversation_title(user_id, conversation_id, _title_from_content(payload.content))

    async def event_stream():
        answer_parts: list[str] = []
        sources: list[dict] = []
        try:
            async for item in rag.stream_answer(payload.content):
                if item["type"] == "sources":
                    sources = item["data"]
                    yield _sse("sources", sources)
                elif item["type"] == "token":
                    answer_parts.append(item["data"])
                    yield _sse("token", item["data"])
            answer = "".join(answer_parts).strip()
            repo.create_message(user_id, conversation_id, "assistant", answer, sources=sources)
            logger.info(
                "Assistant message stored user_id=%s conversation_id=%s", user_id, conversation_id
            )
            yield _sse("done", {"conversation_id": conversation_id})
        except Exception as exc:
            logger.exception(
                "Stream message error user_id=%s conversation_id=%s", user_id, conversation_id
            )
            yield _sse("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(conversation_id: str, user_id: UserId, repo: Repository):
    repo.delete_conversation(user_id, conversation_id)
    return None
