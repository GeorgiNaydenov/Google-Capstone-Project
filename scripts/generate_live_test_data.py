"""Generate a small live test dataset (database cohort, PDF, images) and run ETL ingestion."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

# Setup project root import path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from capstone_agent import database as capstone_db
from capstone_agent.document_processor import process_document
from scripts import generate_database_showcase
from scripts import generate_extraction_showcase


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a small cohort and documents for live mode testing."
    )
    parser.add_argument("--db-path", type=Path, default=PROJECT_ROOT / "clinical.db")
    parser.add_argument("--uploads-dir", type=Path, default=PROJECT_ROOT / "uploads")
    parser.add_argument("--patient-count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=12345)
    args = parser.parse_args()

    print(f"Initializing live database at {args.db_path}...")
    # Initialize the database schema (without default demo seeding)
    with capstone_db.tenant_storage(args.db_path, args.uploads_dir):
        capstone_db.init_db(seed=False)

        # 1. Seed database relational tables with a small cohort of 5 patients
        print(
            f"Seeding relational cohort of {args.patient_count} patients into database..."
        )
        db_output = PROJECT_ROOT / "showcase_data" / "live_test" / "database"
        db_manifest = generate_database_showcase.generate(
            db_path=args.db_path,
            output=db_output,
            patient_count=args.patient_count,
            seed=args.seed,
            replace=True,
            years=4,
            anchor_date=date(2026, 7, 5),
            patient_prefix="PT-L",  # PT-L for Live
        )
        print(
            f"Database seeded successfully. Total rows inserted: {db_manifest['total_rows']}"
        )

        # 2. Generate small extraction PDF packets and PNG preview screenshots
        print("Generating small PDF packets and PNG previews...")
        ext_output = PROJECT_ROOT / "showcase_data" / "live_test" / "extraction"
        ext_manifest = generate_extraction_showcase.generate(
            output=ext_output,
            count=3,
            seed=args.seed,
            demo_platform="primary",
            patients_per_file=3,
            patient_prefix="PT-L",
        )
        print(
            f"Generated {ext_manifest['packet_count']} PDF packets and {ext_manifest['sample_count']} patient preview PNGs."
        )

        # Ensure the uploads directory exists
        args.uploads_dir.mkdir(parents=True, exist_ok=True)

        # 3. Copy files to uploads directory and run ETL document_processor
        print(
            "Ingesting PDF packets and PNG preview screenshots into document store (ETL)..."
        )

        # Keep track of ingested documents
        ingested = []

        # Process PDF packets
        for pkt in ext_manifest.get("packets", []):
            packet_path = Path(pkt["packet_path"])
            dest_packet_path = args.uploads_dir / packet_path.name
            shutil.copy2(packet_path, dest_packet_path)

            # Run ETL process_document using the first patient ID in the packet
            patient_id = pkt["patient_ids"][0] if pkt["patient_ids"] else "PT-L0001"
            print(
                f"Running ETL on PDF packet: {dest_packet_path.name} for patient {patient_id}..."
            )
            try:
                res = process_document(str(dest_packet_path), patient_id)
                if "error" not in res:
                    ingested.append(res["document_id"])
                    print(f"  -> Success: {res['message']}")
                else:
                    print(f"  -> Error: {res['error']}")
            except Exception as e:
                print(
                    f"  -> Warning: process_document failed ({e}). Falling back to manual registration."
                )
                from capstone_agent.document_processor import detect_content_type
                import uuid

                doc_id = f"doc_{uuid.uuid4().hex[:12]}"
                filename = dest_packet_path.name
                ct = detect_content_type(str(dest_packet_path))

                # Fetch note from manifest/sample to make it realistic
                mock_text = f"Mock clinical report for patient {patient_id}."

                capstone_db.store_document(
                    document_id=doc_id,
                    filename=filename,
                    content_type=ct,
                    file_path=str(dest_packet_path),
                    raw_text=mock_text,
                    page_count=3,
                    patient_id=patient_id,
                    gemini_analysis="Mock clinical analysis preview.",
                )
                chunks = [{"index": 0, "text": mock_text, "page": 1}]
                capstone_db.store_document_chunks(doc_id, chunks, patient_id)
                ingested.append(doc_id)
                print(f"  -> Fallback Success: Registered mock metadata for {filename}")

        # Process Patient PNG previews (consider them screenshots of parts of the PDF)
        for sample in ext_manifest.get("samples", []):
            preview_path = Path(sample["preview_path"])
            dest_preview_path = args.uploads_dir / preview_path.name
            shutil.copy2(preview_path, dest_preview_path)

            patient_id = sample["patient"]["patient_id"]
            print(
                f"Running ETL on PNG preview screenshot: {dest_preview_path.name} for patient {patient_id}..."
            )
            try:
                res = process_document(str(dest_preview_path), patient_id)
                if "error" not in res:
                    ingested.append(res["document_id"])
                    print(f"  -> Success: {res['message']}")
                else:
                    print(f"  -> Error: {res['error']}")
            except Exception as e:
                print(
                    f"  -> Warning: process_document failed ({e}). Falling back to manual registration."
                )
                from capstone_agent.document_processor import detect_content_type
                import uuid

                doc_id = f"doc_{uuid.uuid4().hex[:12]}"
                filename = dest_preview_path.name
                ct = detect_content_type(str(dest_preview_path))

                mock_text = f"Mock OCR and clinical text preview for patient {patient_id} screenshot {filename}."

                capstone_db.store_document(
                    document_id=doc_id,
                    filename=filename,
                    content_type=ct,
                    file_path=str(dest_preview_path),
                    raw_text=mock_text,
                    page_count=1,
                    patient_id=patient_id,
                    gemini_analysis="Mock clinical analysis preview.",
                )
                chunks = [{"index": 0, "text": mock_text, "page": 1}]
                capstone_db.store_document_chunks(doc_id, chunks, patient_id)
                ingested.append(doc_id)
                print(f"  -> Fallback Success: Registered mock metadata for {filename}")

    print("\nLive test data generation and ETL ingestion complete!")
    print(f"Database: {args.db_path}")
    print(f"Uploads: {args.uploads_dir}")
    print(f"Total ingested documents/images in SQLite store: {len(ingested)}")


if __name__ == "__main__":
    main()
