"""Reproducible synthetic banking data generator.

Everything is fictional.  Given the same :class:`SeedConfig` the generator
produces byte-for-byte comparable business data (identifiers are sequential and
all randomness flows from a single seeded :class:`random.Random`).

The generator deliberately seeds anomalies.  It returns a *manifest* describing
exactly which records were seeded with which problem so the data-quality and
reconciliation engines can be verified against ground truth.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from faker import Faker
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core import constants as C
from app.db.models import (
    AiRequest,
    AiToolExecution,
    AuditEvent,
    Collateral,
    Counterparty,
    CreditRating,
    Customer,
    DataQualityFinding,
    DataQualityRule,
    DataQualityRun,
    DocumentChunk,
    Exposure,
    ExposureCollateral,
    FxRate,
    Portfolio,
    ReconciliationResult,
    ReconciliationRun,
    RegulatoryDocument,
    RiskWeightRule,
    RwaCalculationResult,
    RwaCalculationRun,
    SourceExposure,
    SourceSnapshot,
)
from app.seed import reference_data as ref

SNAPSHOT_A = "SRC-A"
SNAPSHOT_B = "SRC-B"


@dataclass
class SeedConfig:
    seed: int = 42
    n_customers: int = 400
    n_counterparties: int = 1000
    n_portfolios: int = 8
    n_exposures: int = 5000
    n_collateral: int = 800

    # Data-quality anomalies (master layer)
    n_invalid_amount: int = 20
    n_unsupported_currency: int = 15
    n_invalid_rating: int = 18
    n_invalid_class: int = 12
    n_invalid_dates: int = 15

    # Data-quality anomalies (source layer)
    n_missing_counterparty: int = 10
    n_missing_amount: int = 8
    n_missing_currency: int = 7
    n_broken_counterparty_ref: int = 12
    n_invalid_collateral_ref: int = 10
    n_source_duplicates: int = 15

    # Reconciliation discrepancies (A vs B)
    n_amount_mismatch: int = 40
    n_missing_in_b: int = 30
    n_extra_in_b: int = 20

    clear_existing: bool = True


@dataclass
class SeedResult:
    counts: dict[str, int]
    manifest: dict[str, object] = field(default_factory=dict)


_UNSUPPORTED_CURRENCY = "XXX"
_INVALID_RATING = "DEFAULT"
_INVALID_CLASS = "EQUITY"
_UNKNOWN_COUNTERPARTY = "CP-99999"
_UNKNOWN_COLLATERAL = "COL-99999"

_COUNTRY_CODES = ["US", "GB", "DE", "FR", "IN", "JP", "CH", "SG", "AE", "CA"]
_SECTORS = [
    "Manufacturing", "Financials", "Energy", "Technology", "Healthcare",
    "Utilities", "Real Estate", "Consumer", "Government", "Telecom",
]
_PRODUCTS = ["TERM_LOAN", "REVOLVING_CREDIT", "MORTGAGE", "OVERDRAFT", "BOND_HOLDING"]
_GRADE_WEIGHTS = {
    "AAA": 0.04, "AA": 0.09, "A": 0.18, "BBB": 0.24,
    "BB": 0.18, "B": 0.12, "CCC": 0.05, "UNRATED": 0.10,
}

_MODELS = [
    AiToolExecution, AiRequest, AuditEvent, DocumentChunk, RegulatoryDocument,
    RwaCalculationResult, RwaCalculationRun, ReconciliationResult, ReconciliationRun,
    DataQualityFinding, DataQualityRun, DataQualityRule, SourceExposure, SourceSnapshot,
    ExposureCollateral, Collateral, Exposure, CreditRating, Counterparty, Customer,
    Portfolio, RiskWeightRule, FxRate,
]


def _clear(session: Session) -> None:
    for model in _MODELS:
        session.execute(delete(model))
    session.flush()


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _pick_grade(rng: random.Random) -> str:
    grades = list(_GRADE_WEIGHTS)
    weights = list(_GRADE_WEIGHTS.values())
    return rng.choices(grades, weights=weights, k=1)[0]


def _grade_to_code(grade: str) -> str:
    return {"UNRATED": "NR"}.get(grade, grade)


def seed_database(session: Session, config: SeedConfig | None = None) -> SeedResult:
    """Populate the database with synthetic data and return a manifest."""
    cfg = config or SeedConfig()
    rng = random.Random(cfg.seed)
    fake = Faker()
    Faker.seed(cfg.seed)
    fake.seed_instance(cfg.seed)

    if cfg.clear_existing:
        _clear(session)

    counts: dict[str, int] = {}
    dq_manifest: list[dict[str, object]] = []

    # -- Reference data -----------------------------------------------------
    session.add_all(RiskWeightRule(**row) for row in ref.risk_weight_rules())
    session.add_all(FxRate(**row) for row in ref.fx_rate_rows())
    session.add_all(DataQualityRule(rule_version="1.0", enabled=True, **row) for row in ref.DQ_RULES)
    session.flush()
    counts["risk_weight_rules"] = len(ref.risk_weight_rules())
    counts["fx_rates"] = len(ref.FX_RATES)
    counts["data_quality_rules"] = len(ref.DQ_RULES)

    # -- Portfolios ---------------------------------------------------------
    portfolios: list[Portfolio] = []
    for i in range(cfg.n_portfolios):
        portfolios.append(
            Portfolio(
                code=f"PF-{i + 1:03d}",
                name=fake.catch_phrase()[:110],
                description=f"{fake.bs()[:150]}",
                base_currency=C.REPORTING_CURRENCY,
            )
        )
    session.add_all(portfolios)
    session.flush()
    counts["portfolios"] = len(portfolios)

    # -- Customers ----------------------------------------------------------
    customers: list[Customer] = []
    for i in range(cfg.n_customers):
        customers.append(
            Customer(
                customer_ref=f"CUST-{i + 1:05d}",
                full_name=fake.name(),
                segment=rng.choice(["RETAIL", "SME", "MID_CORPORATE", "LARGE_CORPORATE"]),
                country=rng.choice(_COUNTRY_CODES),
            )
        )
    session.add_all(customers)
    session.flush()
    counts["customers"] = len(customers)

    # -- Counterparties (+ rating history) ----------------------------------
    counterparties: list[Counterparty] = []
    ratings: list[CreditRating] = []
    today = date(2026, 1, 1)
    for i in range(cfg.n_counterparties):
        ctype = rng.choices(
            ["SOVEREIGN", "BANK", "CORPORATE", "RETAIL"], weights=[3, 15, 62, 20], k=1
        )[0]
        grade = _pick_grade(rng)
        cp = Counterparty(
            external_ref=f"CP-{i + 1:05d}",
            legal_name=fake.company()[:190],
            counterparty_type=ctype,
            country=rng.choice(_COUNTRY_CODES),
            sector="Government" if ctype == "SOVEREIGN" else rng.choice(_SECTORS),
            is_financial=ctype == "BANK",
            external_rating=_grade_to_code(grade),
            rating_grade=grade,
            customer_id=customers[rng.randrange(len(customers))].id if ctype != "SOVEREIGN" else None,
        )
        counterparties.append(cp)
    session.add_all(counterparties)
    session.flush()
    counts["counterparties"] = len(counterparties)

    for cp in counterparties:
        for years_ago in (0, 1, 2):
            ratings.append(
                CreditRating(
                    counterparty_id=cp.id,
                    agency=rng.choice(["Moody's", "S&P", "Fitch", "Internal"]),
                    rating_code=_grade_to_code(cp.rating_grade),
                    grade=cp.rating_grade,
                    effective_date=date(today.year - years_ago, 1, 1),
                )
            )
    session.add_all(ratings)
    session.flush()
    counts["credit_ratings"] = len(ratings)

    # -- Collateral ---------------------------------------------------------
    collateral: list[Collateral] = []
    for i in range(cfg.n_collateral):
        ctype = rng.choices(
            [C.COLLATERAL_CASH, C.COLLATERAL_GOVT_BOND, C.COLLATERAL_CORP_BOND,
             C.COLLATERAL_REAL_ESTATE],
            weights=[15, 30, 30, 25], k=1,
        )[0]
        eligible = ctype in C.ELIGIBLE_COLLATERAL_TYPES
        haircut = C.COLLATERAL_HAIRCUTS.get(ctype, 0.2)
        collateral.append(
            Collateral(
                collateral_ref=f"COL-{i + 1:05d}",
                collateral_type=ctype,
                currency=rng.choice(["USD", "EUR", "GBP"]),
                market_value=_money(rng.uniform(50_000, 5_000_000)),
                haircut_pct=Decimal(str(haircut)),
                valuation_date=date(today.year, rng.randint(1, 12), 1),
                is_eligible=eligible,
            )
        )
    session.add_all(collateral)
    session.flush()
    counts["collateral"] = len(collateral)

    # -- Exposures ----------------------------------------------------------
    # Reserve indices for anomalies so detection expectations are exact.
    all_idx = list(range(cfg.n_exposures))
    rng.shuffle(all_idx)
    pool = iter(all_idx)

    invalid_amount_idx = {next(pool) for _ in range(cfg.n_invalid_amount)}
    unsupported_ccy_idx = {next(pool) for _ in range(cfg.n_unsupported_currency)}
    invalid_rating_idx = {next(pool) for _ in range(cfg.n_invalid_rating)}
    invalid_class_idx = {next(pool) for _ in range(cfg.n_invalid_class)}
    invalid_dates_idx = {next(pool) for _ in range(cfg.n_invalid_dates)}

    exposures: list[Exposure] = []
    links: list[ExposureCollateral] = []
    used_collateral: set[int] = set()

    for i in range(cfg.n_exposures):
        cp = counterparties[rng.randrange(len(counterparties))]
        exposure_class = {
            "SOVEREIGN": C.EXPOSURE_SOVEREIGN,
            "BANK": C.EXPOSURE_BANK,
            "CORPORATE": rng.choice([C.EXPOSURE_CORPORATE, C.EXPOSURE_REAL_ESTATE]),
            "RETAIL": C.EXPOSURE_RETAIL,
        }[cp.counterparty_type]
        currency = rng.choices(
            list(C.SUPPORTED_CURRENCIES), weights=[45, 20, 12, 8, 8, 7], k=1
        )[0]
        original = _money(rng.lognormvariate(13.0, 1.4))
        utilization = rng.uniform(0.3, 1.0)
        drawn = _money(float(original) * utilization)
        undrawn = _money(float(original) - float(drawn))
        issue = today - timedelta(days=rng.randint(30, 3650))
        maturity = issue + timedelta(days=rng.randint(365, 3650))

        ref_id = f"EXP-{i + 1:07d}"
        grade = cp.rating_grade
        cls = exposure_class

        if i in invalid_amount_idx:
            drawn = _money(-abs(rng.uniform(1_000, 100_000)))
            dq_manifest.append({"rule_code": "DQ-003", "entity": "exposures",
                                "record_key": ref_id, "field": "drawn_amount"})
        if i in unsupported_ccy_idx:
            currency = _UNSUPPORTED_CURRENCY
            dq_manifest.append({"rule_code": "DQ-004", "entity": "exposures",
                                "record_key": ref_id, "field": "currency"})
        if i in invalid_rating_idx:
            grade = _INVALID_RATING
            dq_manifest.append({"rule_code": "DQ-006", "entity": "exposures",
                                "record_key": ref_id, "field": "rating_grade"})
        if i in invalid_class_idx:
            cls = _INVALID_CLASS
            dq_manifest.append({"rule_code": "DQ-007", "entity": "exposures",
                                "record_key": ref_id, "field": "exposure_class"})
        if i in invalid_dates_idx:
            maturity = issue
            dq_manifest.append({"rule_code": "DQ-008", "entity": "exposures",
                                "record_key": ref_id, "field": "maturity_date"})

        exp = Exposure(
            exposure_ref=ref_id,
            counterparty_id=cp.id,
            portfolio_id=portfolios[rng.randrange(len(portfolios))].id,
            exposure_class=cls,
            product_type=rng.choice(_PRODUCTS),
            currency=currency,
            original_amount=original,
            drawn_amount=drawn,
            undrawn_amount=undrawn,
            issue_date=issue,
            maturity_date=maturity,
            is_defaulted=rng.random() < 0.02,
            rating_grade=grade,
            source_system=rng.choice(["CORE", "LEGACY"]),
        )
        exposures.append(exp)

    session.add_all(exposures)
    session.flush()
    counts["exposures"] = len(exposures)

    # -- Exposure-collateral links -----------------------------------------
    for exp in exposures:
        if rng.random() < 0.35 and collateral:
            col = collateral[rng.randrange(len(collateral))]
            if col.id in used_collateral:
                continue
            used_collateral.add(col.id)
            allocated = _money(min(float(col.market_value), float(exp.drawn_amount) * rng.uniform(0.1, 0.8)))
            if allocated <= 0:
                allocated = _money(1000)
            links.append(ExposureCollateral(
                exposure_id=exp.id, collateral_id=col.id, allocated_amount=allocated
            ))
    session.add_all(links)
    session.flush()
    counts["exposure_collateral"] = len(links)

    # -- Source snapshots ---------------------------------------------------
    snap_a = SourceSnapshot(
        snapshot_code=SNAPSHOT_A,
        source_system="CORE",
        as_of_date=date(2026, 1, 31),
        description="Primary source-system snapshot.",
    )
    snap_b = SourceSnapshot(
        snapshot_code=SNAPSHOT_B,
        source_system="LEGACY",
        as_of_date=date(2026, 1, 31),
        description="Secondary source-system snapshot (seeded discrepancies).",
    )
    session.add_all([snap_a, snap_b])
    session.flush()
    counts["source_snapshots"] = 2

    # Build base records for snapshot A from the (mostly valid) exposures.
    base_records = [
        {
            "business_key": e.exposure_ref,
            "counterparty_ref": f"CP-{e.counterparty_id:05d}",
            "exposure_class": e.exposure_class,
            "currency": e.currency,
            "amount": e.drawn_amount,
            "rating_grade": e.rating_grade,
            "maturity_date": e.maturity_date,
        }
        for e in exposures
    ]

    a_rows: list[SourceExposure] = []

    def _add_source(snapshot_id: int, rec: dict, rows: list[SourceExposure]) -> None:
        rows.append(SourceExposure(snapshot_id=snapshot_id, **rec))

    # Source-layer DQ anomalies (on snapshot A) -----------------------------
    src_idx = list(range(len(base_records)))
    rng.shuffle(src_idx)
    src_pool = iter(src_idx)

    missing_cp = [next(src_pool) for _ in range(cfg.n_missing_counterparty)]
    missing_amt = [next(src_pool) for _ in range(cfg.n_missing_amount)]
    missing_ccy = [next(src_pool) for _ in range(cfg.n_missing_currency)]
    broken_cp = [next(src_pool) for _ in range(cfg.n_broken_counterparty_ref)]
    bad_col = [next(src_pool) for _ in range(cfg.n_invalid_collateral_ref)]

    for idx, base in enumerate(base_records):
        rec = dict(base)
        rec["raw_payload"] = json.dumps({k: str(v) for k, v in base.items()})
        if idx in missing_cp:
            rec["counterparty_ref"] = None
            dq_manifest.append({"rule_code": "DQ-001", "entity": "source_exposures",
                                "record_key": rec["business_key"], "field": "counterparty_ref"})
        if idx in missing_amt:
            rec["amount"] = None
            dq_manifest.append({"rule_code": "DQ-001", "entity": "source_exposures",
                                "record_key": rec["business_key"], "field": "amount"})
        if idx in missing_ccy:
            rec["currency"] = None
            dq_manifest.append({"rule_code": "DQ-001", "entity": "source_exposures",
                                "record_key": rec["business_key"], "field": "currency"})
        if idx in broken_cp:
            rec["counterparty_ref"] = _UNKNOWN_COUNTERPARTY
            dq_manifest.append({"rule_code": "DQ-005", "entity": "source_exposures",
                                "record_key": rec["business_key"], "field": "counterparty_ref"})
        if idx in bad_col:
            rec["collateral_ref"] = _UNKNOWN_COLLATERAL
            dq_manifest.append({"rule_code": "DQ-009", "entity": "source_exposures",
                                "record_key": rec["business_key"], "field": "collateral_ref"})
        _add_source(snap_a.id, rec, a_rows)

    # Snapshot B = A minus removed keys, plus extra keys, plus amount changes,
    # plus duplicates.
    clean_idx = [i for i in range(len(base_records))
                 if not ({i} & (set(missing_cp) | set(missing_amt) | set(missing_ccy)
                                | set(broken_cp) | set(bad_col)))]
    rng.shuffle(clean_idx)
    b_pool = iter(clean_idx)

    missing_in_b = {next(b_pool) for _ in range(cfg.n_missing_in_b)}
    amount_mismatch = {next(b_pool) for _ in range(cfg.n_amount_mismatch)}
    duplicate_keys = {next(b_pool) for _ in range(cfg.n_source_duplicates)}

    b_rows: list[SourceExposure] = []
    for idx in clean_idx:
        if idx in missing_in_b:
            continue  # present only in A -> SOURCE_ONLY_A
        rec = dict(base_records[idx])
        rec["raw_payload"] = json.dumps({k: str(v) for k, v in base_records[idx].items()})
        if idx in amount_mismatch:
            new_amount = _money(float(rec["amount"]) * 1.05 + 10)
            rec["amount"] = new_amount
        _add_source(snap_b.id, rec, b_rows)
        if idx in duplicate_keys:
            dup = dict(rec)
            _add_source(snap_b.id, dup, b_rows)

    # Extra records present only in B -> SOURCE_ONLY_B
    for k in range(cfg.n_extra_in_b):
        key = f"EXP-9{k + 1:06d}"
        rec = {
            "business_key": key,
            "counterparty_ref": f"CP-{rng.randint(1, cfg.n_counterparties):05d}",
            "exposure_class": rng.choice(list(C.EXPOSURE_CLASSES)),
            "currency": rng.choice(list(C.SUPPORTED_CURRENCIES)),
            "amount": _money(rng.uniform(10_000, 2_000_000)),
            "rating_grade": rng.choice(list(C.RATING_GRADES)),
            "maturity_date": today + timedelta(days=rng.randint(200, 3000)),
            "raw_payload": None,
        }
        _add_source(snap_b.id, rec, b_rows)

    session.add_all(a_rows)
    session.add_all(b_rows)
    session.flush()
    counts["source_exposures"] = len(a_rows) + len(b_rows)

    for key in sorted(duplicate_keys):
        dq_manifest.append({"rule_code": "DQ-002", "entity": "source_exposures",
                            "record_key": base_records[key]["business_key"], "field": "business_key"})

    manifest: dict[str, object] = {
        "seed": cfg.seed,
        "generated_at": date.today().isoformat(),
        "counts": counts,
        "data_quality_anomalies": dq_manifest,
        "anomaly_totals": _tally(dq_manifest),
        "reconciliation": {
            "source_a": SNAPSHOT_A,
            "source_b": SNAPSHOT_B,
            "business_key": "business_key",
            "expected": {
                "amount_mismatch": cfg.n_amount_mismatch,
                "missing_in_b": cfg.n_missing_in_b,
                "extra_in_b": cfg.n_extra_in_b,
                "duplicates_in_b": cfg.n_source_duplicates,
            },
        },
    }
    return SeedResult(counts=counts, manifest=manifest)


def _tally(rows: list[dict[str, object]]) -> dict[str, int]:
    tally: dict[str, int] = {}
    for row in rows:
        code = str(row["rule_code"])
        tally[code] = tally.get(code, 0) + 1
    return dict(sorted(tally.items()))
