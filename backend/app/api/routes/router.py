"""API router aggregate and route modules."""

from fastapi import APIRouter

from app.api.routes import (
    assistant,
    audit,
    dashboard,
    documents,
    exposures,
    health,
    quality,
    reconciliation,
    risk,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="")
api_router.include_router(dashboard.router)
api_router.include_router(exposures.router)
api_router.include_router(risk.router)
api_router.include_router(quality.router)
api_router.include_router(reconciliation.router)
api_router.include_router(documents.router)
api_router.include_router(assistant.router)
api_router.include_router(audit.router)

__all__ = ["api_router"]