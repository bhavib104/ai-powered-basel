# Regulatory Sources

> **Status:** Final for the demo corpus — three clearly-labelled **sample**
> documents bundled with the repo. Official texts are intentionally **not**
> downloaded in this project; the corpus is designed to demonstrate the RAG
> pipeline and citation mechanism offline.

## Corpus policy

- Only documents that can be legally obtained are ever ingested
  (`source_url`, checksum and version recorded for every file).
- Every document is deduplicated by **SHA-256 file checksum** at ingestion.
- Documents are preserved; a re-upload with identical checksum returns the
  existing record rather than creating a duplicate.
- No confidential or non-public documents are used.
- Files marked `is_sample = true` are clearly labelled sample content written
  for the demo (each file begins with a `SAMPLE DOCUMENT FOR DEMONSTRATION
  PURPOSES ONLY` banner) so they can never be mistaken for real law.

## Bundled sample documents (`backend/data/sample_docs/`)

| Title | Identifier | Authority | Version | Source URL | Status |
|---|---|---|---|---|---|
| Sample — Standardised Approach RWA (corporate exposures, CRM) | `DEMO-STA-RWA-001` | Sample Regulatory Text (not an official authority) | demo-1.0 | `https://example.invalid/sample-standardised-approach-rwa` | Ingested (5 chunks) |
| Sample — Retail, Sovereign and Bank Exposures | `DEMO-CRM-EXPO-002` | Sample Regulatory Text (not an official authority) | demo-1.0 | `https://example.invalid/sample-retail-sovereign-bank-exposures` | Ingested (5 chunks) |
| Sample — Data Quality and Reconciliation Governance | `DEMO-DQR-003` | Sample Regulatory Text (not an official authority) | demo-1.0 | `https://example.invalid/sample-data-quality-reconciliation` | Ingested (5 chunks) |

> The `example.invalid` domain is reserved by IANA and can never resolve, so the
> URLs are self-evidently placeholders. Checksums are stored in
> `regulatory_documents.file_checksum` per document.

## Ingesting real regulatory texts (for a future production build)

1. Download the official PDF/MD from the regulator's website.
2. Upload through **Regulatory Documents → Ingest**, filling the
   document identifier, issuing authority, version and source URL.
3. Text-based PDFs are supported; scanned PDFs are reported as
   `UNSUPPORTED_OCR` instead of silently producing empty text.
4. Verify provenance in the knowledge-base table and cross-check citations in
   the AI assistant (each citation carries document id, page, section, snippet
   and score).

Recommended authoritative sources when extending the corpus beyond the bundled
samples: Basel Committee publications (`bis.org/bcbs`) and RBI master
directions (`rbi.org.in`), always citing the exact document identifiers and
as-of versions shown at those sites.