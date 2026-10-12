"""Reconciliation engine.

Compares two source snapshots on a business key and classifies every key as
matched, mismatched, source-only, or duplicate.  Original source values and
field-level differences are preserved.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import constants as C
from app.core.exceptions import NotFoundError
from app.core.refs import new_ref
from app.db.models import (
    ReconciliationResult,
    ReconciliationRun,
    SourceExposure,
    SourceSnapshot,
)
from app.services import audit

_COMPARE_FIELDS = ("counterparty_ref", "exposure_class", "currency", "rating_grade", "maturity_date")


def _serialise(row: SourceExposure) -> dict[str, str | None]:
    return {
        "business_key": row.business_key,
        "counterparty_ref": row.counterparty_ref,
        "exposure_class": row.exposure_class,
        "currency": row.currency,
        "amount": str(row.amount) if row.amount is not None else None,
        "rating_grade": row.rating_grade,
        "maturity_date": row.maturity_date.isoformat() if row.maturity_date else None,
    }


def _group(session: Session, snapshot_id: int) -> dict[str, list[SourceExposure]]:
    rows = session.execute(
        select(SourceExposure).where(SourceExposure.snapshot_id == snapshot_id)
    ).scalars()
    grouped: dict[str, list[SourceExposure]] = {}
    for row in rows:
        grouped.setdefault(row.business_key, []).append(row)
    return grouped


def run_reconciliation(
    session: Session,
    *,
    source_a: str,
    source_b: str,
    tolerance: Decimal | None = None,
    persist: bool = True,
) -> ReconciliationRun:
    snap_a = session.execute(
        select(SourceSnapshot).where(SourceSnapshot.snapshot_code == source_a)
    ).scalar_one_or_none()
    snap_b = session.execute(
        select(SourceSnapshot).where(SourceSnapshot.snapshot_code == source_b)
    ).scalar_one_or_none()
    if snap_a is None:
        raise NotFoundError(f"Source snapshot '{source_a}' was not found.")
    if snap_b is None:
        raise NotFoundError(f"Source snapshot '{source_b}' was not found.")

    tol = tolerance if tolerance is not None else Decimal("0.01")
    group_a = _group(session, snap_a.id)
    group_b = _group(session, snap_b.id)

    run = ReconciliationRun(
        run_ref=new_ref("RECON"),
        source_a_key=source_a,
        source_b_key=source_b,
        tolerance=tol,
        status="RUNNING",
        started_at=datetime.now(UTC),
    )
    if persist:
        session.add(run)
        session.flush()

    counts = {C.RECON_MATCHED: 0, C.RECON_MISMATCHED: 0,
              C.RECON_SOURCE_ONLY_A: 0, C.RECON_SOURCE_ONLY_B: 0, C.RECON_DUPLICATE: 0}
    results: list[dict[str, object]] = []

    for key in sorted(set(group_a) | set(group_b)):
        a_rows = group_a.get(key, [])
        b_rows = group_b.get(key, [])
        a_val = _serialise(a_rows[0]) if a_rows else None
        b_val = _serialise(b_rows[0]) if b_rows else None

        if len(a_rows) > 1 or len(b_rows) > 1:
            status = C.RECON_DUPLICATE
            differences = {"duplicate": True, "a_count": len(a_rows), "b_count": len(b_rows)}
        elif a_rows and b_rows:
            differences = _compare(a_rows[0], b_rows[0], tol)
            status = C.RECON_MATCHED if not differences else C.RECON_MISMATCHED
        elif a_rows:
            status = C.RECON_SOURCE_ONLY_A
            differences = {"present_in": source_a}
        else:
            status = C.RECON_SOURCE_ONLY_B
            differences = {"present_in": source_b}

        counts[status] += 1
        results.append(
            {
                "business_key": key,
                "status": status,
                "source_a_value": json.dumps(a_val) if a_val else None,
                "source_b_value": json.dumps(b_val) if b_val else None,
                "differences_json": json.dumps(differences) if differences else None,
            }
        )

    if persist:
        for r in results:
            session.add(ReconciliationResult(run_id=run.id, **r))

    run.matched = counts[C.RECON_MATCHED]
    run.mismatched = counts[C.RECON_MISMATCHED]
    run.source_only_a = counts[C.RECON_SOURCE_ONLY_A]
    run.source_only_b = counts[C.RECON_SOURCE_ONLY_B]
    run.duplicates = counts[C.RECON_DUPLICATE]
    run.status = "COMPLETED"
    run.finished_at = datetime.now(UTC)
    run.summary_json = json.dumps({"counts": counts, "tolerance": str(tol)})

    if persist:
        audit.record_event(
            session,
            event_type="reconciliation",
            action="run_reconciliation",
            entity_type="reconciliation_run",
            entity_id=run.run_ref,
            details={"counts": counts},
        )
        session.commit()
        session.refresh(run)

    return run


def _compare(a: SourceExposure, b: SourceExposure, tolerance: Decimal) -> dict[str, object]:
    diffs: dict[str, object] = {}
    for field in _COMPARE_FIELDS:
        av = getattr(a, field)
        bv = getattr(b, field)
        av = av.isoformat() if hasattr(av, "isoformat") else av
        bv = bv.isoformat() if hasattr(bv, "isoformat") else bv
        if av != bv:
            diffs[field] = {"a": av, "b": bv}

    if a.amount is None or b.amount is None:
        if a.amount != b.amount:
            diffs["amount"] = {
                "a": str(a.amount) if a.amount is not None else None,
                "b": str(b.amount) if b.amount is not None else None,
            }
    else:
        delta = abs(Decimal(a.amount) - Decimal(b.amount))
        if delta > tolerance:
            diffs["amount"] = {
                "a": str(a.amount),
                "b": str(b.amount),
                "delta": str(delta),
                "tolerance": str(tolerance),
            }
    return diffs
