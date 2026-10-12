"""Vector retrieval over indexed document chunks.

Embeddings are stored as float32 bytes in SQLite; similarity is computed with
NumPy.  At this scale (thousands of chunks) brute-force cosine search is fast
and removes the need for a separate vector database (ADR-006).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk, RegulatoryDocument
from app.providers import get_embedding_provider


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    document_title: str
    page_number: int | None
    section: str | None
    content: str
    score: float


def _matrix(rows: list[DocumentChunk]) -> np.ndarray:
    dim = rows[0].embedding_dim or 0
    matrix = np.zeros((len(rows), dim), dtype=np.float32)
    for i, row in enumerate(rows):
        if row.embedding is not None and row.embedding_dim:
            matrix[i] = np.frombuffer(row.embedding, dtype=np.float32)
    return matrix


def retrieve(
    session: Session,
    query: str,
    *,
    top_k: int = 5,
    min_score: float = 0.25,
    document_ids: list[int] | None = None,
) -> list[RetrievedChunk]:
    """Return the most similar chunks above ``min_score``."""
    stmt = select(DocumentChunk).where(DocumentChunk.embedding.is_not(None))
    if document_ids:
        stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
    rows = list(session.execute(stmt).scalars())
    if not rows:
        return []

    matrix = _matrix(rows)
    if matrix.shape[1] == 0:
        return []

    embedder = get_embedding_provider()
    query_vec = np.asarray(embedder.embed([query])[0], dtype=np.float32)
    if query_vec.shape[0] != matrix.shape[1]:
        # Dimension mismatch (e.g. embedder changed) -> no meaningful results.
        return []

    scores = matrix @ query_vec  # vectors are L2-normalised -> cosine
    order = np.argsort(-scores)

    titles = {
        d.id: d.title
        for d in session.execute(select(RegulatoryDocument)).scalars()
    }

    results: list[RetrievedChunk] = []
    for idx in order:
        score = float(scores[idx])
        if score < min_score:
            continue
        row = rows[int(idx)]
        results.append(
            RetrievedChunk(
                chunk_id=row.id,
                document_id=row.document_id,
                document_title=titles.get(row.document_id, "Unknown document"),
                page_number=row.page_number,
                section=row.section,
                content=row.content,
                score=round(score, 4),
            )
        )
        if len(results) >= top_k:
            break
    return results
