"""Embedding providers.

* :class:`SentenceTransformerEmbedder` — real local embeddings (default).
* :class:`HashingEmbedder` — deterministic, dependency-free fallback used for
  tests and offline environments.

Both are L2-normalised so cosine similarity is a simple dot product.
"""

from __future__ import annotations

import hashlib
import logging
import math

from app.providers.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class HashingEmbedder(EmbeddingProvider):
    """Deterministic bag-of-words hashing embedder (no model download)."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim
        self.name = f"hashing-{dim}"

    def _vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in text.lower().split():
            token = token.strip(".,;:()[]{}\"'")
            if not token:
                continue
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            idx = int(digest, 16) % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in texts]


class SentenceTransformerEmbedder(EmbeddingProvider):
    """Local sentence-transformers embedder (default model: all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # imported lazily

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())
        self.name = model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]
