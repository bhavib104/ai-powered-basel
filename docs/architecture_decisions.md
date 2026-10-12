# Architecture Decision Records (ADRs)

Each ADR records a decision, the alternatives considered, and the trade-off.

---

## ADR-001 — Database: SQLite (via SQLAlchemy + Alembic)

**Context.** The app must run locally with minimal setup, hold structured
banking data plus processing history, and be swappable later.

**Decision.** Use SQLite through SQLAlchemy 2.x with Alembic migrations.

**Alternatives considered.**
- *PostgreSQL in Docker* — more production-like, but Docker was not running on
  the target machine and it adds setup friction for no MVP benefit.
- *DuckDB* — great for analytics, weaker fit for transactional writes and ORM use.

**Consequences.** Zero-install, single-file, trivially reproducible (regenerate
from seed). Because all access goes through SQLAlchemy, switching to PostgreSQL
later means changing `DATABASE_URL` and running migrations.
Fixed-precision decimals are used for all monetary values.

---

## ADR-002 — Backend: Python + FastAPI

**Context.** The backend hosts deterministic financial logic *and* the AI/RAG
pipeline.

**Decision.** Python 3.13 with FastAPI.

**Alternatives considered.**
- *Node/TypeScript backend* — one language with the frontend, but a weaker
  ecosystem for embeddings/RAG and numerical work.
- *Flask/Django* — Django is heavier than needed; Flask lacks built-in typed
  validation.

**Consequences.** Strong AI/data ecosystem, typed schemas via Pydantic,
auto-generated OpenAPI docs. Two languages in the repo (Python + TypeScript) —
an accepted cost.

---

## ADR-003 — Frontend: React + Vite + TypeScript + Tailwind

**Context.** A professional, responsive risk-analyst UI with tables and charts.

**Decision.** React 19 + Vite 8 + TypeScript + Tailwind CSS 4 + Recharts, as a
client-side SPA talking to the FastAPI REST API.

**Alternatives considered.**
- *Next.js* — server rendering is unnecessary for a local tool that talks to a
  separate API; it adds complexity.
- *Plain templating (Jinja)* — poor fit for interactive tables/charts.

**Consequences.** Fast dev loop (`npm run dev`), strong typing, easy
component reuse. Requires running two processes locally (documented).

---

## ADR-004 — Embeddings: local sentence-transformers

**Decision.** `sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, run
locally on CPU.

**Alternatives considered.** OpenAI embeddings (requires a paid key and sends
data to a third party); larger local models (slower, no MVP benefit).

**Consequences.** Free and fully offline; already available on the target
machine. Quality is adequate for a small, well-structured regulatory corpus.
The embedder sits behind an interface so it can be swapped.

---

## ADR-005 — LLM: local Ollama first, with pluggable providers + mock

**Decision.** Default to local **Ollama** (`mistral`), but code against a
provider interface with **OpenAI** and **mock** implementations.

**Rationale.** Keeps the project free and offline by default (a requirement),
while allowing a stronger cloud model later. The **mock** provider returns
deterministic responses so tests and CI never depend on a paid model.

**Consequences.** Local models are weaker than frontier models; answer quality
is protected by strict grounding, citation verification and deterministic tools
rather than raw model strength.

---

## ADR-006 — Vector storage: in-database + NumPy cosine search

**Decision.** Store chunk embeddings as binary blobs in SQLite and compute
cosine similarity with NumPy (optionally an SQLite vector extension later).

**Alternatives considered.** ChromaDB/FAISS/Qdrant as separate services.

**Consequences.** No extra process to run or configure; trivially reproducible.
At a few thousand chunks, brute-force search is fast enough. The retrieval
interface hides the implementation so a vector DB can be introduced if scale
demands it.

---

## ADR-007 — Architecture: modular monolith

**Decision.** One deployable backend with clearly separated internal modules,
rather than microservices.

**Rationale.** Matches the project scale; avoids distributed-system complexity
with no benefit. Boundaries are enforced by module structure and interfaces.

---

## ADR-008 — Orchestration: deterministic routing before any agent planning

**Decision.** Begin with a bounded, explicit tool-calling loop: allow-listed
tools, validated arguments, execution timeouts, result limits, a maximum tool
call count, and full audit logging. Dynamic planning is only considered later if
it is measurable and evaluable.

**Rationale.** Matches the TRD, and is far easier to test and reason about than
an autonomous agent.

---

## ADR-009 — Currency: single reporting currency + seeded FX table

**Context.** The PRD mentions multiple currencies, but RWA needs one consistent
eligible amount.

**Decision.** Store a small, seeded FX-rate table with effective dates and
convert exposure amounts to a single **reporting currency**. Documented as a
deliberate simplification in `risk_methodology.md`.

**Alternatives considered.** Single-currency-only MVP (simpler, but loses
realism) — kept the FX table because it is cheap and more representative.

---

## ADR-010 — Full-download avoidance for Python deps

**Decision.** Create the backend virtual environment with
`--system-site-packages` so the machine's existing scientific/AI stack (NumPy,
pandas, torch, sentence-transformers) is reused.

**Consequences.** Much faster local setup (avoids re-downloading a large PyTorch
wheel). `requirements.txt` remains authoritative for clean machines and CI; this
choice only affects the *local* venv.
