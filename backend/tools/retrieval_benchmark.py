"""Simple retrieval benchmark over the bundled sample corpus.

Runs a small labelled question set against the vector index and reports
precision@1 (is the right document the top hit?) and recall@3 (does the right
document appear in the top 3?) for every query, plus aggregates.

Requires the sample documents to be ingested and embedded first:

    python -m app.seed.ingest_samples
    python tools/retrieval_benchmark.py

Numbers produced here are quoted in docs/evaluation.md.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running as a plain script from the backend directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.models import RegulatoryDocument  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.retrieval import retrieve  # noqa: E402

# (query, distinctive substring of the expected document title)
QUESTION_SET: list[tuple[str, str]] = [
    ("What is the risk weight for residential retail mortgages?", "Retail, Sovereign and Bank"),
    ("How is a sovereign exposure treated under the standardised approach?", "Retail, Sovereign and Bank"),
    ("What risk weights apply to corporate exposures by external rating?", "Standardised Approach RWA"),
    ("How is eligible collateral, such as cash and government bonds, applied?", "Standardised Approach RWA"),
    ("What happens when an exposure class is not supported by the rules?", "Standardised Approach RWA"),
    ("Which data-quality rules detect missing fields and duplicate records?", "Data Quality and Reconciliation"),
    ("How does reconciliation match records by business key between sources?", "Data Quality and Reconciliation"),
    ("Why is an append-only audit trail important for regulatory reporting?", "Data Quality and Reconciliation"),
    ("What is the risk weight of a BBB-rated bank exposure?", "Standardised Approach RWA"),
    ("What makes a loan qualify as a retail exposure?", "Retail, Sovereign and Bank"),
]


def main() -> int:
    with SessionLocal() as session:
        titles = {
            doc.id: doc.title
            for doc in session.execute(select(RegulatoryDocument)).scalars()
        }
        if not titles:
            print("No documents indexed. Run: python -m app.seed.ingest_samples", file=sys.stderr)
            return 1

        print(f"{'query':<74} {'p@1':>4} {'r@3':>4}  top hit")
        print("-" * 120)
        hits_1 = 0
        hits_3 = 0
        total = len(QUESTION_SET)
        for query, expected in QUESTION_SET:
            results = retrieve(session, query, top_k=3, min_score=0.0)
            top_titles = [r.document_title for r in results]
            p1 = any(expected in t for t in top_titles[:1])
            r3 = any(expected in t for t in top_titles[:3])
            hits_1 += int(p1)
            hits_3 += int(r3)
            top = top_titles[0] if top_titles else "(none)"
            print(f"{query[:74]:<74} {'OK' if p1 else '--':>4} "
                  f"{'OK' if r3 else '--':>4}  {top[:60]}")

        print("-" * 120)
        print(f"Precision@1: {hits_1}/{total} ({hits_1 / total:.0%})")
        print(f"Recall@3:    {hits_3}/{total} ({hits_3 / total:.0%})")
        return 0


if __name__ == "__main__":
    os.environ.setdefault("EMBEDDING_BACKEND", "auto")
    sys.exit(main())