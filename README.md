# AI-Powered Basel Regulatory Risk Intelligence Platform

An applied-AI / FinTech project that combines **deterministic banking risk
calculations** with **AI-assisted regulatory document intelligence** and a
**controlled AI assistant**.

> **Important**: This is an educational / portfolio project built entirely on
> **synthetic banking data** and **publicly available regulatory documents**.
> It is **not** a certified Basel/RBI capital calculation engine and must never
> be used for real regulatory submissions.

---

## What it does

For a banking risk analyst, the platform will provide:

- Exploration of exposures and portfolio-level risk metrics.
- Data quality validation and reconciliation of inconsistent source records.
- Risk-weighted asset (RWA) calculation using **configurable, versioned rules**.
- Retrieval-augmented question answering over public regulatory documents,
  with **verifiable citations**.
- A **controlled AI assistant** that can query structured risk data through
  approved, read-only tools.

### The core safety rule

All authoritative financial values (RWA, risk weights, eligibility) are computed
by **deterministic, tested code**. The LLM may interpret questions and summarize
results, but it **never** invents numbers, risk weights, or regulatory rules.

---

## Repository layout

```
ai-powered-basel/
├─ backend/     FastAPI application (Python) — APIs, engines, AI, data
├─ frontend/    React + TypeScript + Vite UI
├─ docs/        Architecture, methodology, and evaluation documentation
└─ README.md
```

---

## Status

The MVP is **complete**: deterministic engines, backend APIs, RAG over bundled
sample regulatory documents, a controlled AI assistant, a full React UI and
SQLAlchemy migrations — all verified by 54 passing tests. See
[`docs/implementation_status.md`](docs/implementation_status.md) for the current
state and [`docs/architecture.md`](docs/architecture.md) for the design.

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment inspection & stack recommendation | ✅ Done |
| 1 | Foundation (structure, config, health check) | ✅ Done |
| 2 | Data foundation (schema + synthetic data) | ✅ Done |
| 3 | Risk engine | ✅ Done |
| 4 | Data quality & reconciliation | ✅ Done |
| 5 | Backend APIs | ✅ Done |
| 6 | Regulatory document ingestion | ✅ Done |
| 7 | RAG (retrieval + citations) | ✅ Done |
| 8 | AI tools & orchestration | ✅ Done |
| 9 | Frontend | ✅ Done |
| 10 | Hardening & documentation | ✅ Done |

---

## Quick start

### 1. Backend

```powershell
cd backend
python -m venv --system-site-packages .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Create the database with reproducible synthetic data (1,000 counterparties,
5,000 exposures, seeded anomalies, rule & FX tables):

```powershell
python -m app.seed.run_seed          # writes data/basel.db + seed_manifest.json
python -m app.seed.ingest_samples    # index the 3 sample regulatory docs for RAG
```

Run the API:

```powershell
uvicorn app.main:app --port 8000
```

Open <http://localhost:8000/api/v1/health>.

> Alternatively migrate an empty schema with Alembic instead of seeding:
> `python -m alembic upgrade head` (baseline includes every table; data seeding
> is then optional).

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Then open <http://localhost:5173>.

### 3. Try it

- **Risk & RWA** → *Run calculation* (rule version `2024.1`), then open any
  row to see the step-by-step explanation JSON.
- **Data Quality** → *Run checks* (the seeded dataset surfaces 142 findings).
- **Reconciliation** → reconcile `SRC-A` ↔ `SRC-B`.
- **Regulatory Documents** → search e.g. *"risk weight for retail mortgages"*
  or ingest your own `.txt` / `.md` / text-PDF.
- **AI Risk Assistant** → ask a structured-data question (e.g. *"total RWA for
  corporate exposures"*) or a regulatory question (e.g. *"how is eligible
  collateral treated?"*). Answers show citations and the tool trail; with no
  matching evidence the assistant says so instead of inventing text.
- **Audit & Runs** → every run and assistant exchange is in the append-only
  audit trail.

### Tests & lint

```powershell
cd backend
python -m pytest          # 54 tests, isolated seeded DBs
python -m ruff check app tests
cd ..\frontend
npm run typecheck && npm run lint && npm run build
```

> **AI settings:** `llm_provider` defaults to `ollama` (model `mistral`).
> Set `LLM_PROVIDER=mock` in `backend/.env` for deterministic, offline answers,
> or `LLM_PROVIDER=openai` (requires `OPENAI_API_KEY`). Embeddings default to
> `auto` — real model when installed, deterministic hashing otherwise.

---

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design
- [`docs/architecture_decisions.md`](docs/architecture_decisions.md) — ADRs / trade-offs
- [`docs/risk_methodology.md`](docs/risk_methodology.md) — RWA methodology & assumptions
- [`docs/data_dictionary.md`](docs/data_dictionary.md) — schema reference
- [`docs/regulatory_sources.md`](docs/regulatory_sources.md) — document provenance
- [`docs/threat_model.md`](docs/threat_model.md) — security controls & limitations
- [`docs/evaluation.md`](docs/evaluation.md) — AI & engine evaluation results
- [`docs/implementation_status.md`](docs/implementation_status.md) — build progress

---

## License & data

- Code: for educational use.
- Data: **100% synthetic**. No employer, client, or customer data is used.
- Regulatory documents: only legally obtained public sources, with provenance
  recorded in `docs/regulatory_sources.md`.
