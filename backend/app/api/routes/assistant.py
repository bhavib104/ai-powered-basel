"""AI Risk Assistant endpoints."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.db.models import AiRequest, AiToolExecution
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services import orchestration

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _tool_out(execution: AiToolExecution) -> dict[str, object]:
    return {
        "tool_name": execution.tool_name,
        "arguments": json.loads(execution.arguments_json) if execution.arguments_json else {},
        "status": execution.status,
        "result_summary": execution.result_summary,
        "error": execution.error,
        "duration_ms": execution.duration_ms,
    }


@router.post("/query", response_model=AssistantResponse, summary="Ask a natural-language question")
def query(payload: AssistantRequest, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    result = orchestration.answer_question(db, payload.question)
    return {
        "request_ref": result.request_ref,
        "answer": result.answer,
        "citations": result.citations,
        "insufficient_evidence": result.insufficient_evidence,
        "tool_executions": [
            {
                "tool_name": e.tool_name,
                "arguments": e.arguments,
                "status": e.status,
                "result_summary": e.result_summary,
                "error": e.error,
                "duration_ms": e.duration_ms,
            }
            for e in result.tool_executions
        ],
        "provider": result.provider,
        "model": result.model,
    }


@router.get("/requests", summary="Assistant request history")
def requests(db: Annotated[Session, Depends(get_db)], limit: int = Query(30, ge=1, le=100)) -> dict[str, object]:
    rows = db.execute(
        select(AiRequest).order_by(AiRequest.id.desc()).limit(limit)
    ).scalars().all()
    return {
        "items": [
            {
                "id": r.id,
                "request_ref": r.request_ref,
                "question": r.question,
                "provider": r.provider,
                "status": r.status,
                "answer": r.answer,
                "insufficient_evidence": r.insufficient_evidence,
                "latency_ms": r.latency_ms,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


@router.get("/requests/{request_ref}", summary="One assistant exchange with tool executions")
def request_detail(request_ref: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    row = db.execute(
        select(AiRequest)
        .options(selectinload(AiRequest.tool_executions))
        .where(AiRequest.request_ref == request_ref)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Assistant request not found.")
    return {
        "id": row.id,
        "request_ref": row.request_ref,
        "question": row.question,
        "provider": row.provider,
        "model": row.model,
        "status": row.status,
        "answer": row.answer,
        "insufficient_evidence": row.insufficient_evidence,
        "citations": json.loads(row.citations_json) if row.citations_json else [],
        "latency_ms": row.latency_ms,
        "error": row.error,
        "created_at": row.created_at.isoformat(),
        "tool_executions": [_tool_out(e) for e in row.tool_executions],
    }