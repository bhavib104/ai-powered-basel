"""Risk calculation endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import RwaCalculationResult, RwaCalculationRun
from app.schemas.risk import CalculateRequest
from app.services import risk_engine

router = APIRouter(prefix="/risk", tags=["risk"])


def _run_out(run: RwaCalculationRun) -> dict[str, object]:
    return {
        "id": run.id,
        "run_ref": run.run_ref,
        "rule_version": run.rule_version,
        "as_of_date": run.as_of_date.isoformat(),
        "reporting_currency": run.reporting_currency,
        "status": run.status,
        "exposure_count": run.exposure_count,
        "calculated": run.calculated_count,
        "unsupported": run.unsupported_count,
        "total_eligible_amount": float(run.total_eligible_amount),
        "total_rwa": float(run.total_rwa),
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.post("/calculate", summary="Run RWA calculation for all exposures")
def calculate(payload: CalculateRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    run = risk_engine.run_calculation(
        db,
        rule_version=payload.rule_version,
        as_of_date=payload.as_of_date,
        limit=payload.limit,
    )
    return _run_out(run)


@router.get("/runs", summary="List calculation runs")
def runs(db: Annotated[Session, Depends(get_db)], limit: int = Query(50, ge=1, le=200)) -> dict[str, object]:
    rows = db.execute(
        select(RwaCalculationRun).order_by(RwaCalculationRun.id.desc()).limit(limit)
    ).scalars().all()
    return {"items": [_run_out(r) for r in rows]}


@router.get("/runs/{run_id}/results", summary="Exposure-level calculation breakdowns")
def run_results(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> dict[str, object]:
    stmt = select(RwaCalculationResult).where(RwaCalculationResult.run_id == run_id)
    if status:
        stmt = stmt.where(RwaCalculationResult.status == status)
    rows = db.execute(
        stmt.order_by(RwaCalculationResult.id).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    items = []
    for r in rows:
        items.append(
            {
                "id": r.id,
                "exposure_ref": r.exposure_ref,
                "exposure_class": r.exposure_class,
                "rating_grade": r.rating_grade,
                "currency": r.currency,
                "original_amount": float(r.original_amount),
                "amount_reporting": float(r.amount_reporting),
                "collateral_credit": float(r.collateral_credit),
                "eligible_amount": float(r.eligible_amount),
                "risk_weight": float(r.risk_weight) if r.risk_weight is not None else None,
                "rwa": float(r.rwa) if r.rwa is not None else None,
                "status": r.status,
                "explanation": r.explanation_json,
            }
        )
    return {"run_id": run_id, "items": items, "count": len(items)}