import json
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings
from app.rag.runner_manager import RunnerManager

logger = logging.getLogger(__name__)

ChatMessage = dict[str, str]


class LLMClient(ABC):
    @abstractmethod
    async def stream_chat(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        pass


class OpenAICompatibleClient(LLMClient):
    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str,
        temperature: float = 0.2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.temperature = temperature

    async def stream_chat(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": True,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        logger.warning("Unable to decode local LLM stream event: %s", data)
                        continue
                    token = (
                        event.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if token:
                        yield token


class RunnerLLMClient(LLMClient):
    def __init__(self, runner_manager: RunnerManager, settings: Settings) -> None:
        self.runner_manager = runner_manager
        self.settings = settings

    async def stream_chat(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        async for token in self.runner_manager.generate(
            messages=messages,
            model=self.settings.local_llm_model,
            temperature=0.2,
            timeout_seconds=self.settings.runner_request_timeout_seconds,
        ):
            yield token


def build_llm_client(settings: Settings, runner_manager: RunnerManager) -> LLMClient:
    if settings.llm_provider == "runner":
        return RunnerLLMClient(runner_manager, settings)

    return OpenAICompatibleClient(
        base_url=settings.local_llm_base_url,
        model=settings.local_llm_model,
        api_key=settings.local_llm_api_key,
    )
