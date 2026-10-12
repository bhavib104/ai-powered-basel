"""Shared pytest fixtures.

Important: environment switches for providers are set *before* any ``app``
module is imported so factories pick up deterministic backends (hashing
embeddings, mock LLM) — tests never require network or model downloads.
"""

from __future__ import annotations

import os

os.environ["EMBEDDING_BACKEND"] = "hashing"
os.environ["LLM_PROVIDER"] = "mock"

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.db.models  # noqa: F401  (register every model on Base.metadata)
from app.db.base import Base
from app.seed.generator import SeedConfig, seed_database


def _make_session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    return engine, session


@pytest.fixture
def db(tmp_path):
    """A clean, isolated database session for each test."""
    engine, session = _make_session(tmp_path)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def seeded_db(db):
    """A small but fully-seeded synthetic database."""
    result = seed_database(db, SeedConfig(
        seed=42,
        n_customers=50,
        n_counterparties=100,
        n_portfolios=4,
        n_exposures=500,
        n_collateral=100,
    ))
    db.commit()
    # Attach the seed manifest so tests can assert against ground truth.
    db._seed_manifest = result.manifest  # type: ignore[attr-defined]
    return db


@pytest.fixture
def client(seeded_db):
    """TestClient with the API's DB dependency overridden to the test database."""
    from app.db import get_db
    from app.main import app

    def override():
        yield seeded_db

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()