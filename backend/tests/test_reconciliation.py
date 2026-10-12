"""Reconciliation-engine tests, validated against the seeded discrepancies."""

from __future__ import annotations

from app.services import reconciliation


def test_seeded_discrepancies_are_detected(seeded_db) -> None:
    manifest = seeded_db._seed_manifest  # type: ignore[attr-defined]
    expected = manifest["reconciliation"]["expected"]

    run = reconciliation.run_reconciliation(seeded_db, source_a="SRC-A", source_b="SRC-B")

    assert run.status == "COMPLETED"
    assert run.mismatched == expected["amount_mismatch"]
    assert run.duplicates == expected["duplicates_in_b"]
    assert run.source_only_b == expected["extra_in_b"]

    # Missing-in-B keys plus source-layer DQ records exist only in snapshot A.
    # (Every source-layer anomaly *except* DQ-002 duplicates removes that
    # record's key from snapshot B while keeping it in snapshot A.)
    source_anomalies = sum(
        1
        for a in manifest["data_quality_anomalies"]
        if a["entity"] == "source_exposures" and a["rule_code"] != "DQ-002"
    )
    assert run.source_only_a == expected["missing_in_b"] + source_anomalies


def test_tolerance_does_not_swallow_real_differences(seeded_db) -> None:
    """Mismatches are seeded at ~5%+ of the amount, well beyond any sane tolerance."""
    from decimal import Decimal

    run = reconciliation.run_reconciliation(
        seeded_db,
        source_a="SRC-A",
        source_b="SRC-B",
        tolerance=Decimal("0.01"),
    )
    assert run.mismatched == 40  # every seeded amount delta exceeds tolerance


def test_totals_are_consistent(seeded_db) -> None:
    run = reconciliation.run_reconciliation(seeded_db, source_a="SRC-A", source_b="SRC-B")
    parts = (
        run.matched,
        run.mismatched,
        run.source_only_a,
        run.source_only_b,
        run.duplicates,
    )
    assert sum(parts) == 520  # 500 keys in A + 20 extra keys in B


def test_unknown_snapshot_raises(db) -> None:
    import pytest

    from app.core.exceptions import NotFoundError

    with pytest.raises(NotFoundError):
        reconciliation.run_reconciliation(db, source_a="SRC-NOPE", source_b="SRC-B")