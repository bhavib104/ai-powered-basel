# Data Dictionary

> **Status:** Final — mirrors `backend/app/db/models/` (23 tables). Column types
> below are the SQLAlchemy/SQLite forms; every monetary column is a fixed
> precision `Numeric` (i.e. decimal, never floating point). All rows carry a
> UTC `created_at` (via `TimestampMixin`).

---

## Conventions

- `Numeric(18,2)` / `Numeric(20,2)` — money, 2 decimals.
- `Numeric(6,4)` — a decimal fraction (e.g. risk weight `0.20` = 20 %).
- `String(n)` — bounded text; `Text` — unbounded.
- Foreign keys use `ondelete` policies (`RESTRICT`, `CASCADE`, `SET NULL`) and
  are enforced by SQLite `PRAGMA foreign_keys=ON` (WAL journal mode).

## 1. Master data

### `customers`

A bank customer (the commercial relationship). `customer_ref` unique.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| customer_ref | String(32) | unique, indexed |
| full_name | String(200) | |
| segment | String(40) | e.g. Retail / SME / Corporate |
| country | String(2) | ISO country code |

### `counterparties`

An entity the bank is exposed to. Denormalised current rating used by the risk
engine; full history in `credit_ratings`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| external_ref | String(32) | unique, indexed |
| legal_name | String(200) | |
| counterparty_type | String(20) | indexed: SOVEREIGN/BANK/CORPORATE/RETAIL |
| country | String(2) | indexed |
| sector | String(60) | |
| is_financial | bool | |
| external_rating | String(8) | raw agency code |
| rating_grade | String(8) | indexed; ladder AAA…CCC/UNRATED |
| customer_id | int FK → customers | nullable, SET NULL, indexed |

### `credit_ratings`

Point-in-time rating history. Unique on `(counterparty_id, agency,
effective_date)`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| counterparty_id | int FK → counterparties | CASCADE, indexed |
| agency | String(40) | |
| rating_code | String(12) | |
| grade | String(8) | indexed |
| effective_date | Date | |

### `portfolios`

Grouping of exposures (a lending book). `code` unique.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| code | String(24) | unique, indexed |
| name | String(120) | |
| description | Text | nullable |
| base_currency | String(3) | default USD |

### `exposures`

A single credit exposure. Composite index `(exposure_class, rating_grade)`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| exposure_ref | String(40) | unique, indexed |
| counterparty_id | int FK → counterparties | RESTRICT, indexed |
| portfolio_id | int FK → portfolios | RESTRICT, indexed |
| exposure_class | String(20) | indexed; 5 supported classes |
| product_type | String(40) | |
| currency | String(3) | indexed |
| original_amount | Numeric(18,2) | |
| drawn_amount | Numeric(18,2) | used by the risk engine |
| undrawn_amount | Numeric(18,2) | default 0 |
| issue_date | Date | |
| maturity_date | Date | indexed |
| is_defaulted | bool | |
| rating_grade | String(8) | indexed; effective rating for the exposure |
| source_system | String(40) | nullable, e.g. `SRC-A`/`SRC-B` |

### `collateral`

Collateral items. Only eligible types (cash, government bonds) reduce exposure
under the simplified simple approach.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| collateral_ref | String(32) | unique, indexed |
| collateral_type | String(24) | indexed (CASH/GOVERNMENT_BOND/…) |
| currency | String(3) | |
| market_value | Numeric(18,2) | |
| haircut_pct | Numeric(6,4) | default 0; 0.05 for gov bonds |
| valuation_date | Date | |
| is_eligible | bool | |

### `exposure_collateral`

Allocation of a collateral item to an exposure. Unique on
`(exposure_id, collateral_id)`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| exposure_id | int FK → exposures | CASCADE, indexed |
| collateral_id | int FK → collateral | CASCADE, indexed |
| allocated_amount | Numeric(18,2) | |

## 2. Rules & reference data

