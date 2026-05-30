import pytest

from app.api.chats import stream_message
from app.schemas.chat import ChatMessageRequest


class FakeRepository:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    def get_conversation(self, user_id, conversation_id):
        return {"id": conversation_id, "title": "Existing chat"}

    def create_message(self, user_id, conversation_id, role, content, sources=None):
        self.messages.append(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "sources": sources or [],
            }
        )


class FailingRag:
    async def stream_answer(self, question):
        yield {"type": "sources", "data": []}
        raise RuntimeError("No local LLM runner is connected.")


@pytest.mark.asyncio
async def test_stream_error_does_not_store_assistant_message():
    repo = FakeRepository()

    response = await stream_message(
        conversation_id="chat-1",
        payload=ChatMessageRequest(content="hello"),
        user_id="user-1",
        repo=repo,
        rag=FailingRag(),
    )
    body = ""
    async for chunk in response.body_iterator:
        body += chunk.decode() if isinstance(chunk, bytes) else chunk

    assert "event: error" in body
    assert [message["role"] for message in repo.messages] == ["user"]
