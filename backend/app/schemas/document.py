"""Document schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class DocumentMeta(BaseModel):
    id: int
    title: str
    document_identifier: str | None = None
    issuing_authority: str | None = None
    publication_date: date | None = None
    document_version: str | None = None
    source_url: str | None = None
    file_name: str
    file_type: str
    file_checksum: str
    page_count: int
    chunk_count: int
    status: str
    error_message: str | None = None
    is_sample: bool
    ingested_at: datetime


class DocumentListOut(BaseModel):
    items: list[DocumentMeta]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(5, ge=1, le=20)
    min_score: float | None = Field(None, ge=0.0, le=1.0)


class SearchHit(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    page: int | None = None
    section: str | None = None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    hits: list[SearchHit]
    insufficient_evidence: bool