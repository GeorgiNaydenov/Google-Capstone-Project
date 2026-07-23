"""Smoke tests for showcase data generators."""

from datetime import date
import json
from pathlib import Path
import sqlite3

import pytest


def test_extraction_generator_creates_uploadable_pdf_packets(tmp_path: Path) -> None:
    """Extraction showcase emits five-patient PDF packets plus visual previews."""

    pytest.importorskip("PIL")
    from scripts.generate_extraction_showcase import generate

    manifest = generate(tmp_path / "extraction", count=5, seed=7, patients_per_file=5)

    assert manifest["sample_count"] == 5
    assert manifest["packet_count"] == 1
    assert manifest["patients_per_file"] == 5
    assert manifest["upload_contract"]["contentType"] == "application/pdf"
    assert "application/pdf" in manifest["upload_contract"]["contentTypes"]
    contract = manifest["frontend_contract"]
    assert contract["dashboardSeed"]["imageExtractionsToday"] == 5
    assert contract["dashboardSeed"]["sourcePackets"] == 1
    assert contract["dashboardSeed"]["patientsPerFile"] == 5
    assert contract["storageSeed"]["relationalRows"] >= 5
    assert {row["pipeline"] for row in contract["agentMonitoringSeed"]} == {
        "extraction"
    }
    for sample in manifest["samples"]:
        assert Path(sample["asset_path"]).is_file()
        assert Path(sample["preview_path"]).is_file()
        assert sample["content_type"] == "application/pdf"
        assert sample["patient_count_in_file"] == 5
        assert sample["expected_agent_output"]["visualization"]["points"]


