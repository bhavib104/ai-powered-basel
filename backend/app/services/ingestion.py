"""Regulatory document ingestion.

Supports text-based PDFs (via ``pypdf``) and plain text/markdown.  Preserves
document provenance, computes a checksum, prevents accidental duplicate
ingestion, and records failures explicitly.  Scanned PDFs that need OCR are
reported as unsupported rather than silently producing empty text.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.db.models import DocumentChunk, RegulatoryDocument
from app.providers import get_embedding_provider
from app.services import audit, chunking

logger = logging.getLogger(__name__)

ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}
MAX_FILE_BYTES = 25 * 1024 * 1024


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_pages(path: Path) -> list[tuple[int, str]]:
    """Return ``[(page_number, text), ...]`` for a supported file."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return [(1, path.read_text(encoding="utf-8", errors="replace"))]
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [(i + 1, (page.extract_text() or "")) for i, page in enumerate(reader.pages)]
    raise ValidationError(f"Unsupported file type '{suffix}'. Allowed: pdf, txt, md.")


def ingest_document(
    session: Session,
    *,
    path: str | Path,
    title: str,
    document_identifier: str | None = None,
    issuing_authority: str | None = None,
    publication_date: date | None = None,
    document_version: str | None = None,
    source_url: str | None = None,
    is_sample: bool = False,
) -> RegulatoryDocument:
    """Ingest one document and index its chunks."""
    file_path = Path(path)
    if not file_path.exists():
        raise ValidationError(f"File not found: {file_path}")
    if file_path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValidationError(f"Unsupported file type '{file_path.suffix}'. Allowed: pdf, txt, md.")
    if file_path.stat().st_size > MAX_FILE_BYTES:
        raise ValidationError("File exceeds the 25 MB ingestion limit.")

    checksum = _checksum(file_path)

    existing = session.execute(
        select(RegulatoryDocument).where(RegulatoryDocument.file_checksum == checksum)
    ).scalar_one_or_none()
    if existing is not None:
        logger.info("Document already ingested (checksum match): %s", existing.title)
        return existing

    doc = RegulatoryDocument(
        title=title,
        document_identifier=document_identifier,
        issuing_authority=issuing_authority,
        publication_date=publication_date,
        document_version=document_version,
        source_url=source_url,
        file_name=file_path.name,
        file_type=file_path.suffix.lower().lstrip("."),
        file_checksum=checksum,
        status="RUNNING",
        is_sample=is_sample,
        ingested_at=datetime.now(UTC),
    )
    session.add(doc)
    session.flush()

    try:
        pages = extract_pages(file_path)
    except Exception as exc:  # noqa: BLE001 - record failure explicitly
        doc.status = "FAILED"
        doc.error_message = str(exc)
        session.commit()
        return doc

    text_len = sum(len(t) for _, t in pages)
    if text_len == 0:
        doc.status = "UNSUPPORTED_OCR"
        doc.error_message = "No extractable text found; this PDF likely requires OCR (unsupported)."
        doc.page_count = len(pages)
        session.commit()
        return doc

    drafts = chunking.chunk_pages(pages)
    embedder = get_embedding_provider()
    vectors = embedder.embed([d.text for d in drafts]) if drafts else []

    for draft, vector in zip(drafts, vectors, strict=False):
        arr = np.asarray(vector, dtype=np.float32)
        session.add(
            DocumentChunk(
                document_id=doc.id,
                chunk_index=draft.index,
                page_number=draft.page_number,
                section=draft.section,
                content=draft.text,
                token_estimate=max(1, len(draft.text) // 4),
                embedding=arr.tobytes(),
                embedding_model=embedder.name,
                embedding_dim=embedder.dim,
            )
        )

    doc.page_count = len(pages)
    doc.chunk_count = len(drafts)
    doc.status = "INGESTED"
    audit.record_event(
        session,
        event_type="document",
        action="ingest",
        entity_type="regulatory_document",
        entity_id=doc.file_checksum[:12],
        details={"title": title, "chunks": len(drafts)},
    )
    session.commit()
    session.refresh(doc)
    return doc
