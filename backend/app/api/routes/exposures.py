"""Exposure query endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.db.models import Exposure, ExposureCollateral, RwaCalculationResult
from app.schemas.exposure import ExposureDetailOut, ExposureListOut

router = APIRouter(prefix="/exposures", tags=["exposures"])


def _exposure_out(exposure: Exposure) -> dict[str, object]:
    return {
        "id": exposure.id,
        "exposure_ref": exposure.exposure_ref,
        "counterparty": exposure.counterparty.legal_name if exposure.counterparty else None,
        "counterparty_type": exposure.counterparty.counterparty_type if exposure.counterparty else None,
        "portfolio_code": exposure.portfolio.code if exposure.portfolio else None,
        "exposure_class": exposure.exposure_class,
        "product_type": exposure.product_type,
        "currency": exposure.currency,
        "original_amount": float(exposure.original_amount),
        "drawn_amount": float(exposure.drawn_amount),
        "undrawn_amount": float(exposure.undrawn_amount),
        "issue_date": exposure.issue_date,
        "maturity_date": exposure.maturity_date,
        "is_defaulted": exposure.is_defaulted,
        "rating_grade": exposure.rating_grade,
        "source_system": exposure.source_system,
    }


@router.get("", response_model=ExposureListOut, summary="List exposures (filterable, paginated)")
def list_exposures(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, max_length=120),
    exposure_class: str | None = Query(None),
    rating_grade: str | None = Query(None),
    currency: str | None = Query(None, max_length=3),
    portfolio_code: str | None = Query(None),
    is_defaulted: bool | None = Query(None),
) -> dict[str, object]:
    stmt = (
        select(Exposure)
        .options(selectinload(Exposure.counterparty), selectinload(Exposure.portfolio))
        .order_by(Exposure.id)
    )
    count_stmt = select(func.count(Exposure.id))

    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            Exposure.exposure_ref.like(like) | Exposure.product_type.like(like)
        )
    if exposure_class:
        stmt = stmt.where(Exposure.exposure_class == exposure_class.upper())
    if rating_grade:
        stmt = stmt.where(Exposure.rating_grade == rating_grade.upper())
    if currency:
        stmt = stmt.where(Exposure.currency == currency.upper())
    if portfolio_code:
        stmt = stmt.where(Exposure.portfolio.has(code=portfolio_code.upper()))
    if is_defaulted is not None:
        stmt = stmt.where(Exposure.is_defaulted.is_(is_defaulted))

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    items = [_exposure_out(e) for e in rows]
    return {
        "items": items,
        "page": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total else 1,
        },
    }


@router.get("/{exposure_id}", response_model=ExposureDetailOut, summary="Exposure detail with breakdown")
def exposure_detail(exposure_id: int, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    exposure = db.execute(
        select(Exposure)
        .options(
            selectinload(Exposure.counterparty),
            selectinload(Exposure.portfolio),
            selectinload(Exposure.collateral_links).selectinload(ExposureCollateral.collateral),
        )
        .where(Exposure.id == exposure_id)
    ).scalar_one_or_none()
    if exposure is None:
        raise HTTPException(status_code=404, detail=f"Exposure {exposure_id} not found.")

    out = _exposure_out(exposure)
    out["collateral"] = [
        {
            "collateral_ref": link.collateral.collateral_ref if link.collateral else None,
            "collateral_type": link.collateral.collateral_type if link.collateral else None,
            "allocated_amount": float(link.allocated_amount),
            "eligible": bool(link.collateral.is_eligible) if link.collateral else False,
        }
        for link in exposure.collateral_links
        if link.collateral is not None
    ]

    calc = db.execute(
        select(RwaCalculationResult)
        .where(RwaCalculationResult.exposure_ref == exposure.exposure_ref)
        .order_by(RwaCalculationResult.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if calc is not None:
        out["collateral_credit"] = float(calc.collateral_credit)
        out["latest_calculation"] = {
            "status": calc.status,
            "eligible_amount": float(calc.eligible_amount),
            "risk_weight": float(calc.risk_weight) if calc.risk_weight is not None else None,
            "rwa": float(calc.rwa) if calc.rwa is not None else None,
            "explanation": calc.explanation_json,
        }
    return out