"""Deterministic mock LLM used when no model provider is available.

It returns an empty string; the generation service then composes the answer
deterministically from the retrieved evidence.  This keeps the whole pipeline
exercisable offline and in CI, with no paid model calls.
"""

from __future__ import annotations

from app.providers.base import LLMProvider


class MockLLM(LLMProvider):
    name = "mock"

    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        return ""

    @property
    def is_mock(self) -> bool:
        return True
