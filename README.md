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

This project is being built **phase by phase**. See
[`docs/implementation_status.md`](docs/implementation_status.md) for the current
state and [`docs/architecture.md`](docs/architecture.md) for the design.

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment inspection & stack recommendation | ✅ Done |
| 1 | Foundation (structure, config, health check) | ✅ Done |
| 2 | Data foundation (schema + synthetic data) | 🚧 Next |
| 3 | Risk engine | ⏳ Pending |
| 4 | Data quality & reconciliation | ⏳ Pending |
| 5 | Backend APIs | ⏳ Pending |
| 6 | Regulatory document ingestion | ⏳ Pending |
| 7 | RAG (retrieval + citations) | ⏳ Pending |
| 8 | AI tools & orchestration | ⏳ Pending |
| 9 | Frontend | ⏳ Pending |
| 10 | Hardening & documentation | ⏳ Pending |

---

## Quick start

> Setup instructions are completed as each phase lands. Full details will live
> here and in `docs/architecture.md`.

### Backend

```powershell
cd backend
python -m venv --system-site-packages .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Then open <http://localhost:8000/api/v1/health>.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Then open <http://localhost:5173>.

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
