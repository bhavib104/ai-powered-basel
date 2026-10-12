"""Approved-tool tests: bounds, filtering, and failure behaviour."""

from __future__ import annotations

from app.tools import TOOLS, run_tool


def test_portfolio_summary_reports_counts(seeded_db) -> None:
    result, _duration, error = run_tool(seeded_db, "get_portfolio_summary", {})
    assert error == ""
    assert result["exposure_count"] == 500
    assert result["reporting_currency"] == "USD"


def test_lookup_exposures_honours_filters(seeded_db) -> None:
    result, _d, _e = run_tool(
        seeded_db,
        "lookup_exposures",
        {"rating_grade": "BBB", "limit": 100},
    )
    assert result["count"] > 0
    assert all(row["rating_grade"] == "BBB" for row in result["exposures"])


def test_search_regulations_empty_corpus(seeded_db) -> None:
    result, _d, _e = run_tool(seeded_db, "search_regulations", {"query": "basel"})
    assert result["count"] == 0
    assert result["hits"] == []


def test_unknown_tool_fails_cleanly(seeded_db) -> None:
    result, _d, error = run_tool(seeded_db, "drop_table", {})
    assert result is None
    assert "Unknown tool" in error


def test_registry_is_read_only_by_design() -> None:
    assert set(TOOLS)
    assert all(spec.read_only for spec in TOOLS.values())
    assert "sql" not in {t for t in TOOLS}