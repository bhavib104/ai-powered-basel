"""Reference / configuration data seeded into the database.

All values here are **educational simplifications** of the Basel Standardised
Approach.  They are deliberately small and explicit.  See
``docs/risk_methodology.md`` for the full set of assumptions and exclusions.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.core import constants as C

# ---------------------------------------------------------------------------
# Risk-weight rules (version 2024.1, effective 2024-01-01)
# ---------------------------------------------------------------------------
RULE_VERSION = "2024.1"
RULE_EFFECTIVE_FROM = date(2024, 1, 1)

# weight as a decimal fraction (0.20 == 20%)
_SOVEREIGN = {
    "AAA": "0.00", "AA": "0.00", "A": "0.20", "BBB": "0.50",
    "BB": "1.00", "B": "1.00", "CCC": "1.50", "UNRATED": "1.00",
}
_BANK = {
    "AAA": "0.20", "AA": "0.20", "A": "0.30", "BBB": "0.50",
    "BB": "1.00", "B": "1.00", "CCC": "1.50", "UNRATED": "1.00",
}
_CORPORATE = {
    "AAA": "0.20", "AA": "0.20", "A": "0.20", "BBB": "0.50",
    "BB": "1.00", "B": "1.50", "CCC": "1.50", "UNRATED": "1.00",
}
# Retail and real-estate have a flat weight under this simplification.
_RETAIL = {g: "0.75" for g in C.RATING_GRADES}
_REAL_ESTATE = {g: "0.35" for g in C.RATING_GRADES}

RISK_WEIGHT_MATRIX: dict[str, dict[str, str]] = {
    C.EXPOSURE_SOVEREIGN: _SOVEREIGN,
    C.EXPOSURE_BANK: _BANK,
    C.EXPOSURE_CORPORATE: _CORPORATE,
    C.EXPOSURE_RETAIL: _RETAIL,
    C.EXPOSURE_REAL_ESTATE: _REAL_ESTATE,
}

RULE_SOURCE = "Educational simplification of the Basel Standardised Approach"


def risk_weight_rules() -> list[dict[str, object]]:
    """Expand the matrix into individual, effective-dated rule rows."""
    rows: list[dict[str, object]] = []
    for exposure_class, grades in RISK_WEIGHT_MATRIX.items():
        for grade, weight in grades.items():
            rows.append(
                {
                    "rule_version": RULE_VERSION,
                    "exposure_class": exposure_class,
                    "rating_grade": grade,
                    "risk_weight": Decimal(weight),
                    "effective_from": RULE_EFFECTIVE_FROM,
                    "effective_to": None,
                    "jurisdiction": "GLOBAL",
                    "source_reference": RULE_SOURCE,
                    "notes": f"Simplified SA weight for {exposure_class} / {grade}.",
                }
            )
    return rows


# ---------------------------------------------------------------------------
# FX rates -> reporting currency (USD), effective 2024-01-01
# ---------------------------------------------------------------------------
FX_EFFECTIVE_DATE = date(2024, 1, 1)

# 1 unit of `base` is worth `rate` USD.
FX_RATES: dict[str, str] = {
    "USD": "1.0",
    "EUR": "1.08",
    "GBP": "1.27",
    "CHF": "1.12",
    "JPY": "0.0067",
    "INR": "0.012",
}


def fx_rate_rows() -> list[dict[str, object]]:
    return [
        {
            "base_currency": base,
            "quote_currency": C.REPORTING_CURRENCY,
            "rate": Decimal(rate),
            "effective_date": FX_EFFECTIVE_DATE,
        }
        for base, rate in FX_RATES.items()
    ]


# ---------------------------------------------------------------------------
# Data-quality rule registry
# ---------------------------------------------------------------------------
DQ_RULES: list[dict[str, object]] = [
    {
        "rule_code": "DQ-001",
        "description": "Missing mandatory field on a source record.",
        "severity": C.SEVERITY_HIGH,
        "target_entity": "source_exposures",
        "target_field": "counterparty_ref,currency,amount",
    },
    {
        "rule_code": "DQ-002",
        "description": "Duplicate business key within a source snapshot.",
        "severity": C.SEVERITY_HIGH,
        "target_entity": "source_exposures",
        "target_field": "business_key",
    },
    {
        "rule_code": "DQ-003",
        "description": "Invalid monetary value (zero or negative amount).",
        "severity": C.SEVERITY_HIGH,
        "target_entity": "exposures",
        "target_field": "drawn_amount",
    },
    {
        "rule_code": "DQ-004",
        "description": "Unsupported or unknown currency.",
        "severity": C.SEVERITY_MEDIUM,
        "target_entity": "exposures",
        "target_field": "currency",
    },
    {
        "rule_code": "DQ-005",
        "description": "Broken relationship (unknown counterparty reference).",
        "severity": C.SEVERITY_CRITICAL,
        "target_entity": "source_exposures",
        "target_field": "counterparty_ref",
    },
    {
        "rule_code": "DQ-006",
        "description": "Invalid rating grade.",
        "severity": C.SEVERITY_MEDIUM,
        "target_entity": "exposures",
        "target_field": "rating_grade",
    },
    {
        "rule_code": "DQ-007",
        "description": "Invalid exposure classification.",
        "severity": C.SEVERITY_HIGH,
        "target_entity": "exposures",
        "target_field": "exposure_class",
    },
    {
        "rule_code": "DQ-008",
        "description": "Invalid date relationship (maturity on or before issue).",
        "severity": C.SEVERITY_MEDIUM,
        "target_entity": "exposures",
        "target_field": "maturity_date",
    },
    {
        "rule_code": "DQ-009",
        "description": "Missing or invalid collateral reference.",
        "severity": C.SEVERITY_MEDIUM,
        "target_entity": "source_exposures",
        "target_field": "collateral_ref",
    },
]
