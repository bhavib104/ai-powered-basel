"""Data-quality engine tests, validated against the seeded ground-truth manifest."""

from __future__ import annotations

from sqlalchemy import select

from app.db.models import DataQualityFinding
from app.services import data_quality


def test_seeded_anomalies_are_detected(seeded_db) -> None:
    manifest = seeded_db._seed_manifest  # type: ignore[attr-defined]
    run = data_quality.run_checks(seeded_db)
    assert run.status == "COMPLETED"
    assert run.rule_count == 9

    findings = {
        (f.rule_code, f.record_key)
        for f in seeded_db.execute(select(DataQualityFinding)).scalars()
    }
    for anomaly in manifest["data_quality_anomalies"]:
        key = (anomaly["rule_code"], anomaly["record_key"])
        assert key in findings, f"Seeded anomaly was not detected: {anomaly}"


def test_finding_totals_match_manifest(seeded_db) -> None:
    manifest = seeded_db._seed_manifest  # type: ignore[attr-defined]
    run = data_quality.run_checks(seeded_db)
    totals = manifest["anomaly_totals"]

    by_rule: dict[str, int] = {}
    for f in seeded_db.execute(select(DataQualityFinding)).scalars():
        by_rule[f.rule_code] = by_rule.get(f.rule_code, 0) + 1

    assert run.finding_count == sum(totals.values())
    for code, expected in totals.items():
        assert by_rule.get(code, 0) == expected, f"Rule {code} finding count mismatch"


def test_severity_is_taken_from_rule_registry(seeded_db) -> None:
    data_quality.run_checks(seeded_db)
    finding = seeded_db.execute(
        select(DataQualityFinding).where(DataQualityFinding.rule_code == "DQ-005")
    ).scalars().first()
    assert finding is not None
    assert finding.severity == "CRITICAL"  # broken relationship


def test_invalid_rating_seeded_as_unsupported(seeded_db) -> None:
    """Records with an invalid rating fail the risk engine silently-cleanly."""
    from app.services import risk_engine

    run = risk_engine.run_calculation(seeded_db, rule_version="2024.1")
    assert run.unsupported_count > 0