"""Tests for the health endpoint and service banner."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_banner() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "service" in body
    assert body["health"].endswith("/health")


def test_health_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["api"] == "ok"
    assert "version" in body
