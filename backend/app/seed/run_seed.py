"""Simplest local bootstrap: create tables and (optionally) seed data.

Usage::

    python -m app.seed.run_seed            # create schema + full seed
    python -m app.seed.run_seed --counts 100 500    # smaller dataset
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from app.core.logging import configure_logging

configure_logging("INFO")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the database with synthetic data.")
    parser.add_argument("--counterparties", type=int, default=1000)
    parser.add_argument("--exposures", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-clear", action="store_true")
    parser.add_argument("--manifest-path", type=str, default="data/seed_manifest.json")
    args = parser.parse_args()

    # Import lazily so plain `python -m app.seed.run_seed --help` is fast.
    from app.db import (
        Base,
        SessionLocal,
        engine,
        models,  # noqa: F401  (register models on Base.metadata)
    )
    from app.seed.generator import SeedConfig, seed_database

    Base.metadata.create_all(engine)
    logging.getLogger(__name__).info("Schema ready at %s", engine.url)

    config = SeedConfig(
        seed=args.seed,
        n_counterparties=args.counterparties,
        n_exposures=args.exposures,
        clear_existing=not args.no_clear,
    )

    with SessionLocal() as session:
        result = seed_database(session, config)
        session.commit()
        counts = result.counts

    manifest_path = Path(args.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result.manifest, indent=2), encoding="utf-8")

    print(json.dumps(counts, indent=2, sort_keys=True))
    print(f"\nManifest written to {manifest_path}")
    print("Anomaly totals:", json.dumps(result.manifest["anomaly_totals"], sort_keys=True))


if __name__ == "__main__":
    sys.exit(main())