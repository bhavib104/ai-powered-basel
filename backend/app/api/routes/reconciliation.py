"""Reconciliation endpoints."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import ReconciliationResult, ReconciliationRun
from app.schemas.risk import ReconciliationRequest
from app.services import reconciliation

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


def _run_out(run: ReconciliationRun) -> dict[str, object]:
    return {
        "id": run.id,
        "run_ref": run.run_ref,
        "source_a": run.source_a_key,
        "source_b": run.source_b_key,
        "tolerance": str(run.tolerance),
        "status": run.status,
        "matched": run.matched,
        "mismatched": run.mismatched,
        "source_only_a": run.source_only_a,
        "source_only_b": run.source_only_b,
        "duplicates": run.duplicates,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.post("/run", summary="Reconcile two source snapshots")
def run(payload: ReconciliationRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    tolerance = Decimal(str(payload.tolerance)) if payload.tolerance is not None else None
    run = reconciliation.run_reconciliation(
        db,
        source_a=payload.source_a,
        source_b=payload.source_b,
        tolerance=tolerance,
    )
    return _run_out(run)


@router.get("/runs", summary="List reconciliation runs")
def runs(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100)) -> dict[str, object]:
    rows = db.execute(
        select(ReconciliationRun).order_by(ReconciliationRun.id.desc()).limit(limit)
    ).scalars().all()
    return {"items": [_run_out(r) for r in rows]}


@router.get("/runs/{run_id}/results", summary="Record-level reconciliation results")
def run_results(
    run_id: int,
    db: Annotated[Session, Depends(get_db)],
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> dict[str, object]:
    stmt = select(ReconciliationResult).where(ReconciliationResult.run_id == run_id)
    if status:
        stmt = stmt.where(ReconciliationResult.status == status)
    rows = db.execute(
        stmt.order_by(ReconciliationResult.business_key).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    items = []
    for r in rows:
        items.append(
            {
                "id": r.id,
                "business_key": r.business_key,
                "status": r.status,
                "source_a_value": json.loads(r.source_a_value) if r.source_a_value else None,
                "source_b_value": json.loads(r.source_b_value) if r.source_b_value else None,
                "differences": json.loads(r.differences_json) if r.differences_json else None,
            }
        )
    return {"run_id": run_id, "items": items, "count": len(items)}