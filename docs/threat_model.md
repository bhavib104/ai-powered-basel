# Threat Model

> **Status:** Placeholder — completed in **Phases 8 and 10** alongside the AI
> orchestration and security hardening.

Planned contents:

- **Assets:** stored banking data, audit trail, API integrity, secrets.
- **Trust boundaries:** browser → API → services → database; API → LLM provider;
  uploaded/pasted external documents (untrusted).
- **Key threats and mitigations:**
  - *Prompt injection via regulatory documents* — retrieved content is treated as
    untrusted evidence, never as instructions; tools have fixed, allow-listed
    schemas.
  - *Arbitrary or destructive database access through the AI* — the AI layer has
    read-only, typed tools only; no raw SQL, no writes.
  - *SQL injection* — parameterised ORM/SQL access throughout.
  - *Secret leakage* — secrets via environment variables; `.env` git-ignored;
    credentials never logged.
  - *Untrusted uploads* — file type and size validation; checksummed ingestion.
- **Explicit limitations:** no authentication/multi-user roles in the MVP
  (local single-user); not hardened for public deployment.
