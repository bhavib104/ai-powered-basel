"""AI provider package: LLM and embedding adapters behind small interfaces."""

from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.factory import get_embedding_provider, get_llm_provider

__all__ = [
    "EmbeddingProvider",
    "LLMProvider",
    "get_embedding_provider",
    "get_llm_provider",
]
