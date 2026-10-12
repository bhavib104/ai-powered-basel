"""Shared API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PageInfo(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedReadQuery:
    """Reusable query params for paginated GET endpoints."""

    def __init__(
        self,
        page: int = Field(1, ge=1),
        page_size: int = Field(50, ge=1, le=200),
        search: str | None = Field(None, max_length=120),
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.search = search