### `risk_weight_rules`

Versioned, **effective-dated** risk-weight rules. Lookup index
`(rule_version, exposure_class, rating_grade, effective_from)`. If no rule
matches, the engine fails explicitly — it never assumes a default weight.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| rule_version | String(16) | indexed, e.g. `2024.1` |
| exposure_class | String(20) | indexed |
| rating_grade | String(8) | indexed |
| risk_weight | Numeric(6,4) | decimal fraction |
| effective_from | Date | indexed |
| effective_to | Date | nullable = open-ended |
| jurisdiction | String(16) | default GLOBAL |
| source_reference | String(200) | provenance |
| notes | Text | nullable |

### `fx_rates`

Single seeded rate per currency to USD. Lookup index
`(base_currency, quote_currency, effective_date)`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| base_currency | String(3) | indexed |
| quote_currency | String(3) | indexed (always USD) |
| rate | Numeric(18,8) | 1 base = rate USD |
| effective_date | Date | indexed |

## 3. Source snapshots (reconciliation input)

### `source_snapshots`

`snapshot_code` unique; `source_system` e.g. `SRC-A`/`SRC-B`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| snapshot_code | String(40) | unique, indexed |
| source_system | String(40) | |
| as_of_date | Date | |
| description | Text | nullable |

### `source_exposures`

Flat records inside a snapshot; most fields nullable because snapshot-layer
quality is deliberately imperfect (anomalies). Index
`(snapshot_id, business_key)`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| snapshot_id | int FK → source_snapshots | CASCADE, indexed |
| business_key | String(40) | indexed |
| counterparty_ref | String(32) | nullable |
| exposure_class | String(20) | nullable |
| currency | String(3) | nullable |
| amount | Numeric(18,2) | nullable |
| rating_grade | String(8) | nullable |
| maturity_date | Date | nullable |
| collateral_ref | String(32) | nullable |
| raw_payload | Text | nullable |

## 4. Processing history

### `data_quality_rules`

Versioned rule registry (DQ-001…DQ-009).

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| rule_code | String(16) | unique, indexed |
| description | Text | |
| severity | String(12) | indexed: CRITICAL/HIGH/MEDIUM/LOW |
| target_entity | String(40) | exposures or source_exposures |
| target_field | String(80) | nullable |
| enabled | bool | |
| rule_version | String(16) | default 1.0 |

### `data_quality_runs`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| run_ref | String(40) | unique, indexed (e.g. `DQ-…`) |
| scope | String(40) | default ALL |
| status | String(20) | |
| rule_count | int | |
| finding_count | int | |
| summary_json | Text | `{finding_count, by_severity, by_rule}` |
| started_at / finished_at | DateTime(tz) | |

### `data_quality_findings`

Record-level anomaly. Indexed by `run_id`, `rule_code`, `severity`,
`record_key`.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| run_id | int FK → data_quality_runs | CASCADE, indexed |
| rule_code | String(16) | indexed |
| severity | String(12) | indexed |
| entity_type | String(40) | target layer |
| record_key | String(60) | indexed |
| field | String(80) | nullable |
| description | Text | |
| detected_value | Text | nullable |

### `reconciliation_runs`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| run_ref | String(40) | unique, indexed |
| source_a_key / source_b_key | String(40) | snapshot keys compared |
| business_key | String(40) | match key |
| tolerance | Numeric(18,4) | stored per run (auditable) |
| status | String(20) | |
| matched / mismatched / source_only_a / source_only_b / duplicates | int | five outcome buckets |
| summary_json | Text | |
| started_at / finished_at | DateTime(tz) | |

### `reconciliation_results`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| run_id | int FK → reconciliation_runs | CASCADE, indexed |
| business_key | String(40) | indexed |
| status | String(20) | indexed (MATCHED/MISMATCHED/SOURCE_ONLY_A/B/DUPLICATE) |
| source_a_value | Text | JSON of A record |
| source_b_value | Text | JSON of B record |
| differences_json | Text | field → (a, b) differences |

