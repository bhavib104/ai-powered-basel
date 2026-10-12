"""Dashboard aggregation service — real numbers from persisted data."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import REPORTING_CURRENCY
from app.db.models import (
    DataQualityRun,
    Exposure,
    ReconciliationRun,
    RegulatoryDocument,
    RwaCalculationRun,
)
from app.services import fx


def get_dashboard_summary(session: Session) -> dict[str, object]:
    """Aggregate dashboard metrics from actual database content."""

    exposure_count = session.execute(select(func.count(Exposure.id))).scalar_one()
    as_of = date.today()
    total_drawn: float = 0.0
    for amount, currency in session.execute(
        select(Exposure.drawn_amount, Exposure.currency)
    ):
        converted = fx.to_reporting(session, amount, currency, as_of)
        if converted is not None:
            total_drawn += float(converted)

    latest_rwa = session.execute(
        select(RwaCalculationRun).order_by(RwaCalculationRun.id.desc()).limit(1)
    ).scalar_one_or_none()
    latest_dq = session.execute(
        select(DataQualityRun).order_by(DataQualityRun.id.desc()).limit(1)
    ).scalar_one_or_none()
    latest_recon = session.execute(
        select(ReconciliationRun).order_by(ReconciliationRun.id.desc()).limit(1)
    ).scalar_one_or_none()
    doc_count = session.execute(
        select(func.count(RegulatoryDocument.id))
    ).scalar_one()
    doc_ingested = session.execute(
        select(func.count(RegulatoryDocument.id)).where(RegulatoryDocument.status == "INGESTED")
    ).scalar_one()

    def _dq_summary(run: DataQualityRun | None) -> dict[str, object] | None:
        if run is None:
            return None
        import json

        return {
            "run_ref": run.run_ref,
            "finding_count": run.finding_count,
            "summary": json.loads(run.summary_json) if run.summary_json else None,
        }

    def _recon_summary(run: ReconciliationRun | None) -> dict[str, object] | None:
        if run is None:
            return None
        return {
            "run_ref": run.run_ref,
            "source_a": run.source_a_key,
            "source_b": run.source_b_key,
            "matched": run.matched,
            "mismatched": run.mismatched,
            "source_only_a": run.source_only_a,
            "source_only_b": run.source_only_b,
            "duplicates": run.duplicates,
        }

    return {
        "exposures": {"count": exposure_count, "total_drawn_amount": round(total_drawn, 2), "currency": REPORTING_CURRENCY},
        "rwa": (
            {
                "run_ref": latest_rwa.run_ref,
                "rule_version": latest_rwa.rule_version,
                "total_rwa": float(latest_rwa.total_rwa),
                "total_eligible_amount": float(latest_rwa.total_eligible_amount),
                "calculated": latest_rwa.calculated_count,
                "unsupported": latest_rwa.unsupported_count,
            }
            if latest_rwa
            else None
        ),
        "data_quality": _dq_summary(latest_dq),
        "reconciliation": _recon_summary(latest_recon),
        "documents": {"count": doc_count, "ingested": doc_ingested},
        "recent_runs": {
            "rwa": [latest_rwa.run_ref, latest_rwa.finished_at.isoformat()] if latest_rwa else None,
            "data_quality": [latest_dq.run_ref, latest_dq.finished_at.isoformat()] if latest_dq else None,
            "reconciliation": [latest_recon.run_ref, latest_recon.finished_at.isoformat()] if latest_recon else None,
        },
    }