def test_multimodal_generator_creates_pdf_and_knowledge_base_corpus(
    tmp_path: Path,
) -> None:
    """Q&A showcase emits PDFs plus mixed-format knowledge-base upload files."""

    pytest.importorskip("matplotlib")
    from scripts.generate_multimodal_patient_showcase import KB_EXTENSIONS, generate

    manifest = generate(
        tmp_path / "multimodal",
        bundle_count=1,
        days=14,
        comparators=5,
        seed=9,
        pdfs_per_bundle=3,
        kb_docs_per_bundle=5,
    )
    bundle_path = Path(manifest["bundles"][0]["path"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert manifest["pdf_count"] == 3
    assert manifest["knowledge_base_document_count"] == 5
    assert manifest["frontend_contract"]["dashboardSeed"]["storedAssets"] == 8
    assert manifest["frontend_contract"]["dashboardSeed"]["knowledgeBaseDocuments"] == 5
    assert {
        row["pipeline"] for row in manifest["frontend_contract"]["agentMonitoringSeed"]
    } == {"qa"}
    assert {
        Path(item["path"]).suffix for item in bundle["knowledge_base_documents"]
    } == set(KB_EXTENSIONS)
    assert all(Path(item["path"]).is_file() for item in bundle["pdf_documents"])
    assert any(citation["kind"] == "document" for citation in bundle["citations"])


def test_database_generator_creates_four_year_sqlite_showcase(tmp_path: Path) -> None:
    """Database showcase emits SQLite, textual insights, SQL, Plotly, and PNG charts."""

    pytest.importorskip("matplotlib")
    from scripts.generate_database_showcase import generate

    output = tmp_path / "database"
    db_path = output / "clinical_showcase.db"
    manifest = generate(
        db_path,
        output,
        patient_count=5,
        seed=11,
        replace=True,
        years=4,
        anchor_date=date(2026, 7, 5),
    )
    queries = json.loads((output / "query_showcase.json").read_text(encoding="utf-8"))

    assert manifest["row_counts"]["patients_core"] == 5
    assert manifest["row_counts"]["patient_conditions"] >= 5
    assert manifest["row_counts"]["medications"] >= 5
    assert manifest["row_counts"]["providers"] >= 1
    assert manifest["row_counts"]["insurance_policies"] >= 5
    assert manifest["row_counts"]["appointments"] >= 5
    assert manifest["row_counts"]["immunizations"] >= 5
    assert manifest["row_counts"]["family_history"] >= 5
    assert manifest["row_counts"]["encounters"] >= manifest["row_counts"]["sessions"]
    assert manifest["row_counts"]["vital_signs"] >= manifest["row_counts"]["sessions"]
    assert (
        manifest["frontend_contract"]["storageSeed"]["relationalRows"]
        == manifest["total_rows"]
    )
    assert manifest["frontend_contract"]["dashboardSeed"]["patients"] == 5
    assert (
        manifest["frontend_contract"]["dashboardSeed"]["databaseRows"]
        == manifest["total_rows"]
    )
    assert manifest["frontend_contract"]["dashboardSeed"]["completeness"] > 0
    assert {
        row["pipeline"] for row in manifest["frontend_contract"]["agentMonitoringSeed"]
    } == {"database"}
    assert manifest["minimum_required_patients"] == 1500
    assert manifest["coverage_years"] == 4
    assert manifest["date_range"]["end"] == "2026-07-05"
    assert all(
        {"question", "sql", "insight", "plotly", "matplotlib_png"} <= set(item)
        for item in queries
    )
    assert Path(queries[0]["matplotlib_png"]).is_file()
    charted = [item["plotly"]["data"][0] for item in queries if item["plotly"]["data"]]
    assert any(
        trace["type"] == "heatmap" and trace.get("showscale") for trace in charted
    )
    assert all(trace["marker"]["color"] for trace in charted if trace["type"] == "bar")
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), MIN(session_date), MAX(session_date) FROM sessions"
        ).fetchone()
        schema_tables = {
            item[0]
            for item in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert row[0] == manifest["row_counts"]["sessions"]
    assert row[1] <= "2022-07-10"
    assert row[2] <= "2026-07-05"
    assert {
        "patient_conditions",
        "medications",
        "vital_signs",
        "care_gaps",
        "social_determinants",
        "insurance_policies",
        "appointments",
        "immunizations",
        "family_history",
    } <= schema_tables


def test_generated_showcase_dataset_drives_demo_dashboard_stats(tmp_path: Path) -> None:
    """Product loader merges all generator manifests into dashboard/storage stats."""

    pytest.importorskip("PIL")
    pytest.importorskip("matplotlib")
    from scripts.generate_database_showcase import generate as generate_database
    from scripts.generate_extraction_showcase import generate as generate_extraction
    from scripts.generate_multimodal_patient_showcase import (
        generate as generate_multimodal,
    )
    from clinical_app.repository import DemoRepository, load_showcase_dataset

    base = tmp_path / "showcase"
    generate_database(
        base / "database" / "clinical_showcase.db",
        base / "database",
        patient_count=6,
        seed=21,
        replace=True,
        years=1,
        anchor_date=date(2026, 7, 5),
    )
    generate_extraction(base / "extraction", count=3, seed=22, frontend_public=None)
    generate_multimodal(
        base / "multimodal",
        bundle_count=1,
        days=7,
        comparators=3,
        seed=23,
        pdfs_per_bundle=2,
        kb_docs_per_bundle=5,
    )

    dataset = load_showcase_dataset("generated", base, notifications=[], users=[])

    assert dataset is not None
    assert dataset.dashboard_seed is not None
    assert dataset.storage_seed is not None
    assert dataset.dashboard_seed["patients"] == 6
    assert dataset.dashboard_seed["sessions"] > len(dataset.sessions)
    assert dataset.dashboard_seed["sourcePackets"] == 1
    assert dataset.dashboard_seed["patientsPerFile"] == 5
    assert (
        dataset.dashboard_seed["storedAssets"] == dataset.storage_seed["cloudObjects"]
    )
    assert dataset.storage_seed["relationalRows"] > dataset.dashboard_seed["patients"]
    assert {"database", "extraction", "qa"} <= {
        row["pipeline"] for row in dataset.monitor_baseline
    }
    repo = DemoRepository(dataset)
    extraction_uploads = [
        item for item in repo.uploads.values() if item.get("sourceUse") == "extraction"
    ]
    assert extraction_uploads and {
        item["contentType"] for item in extraction_uploads
    } == {"application/pdf"}
    assert [item["action"] for item in repo.audit] == [
        "showcase_database_loaded",
        "showcase_extraction_assets_loaded",
        "showcase_multimodal_corpus_loaded",
    ]
    # Every seeded audit event resolves to a real bootstrap run so log
    # click-through never dead-ends, and seeded runs stay out of /runs lists.
    assert {"RUN-SEED-DB", "RUN-SEED-EXT", "RUN-SEED-QA"} <= set(repo.runs)
    assert all(
        repo.runs[run_id]["seeded"] and repo.runs[run_id]["status"] == "completed"
        for run_id in ("RUN-SEED-DB", "RUN-SEED-EXT", "RUN-SEED-QA")
    )
