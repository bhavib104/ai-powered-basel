# Risk Methodology

> **Status:** Placeholder — completed in **Phase 3** with the risk engine.

This document will state exactly what the educational RWA engine does and does
**not** do. Planned contents:

- The supported exposure classes and the precise simplified formula
  `RWA = eligible exposure amount × applicable risk weight`.
- Rule resolution: versioned, effective-dated risk-weight lookup, and the
  behaviour when no valid rule can be resolved (explicit failure — never a
  silent default).
- Collateral treatment: which adjustments are supported and which are excluded.
- Currency handling: single reporting currency with a seeded FX table (a
  documented simplification — see ADR-009).
- Assumptions, exclusions and simplifications relative to the real Basel
  framework.
- A prominent statement that this is **not** a compliant capital calculation.

**Important:** This implementation is educational and simplified. It must not be
presented as complete Basel or RBI compliance.
