"""Exposure response schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.common import PageInfo


class ExposureOut(BaseModel):
    id: int
    exposure_ref: str
    counterparty: str | None
    counterparty_type: str | None
    portfolio_code: str | None
    exposure_class: str
    product_type: str
    currency: str
    original_amount: float
    drawn_amount: float
    undrawn_amount: float
    issue_date: date
    maturity_date: date
    is_defaulted: bool
    rating_grade: str
    source_system: str | None

    model_config = {"from_attributes": True}


class ExposureListOut(BaseModel):
    items: list[ExposureOut]
    page: PageInfo


class ExposureDetailOut(ExposureOut):
    collateral: list[dict[str, object]] = []
    collateral_credit: float = 0.0
    latest_calculation: dict[str, object] | None = None