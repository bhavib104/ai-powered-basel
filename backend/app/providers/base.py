"""Provider interfaces.

Both the LLM and the embedding model sit behind small interfaces so they can be
swapped (local <-> cloud <-> mock) without touching business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """A text-generation model."""

    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str, *, temperature: float = 0.0) -> str:
        """Return a completion for the given system+user prompt."""

    @property
    def is_mock(self) -> bool:
        return False


class EmbeddingProvider(ABC):
    """Maps text to fixed-length vectors."""

    name: str = "base"
    dim: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text."""
