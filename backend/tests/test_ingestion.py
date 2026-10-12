"""Document ingestion tests (text files are used; the same pipeline handles PDFs)."""

from __future__ import annotations

import hashlib

from sqlalchemy import select

from app.db.models import DocumentChunk, RegulatoryDocument
from app.services import ingestion

_SAMPLE = (
    "1. Capital Requirements\n"
    "Banks must maintain minimum capital ratios proportional to the risk of their assets.\n"
    "2. Credit Risk\n"
    "Credit risk is the risk of loss if a counterparty fails to meet its obligations.\n"
)


def test_ingest_txt_creates_chunks(tmp_path, db) -> None:
    path = tmp_path / "basel_sample.txt"
    path.write_text(_SAMPLE, encoding="utf-8")

    doc = ingestion.ingest_document(
        db,
        path=path,
        title="Sample Basel note",
        document_identifier="SAMPLE-001",
        issuing_authority="Test Authority",
        is_sample=True,
    )

    assert doc.status == "INGESTED"
    assert doc.page_count == 1
    assert doc.chunk_count > 0
    assert doc.file_checksum == hashlib.sha256(path.read_bytes()).hexdigest()

    chunks = db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).scalars().all()
    assert len(chunks) == doc.chunk_count
    assert all(c.embedding_dim and c.embedding is not None for c in chunks)


def test_duplicate_ingest_is_skipped(tmp_path, db) -> None:
    path = tmp_path / "dup.txt"
    path.write_text(_SAMPLE, encoding="utf-8")

    first = ingestion.ingest_document(db, path=path, title="First")
    second = ingestion.ingest_document(db, path=path, title="Second")

    assert second.id == first.id
    assert db.execute(select(RegulatoryDocument)).scalars().all().__len__() == 1


def test_unsupported_file_type_is_rejected(tmp_path, db) -> None:
    import pytest

    from app.core.exceptions import ValidationError

    path = tmp_path / "x.docx"
    path.write_text("hi", encoding="utf-8")
    with pytest.raises(ValidationError):
        ingestion.ingest_document(db, path=path, title="Bad")