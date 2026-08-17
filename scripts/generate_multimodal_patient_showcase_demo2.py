"""Generate the second-platform multimodal Q&A demo bundle set."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


DEFAULT_OUTPUT = Path("showcase_data/demo2/multimodal")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate second-platform multimodal Q&A demo bundles."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bundle-count", type=int, default=14)
    parser.add_argument("--days", type=int, default=540)
    parser.add_argument("--comparators", type=int, default=520)
    parser.add_argument("--pdfs-per-bundle", type=int, default=42)
    parser.add_argument("--kb-docs-per-bundle", type=int, default=30)
    parser.add_argument("--seed", type=int, default=260707)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--patient-prefix", default="PT-N")
    args = parser.parse_args()
    from scripts.generate_multimodal_patient_showcase import generate

    manifest = generate(
        args.output,
        args.bundle_count,
        args.days,
        args.comparators,
        args.seed,
        args.pdfs_per_bundle,
        args.kb_docs_per_bundle,
        args.template,
        "demo2",
        args.patient_prefix,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "bundle_count": manifest["bundle_count"],
                "pdf_count": manifest["pdf_count"],
                "knowledge_base_document_count": manifest[
                    "knowledge_base_document_count"
                ],
                "demo_platform": "demo2",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
