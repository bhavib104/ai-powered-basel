"""Controlled AI orchestration.

A **deterministic intent router** decides which approved tools to call and which
documents to retrieve.  Results become the evidence; the LLM (when available)
writes a grounded summary, otherwise a deterministic composer does.  Every tool
call is validated, bounded, timed and audited.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.refs import new_ref
from app.db.models import AiRequest, AiToolExecution
from app.providers import get_llm_provider
from app.services import audit, generation
from app.tools import run_tool

logger = logging.getLogger(__name__)

_REGULATORY = (
    "basel", "regulatory", "regulation", "rbi", "circular", "guideline",
    "accord", "pillar", "capital requirement", "risk weight", "framework",
    "bcbs", "document", "paragraph", "standard", "reference",
)
_DATA = (
    "exposure", "portfolio", "rating", "counterparty", "summary", "rwa",
    "risk-weighted", "total", "data quality", "finding", "reconcil", "mismat",
    "source", "loan", "amount", "collateral",
)
_EXPOSURE_HINTS = ("exposure", "loan", "counterparty", "high-risk", "rating", "borrower")
_DQ_HINTS = ("data quality", "quality", "finding", "anomal", "invalid")
_RECON_HINTS = ("reconcil", "mismatch", "source", "match", "duplicate")
_RWA_HINTS = ("rwa", "risk-weight", "calculate")
_EXCEPTION_RE = re.compile(r"\b(EXP-\d{7})\b")


@dataclass
class ToolExecutionRecord:
    tool_name: str
    arguments: dict[str, object]
    status: str = "OK"
    result_summary: str | None = None
    error: str | None = None
    duration_ms: int | None = None


@dataclass
class AssistantResult:
    answer: str
    citations: list[dict[str, object]] = field(default_factory=list)
    insufficient_evidence: bool = False
    tool_executions: list[ToolExecutionRecord] = field(default_factory=list)
    provider: str = "mock"
    model: str | None = None
    request_ref: str | None = None


def _plan(question: str) -> list[tuple[str, dict[str, object]]]:
    """Deterministic routing: map a question to approved tools."""
    q = question.lower()
    plan: list[tuple[str, dict[str, object]]] = []
    regulatory = any(k in q for k in _REGULATORY)
    data = any(k in q for k in _DATA)
    dq = any(k in q for k in _DQ_HINTS)
    recon = any(k in q for k in _RECON_HINTS)
    rwa = any(k in q for k in _RWA_HINTS)

    if regulatory:
        plan.append(("search_regulations", {"query": question, "top_k": 5}))
    if data or rwa:
        plan.append(("get_portfolio_summary", {}))
    if (data or rwa) and any(k in q for k in _EXPOSURE_HINTS):
        plan.append(("lookup_exposures", {"limit": 20}))
    if dq:
        plan.append(("get_data_quality_findings", {"limit": 50}))
    if recon:
        plan.append(("get_reconciliation_summary", {}))
    match = _EXCEPTION_RE.search(question)
    if match:
        plan.append(("get_exception_details", {"record_key": match.group(1)}))

    # Collapse duplicates while preserving order.
    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, dict[str, object]]] = []
    for name, args in plan:
        key = (name, json.dumps(args, sort_keys=True))
        if key not in seen:
            seen.add(key)
            unique.append((name, args))
    return unique


def answer_question(session: Session, question: str, *, persist: bool = True) -> AssistantResult:
    """Answer a natural-language question with bounded, audited tool use."""
    settings = get_settings()
    provider = get_llm_provider()
    started = datetime.now(UTC)
    plan = _plan(question)

    executions: list[ToolExecutionRecord] = []
    evidence: list[dict[str, object]] = []
    citations: list[dict[str, object]] = []

    for name, args in plan[: settings.ai_max_tool_calls]:
        result, duration_ms, error = run_tool(session, name, args)
        record = ToolExecutionRecord(
            tool_name=name,
            arguments=args,
            status="ERROR" if error else "OK",
            error=error or None,
            duration_ms=int(duration_ms),
        )
        executions.append(record)

        if error:
            continue
        if name == "search_regulations":
            for hit in result.get("hits", []):  # type: ignore[union-attr]
                evidence.append(
                    {
                        "source": hit["document_title"],
                        "page": hit.get("page"),
                        "section": hit.get("section"),
                        "text": hit["text"],
                    }
                )
                citations.append(
                    {
                        "index": len(citations) + 1,
                        "chunk_id": hit["chunk_id"],
                        "document_id": hit["document_id"],
                        "document_title": hit["document_title"],
                        "page": hit.get("page"),
                        "section": hit.get("section"),
                        "snippet": hit["text"][:300],
                        "score": hit.get("score"),
                    }
                )
            record.result_summary = f"Retrieved {result.get('count', 0)} passage(s)."
        else:
            record.result_summary = json.dumps(result, default=str)[:500]
            evidence.append(
                {
                    "source": f"Structured data tool: {name}",
                    "page": None,
                    "section": None,
                    "text": json.dumps(result, default=str)[:2000],
                }
            )

    answer = generation.synthesize(question, evidence, provider)
    insufficient = bool(citations) is False and any(reg in question.lower() for reg in _REGULATORY) and len(evidence) == 0

    request_ref = new_ref("AI")
    latency_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)

    if persist:
        db_request = AiRequest(
            request_ref=request_ref,
            question=question,
            provider=provider.name,
            model=getattr(provider, "model", None),
            status="COMPLETED",
            answer=answer,
            insufficient_evidence=insufficient,
            citations_json=json.dumps(citations, default=str) if citations else None,
            latency_ms=latency_ms,
            started_at=started,
            finished_at=datetime.now(UTC),
        )
        session.add(db_request)
        session.flush()
        for rec in executions:
            session.add(
                AiToolExecution(
                    request_id=db_request.id,
                    tool_name=rec.tool_name,
                    arguments_json=json.dumps(rec.arguments, default=str),
                    result_summary=rec.result_summary,
                    status=rec.status,
                    duration_ms=rec.duration_ms,
                    error=rec.error,
                )
            )
        audit.record_event(
            session,
            event_type="assistant",
            action="answer_question",
            entity_type="ai_request",
            entity_id=request_ref,
            details={"tools": [e.tool_name for e in executions], "insufficient_evidence": insufficient},
        )
        session.commit()

    return AssistantResult(
        answer=answer,
        citations=citations,
        insufficient_evidence=insufficient,
        tool_executions=executions,
        provider=provider.name,
        model=getattr(provider, "model", None),
        request_ref=request_ref,
    )