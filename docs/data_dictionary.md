# Data Dictionary

> **Status:** Placeholder — populated in **Phase 2** together with the database
> schema. It will document every table, column, type, constraint, index and
> relationship, plus the meaning and units of each field.

Planned coverage:

- Core entities: customers/counterparties, portfolios, exposures, collateral,
  exposure–collateral links, credit ratings.
- Rules: risk-weight rules (versioned, effective-dated).
- Source data: source-system snapshots.
- Processing history: RWA calculation runs/results, data-quality rules/runs/
  findings, reconciliation runs/results.
- AI: regulatory documents and chunks, AI requests and tool executions.
- Audit: audit events.

Monetary values use fixed-precision decimals; foreign keys and uniqueness
constraints are defined in the schema and enforced by the database.
