"""End-to-end API tests (FastAPI TestClient, seeded test database)."""

from __future__ import annotations


def test_root_banner(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"].endswith("/health")


def test_health(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["api"] == "ok"


def test_dashboard_summary(client) -> None:
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["exposures"]["count"] == 500
    assert body["exposures"]["currency"] == "USD"


def test_exposures_pagination_and_filter(client) -> None:
    response = client.get("/api/v1/exposures", params={"page_size": 10})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 10
    assert body["page"]["total"] == 500

    filtered = client.get("/api/v1/exposures", params={"rating_grade": "BBB", "page_size": 200})
    rows = filtered.json()["items"]
    assert rows and all(r["rating_grade"] == "BBB" for r in rows)


def test_exposure_detail(client) -> None:
    response = client.get("/api/v1/exposures/1")
    assert response.status_code == 200
    body = response.json()
    assert body["exposure_ref"].startswith("EXP-")


def test_exposure_detail_not_found(client) -> None:
    assert client.get("/api/v1/exposures/999999").status_code == 404


def test_risk_calculation(client) -> None:
    response = client.post("/api/v1/risk/calculate", json={"rule_version": "2024.1"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["exposure_count"] == 500
    assert body["calculated"] == 435  # 65 seeded unsupported inputs fail explicitly
    assert body["unsupported"] == 65
    assert body["total_rwa"] > 0


def test_risk_run_results(client) -> None:
    run = client.post("/api/v1/risk/calculate", json={"rule_version": "2024.1"}).json()
    response = client.get(
        f"/api/v1/risk/runs/{run['id']}/results",
        params={"status": "OK", "page_size": 500},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 435


def test_data_quality_run_matches_manifest(client, seeded_db) -> None:
    manifest = seeded_db._seed_manifest  # type: ignore[attr-defined]
    response = client.post("/api/v1/quality/run", json={"scope": "ALL"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["finding_count"] == sum(manifest["anomaly_totals"].values())


def test_quality_findings_list(client) -> None:
    client.post("/api/v1/quality/run", json={"scope": "ALL"})
    response = client.get("/api/v1/quality/findings", params={"severity": "CRITICAL"})
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert all(i["severity"] == "CRITICAL" for i in body["items"])


def test_reconciliation_run(client, seeded_db) -> None:
    manifest = seeded_db._seed_manifest  # type: ignore[attr-defined]
    expected = manifest["reconciliation"]["expected"]
    response = client.post(
        "/api/v1/reconciliation/run",
        json={"source_a": "SRC-A", "source_b": "SRC-B"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["mismatched"] == expected["amount_mismatch"]
    assert body["duplicates"] == expected["duplicates_in_b"]


def test_document_search_with_no_documents(client) -> None:
    response = client.post(
        "/api/v1/documents/search", json={"query": "Basel leverage ratio", "top_k": 3}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["hits"] == []
    assert body["insufficient_evidence"] is True


def test_assistant_query_endpoint(client) -> None:
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "What is the total exposure amount in the portfolio?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["tool_executions"]
    assert body["provider"] == "mock"
    assert body["request_ref"].startswith("AI-")


def test_regulatory_question_returns_evidence_disclaimer(client) -> None:
    response = client.post(
        "/api/v1/assistant/query",
        json={"question": "What does Basel III require for the leverage ratio?"},
    )
    body = response.json()
    assert body["insufficient_evidence"] is True


def test_audit_events_are_recorded(client) -> None:
    client.post("/api/v1/quality/run", json={"scope": "ALL"})
    response = client.get("/api/v1/audit/events")
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert any(e["event_type"] == "data_quality" for e in body["items"])