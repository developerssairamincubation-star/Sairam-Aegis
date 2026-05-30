import asyncio
import json
import logging
import os
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
import websockets

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("aegis-runner")


def setting(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def with_token(url: str, token: str) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query["token"] = token
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class LocalLLMClient:
    def __init__(self) -> None:
        self.base_url = setting("LOCAL_LLM_BASE_URL").rstrip("/")
        self.model = setting("LOCAL_LLM_MODEL")
        self.api_key = setting("LOCAL_LLM_API_KEY")

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None,
        temperature: float,
    ):
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if not data or data == "[DONE]":
                        continue
                    event = json.loads(data)
                    token = (
                        event.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if token:
                        yield token


class Runner:
    def __init__(self) -> None:
        self.backend_ws_url = setting("BACKEND_WS_URL")
        self.shared_secret = setting("RUNNER_SHARED_SECRET")
        self.llm = LocalLLMClient()
        self.active_jobs: dict[str, asyncio.Task] = {}
        self.send_lock = asyncio.Lock()

    async def run_forever(self) -> None:
        while True:
            try:
                await self.connect_once()
            except Exception:
                logger.exception("Runner connection failed")
            await asyncio.sleep(5)

    async def connect_once(self) -> None:
        url = with_token(self.backend_ws_url, self.shared_secret)
        logger.info("Connecting to backend runner endpoint")
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
            await self.send(
                websocket,
                {
                    "type": "runner_ready",
                    "model": self.llm.model,
                    "capabilities": {"streaming": True, "openai_compatible": True},
                },
            )
            heartbeat_task = asyncio.create_task(self.heartbeat(websocket))
            try:
                async for raw_message in websocket:
                    message = json.loads(raw_message)
                    await self.handle_message(websocket, message)
            finally:
                heartbeat_task.cancel()
                for task in self.active_jobs.values():
                    task.cancel()
                self.active_jobs.clear()

    async def heartbeat(self, websocket) -> None:
        while True:
            await asyncio.sleep(15)
            await self.send(websocket, {"type": "heartbeat"})

    async def handle_message(self, websocket, message: dict[str, Any]) -> None:
        message_type = message.get("type")
        request_id = message.get("request_id")
        if message_type == "cancel" and request_id:
            task = self.active_jobs.pop(request_id, None)
            if task:
                task.cancel()
            return
        if message_type != "generate" or not request_id:
            logger.warning("Ignoring unsupported backend message: %s", message)
            return

        task = asyncio.create_task(self.generate(websocket, message))
        self.active_jobs[request_id] = task

    async def generate(self, websocket, message: dict[str, Any]) -> None:
        request_id = message["request_id"]
        try:
            async for token in self.llm.stream_chat(
                messages=message["messages"],
                model=message.get("model"),
                temperature=float(message.get("temperature", 0.2)),
            ):
                await self.send(
                    websocket,
                    {"type": "token", "request_id": request_id, "data": token},
                )
            await self.send(websocket, {"type": "done", "request_id": request_id})
        except Exception as exc:
            logger.exception("Generation failed request_id=%s", request_id)
            await self.send(
                websocket,
                {
                    "type": "error",
                    "request_id": request_id,
                    "message": str(exc),
                },
            )
        finally:
            self.active_jobs.pop(request_id, None)

    async def send(self, websocket, payload: dict[str, Any]) -> None:
        async with self.send_lock:
            await websocket.send(json.dumps(payload))


if __name__ == "__main__":
    asyncio.run(Runner().run_forever())
