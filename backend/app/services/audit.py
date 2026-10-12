"""Audit logging service.

Records *what happened* without storing credentials or unnecessary sensitive
content.  All writes are append-only.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditEvent

logger = logging.getLogger(__name__)


def record_event(
    session: Session,
    *,
    event_type: str,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor: str = "system",
    details: dict[str, Any] | None = None,
    commit: bool = False,
) -> AuditEvent:
    """Persist an audit event and return it."""
    event = AuditEvent(
        event_type=event_type,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        actor=actor,
        details_json=json.dumps(details, default=str) if details else None,
    )
    session.add(event)
    if commit:
        session.commit()
    logger.info("audit | %s | %s | %s", event_type, action, entity_id or "-")
    return event
