"""AI request and tool-execution audit models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import TimestampMixin


class AiRequest(TimestampMixin, Base):
    """A single user question handled by the AI assistant."""

    __tablename__ = "ai_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    question: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    insufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tool_executions: Mapped[list[AiToolExecution]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class AiToolExecution(TimestampMixin, Base):
    """An audited invocation of an approved AI tool."""

    __tablename__ = "ai_tool_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("ai_requests.id", ondelete="CASCADE"), index=True
    )
    tool_name: Mapped[str] = mapped_column(String(60), index=True)
    arguments_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="OK")
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    request: Mapped[AiRequest] = relationship(back_populates="tool_executions")
