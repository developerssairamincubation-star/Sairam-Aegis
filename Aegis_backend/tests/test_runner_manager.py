import asyncio

import pytest
from starlette.websockets import WebSocketState

from app.rag.runner_manager import RunnerManager


class FakeWebSocket:
    client_state = WebSocketState.CONNECTED

    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


@pytest.mark.asyncio
async def test_generate_requires_connected_runner():
    manager = RunnerManager()

    with pytest.raises(RuntimeError, match="No local LLM runner"):
        async for _ in manager.generate([], "model", 0.2, 1):
            pass


@pytest.mark.asyncio
async def test_generate_streams_runner_tokens_in_order():
    manager = RunnerManager()
    websocket = FakeWebSocket()
    manager._websocket = websocket

    tokens: list[str] = []

    async def consume():
        async for token in manager.generate(
            messages=[{"role": "user", "content": "hello"}],
            model="llama3.1",
            temperature=0.2,
            timeout_seconds=1,
        ):
            tokens.append(token)

    task = asyncio.create_task(consume())
    while not websocket.sent:
        await asyncio.sleep(0)

    request_id = websocket.sent[0]["request_id"]
    await manager._handle_runner_message(
        {"type": "token", "request_id": request_id, "data": "hel"}
    )
    await manager._handle_runner_message(
        {"type": "token", "request_id": request_id, "data": "lo"}
    )
    await manager._handle_runner_message({"type": "done", "request_id": request_id})
    await task

    assert tokens == ["hel", "lo"]
