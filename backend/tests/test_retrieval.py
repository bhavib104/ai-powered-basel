"""Retrieval tests over the deterministic hashing embedder (offline-safe)."""

from __future__ import annotations

from app.services import ingestion, retrieval


def _ingest_two_documents(tmp_path, db) -> None:
    basel = tmp_path / "basel.txt"
    basel.write_text(
        "Basel III requires banks to hold capital against credit risk.\n"
        "Risk-weighted assets determine the minimum capital requirement.",
        encoding="utf-8",
    )
    avocado = tmp_path / "avocado.txt"
    avocado.write_text(
        "Avocado farming in Peru requires fertile soil and consistent irrigation.\n"
        "The annual yield depends on seasonal rainfall patterns.",
        encoding="utf-8",
    )
    ingestion.ingest_document(db, path=basel, title="Basel capital rules", is_sample=True)
    ingestion.ingest_document(db, path=avocado, title="Avocado farming research", is_sample=True)


def test_retrieval_ranks_relevant_document_first(tmp_path, db) -> None:
    _ingest_two_documents(tmp_path, db)
    hits = retrieval.retrieve(db, "Basel capital requirement credit risk", top_k=3, min_score=0.0)
    assert hits, "Expected at least one hit at min_score=0"
    assert hits[0].document_title == "Basel capital rules"
    assert hits[0].score > 0.0


def test_min_score_filters_weak_matches(tmp_path, db) -> None:
    _ingest_two_documents(tmp_path, db)
    hits = retrieval.retrieve(db, "Basel capital requirement credit risk", top_k=5, min_score=0.9)
    assert hits == []  # hashing vectors never reach 0.9 with mixed vocabulary


def test_retrieve_empty_corpus_returns_empty(db) -> None:
    assert retrieval.retrieve(db, "anything", top_k=5) == []