"""Dashboard endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services import dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", summary="Aggregate dashboard metrics")
def summary(db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return dashboard.get_dashboard_summary(db)