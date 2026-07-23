"""Backfill the semantic vector index for a tenant clinical database.

Embeds existing clinical notes, document chunks, and extracted fields with
Vertex AI ``gemini-embedding-001`` (Application Default Credentials) and
persists them into the tenant's ``vector_chunks`` table so semantic Q&A
retrieval works immediately instead of waiting for the lazy first-query
backfill.

Usage:
    uv run python scripts/build_vector_index.py                 # default clinical.db
    uv run python scripts/build_vector_index.py --db capstone.db --uploads uploads_capstone
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from capstone_agent import database  # noqa: E402
from capstone_agent import vector_store  # noqa: E402


def main() -> int:
    """Run the backfill against the requested tenant database."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", default=None, help="Tenant SQLite file (default: clinical.db)"
    )
    parser.add_argument("--uploads", default=None, help="Tenant uploads directory")
    parser.add_argument(
        "--limit", type=int, default=400, help="Maximum chunks to embed"
    )
    args = parser.parse_args()

    if not vector_store.store.available():
        print(
            "Vector search unavailable: Vertex credentials or ENABLE_VECTOR_SEARCH missing."
        )
        return 1

    db_path = ROOT / args.db if args.db else None
    uploads = ROOT / args.uploads if args.uploads else None
    if db_path is not None:
        with database.tenant_storage(db_path, uploads):
            outcome = vector_store.backfill_vector_index(limit=args.limit)
            status = vector_store.vector_index_status()
    else:
        outcome = vector_store.backfill_vector_index(limit=args.limit)
        status = vector_store.vector_index_status()

    print(json.dumps({"backfill": outcome, "status": status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
