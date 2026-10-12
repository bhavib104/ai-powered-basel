"""Factories that select and cache providers based on configuration."""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import EmbeddingProvider, LLMProvider
from app.providers.embeddings import HashingEmbedder, SentenceTransformerEmbedder
from app.providers.llm_mock import MockLLM
from app.providers.llm_ollama import OllamaLLM
from app.providers.llm_openai import OpenAILLM

logger = logging.getLogger(__name__)


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Return the configured LLM provider, falling back to mock on failure."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    try:
        if provider == "openai":
            return OpenAILLM(settings.openai_api_key or "", settings.openai_model)
        if provider == "ollama":
            return OllamaLLM(settings.ollama_base_url, settings.ollama_model)
        return MockLLM()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Falling back to mock LLM: %s", exc)
        return MockLLM()


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    """Return the configured embedding provider.

    ``auto`` attempts real embeddings first and silently falls back to the
    deterministic hashing embedder (so the app never hard-fails offline).
    """
    settings = get_settings()
    backend = settings.embedding_backend.lower()
    if backend == "hashing":
        return HashingEmbedder()
    try:
        return SentenceTransformerEmbedder(settings.embedding_model)
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.warning("Falling back to hashing embedder (%s): %s", settings.embedding_model, exc)
        return HashingEmbedder()
