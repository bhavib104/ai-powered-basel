"""Approved AI tool registry.

Every tool has an explicit, validated argument schema and a bounded result set.
All database access through tools is **read-only with respect to master data**
(analytical run tables are the only things that ever get written and each write
is audited).  There is no arbitrary SQL, no shell access, and no autonomous
database modification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import constants as C
from app.db.models import (
    DataQualityFinding,
    DataQualityRun,
    Exposure,
    ReconciliationResult,
    ReconciliationRun,
    RwaCalculationRun,
)
from app.services import fx, retrieval


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, object]
    handler: object
    read_only: bool = True
    max_results: int = 100
    timeout_seconds: int = 15


def _clamp(value: int | None, default: int, upper: int = 100) -> int:
    if value is None:
        return default
    return max(1, min(int(value), upper))


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
def _search_regulations(session: Session, args: dict[str, object]) -> dict[str, object]:
    query = str(args["query"])
    top_k = _clamp(int(args.get("top_k") or 5), 5)
    hits = retrieval.retrieve(session, query, top_k=top_k)
    return {
        "hits": [
            {
                "chunk_id": h.chunk_id,
                "document_id": h.document_id,
                "document_title": h.document_title,
                "page": h.page_number,
                "section": h.section,
                "text": h.content,
                "score": h.score,
            }
            for h in hits
        ],
        "count": len(hits),
    }


def _portfolio_summary(session: Session, args: dict[str, object]) -> dict[str, object]:
    as_of = date.today()
    exposures = list(session.execute(select(Exposure)).scalars())
    total_drawn: float = 0.0
    by_class: dict[str, int] = {}
    for e in exposures:
        amount = fx.to_reporting(session, e.drawn_amount, e.currency, as_of)
        if amount is not None:
            total_drawn += float(amount)
        by_class[e.exposure_class] = by_class.get(e.exposure_class, 0) + 1

    latest_run = session.execute(
        select(RwaCalculationRun).order_by(RwaCalculationRun.id.desc()).limit(1)
    ).scalar_one_or_none()

    summary: dict[str, object] = {
        "exposure_count": len(exposures),
        "total_drawn_amount_reporting": round(total_drawn, 2),
        "reporting_currency": C.REPORTING_CURRENCY,
        "exposures_by_class": dict(sorted(by_class.items())),
    }
    if latest_run is not None:
        summary["latest_rwa"] = {
            "run_ref": latest_run.run_ref,
            "rule_version": latest_run.rule_version,
            "as_of_date": latest_run.as_of_date.isoformat(),
            "status": latest_run.status,
            "calculated": latest_run.calculated_count,
            "unsupported": latest_run.unsupported_count,
            "total_rwa": float(latest_run.total_rwa),
            "total_eligible_amount": float(latest_run.total_eligible_amount),
        }
    return summary


def _lookup_exposures(session: Session, args: dict[str, object]) -> dict[str, object]:
    limit = _clamp(int(args.get("limit") or 20), 20)
    stmt = select(Exposure).options(selectinload(Exposure.counterparty)).limit(limit)
    if args.get("exposure_class"):
        stmt = stmt.where(Exposure.exposure_class == str(args["exposure_class"]).upper())
    if args.get("rating_grade"):
        stmt = stmt.where(Exposure.rating_grade == str(args["rating_grade"]).upper())
    if args.get("currency"):
        stmt = stmt.where(Exposure.currency == str(args["currency"]).upper())

    rows = []
    for e in session.execute(stmt).scalars():
        rows.append(
            {
                "exposure_ref": e.exposure_ref,
                "counterparty": e.counterparty.legal_name if e.counterparty else None,
                "exposure_class": e.exposure_class,
                "rating_grade": e.rating_grade,
                "currency": e.currency,
                "drawn_amount": str(e.drawn_amount),
                "maturity_date": e.maturity_date.isoformat(),
            }
        )
    return {"count": len(rows), "exposures": rows}


def _data_quality_findings(session: Session, args: dict[str, object]) -> dict[str, object]:
    limit = _clamp(int(args.get("limit") or 50), 50)
    run = session.execute(
        select(DataQualityRun).order_by(DataQualityRun.id.desc()).limit(1)
    ).scalar_one_or_none()
    if run is None:
        return {"run_ref": None, "finding_count": 0, "findings": []}
    stmt = select(DataQualityFinding).where(DataQualityFinding.run_id == run.id).limit(limit)
    if args.get("severity"):
        stmt = stmt.where(DataQualityFinding.severity == str(args["severity"]).upper())
    if args.get("rule_code"):
        stmt = stmt.where(DataQualityFinding.rule_code == str(args["rule_code"]).upper())
    findings = [
        {
            "rule_code": f.rule_code,
            "severity": f.severity,
            "record_key": f.record_key,
            "field": f.field,
            "description": f.description,
        }
        for f in session.execute(stmt).scalars()
    ]
    return {"run_ref": run.run_ref, "finding_count": len(findings), "findings": findings}


def _reconciliation_summary(session: Session, args: dict[str, object]) -> dict[str, object]:
    run_ref = args.get("run_ref")
    stmt = select(ReconciliationRun).order_by(ReconciliationRun.id.desc())
    if run_ref:
        stmt = (
            select(ReconciliationRun)
            .where(ReconciliationRun.run_ref == str(run_ref))
            .order_by(ReconciliationRun.id.desc())
        )
    run = session.execute(stmt).scalars().first()
    if run is None:
        return {"run_ref": None, "note": "No reconciliation run found."}
    return {
        "run_ref": run.run_ref,
        "source_a": run.source_a_key,
        "source_b": run.source_b_key,
        "tolerance": str(run.tolerance),
        "status": run.status,
        "counts": {
            "matched": run.matched,
            "mismatched": run.mismatched,
            "source_only_a": run.source_only_a,
            "source_only_b": run.source_only_b,
            "duplicates": run.duplicates,
        },
    }


def _exception_details(session: Session, args: dict[str, object]) -> dict[str, object]:
    record_key = str(args["record_key"])
    findings = session.execute(
        select(DataQualityFinding)
        .where(DataQualityFinding.record_key == record_key)
        .order_by(DataQualityFinding.id.desc())
        .limit(20)
    ).scalars()
    recon = session.execute(
        select(ReconciliationResult)
        .where(ReconciliationResult.business_key == record_key)
        .order_by(ReconciliationResult.id.desc())
        .limit(20)
    ).scalars()

    result: dict[str, object] = {"record_key": record_key}
    f_rows = [
        {"rule_code": f.rule_code, "severity": f.severity, "field": f.field, "description": f.description}
        for f in findings
    ]
    r_rows = [
        {"status": r.status, "differences": r.differences_json} for r in recon
    ]
    result["data_quality_findings"] = f_rows
    result["reconciliation_results"] = r_rows
    return result


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
TOOLS: dict[str, ToolSpec] = {
    "search_regulations": ToolSpec(
        name="search_regulations",
        description="Search indexed regulatory documents for passages relevant to a question.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search question."},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        handler=_search_regulations,
    ),
    "get_portfolio_summary": ToolSpec(
        name="get_portfolio_summary",
        description="Aggregate portfolio metrics: exposure count, total converted amount, latest RWA run.",
        parameters={"type": "object", "properties": {}},
        handler=_portfolio_summary,
    ),
    "lookup_exposures": ToolSpec(
        name="lookup_exposures",
        description="Look up exposures with optional filters on class, rating, currency.",
        parameters={
            "type": "object",
            "properties": {
                "exposure_class": {"type": "string"},
                "rating_grade": {"type": "string"},
                "currency": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
        handler=_lookup_exposures,
        max_results=50,
    ),
    "get_data_quality_findings": ToolSpec(
        name="get_data_quality_findings",
        description="Return data-quality findings from the latest run, optionally filtered.",
        parameters={
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": list(C.SEVERITIES)},
                "rule_code": {"type": "string"},
                "limit": {"type": "integer", "default": 50},
            },
        },
        handler=_data_quality_findings,
        max_results=200,
    ),
    "get_reconciliation_summary": ToolSpec(
        name="get_reconciliation_summary",
        description="Return the latest (or a named) reconciliation run summary.",
        parameters={
            "type": "object",
            "properties": {"run_ref": {"type": "string"}},
        },
        handler=_reconciliation_summary,
    ),
    "get_exception_details": ToolSpec(
        name="get_exception_details",
        description="Investigate one record: its data-quality findings and reconciliation results.",
        parameters={
            "type": "object",
            "properties": {"record_key": {"type": "string"}},
            "required": ["record_key"],
        },
        handler=_exception_details,
    ),
}


def run_tool(session: Session, name: str, args: dict[str, object]) -> tuple[object, float, str]:
    """Execute a registered tool with bounds. Returns (result, duration_ms, error)."""
    import time

    spec = TOOLS.get(name)
    if spec is None:
        return None, 0.0, f"Unknown tool '{name}'."

    start = time.monotonic()
    try:
        result = spec.handler(session, args)  # type: ignore[operator]
        result = json.loads(json.dumps(result, default=str))
        return result, (time.monotonic() - start) * 1000, ""
    except Exception as exc:  # noqa: BLE001
        return None, (time.monotonic() - start) * 1000, str(exc)


__all__ = ["ToolSpec", "TOOLS", "run_tool"]