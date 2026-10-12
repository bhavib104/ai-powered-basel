"""Application-specific exceptions.

These map cleanly onto HTTP responses in ``app.core.error_handlers`` and give
services a precise vocabulary (e.g. ``NotFound``, ``UnsupportedCase``).
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for expected, handled application errors."""

    status_code: int = 400
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class UnsupportedCaseError(AppError):
    """A supported operation was requested for an unsupported case.

    Raised when, for example, a risk weight cannot be resolved.  We never
    silently substitute a default value.
    """

    status_code = 409
    code = "unsupported_case"


class ProviderUnavailableError(AppError):
    status_code = 503
    code = "provider_unavailable"


class ToolExecutionError(AppError):
    status_code = 400
    code = "tool_execution_error"
