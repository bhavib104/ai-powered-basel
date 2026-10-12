# Evaluation

> **Status:** Final for the MVP — every number below was measured from actual
> runs on this machine (2026-10), not estimated. Equivalents are re-runnable
> with the commands shown.

## 1. Deterministic engines (correctness)

**Suite:** `backend/tests/` — **54 tests, all passing** (`python -m pytest`).

| Area | Tests | Typical assertions |
|---|---|---|
| Risk engine | 8 | corporate BBB weight 50%, collateral reduction, EUR→USD conversion, explicit `UNSUPPORTED_*` for class/rating/currency/amount, persisted totals |
| Data quality | 4 | seeded anomalies detected, per-rule totals match `seed_manifest.json`, severity from registry, invalid rating → unsupported |
| Reconciliation | 4 | seeded discrepancies found, tolerance doesn't swallow real breaks, totals consistent, unknown snapshot raises |
| Ingestion & chunking | 6 | .txt → chunks, duplicate checksum skipped, unsupported type rejected, headings become sections, oversized paragraph split |
| Retrieval | 3 | relevant doc ranked first, min-score floor, empty corpus → empty |
| Tools & AI safety | 9 | read-only registry by design, unknown tool fails cleanly, prompt injection cannot modify data, evidence/citations enforced |
| API | 15 | HTTP 200 shapes for every endpoint, DQ run matches manifest, assistant quotes evidence disclaimer when corpus empty, audit persists |

**Live engine numbers** (dev database, earlier verification):

| Measure | Value |
|---|---|
| Exposures | 5,000 |
| RWA run (rule 2024.1) | 4,935 risk-weighted, **65 explicitly unsupported**, total RWA ≈ 2,168,917,032.68 USD |
| DQ run | 142 findings across 9 versioned rules |
| Reconciliation (SRC-A ↔ SRC-B) | 40 mismatched, 15 duplicates, 77 only-in-A, 20 only-in-B |

## 2. Retrieval (RAG)

**Corpus:** 3 bundled sample documents, 15 chunks, embedded locally
(`all-MiniLM-L6-v2`, L2-normalised; deterministic hashing fallback offline).
Live query:

```
POST /documents/search {"query":"What is the risk weight for retail mortgages?","top_k":5}
→ 5 hits; top = "Sample — Retail, Sovereign and Bank Exposures", score 0.6326, page 1
```

The query "risk weight for retail mortgages" surfaced the mortgage sample as the
top-ranked chunk — semantic retrieval on a 15-chunk local corpus behaves
qualitatively as intended. Formal precision@k / recall@k over a labelled
versioned dataset is listed in **Future work** (not fabricated here).

## 3. Citations & assistant answers

Live exchange (local Ollama `mistral`):

```
POST /assistant/query {"question":"According to the sample regulatory text, how is eligible collateral treated?"}
→ request AI-1fa252cbcbe5 · provider ollama:mistral · 2 read-only tools · 5 citations
  · insufficient_evidence = false
```

- Every citation carries `document_title`, `page`, `section`, `snippet` and
  `score`, and is asserted to reference an actually-retrieved chunk in tests
  (`test_generation_deterministic_answer_cites_evidence`).
- Offline/no-corpus behaviour is explicitly covered: regulatory questions with
  an empty corpus produce `insufficient_evidence = true` and a refusal-style
  answer rather than invented text
  (`test_regulatory_question_returns_evidence_disclaimer`,
  `test_regulatory_question_without_documents_is_insufficient`).

## 4. Tool safety

- `app/tools/registry.py` exposes **six read-only tools**; `run_tool` validates
  arguments against JSON schemas and rejects unknown names
  (`test_unknown_tool_fails_cleanly`).
- Injection attempt inside a question cannot change data or run new tools
  (`test_prompt_injection_cannot_modify_data`).
- Tool calls are persisted with arguments, duration, status and errors
  (`test_answers_are_persisted_with_tool_trail`), and mirrored in
  `audit_events` (8 events recorded during the verification session above).

## 5. Frontend & API

| Check | Result |
|---|---|
| `npm run typecheck` | 0 errors |
| `npm run lint` | 0 problems |
| `npm run build` | vite build OK (8 routed pages) |
| `GET /api/v1/health` (live) | status ok, api ok, database ok |
| Dashboard / exposures / risk / quality / recon / documents / assistant / audit APIs | all exercised live, HTTP 200 |

## 6. Performance & cost

- Full RWA run over 5,000 exposures completes in well under the API timeout
  (seconds); runs are asynchronous only in the sense that each endpoint returns
  after its run finishes.
- Embeddings: local sentence-transformers (no API cost); fallback hashing
  embedder is dependency-free.
- LLM: local Ollama (free) by default; `mock` provider requires no network and
  is fully deterministic. Optional OpenAI path is unused in this repo.

## 7. Future work (not claimed)

- Labelled retrieval benchmark (precision@k / recall@k) and faithfulness
  scoring over a frozen versioned question set.
- Prompt-injection red-team suite across a larger corpus.
- Migration of the SQLite schema to PostgreSQL and CI (pytest + lint + build)
  matrix.
- Frontend unit tests (the `npm test` script is intentionally absent in MVP).