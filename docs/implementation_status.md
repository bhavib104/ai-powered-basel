# Implementation Status

Tracks what is **actually built and verified** at each phase. Nothing is marked
done until its commands have been run and its results observed.

**Last updated:** Phase 1

---

## Verified baseline

| Check | Command | Result |
|---|---|---|
| Backend deps installed | `python -m pip install -r requirements-dev.txt` | ✅ ok |
| Backend tests | `python -m pytest` | ✅ 2 passed |
| Backend starts | `uvicorn app.main:app` → `GET /api/v1/health` | ✅ HTTP 200 |
| Frontend deps installed | `npm install` | ✅ ok |
| Frontend typecheck | `npm run typecheck` | ✅ 0 errors |
| Frontend lint | `npm run lint` | ✅ 0 problems |
| Frontend build | `npm run build` | ✅ built |
| Frontend dev server | `npm run dev` → `GET localhost:5173` | ✅ HTTP 200 |

> Note: the frontend dev server binds to IPv6 `::1`; use
> `http://localhost:5173` (not `127.0.0.1`). The frontend calls the backend at
> `http://127.0.0.1:8000` (uvicorn's IPv4 default).

---

## Phase tracker

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Environment inspection & stack recommendation | ✅ Complete |
| 1 | Foundation (structure, config, health check) | ✅ Complete |
| 2 | Data foundation (schema + synthetic data) | ⏳ Pending |
| 3 | Risk engine | ⏳ Pending |
| 4 | Data quality & reconciliation | ⏳ Pending |
| 5 | Backend APIs | ⏳ Pending |
| 6 | Regulatory document ingestion | ⏳ Pending |
| 7 | RAG (retrieval + citations) | ⏳ Pending |
| 8 | AI tools & orchestration | ⏳ Pending |
| 9 | Frontend | ⏳ Pending |
| 10 | Hardening & documentation | ⏳ Pending |

---

## Phase 1 — Foundation (complete)

**Files created**

- `README.md`, `.gitignore`
- `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/.env.example`
- `backend/pytest.ini`, `backend/ruff.toml`
- `backend/app/__init__.py`, `app/main.py`
- `backend/app/core/{config.py,logging.py}`
- `backend/app/api/routes/health.py`
- `backend/tests/test_health.py`
- `frontend/` (package.json, vite config, tsconfig, eslint config, index.html)
- `frontend/src/` (app shell, layout, health badge, API client, 7 page shells)
- `docs/architecture.md`, `docs/architecture_decisions.md`, `docs/implementation_status.md`

**Features completed**

- FastAPI application factory with lifespan logging and CORS.
- Environment-driven configuration (`text`/`json` logging).
- `GET /api/v1/health` and `GET /` banner.
- React SPA shell with navigation for all seven application areas.
- Live backend health indicator in the UI header.
- Honest placeholder pages that state which phase delivers them.

**Known limitations**

- Frontend automated tests (Vitest) are introduced in Phase 9/10; the
  `npm test` script is intentionally absent until then.
- Health endpoint does not yet probe the database or AI provider (those
  arrive with Phases 2 and 8).
- Placeholder pages show no data yet — by design, they contain no fake metrics.

**Next phase:** Phase 2 — database schema + reproducible synthetic data generator.
