import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import WebSocket
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)


@dataclass
class RunnerInfo:
    connected: bool = False
    model: str | None = None
    last_seen_at: str | None = None
    active_requests: int = 0


class RunnerManager:
    def __init__(self) -> None:
        self._websocket: WebSocket | None = None
        self._send_lock = asyncio.Lock()
        self._pending: dict[str, asyncio.Queue[dict[str, Any]]] = {}
        self._info = RunnerInfo()

    def status(self) -> dict[str, Any]:
        return {
            "connected": self._info.connected,
            "model": self._info.model,
            "last_seen_at": self._info.last_seen_at,
            "active_requests": self._info.active_requests,
        }

    async def connect(self, websocket: WebSocket) -> None:
        if self._websocket is not None:
            await websocket.close(code=1013, reason="A runner is already connected.")
            return

        await websocket.accept()
        self._websocket = websocket
        self._mark_seen()
        self._info.connected = True
        logger.info("Runner connected")

        try:
            while True:
                message = await websocket.receive_json()
                await self._handle_runner_message(message)
        except Exception:
            logger.exception("Runner connection closed")
        finally:
            await self._disconnect_current(websocket)

    async def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        timeout_seconds: int,
    ) -> AsyncIterator[str]:
        websocket = self._websocket
        if websocket is None or websocket.client_state != WebSocketState.CONNECTED:
            raise RuntimeError("No local LLM runner is connected.")

        request_id = str(uuid4())
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pending[request_id] = queue
        self._info.active_requests = len(self._pending)

        job = {
            "type": "generate",
            "request_id": request_id,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        async with self._send_lock:
            await websocket.send_json(job)

        try:
            while True:
                event = await asyncio.wait_for(queue.get(), timeout=timeout_seconds)
                event_type = event.get("type")
                if event_type == "token":
                    yield event.get("data", "")
                elif event_type == "done":
                    return
                elif event_type == "error":
                    raise RuntimeError(event.get("message") or "Runner generation failed.")
        except TimeoutError as exc:
            async with self._send_lock:
                await websocket.send_json({"type": "cancel", "request_id": request_id})
            raise RuntimeError("Runner generation timed out.") from exc
        finally:
            self._pending.pop(request_id, None)
            self._info.active_requests = len(self._pending)

    async def _handle_runner_message(self, message: dict[str, Any]) -> None:
        self._mark_seen()
        message_type = message.get("type")
        if message_type == "runner_ready":
            self._info.model = message.get("model")
            logger.info("Runner ready model=%s", self._info.model)
            return
        if message_type == "heartbeat":
            return

        request_id = message.get("request_id")
        if not request_id:
            logger.warning("Runner message missing request_id: %s", message)
            return
        queue = self._pending.get(request_id)
        if queue is None:
            logger.warning("Runner message for unknown request_id=%s", request_id)
            return
        await queue.put(message)

    async def _disconnect_current(self, websocket: WebSocket) -> None:
        if websocket is not self._websocket:
            return

        self._websocket = None
        self._info.connected = False
        self._info.active_requests = 0
        for request_id, queue in list(self._pending.items()):
            await queue.put(
                {
                    "type": "error",
                    "request_id": request_id,
                    "message": "Runner disconnected during generation.",
                }
            )
        self._pending.clear()
        logger.info("Runner disconnected")

    def _mark_seen(self) -> None:
        self._info.last_seen_at = datetime.now(timezone.utc).isoformat()


runner_manager = RunnerManager()
