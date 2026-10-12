"""FastAPI application entry point.

Run locally with::

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import health
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    logger.info(
        "Starting %s v%s (env=%s, llm=%s)",
        settings.app_name,
        __version__,
        settings.environment,
        settings.llm_provider,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Deterministic banking risk calculations combined with "
            "AI-assisted regulatory document intelligence."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["meta"], summary="Service banner")
    def root() -> dict[str, object]:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    app.include_router(health.router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
