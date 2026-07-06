"""Generate the second-platform database intelligence demo dataset."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


DEFAULT_OUTPUT = Path("showcase_data/demo2/database")
DEFAULT_DB = DEFAULT_OUTPUT / "clinical_showcase_demo2.db"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate second-platform database intelligence demo data.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB)
    parser.add_argument("--patient-count", type=int, default=1500)
    parser.add_argument("--years", type=int, default=4)
    parser.add_argument("--anchor-date", type=date.fromisoformat, default=date(2026, 7, 5))
    parser.add_argument("--seed", type=int, default=260706)
    parser.add_argument("--replace", dest="replace", action="store_true", default=True)
    parser.add_argument("--append", dest="replace", action="store_false", help="Append to an existing demo2 database instead of replacing it.")
    parser.add_argument("--template", type=Path, default=None)
    args = parser.parse_args()
    from scripts.generate_database_showcase import generate

    manifest = generate(args.db_path, args.output, args.patient_count, args.seed, args.replace, args.years, args.anchor_date, args.template, "demo2", "PT-N")
    print(json.dumps({"output": str(args.output), "db_path": str(args.db_path), "total_rows": manifest["total_rows"], "demo_platform": "demo2"}, indent=2))


if __name__ == "__main__":
    main()
