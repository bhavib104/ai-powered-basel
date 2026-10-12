"""Retrieval-augmented generation (RAG) service."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.providers.base import LLMProvider
from app.services import generation, retrieval


@dataclass
class RagResult:
    answer: str
    citations: list[dict[str, object]] = field(default_factory=list)
    insufficient_evidence: bool = False
    retrieved_count: int = 0


def _as_citation(item: retrieval.RetrievedChunk, index: int) -> dict[str, object]:
    return {
        "index": index,
        "chunk_id": item.chunk_id,
        "document_id": item.document_id,
        "document_title": item.document_title,
        "page": item.page_number,
        "section": item.section,
        "snippet": item.content[:300],
        "score": item.score,
    }


def answer_regulatory_question(
    session: Session,
    question: str,
    provider: LLMProvider,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> RagResult:
    """Answer a regulatory question using retrieved, verifiable passages."""
    settings = get_settings()
    top_k = top_k or settings.retrieval_top_k
    min_score = settings.retrieval_min_score if min_score is None else min_score

    hits = retrieval.retrieve(session, question, top_k=top_k, min_score=min_score)

    if not hits:
        return RagResult(
            answer=generation.compose_deterministic(question, []),
            citations=[],
            insufficient_evidence=True,
            retrieved_count=0,
        )

    evidence = [
        {
            "source": h.document_title,
            "page": h.page_number,
            "section": h.section,
            "text": h.content,
        }
        for h in hits
    ]
    answer = generation.synthesize(question, evidence, provider)
    citations = [_as_citation(h, i) for i, h in enumerate(hits, start=1)]

    return RagResult(
        answer=answer,
        citations=citations,
        insufficient_evidence=False,
        retrieved_count=len(hits),
    )