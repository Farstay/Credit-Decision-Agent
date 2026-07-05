import asyncio
from abc import ABC, abstractmethod
import httpx

from app.config import settings


# --- Абстрактный интерфейс LLM-клиента ---
class LLMClient(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Сгенерировать ответ на промпт."""
        ...


# --- Реализация через Ollama ---
class OllamaClient(LLMClient):
    def __init__(self, url: str | None = None, model: str | None = None):
        self.url = url or settings.ollama_url
        self.model = model or settings.ollama_model

    async def generate(self, prompt: str, timeout: float = 180.0, max_retries: int = 3) -> str:
        """Вызов Ollama с таймаутом и ретраями (обработка отказов)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # получаем ответ целиком, не потоком
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(f"{self.url}/api/generate", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["response"]
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.ConnectError) as e:
                last_error = e
                if attempt == max_retries:
                    break
                # экспоненциальный backoff (из блока async!)
                await asyncio.sleep(2 ** (attempt - 1))

        raise RuntimeError(f"LLM недоступна после {max_retries} попыток: {last_error}")