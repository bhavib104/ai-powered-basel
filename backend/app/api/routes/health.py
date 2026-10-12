"""Health and service-metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness / readiness probe")
def health() -> dict[str, object]:
    """Return basic service status.

    This is intentionally dependency-free for now.  As later phases add the
    database and AI providers, this endpoint will report their status too.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
        "checks": {"api": "ok"},
    }
