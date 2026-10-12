"""Short reference-id helpers for run/request identifiers."""

from __future__ import annotations

import uuid


def new_ref(prefix: str) -> str:
    """Return a short, unique, human-readable reference id."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"
