"""Optional cloud LLM provider (OpenAI-compatible chat completions)."""

from __future__ import annotations

import httpx

from app.core.exceptions import ProviderUnavailableError
from app.providers.base import LLMProvider


class OpenAILLM(LLMProvider):
    def __init__(self, api_key: str, model: str, timeout: float = 60.0) -> None:
        if not api_key:
            raise ProviderUnavailableError("OPENAI_API_KEY is not configured.")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.name = f"openai:{model}"

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        return str(data["choices"][0]["message"]["content"]).strip()
