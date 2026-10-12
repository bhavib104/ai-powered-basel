# Risk Methodology

> **Status:** Final — matches `app/services/risk_engine.py` (verified by tests).

This document states exactly what the educational RWA engine computes and what it
explicitly does **not** compute. It is a simplified subset of the Basel
Standardised Approach, not a compliant capital calculation.

---

## 1. Scope

- **Exposure classes:** Sovereign, Bank, Corporate, Retail, Real Estate.
- **Reporting currency:** USD (single reporting currency; see ADR-009).
- **Data:** 100% synthetic seeding data for demonstration.
- **Outcome per exposure:** status, reporting amount, collateral credit,
  eligible amount, applicable risk weight, RWA, and a **step-by-step
  explanation** persisted with every result.

## 2. The formula

For every exposure with a resolvable rule:

```
amount_reporting  = fx.to_reporting(drawn_amount, currency, as_of_date)
collateral_credit = Σ over eligible linked collateral of
                    max(0, allocated_reporting × (1 - haircut))
eligible_amount   = max(0, amount_reporting - collateral_credit)
RWA               = eligible_amount × applicable_risk_weight
```

Monetary values are `Decimal`, quantized to 2 decimals with
`ROUND_HALF_UP`. All arithmetic is deterministic.

## 3. Rule resolution

- Risk-weight rules live in the `risk_weight_rules` table, keyed by
  `(rule_version, exposure_class, rating_grade)` and **effective-dated**
  (`effective_from`, `effective_to`).
- A rule is applicable when `effective_from <= as_of_date <= effective_to`
  (open-ended when `effective_to` is NULL).
- If multiple revisions overlap the as-of date, the most recently
  effective one wins.
- Rating grades are the S&P-style ladder
  `AAA, AA, A, BBB, BB, B, CCC, UNRATED`.

## 4. Seeded rule set (version `2024.1`, effective 2024-01-01)

Illustrative weights, as decimal fractions (1.00 == 100 %):

| Class        | AAA | AA  | A   | BBB | BB  | B   | CCC | UNRATED |
|--------------|-----|-----|-----|-----|-----|-----|-----|---------|
| Sovereign    | 0.0 | 0.0 | 0.2 | 0.5 | 1.0 | 1.0 | 1.5 | 1.0     |
| Bank         | 0.2 | 0.2 | 0.3 | 0.5 | 1.0 | 1.0 | 1.5 | 1.0     |
| Corporate    | 0.2 | 0.2 | 0.2 | 0.5 | 1.0 | 1.5 | 1.5 | 1.0     |
| Retail       | 0.75| 0.75| 0.75| 0.75| 0.75| 0.75| 0.75| 0.75    |
| Real estate  | 0.35| 0.35| 0.35| 0.35| 0.35| 0.35| 0.35| 0.35    |

These values are **educational simplifications** of the Standardised Approach and
must not be used for compliance.

## 5. Collateral (credit risk mitigation)

- Eligible columns under the **simple approach**: cash and government bonds,
  with `net = allocated × (1 - haircut)`.
- Fixed haircuts: cash `0.0`, government bonds `0.05`.
- Corporate bonds and real estate collateral are **recorded but ignored** in this
  framework rather than guessed (ineligible types reduce nothing).
- Only eligible collateral whose value converts to the reporting currency
  contributes; conversion failures are skipped.
- Collateral credit never exceeds the exposure (eligible amount is floored at 0).

## 6. Explicit unsupported outcomes (never guessed)

The engine **never invents a risk weight**. The following statuses are produced
with a stored reason:

| Status                      | When                                                   |
|-----------------------------|--------------------------------------------------------|
| `UNSUPPORTED_EXPOSURE_CLASS`| Class outside the supported five                     |
| `INVALID_INPUT`             | Non-positive drawn amount, or missing FX conversion    |
| `NO_APPLICABLE_RULE`        | No effective-dated rule for the class/rating pair      |

Unsupported exposures contribute **zero** to total RWA and are excluded so a
gap is visible rather than silently absorbed.

## 7. Currency

Drawn/collateral amounts are converted to USD using the seeded `fx_rates`
table (single rate per currency, effective 2024-01-01, e.g. EUR 1.08,
GBP 1.27, INR 0.012). This is a documented simplification — see ADR-009.

## 8. Exclusions and simplifications

- No PD/LGD, no risk-weight floor variation by jurisdiction.
- No maturity-based adjustments, off-balance-sheet credit conversion factors,
  or guarantees.
- No loss-given-default modelling and no internal-ratings approach.
- Defaulted exposures are recorded on the exposure row, but the engine does not
  implement the full defaulted-exposure framework (treated under the rating
  ladder in this subset).
- No stress testing, no portfolio-level aggregation adjustments.

## 9. Disclaimer

**This platform is educational only and is not compliant Basel or RBI capital
calculation software.** Every explanation JSON stored by the engine allows the
figures to be replayed by hand, which is the point of the demonstration: the
numbers are deterministic, auditable and fully explained — not sampled from a
model.