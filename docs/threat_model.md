# Threat Model

> **Status:** Final — reflects the controls actually implemented in
> `app/tools/registry.py`, `app/services/orchestration.py`, `app/db` and
> `app/services/ingestion.py`.

## Assets

- Stored banking data (100% synthetic in this repo, but treated as sensitive).
- Engine determinism and result integrity (RWA, quality findings, reconciliation).
- The append-only audit trail.
- LLM/embedding API keys (never committed, never logged).
- The knowledge base (documents + embeddings).

## Trust boundaries

```
browser ──► FastAPI (/api/v1) ──► services ──► SQLite (local file)
                 │
                 └──► orchestration ──► tools (read-only) ──► services
                 └──► retrieval ──► embeddings ──► (optional) sentence-transformers / LLM API
                 └──► ingestion ◄── uploaded files (untrusted)
```

There is no authentication in the MVP (single local user) — see limitations.

## Key threats and implemented mitigations

### 1. AI writes / destructive database access through the LLM

- The assistant has **no SQL or write path**. All tools come from a fixed,
  allow-listed registry (`app/tools/registry.py`) of six **read-only** tools
  (portfolio summary, exposure lookup, risk-run/results, quality summary,
  reconciliation summary, regulatory search).
- Tool calls are validated against typed JSON schemas before execution and
  bounded by `ai_max_tool_calls` and a timeout.
- The LLM output feeds the *answer text only*; every numeric value in the
  answer comes from tool results, and structured evidence is **never** used as
  an instruction source.
- Database mutating flows (seeding, runs) are invoked only by fixed application
  code paths, never by the model.

### 2. Prompt injection via regulatory documents

- Retrieved content is tagged and treated as untrusted evidence — the answer
  composer treats model instructions and document text as distinct inputs
  (document text is never executed).
- Tools have fixed schemas; the intent router picks tools deterministically from
  a user question, so a document cannot add new capabilities.
- Citations must come from actual retrieved chunks (`citation correctness` is
  asserted by tests).

### 3. SQL injection

- All persistence goes through SQLAlchemy ORM with parameterised statements;
  user strings enter `LIKE ... %escaped%` parameters, never raw SQL fragments.

### 4. Data-quality corruption of downstream numbers

- Master-layer anomalies (invalid amount/currency/rating/class/dates) are
  detected by versioned DQ rules **before** the risk engine consumes the data.
- The risk engine refuses to guess: unsupported inputs produce explicit
  `UNSUPPORTED_*` outcomes with reasons (see `docs/risk_methodology.md`).

### 5. Secret leakage

- Secrets are read from environment variables / `.env`; `.env` is git-ignored;
  API keys are never logged (audit events record tool names, not keys).

### 6. Untrusted file uploads

- Ingestion accepts only `.txt`, `.md`, `.pdf`, with a 25 MB size cap and
  SHA-256 checksum identity.
- Scanned PDFs (no extractable text) are reported as `UNSUPPORTED_OCR`, not
  silently accepted.

### 7. Audit tampering

- Every engine run and assistant exchange appends an `audit_events` row; there
  is no update/delete endpoint for audit records in the platform.

## Residual risks / explicit limitations

- **No authentication or multi-tenancy** — a single local user on localhost;
  do not expose publicly without adding auth.
- **Local dev database** — SQLite in WAL mode; no transport encryption.
- **LLM provider trust** — the model API (or local Ollama) is a
  confidentiality boundary; never send real PII in MVP.
- **Dependency risk** — third-party packages (FastAPI, SQLAlchemy, etc.) are
  pinned in `requirements*.txt` and must be updated deliberately.