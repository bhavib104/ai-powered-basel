"""Local LLM provider backed by Ollama (https://ollama.com)."""

from __future__ import annotations

import logging

import httpx

from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaLLM(LLMProvider):
    def __init__(self, base_url: str, model: str, timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.name = f"ollama:{model}"

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        return str(data.get("message", {}).get("content", "")).strip()
