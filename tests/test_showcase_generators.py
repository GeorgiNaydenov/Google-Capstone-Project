"""Smoke tests for showcase data generators."""

from datetime import date
import json
from pathlib import Path
import sqlite3

import pytest


def test_extraction_generator_creates_uploadable_images(tmp_path: Path) -> None:
    """Extraction showcase emits uploadable clinical images with visual ground truth."""

    pytest.importorskip("PIL")
    from scripts.generate_extraction_showcase import generate

    manifest = generate(tmp_path / "extraction", count=2, seed=7)

    assert manifest["sample_count"] == 2
    assert manifest["upload_contract"]["contentType"] == "image/png"
    for sample in manifest["samples"]:
        assert Path(sample["asset_path"]).is_file()
        assert sample["expected_agent_output"]["visualization"]["points"]


def test_multimodal_generator_creates_pdf_and_knowledge_base_corpus(tmp_path: Path) -> None:
    """Q&A showcase emits PDFs plus mixed-format knowledge-base upload files."""

    pytest.importorskip("matplotlib")
    from scripts.generate_multimodal_patient_showcase import KB_EXTENSIONS, generate

    manifest = generate(tmp_path / "multimodal", bundle_count=1, days=14, comparators=5, seed=9, pdfs_per_bundle=3, kb_docs_per_bundle=5)
    bundle_path = Path(manifest["bundles"][0]["path"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert manifest["pdf_count"] == 3
    assert manifest["knowledge_base_document_count"] == 5
    assert {Path(item["path"]).suffix for item in bundle["knowledge_base_documents"]} == set(KB_EXTENSIONS)
    assert all(Path(item["path"]).is_file() for item in bundle["pdf_documents"])
    assert any(citation["kind"] == "document" for citation in bundle["citations"])


def test_database_generator_creates_four_year_sqlite_showcase(tmp_path: Path) -> None:
    """Database showcase emits SQLite, textual insights, SQL, Plotly, and PNG charts."""

    pytest.importorskip("matplotlib")
    from scripts.generate_database_showcase import generate

    output = tmp_path / "database"
    db_path = output / "clinical_showcase.db"
    manifest = generate(db_path, output, patient_count=5, seed=11, replace=True, years=4, anchor_date=date(2026, 7, 5))
    queries = json.loads((output / "query_showcase.json").read_text(encoding="utf-8"))

    assert manifest["row_counts"]["patients_core"] == 5
    assert manifest["minimum_required_patients"] == 10000
    assert manifest["coverage_years"] == 4
    assert manifest["date_range"]["end"] == "2026-07-05"
    assert all({"question", "sql", "insight", "plotly", "matplotlib_png"} <= set(item) for item in queries)
    assert Path(queries[0]["matplotlib_png"]).is_file()
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*), MIN(session_date), MAX(session_date) FROM sessions").fetchone()
    assert row[0] == manifest["row_counts"]["sessions"]
    assert row[1] <= "2022-07-10"
    assert row[2] <= "2026-07-05"
