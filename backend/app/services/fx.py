"""Foreign-exchange conversion to the single reporting currency.

This is a documented simplification (ADR-009): a small seeded rate table with
effective dates.  If a currency cannot be converted the caller gets ``None`` and
must treat the case as unsupported rather than guessing.
"""

from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import REPORTING_CURRENCY
from app.db.models import FxRate


def get_rate(session: Session, base_currency: str, as_of: date) -> Decimal | None:
    """Return the rate to convert 1 ``base_currency`` into the reporting currency."""
    if base_currency == REPORTING_CURRENCY:
        return Decimal("1")

    stmt = (
        select(FxRate)
        .where(
            FxRate.base_currency == base_currency,
            FxRate.quote_currency == REPORTING_CURRENCY,
            FxRate.effective_date <= as_of,
        )
        .order_by(FxRate.effective_date.desc())
        .limit(1)
    )
    rate = session.execute(stmt).scalar_one_or_none()
    return rate.rate if rate else None


def to_reporting(
    session: Session, amount: Decimal, currency: str, as_of: date
) -> Decimal | None:
    """Convert ``amount`` into the reporting currency, or ``None`` if unknown."""
    rate = get_rate(session, currency, as_of)
    if rate is None:
        return None
    return (Decimal(amount) * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
