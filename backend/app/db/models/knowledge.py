"""Regulatory document and chunk models (document intelligence)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import TimestampMixin


class RegulatoryDocument(TimestampMixin, Base):
    """An ingested regulatory document with full provenance."""

    __tablename__ = "regulatory_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    document_identifier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(160), nullable=True)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str] = mapped_column(String(300))
    file_type: Mapped[str] = mapped_column(String(16))
    file_checksum: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="INGESTED", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_sample: Mapped[bool] = mapped_column(default=False, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(TimestampMixin, Base):
    """A retrievable passage of a document, with page/section metadata and its
    pre-computed embedding."""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("regulatory_documents.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)

    # Embedding stored as raw little-endian float32 bytes.
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    embedding_dim: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped[RegulatoryDocument] = relationship(back_populates="chunks")

    __table_args__ = (Index("ix_chunk_doc_index", "document_id", "chunk_index"),)
