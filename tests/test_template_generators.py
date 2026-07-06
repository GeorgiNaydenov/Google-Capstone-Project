"""Unit tests for template-based showcase data generators."""

from datetime import date
import json
from pathlib import Path
import sqlite3

import pytest


def test_database_generator_with_template(tmp_path: Path) -> None:
    """Database generator correctly parses template JSON and seeds SQLite tables."""
    from scripts.generate_database_showcase import generate
    
    # Create a small template
    template_data = {
        "patients_core": [
            {
                "patient_id": "PT-TEST1",
                "name": "Test Patient",
                "age": 40,
                "sex": "Female",
                "risk_level": "stable",
                "primary_diagnosis": "Diabetes",
                "assigned_clinician": "Dr. Sarah Miller",
                "last_session_date": "2026-07-05",
                "data_completeness_score": 0.90,
                "open_tasks": 0,
                "ai_review_status": "verified",
                "extended_data": {"synthetic": True, "insurance": "Medicare"}
            }
        ],
        "sessions": [
            {
                "session_id": "SES-TEST1",
                "patient_id": "PT-TEST1",
                "session_date": "2026-07-05",
                "uploaded_image_count": 1,
                "extraction_confidence": 0.95,
                "clinician_verification": "verified",
                "json_sync_status": "synced",
                "relational_sync_status": "synced",
                "vector_sync_status": "synced",
                "audit_status": "recorded"
            }
        ]
    }
    
    template_file = tmp_path / "db_template.json"
    template_file.write_text(json.dumps(template_data), encoding="utf-8")
    
    output = tmp_path / "database"
    db_path = output / "clinical_showcase.db"
    
    manifest = generate(
        db_path, output, patient_count=1, seed=42, replace=True,
        years=1, anchor_date=date(2026, 7, 5), template_path=template_file
    )
    
    assert manifest["row_counts"]["patients_core"] == 1
    assert manifest["row_counts"]["sessions"] == 1
    assert manifest["frontend_contract"]["dashboardSeed"]["databaseRows"] >= 2
    assert manifest["frontend_contract"]["storageSeed"]["relationalRows"] >= 1
    assert (output / "app_manifest.json").is_file()
    
    with sqlite3.connect(db_path) as conn:
        patient_row = conn.execute("SELECT name, risk_level, extended_data FROM patients_core WHERE patient_id = 'PT-TEST1'").fetchone()
        session_row = conn.execute("SELECT session_date, extraction_confidence FROM sessions WHERE session_id = 'SES-TEST1'").fetchone()
        
    assert patient_row[0] == "Test Patient"
    assert patient_row[1] == "stable"
    assert json.loads(patient_row[2])["insurance"] == "Medicare"
    assert session_row[0] == "2026-07-05"
    assert session_row[1] == 0.95


def test_extraction_generator_with_template(tmp_path: Path) -> None:
    """Extraction generator renders custom intake sheets and outputs ground truth from template."""
    pytest.importorskip("PIL")
    from scripts.generate_extraction_showcase import generate
    
    template_data = [
        {
            "patient": {
                "patient_id": "PT-TEST2",
                "mrn": "MRN-99999",
                "name": "Nora Jones",
                "age": 45,
                "sex": "Female",
                "diagnosis": "Aortic stenosis",
                "clinician": "Dr. Elena Park"
            },
            "encounter_date": "2026-07-05",
            "note": "Aortic valve assessment.",
            "fields": [
                {
                    "field_name": "tumor_size_cm",
                    "value": 2.5,
                    "unit": "cm",
                    "confidence": 0.98,
                    "needs_review": False
                }
            ],
            "trend_values": [2.1, 2.3, 2.5]
        }
    ]
    
    template_file = tmp_path / "extraction_template.json"
    template_file.write_text(json.dumps(template_data), encoding="utf-8")
    
    manifest = generate(tmp_path / "extraction", count=1, seed=42, template_path=template_file)
    
    assert manifest["sample_count"] == 1
    assert manifest["packet_count"] == 1
    assert manifest["patients_per_file"] == 5
    assert manifest["upload_contract"]["contentType"] == "application/pdf"
    assert manifest["frontend_contract"]["syntheticPickerCount"] == 1
    assert manifest["frontend_contract"]["dashboardSeed"]["sourceImages"] == 1
    assert manifest["frontend_contract"]["storageSeed"]["cloudObjects"] == 1
    assert (tmp_path / "extraction" / "app_manifest.json").is_file()
    sample = manifest["samples"][0]
    assert sample["patient"]["name"] == "Nora Jones"
    assert sample["fields"][0]["field_name"] == "tumor_size_cm"
    assert sample["fields"][0]["value"] == 2.5
    assert Path(sample["asset_path"]).is_file()
    assert sample["content_type"] == "application/pdf"
    assert Path(sample["preview_path"]).is_file()


def test_multimodal_generator_with_template(tmp_path: Path) -> None:
    """Multimodal generator builds bundles, custom PDFs, and knowledge-base documents from template."""
    pytest.importorskip("matplotlib")
    from scripts.generate_multimodal_patient_showcase import generate
    
    template_data = [
        {
            "patient": {
                "patient_id": "PT-TEST3",
                "name": "David Okafor",
                "age": 59,
                "sex": "Male",
                "risk_level": "high",
                "primary_diagnosis": "Retinopathy",
                "assigned_clinician": "Dr. Elena Park"
            },
            "labs": [
                {
                    "date": "2026-07-01",
                    "test": "CMP",
                    "component": "HbA1c",
                    "value": "8.4",
                    "unit": "%",
                    "reference_range": "<5.7",
                    "flag": "high"
                }
            ],
            "notes": [
                {
                    "note_id": "NOTE-TEST3",
                    "date": "2026-07-01",
                    "author": "Dr. Elena Park",
                    "type": "Consult",
                    "text": "Glycemic control progress."
                }
            ],
            "qa_prompts": [
                {
                    "question": "What is the status of David?",
                    "expected_sources": ["clinical_notes"],
                    "expected_output": "The patient is David Okafor."
                }
            ]
        }
    ]
    
    template_file = tmp_path / "multimodal_template.json"
    template_file.write_text(json.dumps(template_data), encoding="utf-8")
    
    manifest = generate(tmp_path / "multimodal", bundle_count=1, days=10, comparators=2, seed=42, template_path=template_file)
    
    assert manifest["bundle_count"] == 1
    assert manifest["frontend_contract"]["dashboardSeed"]["patients"] == 1
    assert manifest["frontend_contract"]["dashboardSeed"]["storedFiles"] >= 2
    assert manifest["frontend_contract"]["storageSeed"]["vectorRecords"] >= 1
    assert (tmp_path / "multimodal" / "app_manifest.json").is_file()
    bundle_path = Path(manifest["bundles"][0]["path"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    
    assert bundle["patient"]["name"] == "David Okafor"
    assert bundle["labs"][0]["metric"] == "HbA1c"
    assert bundle["labs"][0]["value"] == "8.4"
    assert len(bundle["pdf_documents"]) >= 1
    assert len(bundle["knowledge_base_documents"]) >= 1
    assert bundle["qa_prompts"][0]["question"] == "What is the status of David?"
