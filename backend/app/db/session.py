"""Database engine, session factory and FastAPI dependency."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_settings = get_settings()


def _ensure_sqlite_dir(url: str) -> None:
    """Make sure the folder for a file-based SQLite database exists."""
    prefix = "sqlite:///"
    if url.startswith(prefix):
        raw = url[len(prefix) :]
        if raw and raw != ":memory:":
            Path(raw).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(_settings.database_url)

# ``check_same_thread=False`` is required because FastAPI may touch the
# connection from a different thread than the one that created it.
connect_args = {"check_same_thread": False} if _settings.is_sqlite else {}

engine: Engine = create_engine(
    _settings.database_url,
    echo=False,
    future=True,
    connect_args=connect_args,
)


if _settings.is_sqlite:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):  # noqa: ANN001
        """Enable foreign-key enforcement and WAL for SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
