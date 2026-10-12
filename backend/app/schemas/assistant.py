"""AI assistant schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class CitationOut(BaseModel):
    index: int
    chunk_id: int
    document_id: int
    document_title: str
    page: int | None = None
    section: str | None = None
    snippet: str
    score: float | None = None


class ToolExecutionOut(BaseModel):
    tool_name: str
    arguments: dict[str, object]
    status: str
    result_summary: str | None = None
    error: str | None = None
    duration_ms: int | None = None


class AssistantResponse(BaseModel):
    request_ref: str
    answer: str
    citations: list[CitationOut] = []
    insufficient_evidence: bool
    tool_executions: list[ToolExecutionOut] = []
    provider: str
    model: str | None = None


class AssistantRequestHistoryOut(BaseModel):
    id: int
    request_ref: str
    question: str
    provider: str
    status: str
    answer: str | None = None
    insufficient_evidence: bool
    latency_ms: int | None = None
    created_at: str