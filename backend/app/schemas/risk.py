"""Risk / quality / reconciliation request schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    rule_version: str = "2024.1"
    as_of_date: date | None = None
    limit: int | None = Field(None, ge=1, le=10000)


class ReconciliationRequest(BaseModel):
    source_a: str = Field(min_length=1)
    source_b: str = Field(min_length=1)
    tolerance: float | None = Field(None, ge=0.0)


class QualityRunRequest(BaseModel):
    scope: str = "ALL"