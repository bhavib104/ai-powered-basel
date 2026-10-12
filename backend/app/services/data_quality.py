"""Configurable data-quality engine.

Each check is defined by a registry row (``data_quality_rules``) and implemented
in :data:`_CHECKS`.  A run produces a summary and record-level findings.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import constants as C
from app.core.refs import new_ref
from app.db.models import (
    Collateral,
    Counterparty,
    DataQualityFinding,
    DataQualityRule,
    DataQualityRun,
    Exposure,
    SourceExposure,
)
from app.services import audit

Finding = dict[str, object]


def _load_rules(session: Session) -> dict[str, DataQualityRule]:
    rules = session.execute(select(DataQualityRule).where(DataQualityRule.enabled.is_(True))).scalars()
    return {r.rule_code: r for r in rules}


def _check_missing_mandatory(session: Session) -> list[Finding]:
    out: list[Finding] = []
    rows = session.execute(select(SourceExposure)).scalars()
    for row in rows:
        for field in ("counterparty_ref", "currency", "amount"):
            if getattr(row, field) is None:
                out.append(
                    {
                        "record_key": row.business_key,
                        "field": field,
                        "description": f"Source record is missing mandatory field '{field}'.",
                        "detected_value": None,
                    }
                )
    return out


def _check_duplicate_keys(session: Session) -> list[Finding]:
    out: list[Finding] = []
    stmt = (
        select(SourceExposure.snapshot_id, SourceExposure.business_key, func.count())
        .group_by(SourceExposure.snapshot_id, SourceExposure.business_key)
        .having(func.count() > 1)
    )
    for _snapshot_id, business_key, count in session.execute(stmt):
        out.append(
            {
                "record_key": business_key,
                "field": "business_key",
                "description": f"Duplicate business key appears {count} times in a source snapshot.",
                "detected_value": str(count),
            }
        )
    return out


def _check_invalid_amount(session: Session) -> list[Finding]:
    stmt = select(Exposure).where(Exposure.drawn_amount <= 0)
    return [
        {
            "record_key": e.exposure_ref,
            "field": "drawn_amount",
            "description": "Drawn amount is zero or negative.",
            "detected_value": str(e.drawn_amount),
        }
        for e in session.execute(stmt).scalars()
    ]


def _check_unsupported_currency(session: Session) -> list[Finding]:
    stmt = select(Exposure).where(Exposure.currency.notin_(C.SUPPORTED_CURRENCIES))
    return [
        {
            "record_key": e.exposure_ref,
            "field": "currency",
            "description": f"Currency '{e.currency}' is not supported.",
            "detected_value": e.currency,
        }
        for e in session.execute(stmt).scalars()
    ]


def _check_broken_relationship(session: Session) -> list[Finding]:
    known = {ref for (ref,) in session.execute(select(Counterparty.external_ref))}
    out: list[Finding] = []
    stmt = select(SourceExposure).where(SourceExposure.counterparty_ref.is_not(None))
    for row in session.execute(stmt).scalars():
        if row.counterparty_ref not in known:
            out.append(
                {
                    "record_key": row.business_key,
                    "field": "counterparty_ref",
                    "description": f"Counterparty reference '{row.counterparty_ref}' does not exist.",
                    "detected_value": row.counterparty_ref,
                }
            )
    return out


def _check_invalid_rating(session: Session) -> list[Finding]:
    stmt = select(Exposure).where(Exposure.rating_grade.notin_(C.RATING_GRADES))
    return [
        {
            "record_key": e.exposure_ref,
            "field": "rating_grade",
            "description": f"Rating grade '{e.rating_grade}' is not a recognised grade.",
            "detected_value": e.rating_grade,
        }
        for e in session.execute(stmt).scalars()
    ]


def _check_invalid_class(session: Session) -> list[Finding]:
    stmt = select(Exposure).where(Exposure.exposure_class.notin_(C.EXPOSURE_CLASSES))
    return [
        {
            "record_key": e.exposure_ref,
            "field": "exposure_class",
            "description": f"Exposure class '{e.exposure_class}' is not supported.",
            "detected_value": e.exposure_class,
        }
        for e in session.execute(stmt).scalars()
    ]


def _check_invalid_dates(session: Session) -> list[Finding]:
    stmt = select(Exposure).where(Exposure.maturity_date <= Exposure.issue_date)
    return [
        {
            "record_key": e.exposure_ref,
            "field": "maturity_date",
            "description": "Maturity date is on or before the issue date.",
            "detected_value": f"{e.issue_date} -> {e.maturity_date}",
        }
        for e in session.execute(stmt).scalars()
    ]


def _check_invalid_collateral_ref(session: Session) -> list[Finding]:
    known = {ref for (ref,) in session.execute(select(Collateral.collateral_ref))}
    out: list[Finding] = []
    stmt = select(SourceExposure).where(SourceExposure.collateral_ref.is_not(None))
    for row in session.execute(stmt).scalars():
        if row.collateral_ref not in known:
            out.append(
                {
                    "record_key": row.business_key,
                    "field": "collateral_ref",
                    "description": f"Collateral reference '{row.collateral_ref}' does not exist.",
                    "detected_value": row.collateral_ref,
                }
            )
    return out


_CHECKS = {
    "DQ-001": _check_missing_mandatory,
    "DQ-002": _check_duplicate_keys,
    "DQ-003": _check_invalid_amount,
    "DQ-004": _check_unsupported_currency,
    "DQ-005": _check_broken_relationship,
    "DQ-006": _check_invalid_rating,
    "DQ-007": _check_invalid_class,
    "DQ-008": _check_invalid_dates,
    "DQ-009": _check_invalid_collateral_ref,
}


def run_checks(session: Session, *, persist: bool = True, scope: str = "ALL") -> DataQualityRun:
    """Execute every enabled check and (by default) persist findings."""
    rules = _load_rules(session)

    run = DataQualityRun(
        run_ref=new_ref("DQ"),
        scope=scope,
        status="RUNNING",
        rule_count=len(rules),
        started_at=datetime.now(UTC),
    )
    if persist:
        session.add(run)
        session.flush()

    findings: list[dict[str, object]] = []
    for code, rule in rules.items():
        check = _CHECKS.get(code)
        if check is None:
            continue
        for finding in check(session):
            findings.append(
                {
                    "rule_code": code,
                    "severity": rule.severity,
                    "entity_type": rule.target_entity,
                    "record_key": finding["record_key"],
                    "field": finding.get("field"),
                    "description": finding["description"],
                    "detected_value": finding.get("detected_value"),
                }
            )

    if persist:
        for f in findings:
            session.add(DataQualityFinding(run_id=run.id, **f))

    by_severity = Counter(str(f["severity"]) for f in findings)
    by_rule = Counter(str(f["rule_code"]) for f in findings)
    run.finding_count = len(findings)
    run.status = "COMPLETED"
    run.finished_at = datetime.now(UTC)
    run.summary_json = json.dumps(
        {
            "finding_count": len(findings),
            "by_severity": dict(by_severity),
            "by_rule": dict(sorted(by_rule.items())),
        }
    )

    if persist:
        audit.record_event(
            session,
            event_type="data_quality",
            action="run_checks",
            entity_type="data_quality_run",
            entity_id=run.run_ref,
            details={"finding_count": len(findings)},
        )
        session.commit()
        session.refresh(run)

    return run
