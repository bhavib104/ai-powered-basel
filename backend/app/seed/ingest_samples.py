"""CLI: index the bundled sample regulatory documents into the knowledge base.

These files are clearly-labelled sample content (see the ``SAMPLE DOCUMENT``
header in each file) so the RAG demo works fully offline without needing real
regulatory PDFs:

    .venv/Scripts/python.exe -m app.seed.ingest_samples

Embeds chunks with the configured embedding backend.  If sentence-transformers
is unavailable the deterministic hashing embedder is used instead, so the
command always succeeds locally.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from app.db.session import SessionLocal
from app.services import ingestion

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data" / "sample_docs"

METADATA: dict[str, dict[str, object]] = {
    "sample-standardised-approach-rwa.md": {
        "title": "Sample — Standardised Approach RWA (corporate exposures, CRM)",
        "document_identifier": "DEMO-STA-RWA-001",
        "issuing_authority": "Sample Regulatory Text (not an official authority)",
        "publication_date": date(2024, 1, 15),
        "document_version": "demo-1.0",
        "source_url": "https://example.invalid/sample-standardised-approach-rwa",
    },
    "sample-retail-sovereign-bank-exposures.md": {
        "title": "Sample — Retail, Sovereign and Bank Exposures",
        "document_identifier": "DEMO-CRM-EXPO-002",
        "issuing_authority": "Sample Regulatory Text (not an official authority)",
        "publication_date": date(2024, 2, 10),
        "document_version": "demo-1.0",
        "source_url": "https://example.invalid/sample-retail-sovereign-bank-exposures",
    },
    "sample-data-quality-reconciliation.md": {
        "title": "Sample — Data Quality and Reconciliation Governance",
        "document_identifier": "DEMO-DQR-003",
        "issuing_authority": "Sample Regulatory Text (not an official authority)",
        "publication_date": date(2024, 3, 5),
        "document_version": "demo-1.0",
        "source_url": "https://example.invalid/sample-data-quality-reconciliation",
    },
}


def main() -> int:
    db = SessionLocal()
    try:
        files = sorted(SAMPLE_DIR.glob("*.md"))
        if not files:
            print(f"No sample documents found under {SAMPLE_DIR}", file=sys.stderr)
            return 1

        total_chunks = 0
        for path in files:
            meta = METADATA.get(path.name, {})
            doc = ingestion.ingest_document(
                db,
                path=path,
                title=str(meta.get("title") or path.stem),
                document_identifier=meta.get("document_identifier"),  # type: ignore[arg-type]
                issuing_authority=meta.get("issuing_authority"),  # type: ignore[arg-type]
                publication_date=meta.get("publication_date"),  # type: ignore[arg-type]
                document_version=meta.get("document_version"),  # type: ignore[arg-type]
                source_url=meta.get("source_url"),  # type: ignore[arg-type]
                is_sample=True,
            )
            total_chunks += doc.chunk_count
            print(
                f"{doc.status}: {doc.title} — "
                f"{doc.page_count} page(s), {doc.chunk_count} chunk(s)"
            )
        print(f"Done. {total_chunks} chunks indexed across {len(files)} documents.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())