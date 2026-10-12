"""Health and service-metadata endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import get_settings
from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness / readiness probe")
def health(db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    """Report service status, database connectivity, and AI provider state."""
    settings = get_settings()
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False

    provider = settings.llm_provider
    checks = {"api": "ok", "database": "ok" if db_ok else "error"}
    if provider:
        checks["llm_provider"] = provider
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "checks": checks,
    }