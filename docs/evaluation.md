# Evaluation

> **Status:** Placeholder — completed in **Phases 7, 8 and 10**.

Planned contents and metrics (all reported from actual runs; no invented
numbers):

- **Deterministic engines** — risk-calculation correctness, data-quality rule
  correctness, reconciliation correctness (unit + integration tests).
- **Retrieval** — precision/recall at *k* against a labelled question set.
- **Citations** — percentage of citations that reference actual retrieved
  records (citation correctness).
- **Answers** — faithfulness and relevance to retrieved evidence; explicit
  insufficient-evidence behaviour.
- **Tools** — tool-selection correctness and agreement with deterministic
  numeric results.
- **Safety** — behaviour on invalid tool requests and prompt-injection attempts.
- **Performance** — latency and estimated model cost.

A versioned evaluation dataset (including insufficient-evidence, version-conflict
and injection cases) will accompany this document.
