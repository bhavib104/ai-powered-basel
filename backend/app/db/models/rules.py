"""Configuration / reference models: versioned risk-weight rules and FX rates."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.common import TimestampMixin


class RiskWeightRule(TimestampMixin, Base):
    """A versioned, effective-dated risk-weight rule.

    The risk engine resolves a rule by (exposure_class, rating_grade) as of an
    evaluation date.  If no rule matches, the engine fails explicitly — it never
    assumes a default weight.
    """

    __tablename__ = "risk_weight_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_version: Mapped[str] = mapped_column(String(16), index=True)
    exposure_class: Mapped[str] = mapped_column(String(20), index=True)
    rating_grade: Mapped[str] = mapped_column(String(8), index=True)
    risk_weight: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    effective_from: Mapped[date] = mapped_column(Date, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    jurisdiction: Mapped[str] = mapped_column(String(16), default="GLOBAL")
    source_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ix_rwr_lookup",
            "rule_version",
            "exposure_class",
            "rating_grade",
            "effective_from",
        ),
    )


class FxRate(TimestampMixin, Base):
    """A seeded foreign-exchange rate used to convert to the reporting currency."""

    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(3), index=True)
    quote_currency: Mapped[str] = mapped_column(String(3), index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    effective_date: Mapped[date] = mapped_column(Date, index=True)

    __table_args__ = (
        Index("ix_fx_lookup", "base_currency", "quote_currency", "effective_date"),
    )
