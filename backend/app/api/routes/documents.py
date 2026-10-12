"""Regulatory document endpoints."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import RegulatoryDocument
from app.schemas.document import SearchRequest, SearchResponse
from app.services import ingestion, retrieval

router = APIRouter(prefix="/documents", tags=["documents"])


def _meta(doc: RegulatoryDocument) -> dict[str, object]:
    return {
        "id": doc.id,
        "title": doc.title,
        "document_identifier": doc.document_identifier,
        "issuing_authority": doc.issuing_authority,
        "publication_date": doc.publication_date,
        "document_version": doc.document_version,
        "source_url": doc.source_url,
        "file_name": doc.file_name,
        "file_type": doc.file_type,
        "file_checksum": doc.file_checksum,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "error_message": doc.error_message,
        "is_sample": doc.is_sample,
        "ingested_at": doc.ingested_at.isoformat(),
    }


@router.post("/ingest", summary="Ingest a text-based PDF or text file")
def ingest(
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    document_identifier: Annotated[str | None, Form()] = None,
    issuing_authority: Annotated[str | None, Form()] = None,
    publication_date: Annotated[date | None, Form()] = None,
    document_version: Annotated[str | None, Form()] = None,
    source_url: Annotated[str | None, Form()] = None,
    is_sample: Annotated[bool, Form()] = False,
) -> dict[str, object]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ingestion.ALLOWED_SUFFIXES:
        raise HTTPException(status_code=422, detail=f"Unsupported file type '{suffix}'. Allowed: pdf, txt, md.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        doc = ingestion.ingest_document(
            db,
            path=tmp_path,
            title=title,
            document_identifier=document_identifier,
            issuing_authority=issuing_authority,
            publication_date=publication_date,
            document_version=document_version,
            source_url=source_url,
            is_sample=is_sample,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if doc.status in {"FAILED", "UNSUPPORTED_OCR"}:
        raise HTTPException(status_code=422, detail=doc.error_message or f"Ingestion failed with status {doc.status}.")
    return _meta(doc)


@router.get("", summary="List ingested documents")
def documents(db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    rows = db.execute(
        select(RegulatoryDocument).order_by(RegulatoryDocument.id.desc())
    ).scalars().all()
    return {"items": [_meta(d) for d in rows]}


@router.get("/{document_id}", summary="Document metadata")
def document_detail(document_id: int, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    doc = db.get(RegulatoryDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _meta(doc)


@router.post("/search", response_model=SearchResponse, summary="Semantic search over indexed content")
def search(payload: SearchRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    hits = retrieval.retrieve(
        db,
        payload.query,
        top_k=payload.top_k,
        min_score=payload.min_score if payload.min_score is not None else 0.25,
    )
    return {
        "hits": [
            {
                "chunk_id": h.chunk_id,
                "document_id": h.document_id,
                "document_title": h.document_title,
                "page": h.page_number,
                "section": h.section,
                "snippet": h.content[:300],
                "score": h.score,
            }
            for h in hits
        ],
        "insufficient_evidence": len(hits) == 0,
    }