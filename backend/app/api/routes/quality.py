"""Data-quality endpoints."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import DataQualityFinding, DataQualityRun
from app.schemas.risk import QualityRunRequest
from app.services import data_quality

router = APIRouter(prefix="/quality", tags=["data-quality"])


@router.post("/run", summary="Execute all data-quality checks")
def run(payload: QualityRunRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    run = data_quality.run_checks(db, scope=payload.scope)
    summary = json.loads(run.summary_json) if run.summary_json else {}
    return {
        "id": run.id,
        "run_ref": run.run_ref,
        "status": run.status,
        "rule_count": run.rule_count,
        "finding_count": run.finding_count,
        "summary": summary,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/runs", summary="List data-quality runs")
def runs(db: Annotated[Session, Depends(get_db)], limit: int = Query(20, ge=1, le=100)) -> dict[str, object]:
    rows = db.execute(
        select(DataQualityRun).order_by(DataQualityRun.id.desc()).limit(limit)
    ).scalars().all()
    items = []
    for r in rows:
        items.append(
            {
                "id": r.id,
                "run_ref": r.run_ref,
                "status": r.status,
                "rule_count": r.rule_count,
                "finding_count": r.finding_count,
                "started_at": r.started_at.isoformat(),
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
        )
    return {"items": items}


@router.get("/findings", summary="Filter findings by severity / rule / record")
def findings(
    db: Annotated[Session, Depends(get_db)],
    severity: str | None = Query(None),
    rule_code: str | None = Query(None),
    record_key: str | None = Query(None, max_length=60),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
) -> dict[str, object]:
    stmt = select(DataQualityFinding).order_by(DataQualityFinding.id.desc())
    count_stmt = select(func.count(DataQualityFinding.id))
    if severity:
        stmt = stmt.where(DataQualityFinding.severity == severity.upper())
        count_stmt = count_stmt.where(DataQualityFinding.severity == severity.upper())
    if rule_code:
        stmt = stmt.where(DataQualityFinding.rule_code == rule_code.upper())
        count_stmt = count_stmt.where(DataQualityFinding.rule_code == rule_code.upper())
    if record_key:
        stmt = stmt.where(DataQualityFinding.record_key == record_key)
        count_stmt = count_stmt.where(DataQualityFinding.record_key == record_key)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    items = [
        {
            "id": f.id,
            "run_id": f.run_id,
            "rule_code": f.rule_code,
            "severity": f.severity,
            "entity_type": f.entity_type,
            "record_key": f.record_key,
            "field": f.field,
            "description": f.description,
            "detected_value": f.detected_value,
            "created_at": f.created_at.isoformat(),
        }
        for f in rows
    ]
    return {
        "items": items,
        "page": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if total else 1,
        },
    }