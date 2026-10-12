"""Processing models: source snapshots, data-quality, reconciliation and RWA runs."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.common import TimestampMixin


# ---------------------------------------------------------------------------
# Source snapshots (input to reconciliation)
# ---------------------------------------------------------------------------
class SourceSnapshot(TimestampMixin, Base):
    __tablename__ = "source_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    source_system: Mapped[str] = mapped_column(String(40))
    as_of_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    records: Mapped[list[SourceExposure]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class SourceExposure(TimestampMixin, Base):
    """A flat exposure record inside a source snapshot."""

    __tablename__ = "source_exposures"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("source_snapshots.id", ondelete="CASCADE"), index=True
    )
    business_key: Mapped[str] = mapped_column(String(40), index=True)
    counterparty_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    exposure_class: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    rating_grade: Mapped[str | None] = mapped_column(String(8), nullable=True)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    collateral_ref: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    snapshot: Mapped[SourceSnapshot] = relationship(back_populates="records")

    __table_args__ = (Index("ix_source_exposure_key", "snapshot_id", "business_key"),)


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------
class DataQualityRule(TimestampMixin, Base):
    __tablename__ = "data_quality_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_code: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(12), index=True)
    target_entity: Mapped[str] = mapped_column(String(40))
    target_field: Mapped[str | None] = mapped_column(String(80), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(16), default="1.0")


class DataQualityRun(TimestampMixin, Base):
    __tablename__ = "data_quality_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    scope: Mapped[str] = mapped_column(String(40), default="ALL")
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")
    rule_count: Mapped[int] = mapped_column(Integer, default=0)
    finding_count: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    findings: Mapped[list[DataQualityFinding]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class DataQualityFinding(TimestampMixin, Base):
    __tablename__ = "data_quality_findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("data_quality_runs.id", ondelete="CASCADE"), index=True
    )
    rule_code: Mapped[str] = mapped_column(String(16), index=True)
    severity: Mapped[str] = mapped_column(String(12), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    record_key: Mapped[str] = mapped_column(String(60), index=True)
    field: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    detected_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[DataQualityRun] = relationship(back_populates="findings")


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------
class ReconciliationRun(TimestampMixin, Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    source_a_key: Mapped[str] = mapped_column(String(40))
    source_b_key: Mapped[str] = mapped_column(String(40))
    business_key: Mapped[str] = mapped_column(String(40), default="business_key")
    tolerance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.01"))
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")
    matched: Mapped[int] = mapped_column(Integer, default=0)
    mismatched: Mapped[int] = mapped_column(Integer, default=0)
    source_only_a: Mapped[int] = mapped_column(Integer, default=0)
    source_only_b: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list[ReconciliationResult]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class ReconciliationResult(TimestampMixin, Base):
    __tablename__ = "reconciliation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), index=True
    )
    business_key: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    source_a_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_b_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    differences_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[ReconciliationRun] = relationship(back_populates="results")


# ---------------------------------------------------------------------------
# RWA calculation
# ---------------------------------------------------------------------------
class RwaCalculationRun(TimestampMixin, Base):
    __tablename__ = "rwa_calculation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    rule_version: Mapped[str] = mapped_column(String(16))
    as_of_date: Mapped[date] = mapped_column(Date)
    reporting_currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(20), default="COMPLETED")
    exposure_count: Mapped[int] = mapped_column(Integer, default=0)
    calculated_count: Mapped[int] = mapped_column(Integer, default=0)
    unsupported_count: Mapped[int] = mapped_column(Integer, default=0)
    total_eligible_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    total_rwa: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list[RwaCalculationResult]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class RwaCalculationResult(TimestampMixin, Base):
    __tablename__ = "rwa_calculation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("rwa_calculation_runs.id", ondelete="CASCADE"), index=True
    )
    exposure_id: Mapped[int | None] = mapped_column(
        ForeignKey("exposures.id", ondelete="SET NULL"), nullable=True, index=True
    )
    exposure_ref: Mapped[str] = mapped_column(String(40), index=True)
    exposure_class: Mapped[str] = mapped_column(String(20))
    rating_grade: Mapped[str] = mapped_column(String(8))
    currency: Mapped[str] = mapped_column(String(3))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    amount_reporting: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    collateral_credit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))
    eligible_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    risk_weight: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    rwa: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    rule_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[RwaCalculationRun] = relationship(back_populates="results")
