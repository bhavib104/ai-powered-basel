"""Deterministic risk-weighted-asset (RWA) engine.

Simplified, educational subset of the Basel Standardised Approach.  The engine
is pure with respect to its inputs and **never** invents a risk weight: if a
rule cannot be resolved for an exposure, the result is explicitly marked
unsupported.

Formula::

    eligible_amount = max(0, drawn_reporting - eligible_collateral_reporting)
    RWA             = eligible_amount * applicable_risk_weight

See ``docs/risk_methodology.md`` for assumptions and exclusions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core import constants as C
from app.core.refs import new_ref
from app.db.models import (
    Exposure,
    ExposureCollateral,
    RiskWeightRule,
    RwaCalculationResult,
    RwaCalculationRun,
)
from app.services import audit, fx

_ZERO = Decimal("0")
_TWO = Decimal("0.01")


def _q(value: Decimal) -> Decimal:
    return Decimal(value).quantize(_TWO, rounding=ROUND_HALF_UP)


@dataclass
class CalculationOutcome:
    """The deterministic result for one exposure."""

    exposure_ref: str
    status: str
    exposure_class: str
    rating_grade: str
    currency: str
    original_amount: Decimal
    amount_reporting: Decimal | None
    collateral_credit: Decimal
    eligible_amount: Decimal
    risk_weight: Decimal | None
    rwa: Decimal | None
    rule_reference: str | None
    explanation: dict[str, object] = field(default_factory=dict)


class RiskEngine:
    """Resolves versioned rules and computes RWA for exposures."""

    def __init__(
        self,
        session: Session,
        *,
        rule_version: str,
        as_of_date: date,
        reporting_currency: str = C.REPORTING_CURRENCY,
    ) -> None:
        self.session = session
        self.rule_version = rule_version
        self.as_of_date = as_of_date
        self.reporting_currency = reporting_currency
        self._rule_cache: dict[tuple[str, str], RiskWeightRule | None] = {}

    # -- Rule resolution ----------------------------------------------------
    def resolve_rule(self, exposure_class: str, rating_grade: str) -> RiskWeightRule | None:
        key = (exposure_class, rating_grade)
        if key in self._rule_cache:
            return self._rule_cache[key]

        stmt = (
            select(RiskWeightRule)
            .where(
                RiskWeightRule.rule_version == self.rule_version,
                RiskWeightRule.exposure_class == exposure_class,
                RiskWeightRule.rating_grade == rating_grade,
            )
            .order_by(RiskWeightRule.effective_from.desc())
        )
        candidates = list(self.session.execute(stmt).scalars())
        chosen: RiskWeightRule | None = None
        for rule in candidates:
            if rule.effective_from <= self.as_of_date and (
                rule.effective_to is None or rule.effective_to >= self.as_of_date
            ):
                chosen = rule
                break
        self._rule_cache[key] = chosen
        return chosen

    # -- Collateral ---------------------------------------------------------
    def _collateral_credit(self, exposure: Exposure) -> tuple[Decimal, list[dict[str, object]]]:
        credit = _ZERO
        detail: list[dict[str, object]] = []
        for link in exposure.collateral_links:
            col = link.collateral
            if col is None or not col.is_eligible:
                continue
            if col.collateral_type not in C.ELIGIBLE_COLLATERAL_TYPES:
                continue
            allocated_reporting = fx.to_reporting(
                self.session, link.allocated_amount, col.currency, self.as_of_date
            )
            if allocated_reporting is None:
                continue
            haircut = col.haircut_pct if col.haircut_pct is not None else _ZERO
            net = (allocated_reporting * (Decimal("1") - haircut)).quantize(_TWO)
            credit += net
            detail.append(
                {
                    "collateral_ref": col.collateral_ref,
                    "type": col.collateral_type,
                    "allocated_reporting": str(allocated_reporting),
                    "haircut": str(haircut),
                    "net_credit": str(net),
                }
            )
        return credit, detail

    # -- Calculation --------------------------------------------------------
    def calculate(self, exposure: Exposure) -> CalculationOutcome:
        exposure_class = exposure.exposure_class
        rating = exposure.rating_grade
        base = {
            "exposure_ref": exposure.exposure_ref,
            "exposure_class": exposure_class,
            "rating_grade": rating,
            "currency": exposure.currency,
            "original_amount": _q(exposure.drawn_amount),
        }

        if exposure_class not in C.EXPOSURE_CLASSES:
            return self._unsupported(
                base, C.RISK_UNSUPPORTED_CLASS,
                f"Exposure class '{exposure_class}' is not supported.",
            )

        if exposure.drawn_amount is None or Decimal(exposure.drawn_amount) <= 0:
            return self._unsupported(
                base, C.RISK_INVALID_INPUT,
                "Drawn amount must be a positive monetary value.",
            )

        amount_reporting = fx.to_reporting(
            self.session, Decimal(exposure.drawn_amount), exposure.currency, self.as_of_date
        )
        if amount_reporting is None:
            return self._unsupported(
                base, C.RISK_INVALID_INPUT,
                f"No FX rate available for currency '{exposure.currency}'.",
            )

        collateral_credit, collateral_detail = self._collateral_credit(exposure)
        eligible = max(_ZERO, amount_reporting - collateral_credit)

        rule = self.resolve_rule(exposure_class, rating)
        if rule is None:
            return self._unsupported(
                base, C.RISK_NO_RULE,
                f"No risk-weight rule for class '{exposure_class}' / rating '{rating}'.",
                amount_reporting=amount_reporting,
                collateral_credit=collateral_credit,
                eligible=eligible,
            )

        rwa = _q(eligible * rule.risk_weight)
        outcome = CalculationOutcome(
            exposure_ref=exposure.exposure_ref,
            status=C.RISK_OK,
            exposure_class=exposure_class,
            rating_grade=rating,
            currency=exposure.currency,
            original_amount=_q(exposure.drawn_amount),
            amount_reporting=amount_reporting,
            collateral_credit=collateral_credit,
            eligible_amount=eligible,
            risk_weight=rule.risk_weight,
            rwa=rwa,
            rule_reference=rule.source_reference,
        )
        outcome.explanation = {
            "formula": "RWA = max(0, drawn_reporting - eligible_collateral) * risk_weight",
            "rule_version": self.rule_version,
            "as_of_date": self.as_of_date.isoformat(),
            "amount_reporting": str(amount_reporting),
            "collateral_credit": str(collateral_credit),
            "eligible_amount": str(eligible),
            "risk_weight": str(rule.risk_weight),
            "rwa": str(rwa),
            "collateral": collateral_detail,
        }
        return outcome

    def _unsupported(
        self,
        base: dict[str, object],
        status: str,
        message: str,
        *,
        amount_reporting: Decimal | None = None,
        collateral_credit: Decimal = _ZERO,
        eligible: Decimal = _ZERO,
    ) -> CalculationOutcome:
        outcome = CalculationOutcome(
            exposure_ref=str(base["exposure_ref"]),
            status=status,
            exposure_class=str(base["exposure_class"]),
            rating_grade=str(base["rating_grade"]),
            currency=str(base["currency"]),
            original_amount=base["original_amount"],  # type: ignore[arg-type]
            amount_reporting=amount_reporting,
            collateral_credit=collateral_credit,
            eligible_amount=eligible,
            risk_weight=None,
            rwa=None,
            rule_reference=None,
        )
        outcome.explanation = {
            "message": message,
            "rule_version": self.rule_version,
            "as_of_date": self.as_of_date.isoformat(),
        }
        return outcome


# ---------------------------------------------------------------------------
# Run orchestration + persistence
# ---------------------------------------------------------------------------
def run_calculation(
    session: Session,
    *,
    rule_version: str,
    as_of_date: date | None = None,
    limit: int | None = None,
    persist: bool = True,
) -> RwaCalculationRun:
    """Calculate RWA for all exposures and (by default) persist the run."""
    as_of = as_of_date or date.today()
    engine = RiskEngine(session, rule_version=rule_version, as_of_date=as_of)

    stmt = select(Exposure).options(
        selectinload(Exposure.collateral_links).selectinload(ExposureCollateral.collateral)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    exposures = list(session.execute(stmt).scalars())

    run = RwaCalculationRun(
        run_ref=new_ref("RWA"),
        rule_version=rule_version,
        as_of_date=as_of,
        reporting_currency=C.REPORTING_CURRENCY,
        status="RUNNING",
        started_at=datetime.now(UTC),
    )
    if persist:
        session.add(run)
        session.flush()

    total_eligible = _ZERO
    total_rwa = _ZERO
    calculated = 0
    unsupported = 0

    for exposure in exposures:
        outcome = engine.calculate(exposure)
        if outcome.status == C.RISK_OK:
            calculated += 1
            total_eligible += outcome.eligible_amount
            total_rwa += outcome.rwa or _ZERO
        else:
            unsupported += 1

        if persist:
            session.add(
                RwaCalculationResult(
                    run_id=run.id,
                    exposure_id=exposure.id,
                    exposure_ref=outcome.exposure_ref,
                    exposure_class=outcome.exposure_class,
                    rating_grade=outcome.rating_grade,
                    currency=outcome.currency,
                    original_amount=outcome.original_amount,
                    amount_reporting=outcome.amount_reporting or _ZERO,
                    collateral_credit=outcome.collateral_credit,
                    eligible_amount=outcome.eligible_amount,
                    risk_weight=outcome.risk_weight,
                    rwa=outcome.rwa,
                    rule_reference=outcome.rule_reference,
                    status=outcome.status,
                    explanation_json=json.dumps(outcome.explanation, default=str),
                )
            )

    run.exposure_count = len(exposures)
    run.calculated_count = calculated
    run.unsupported_count = unsupported
    run.total_eligible_amount = _q(total_eligible)
    run.total_rwa = _q(total_rwa)
    run.status = "COMPLETED"
    run.finished_at = datetime.now(UTC)
    run.summary_json = json.dumps(
        {
            "rule_version": rule_version,
            "as_of_date": as_of.isoformat(),
            "exposure_count": len(exposures),
            "calculated": calculated,
            "unsupported": unsupported,
            "total_eligible_amount": str(_q(total_eligible)),
            "total_rwa": str(_q(total_rwa)),
            "reporting_currency": C.REPORTING_CURRENCY,
        }
    )

    if persist:
        audit.record_event(
            session,
            event_type="risk",
            action="rwa_calculation",
            entity_type="rwa_calculation_run",
            entity_id=run.run_ref,
            details={"calculated": calculated, "unsupported": unsupported},
        )
        session.commit()
        session.refresh(run)

    return run
