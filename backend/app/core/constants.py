"""Domain constants shared across the backend.

These define the *supported* universe for this educational implementation.
Anything outside these lists is treated as unsupported and must fail loudly
rather than being silently defaulted.
"""

from __future__ import annotations

# --- Exposure classes (simplified Basel Standardised-Approach subset) -------
EXPOSURE_SOVEREIGN = "SOVEREIGN"
EXPOSURE_BANK = "BANK"
EXPOSURE_CORPORATE = "CORPORATE"
EXPOSURE_RETAIL = "RETAIL"
EXPOSURE_REAL_ESTATE = "REAL_ESTATE"

EXPOSURE_CLASSES: tuple[str, ...] = (
    EXPOSURE_SOVEREIGN,
    EXPOSURE_BANK,
    EXPOSURE_CORPORATE,
    EXPOSURE_RETAIL,
    EXPOSURE_REAL_ESTATE,
)

# --- Rating grades ----------------------------------------------------------
RATING_GRADES: tuple[str, ...] = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC", "UNRATED")

# --- Currencies -------------------------------------------------------------
REPORTING_CURRENCY = "USD"
SUPPORTED_CURRENCIES: tuple[str, ...] = ("USD", "EUR", "GBP", "INR", "JPY", "CHF")

# --- Collateral -------------------------------------------------------------
COLLATERAL_CASH = "CASH"
COLLATERAL_GOVT_BOND = "GOVERNMENT_BOND"
COLLATERAL_CORP_BOND = "CORPORATE_BOND"
COLLATERAL_REAL_ESTATE = "REAL_ESTATE"

COLLATERAL_TYPES: tuple[str, ...] = (
    COLLATERAL_CASH,
    COLLATERAL_GOVT_BOND,
    COLLATERAL_CORP_BOND,
    COLLATERAL_REAL_ESTATE,
)

# Simple-approach haircuts for eligible collateral.  Ineligible collateral
# types simply do not reduce the exposure (they are ignored, not guessed).
COLLATERAL_HAIRCUTS: dict[str, float] = {
    COLLATERAL_CASH: 0.0,
    COLLATERAL_GOVT_BOND: 0.05,
}
ELIGIBLE_COLLATERAL_TYPES: tuple[str, ...] = tuple(COLLATERAL_HAIRCUTS.keys())

# --- Severities -------------------------------------------------------------
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITIES: tuple[str, ...] = (
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)

# --- Counterparties ---------------------------------------------------------
COUNTERPARTY_TYPES: tuple[str, ...] = ("SOVEREIGN", "BANK", "CORPORATE", "RETAIL")

# --- Reconciliation statuses ------------------------------------------------
RECON_MATCHED = "MATCHED"
RECON_MISMATCHED = "MISMATCHED"
RECON_SOURCE_ONLY_A = "SOURCE_ONLY_A"
RECON_SOURCE_ONLY_B = "SOURCE_ONLY_B"
RECON_DUPLICATE = "DUPLICATE"

# --- Risk engine outcomes ---------------------------------------------------
RISK_OK = "OK"
RISK_UNSUPPORTED_CLASS = "UNSUPPORTED_EXPOSURE_CLASS"
RISK_UNSUPPORTED_RATING = "UNSUPPORTED_RATING"
RISK_NO_RULE = "NO_APPLICABLE_RULE"
RISK_INVALID_INPUT = "INVALID_INPUT"
