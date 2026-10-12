"""Risk-engine tests: correctness, boundaries, and explicit unsupported cases."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core import constants as C
from app.db.models import (
    Collateral,
    Counterparty,
    Exposure,
    ExposureCollateral,
    FxRate,
    Portfolio,
    RiskWeightRule,
)
from app.services import risk_engine


def _seed_engine_data(db) -> None:
    db.add_all(
        [
            FxRate(base_currency="USD", quote_currency="USD", rate=Decimal("1"), effective_date=date(2024, 1, 1)),
            FxRate(base_currency="EUR", quote_currency="USD", rate=Decimal("1.08"), effective_date=date(2024, 1, 1)),
            RiskWeightRule(rule_version="2024.1", exposure_class="CORPORATE", rating_grade="BBB",
                           risk_weight=Decimal("0.5"), effective_from=date(2024, 1, 1), effective_to=None),
            RiskWeightRule(rule_version="2024.1", exposure_class="CORPORATE", rating_grade="AA",
                           risk_weight=Decimal("0.2"), effective_from=date(2024, 1, 1), effective_to=None),
            RiskWeightRule(rule_version="2024.1", exposure_class="RETAIL", rating_grade="UNRATED",
                           risk_weight=Decimal("0.75"), effective_from=date(2024, 1, 1), effective_to=None),
        ]
    )
    db.flush()


def _make_entities(db):
    cp = Counterparty(external_ref="CP-X", legal_name="Acme Corp", counterparty_type="CORPORATE",
                      country="US", sector="Tech", is_financial=False, rating_grade="BBB")
    portfolio = Portfolio(code="PF-TEST", name="Test")
    db.add_all([cp, portfolio])
    db.flush()
    return cp, portfolio


def _make_exposure(db, *, cp=None, portfolio=None, exposure_class="CORPORATE", rating="BBB",
                   ccy="USD", amount=Decimal("1000000"), drawn=None):
    if cp is None or portfolio is None:
        cp, portfolio = _make_entities(db)
    exp = Exposure(
        exposure_ref=f"EXP-{exposure_class}-{rating}",
        counterparty_id=cp.id,
        portfolio_id=portfolio.id,
        exposure_class=exposure_class,
        product_type="TERM_LOAN",
        currency=ccy,
        original_amount=amount,
        drawn_amount=amount if drawn is None else drawn,
        undrawn_amount=Decimal("0"),
        issue_date=date(2024, 1, 1),
        maturity_date=date(2026, 1, 1),
        is_defaulted=False,
        rating_grade=rating,
    )
    db.add(exp)
    db.flush()
    return exp


def _engine(db) -> risk_engine.RiskEngine:
    return risk_engine.RiskEngine(db, rule_version="2024.1", as_of_date=date(2024, 6, 30))


def test_corporate_bbb_no_collateral(db) -> None:
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="CORPORATE", rating="BBB", amount=Decimal("1000000"))
    out = _engine(db).calculate(exp)
    assert out.status == C.RISK_OK
    assert out.risk_weight == Decimal("0.5")
    assert out.rwa == Decimal("500000.00")


def test_collateral_reduces_exposure(db) -> None:
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="CORPORATE", rating="BBB", amount=Decimal("1000000"))
    collateral = Collateral(collateral_ref="COL-CASH-1", collateral_type=C.COLLATERAL_CASH,
                            currency="USD", market_value=Decimal("200000"), haircut_pct=Decimal("0"),
                            valuation_date=date(2024, 6, 1), is_eligible=True)
    db.add(collateral)
    db.flush()
    db.add(ExposureCollateral(exposure_id=exp.id, collateral_id=collateral.id, allocated_amount=Decimal("200000")))
    db.flush()

    out = _engine(db).calculate(exp)
    assert out.status == C.RISK_OK
    assert out.eligible_amount == Decimal("800000.00")
    assert out.rwa == Decimal("400000.00")


def test_euro_conversion(db) -> None:
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="CORPORATE", rating="BBB", ccy="EUR", amount=Decimal("1000000"))
    out = _engine(db).calculate(exp)
    assert out.amount_reporting == Decimal("1080000.00")
    assert out.rwa == Decimal("540000.00")


def test_unsupported_class_fails_explicitly(db) -> None:
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="EQUITY", rating="BBB")
    out = _engine(db).calculate(exp)
    assert out.status == C.RISK_UNSUPPORTED_CLASS
    assert out.rwa is None


def test_no_rule_for_invalid_rating(db) -> None:
    """The engine must never silently apply a default risk weight."""
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="CORPORATE", rating="DEFAULT")
    out = _engine(db).calculate(exp)
    assert out.status == C.RISK_NO_RULE
    assert out.rwa is None


def test_unknown_currency_invalid_input(db) -> None:
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="CORPORATE", ccy="XXX")
    out = _engine(db).calculate(exp)
    assert out.status == C.RISK_INVALID_INPUT


def test_non_positive_amount_invalid_input(db) -> None:
    _seed_engine_data(db)
    exp = _make_exposure(db, exposure_class="CORPORATE", drawn=Decimal("-5000"))
    out = _engine(db).calculate(exp)
    assert out.status == C.RISK_INVALID_INPUT


def test_run_calculation_persists_totals(db) -> None:
    _seed_engine_data(db)
    cp, portfolio = _make_entities(db)
    _make_exposure(db, cp=cp, portfolio=portfolio, exposure_class="CORPORATE", rating="BBB",
                   amount=Decimal("1000000"))
    _make_exposure(db, cp=cp, portfolio=portfolio, exposure_class="CORPORATE", rating="AA",
                   amount=Decimal("2000000"))
    _make_exposure(db, cp=cp, portfolio=portfolio, exposure_class="EQUITY")


    run = risk_engine.run_calculation(db, rule_version="2024.1", as_of_date=date(2024, 6, 30))
    assert run.status == "COMPLETED"
    assert run.exposure_count == 3
    assert run.calculated_count == 2
    assert run.unsupported_count == 1
    assert run.total_rwa == Decimal("900000.00")  # 500k + 400k

    # Exposure-level results were persisted and are re-readable.
    from sqlalchemy import select

    from app.db.models import RwaCalculationResult

    persisted = db.execute(select(RwaCalculationResult)).scalars().all()
    assert len(persisted) == 3
    assert {r.status for r in persisted} == {C.RISK_OK, C.RISK_UNSUPPORTED_CLASS}