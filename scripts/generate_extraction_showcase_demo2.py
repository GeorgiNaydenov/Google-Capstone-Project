"""Generate the second-platform extraction demo asset set.

This intentionally uses a different seed, output folder, and public demo
namespace from the primary showcase so both demo platforms look distinct.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


DEFAULT_OUTPUT = Path("showcase_data/demo2/extraction")
DEFAULT_FRONTEND_PUBLIC = Path("frontend/public/demo-data/extraction")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate second-platform extraction demo assets."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=64)
    parser.add_argument("--seed", type=int, default=260705)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--frontend-public", type=Path, default=DEFAULT_FRONTEND_PUBLIC)
    parser.add_argument("--patients-per-file", type=int, default=5)
    args = parser.parse_args()
    from scripts.generate_extraction_showcase import generate

    manifest = generate(
        args.output,
        args.count,
        args.seed,
        args.template,
        "demo2",
        args.frontend_public,
        args.patients_per_file,
        "PT-N",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "demo_platform": "demo2",
                "synthetic_picker_count": manifest["frontend_contract"][
                    "syntheticPickerCount"
                ],
                "packet_count": manifest["packet_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
