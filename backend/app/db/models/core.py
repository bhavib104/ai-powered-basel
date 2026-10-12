"""Core master-data models: customers, counterparties, ratings, portfolios,
exposures, collateral and their relationships."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import TimestampMixin


class Customer(TimestampMixin, Base):
    """A bank customer (the commercial relationship)."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200))
    segment: Mapped[str] = mapped_column(String(40))
    country: Mapped[str] = mapped_column(String(2))

    counterparties: Mapped[list[Counterparty]] = relationship(back_populates="customer")


class Counterparty(TimestampMixin, Base):
    """An entity the bank is exposed to."""

    __tablename__ = "counterparties"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    legal_name: Mapped[str] = mapped_column(String(200))
    counterparty_type: Mapped[str] = mapped_column(String(20), index=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    sector: Mapped[str] = mapped_column(String(60))
    is_financial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Current (denormalised) rating used by the risk engine, plus history below.
    external_rating: Mapped[str] = mapped_column(String(8), default="UNRATED")
    rating_grade: Mapped[str] = mapped_column(String(8), default="UNRATED", index=True)

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    customer: Mapped[Customer | None] = relationship(back_populates="counterparties")
    exposures: Mapped[list[Exposure]] = relationship(back_populates="counterparty")
    ratings: Mapped[list[CreditRating]] = relationship(back_populates="counterparty")


class CreditRating(TimestampMixin, Base):
    """Point-in-time credit rating history for a counterparty."""

    __tablename__ = "credit_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    counterparty_id: Mapped[int] = mapped_column(
        ForeignKey("counterparties.id", ondelete="CASCADE"), index=True
    )
    agency: Mapped[str] = mapped_column(String(40))
    rating_code: Mapped[str] = mapped_column(String(12))
    grade: Mapped[str] = mapped_column(String(8), index=True)
    effective_date: Mapped[date] = mapped_column(Date)

    counterparty: Mapped[Counterparty] = relationship(back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("counterparty_id", "agency", "effective_date", name="uq_rating_point_in_time"),
    )


class Portfolio(TimestampMixin, Base):
    """A grouping of exposures (e.g. a lending book)."""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD")

    exposures: Mapped[list[Exposure]] = relationship(back_populates="portfolio")


class Exposure(TimestampMixin, Base):
    """A single credit exposure."""

    __tablename__ = "exposures"

    id: Mapped[int] = mapped_column(primary_key=True)
    exposure_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    counterparty_id: Mapped[int] = mapped_column(
        ForeignKey("counterparties.id", ondelete="RESTRICT"), index=True
    )
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="RESTRICT"), index=True
    )
    exposure_class: Mapped[str] = mapped_column(String(20), index=True)
    product_type: Mapped[str] = mapped_column(String(40))
    currency: Mapped[str] = mapped_column(String(3), index=True)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    drawn_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    undrawn_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    issue_date: Mapped[date] = mapped_column(Date)
    maturity_date: Mapped[date] = mapped_column(Date, index=True)
    is_defaulted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Effective rating for this exposure (denormalised from the counterparty).
    rating_grade: Mapped[str] = mapped_column(String(8), default="UNRATED", index=True)
    source_system: Mapped[str | None] = mapped_column(String(40), nullable=True)

    counterparty: Mapped[Counterparty] = relationship(back_populates="exposures")
    portfolio: Mapped[Portfolio] = relationship(back_populates="exposures")
    collateral_links: Mapped[list[ExposureCollateral]] = relationship(
        back_populates="exposure", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_exposures_class_rating", "exposure_class", "rating_grade"),
    )


class Collateral(TimestampMixin, Base):
    """Collateral that may mitigate an exposure (simple approach only)."""

    __tablename__ = "collateral"

    id: Mapped[int] = mapped_column(primary_key=True)
    collateral_ref: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    collateral_type: Mapped[str] = mapped_column(String(24), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    haircut_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("0"))
    valuation_date: Mapped[date] = mapped_column(Date)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    exposure_links: Mapped[list[ExposureCollateral]] = relationship(back_populates="collateral")


class ExposureCollateral(TimestampMixin, Base):
    """Allocation of a collateral item to an exposure."""

    __tablename__ = "exposure_collateral"

    id: Mapped[int] = mapped_column(primary_key=True)
    exposure_id: Mapped[int] = mapped_column(
        ForeignKey("exposures.id", ondelete="CASCADE"), index=True
    )
    collateral_id: Mapped[int] = mapped_column(
        ForeignKey("collateral.id", ondelete="CASCADE"), index=True
    )
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    exposure: Mapped[Exposure] = relationship(back_populates="collateral_links")
    collateral: Mapped[Collateral] = relationship(back_populates="exposure_links")

    __table_args__ = (
        UniqueConstraint("exposure_id", "collateral_id", name="uq_exposure_collateral"),
    )
