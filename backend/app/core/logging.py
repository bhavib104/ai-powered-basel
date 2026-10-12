"""Logging configuration.

Two formats are supported:

* ``text`` — human-readable, ideal for local development (the default).
* ``json`` — one JSON object per line, suitable for log aggregation.

Structured logs are a requirement (see TRD §17); developers simply get the
friendlier format by default.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Render each log record as a single JSON object."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


_TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(level: str = "INFO", fmt: str = "text") -> None:
    """Configure the root logger.  Safe to call multiple times."""
    handler = logging.StreamHandler(sys.stdout)
    if fmt.lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Uvicorn already logs requests; keep them at WARNING to reduce noise.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