### `rwa_calculation_runs`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| run_ref | String(40) | unique, indexed (e.g. `RWA-…`) |
| rule_version | String(16) | |
| as_of_date | Date | |
| reporting_currency | String(3) | default USD |
| status | String(20) | |
| exposure_count | int | |
| calculated_count / unsupported_count | int | |
| total_eligible_amount / total_rwa | Numeric(20,2) | |
| summary_json | Text | |
| started_at / finished_at | DateTime(tz) | |

### `rwa_calculation_results`

Per-exposure outcome with full explanation JSON.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| run_id | int FK → rwa_calculation_runs | CASCADE, indexed |
| exposure_id | int FK → exposures | SET NULL, indexed |
| exposure_ref | String(40) | indexed |
| exposure_class / rating_grade / currency | String | |
| original_amount | Numeric(18,2) | |
| amount_reporting | Numeric(20,2) | converted to USD |
| collateral_credit | Numeric(20,2) | |
| eligible_amount | Numeric(20,2) | |
| risk_weight | Numeric(6,4) | nullable (unsupported) |
| rwa | Numeric(20,2) | nullable (unsupported) |
| rule_reference | String(200) | nullable |
| status | String(30) | indexed |
| explanation_json | Text | step-by-step, replayable |

## 5. AI / knowledge

### `regulatory_documents`

Provenance and status of an ingested document. `file_checksum` unique.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| title | String(300) | indexed |
| document_identifier | String(120) | nullable |
| issuing_authority | String(160) | nullable |
| publication_date | Date | nullable |
| document_version | String(40) | nullable |
| source_url | String(500) | nullable |
| file_name / file_type | String | |
| file_checksum | String(64) | unique, SHA-256 |
| page_count / chunk_count | int | |
| status | String(20) | indexed (INGESTED/FAILED/UNSUPPORTED_OCR) |
| error_message | Text | nullable |
| is_sample | bool | clearly-labelled sample flag |
| ingested_at | DateTime(tz) | |

### `document_chunks`

Retrievable passage with page/section metadata and pre-computed embedding
(stored as raw little-endian float32 bytes).

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| document_id | int FK → regulatory_documents | CASCADE, indexed |
| chunk_index | int | |
| page_number | int | nullable |
| section | String(200) | nullable |
| content | Text | |
| token_estimate | int | |
| embedding | LargeBinary | nullable |
| embedding_model / embedding_dim | String(120) / int | nullable |

Index `(document_id, chunk_index)`.

### `ai_requests`

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| request_ref | String(40) | unique, indexed (`AI-…`) |
| question | Text | |
| provider | String(20) | ollama/openai/mock |
| model | String(80) | nullable |
| status | String(20) | indexed |
| answer | Text | nullable |
| insufficient_evidence | bool | |
| citations_json | Text | JSON citations with doc/page/snippet/score |
| latency_ms | int | nullable |
| error | Text | nullable |
| started_at / finished_at | DateTime(tz) | |

### `ai_tool_executions`

Audited invocation of an approved (read-only) tool.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| request_id | int FK → ai_requests | CASCADE, indexed |
| tool_name | String(60) | indexed |
| arguments_json | Text | |
| result_summary | Text | |
| status | String(20) | OK/ERROR |
| duration_ms | int | nullable |
| error | Text | nullable |

## 6. Audit

### `audit_events`

Append-only trail; no update/delete path exists in the platform.

| Column | Type | Notes |
|---|---|---|
| id | int PK | |
| event_type | String(40) | indexed (risk/data_quality/reconciliation/assistant/document) |
| entity_type | String(40) | nullable |
| entity_id | String(60) | nullable |
| action | String(60) | |
| actor | String(60) | default system |
| details_json | Text | nullable |

> Never store credentials or unnecessary sensitive content in audit events.