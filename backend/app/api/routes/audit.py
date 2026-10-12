"""Audit endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events", summary="Recent audit events")
def events(
    db: Annotated[Session, Depends(get_db)],
    event_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, object]:
    stmt = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    rows = db.execute(stmt).scalars().all()
    return {
        "items": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "action": e.action,
                "actor": e.actor,
                "details": e.details_json,
                "created_at": e.created_at.isoformat(),
            }
            for e in rows
        ]
    }