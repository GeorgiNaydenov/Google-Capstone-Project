"""Clinical tool integration tests — mock data consistency and HITL.

Validates that mock data fixtures are internally consistent, that
cross-module references resolve correctly, and that the HITL
clinical review tool behaves correctly for all three paths.
"""

import json

import pytest

from capstone_agent import mock_data
from capstone_agent.clinical_schemas import (
    ALLOWED_TABLES,
    execute_query,
    get_schema,
    validate_sql,
)
from capstone_agent.human_in_the_loop import (
    BULK_RECORD_THRESHOLD,
    CONFIDENCE_THRESHOLD,
    request_sensitive_action,
)


# ---------------------------------------------------------------------------
# Mock data consistency
# ---------------------------------------------------------------------------

class TestMockDataConsistency:
    """Ensures fixture data is internally consistent for reliable demos."""

    def test_all_patients_retrievable(self):
        patients = mock_data.get_all_patients()
        assert len(patients) >= 4
        for p in patients:
            assert "patient_id" in p
            assert "name" in p
            assert mock_data.get_patient(p["patient_id"]) is not None

    def test_patient_ids_are_unique(self):
        patients = mock_data.get_all_patients()
        ids = [p["patient_id"] for p in patients]
        assert len(ids) == len(set(ids))

    def test_sessions_reference_valid_patients(self):
        for patient_id, sessions in mock_data.SESSIONS.items():
            assert mock_data.get_patient(patient_id) is not None, (
                f"Sessions key references unknown patient {patient_id}"
            )
            for session in sessions:
                assert session["patient_id"] == patient_id

    def test_clinical_notes_reference_valid_patients(self):
        for patient_id, notes in mock_data.CLINICAL_NOTES.items():
            assert mock_data.get_patient(patient_id) is not None, (
                f"Notes key references unknown patient {patient_id}"
            )
            assert len(notes) > 0
            assert "note_id" in notes[0]

    def test_lab_results_reference_valid_patients(self):
        for patient_id, labs in mock_data.LAB_RESULTS.items():
            assert mock_data.get_patient(patient_id) is not None, (
                f"Labs key references unknown patient {patient_id}"
            )
            assert len(labs) > 0
            assert "test" in labs[0]

    def test_vector_chunks_have_required_fields(self):
        for chunk in mock_data.VECTOR_CHUNKS:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "patient_id" in chunk

    def test_image_quality_db_has_entries(self):
        assert len(mock_data.IMAGE_QUALITY_DB) > 0
        for uri, meta in mock_data.IMAGE_QUALITY_DB.items():
            assert uri.startswith("gs://")
            assert "quality_score" in meta

    def test_search_vectors_returns_results(self):
        results = mock_data.search_vectors("hepatic lesion", "PT-8829")
        assert isinstance(results, list)

    def test_search_vectors_filters_by_patient(self):
        results = mock_data.search_vectors("depression", "PT-5510")
        for r in results:
            assert r["patient_id"] == "PT-5510"

    def test_get_nonexistent_patient_returns_none(self):
        assert mock_data.get_patient("PT-NONEXISTENT") is None

    def test_get_sessions_empty_for_unknown_patient(self):
        sessions = mock_data.get_sessions("PT-NONEXISTENT")
        assert sessions == []


# ---------------------------------------------------------------------------
# Clinical schemas
# ---------------------------------------------------------------------------

class TestClinicalSchemas:
    def test_get_schema_all_returns_full_ddl(self):
        schema = get_schema("all")
        assert "patients_core" in schema
        assert "CREATE TABLE" in schema

    def test_get_schema_specific_table(self):
        schema = get_schema("patients_core")
        assert "patients_core" in schema

    def test_get_schema_unknown_table(self):
        schema = get_schema("nonexistent_table")
        assert "No schemas found" in schema

    def test_allowed_tables_populated(self):
        assert "patients_core" in ALLOWED_TABLES
        assert "sessions" in ALLOWED_TABLES

    def test_validate_sql_safe_select(self):
        result = validate_sql("SELECT * FROM patients_core")
        assert result["safe"] is True

    def test_validate_sql_blocks_drop(self):
        result = validate_sql("DROP TABLE patients_core")
        assert result["safe"] is False
        assert "select" in result["reason"].lower() or "blocked" in result["reason"].lower()

    def test_validate_sql_blocks_insert(self):
        result = validate_sql("INSERT INTO patients_core VALUES (1, 'test')")
        assert result["safe"] is False

    def test_validate_sql_blocks_update(self):
        result = validate_sql("UPDATE patients_core SET name='x' WHERE id=1")
        assert result["safe"] is False

    def test_validate_sql_blocks_system_catalog(self):
        result = validate_sql("SELECT * FROM information_schema.tables")
        assert result["safe"] is False

    def test_validate_sql_blocks_unrecognized_table(self):
        result = validate_sql("SELECT * FROM secret_data")
        assert result["safe"] is False

    def test_execute_query_count_by_risk(self):
        result = execute_query("SELECT risk_level, count(*) FROM patients_core GROUP BY risk_level")
        assert "rows" in result
        assert len(result["rows"]) > 0

    def test_execute_query_returns_columns(self):
        result = execute_query("SELECT risk_level, count(*) FROM patients_core GROUP BY risk_level")
        assert "columns" in result


# ---------------------------------------------------------------------------
# Human-in-the-loop clinical review
# ---------------------------------------------------------------------------

class TestHumanInTheLoop:
    def test_auto_approve_high_confidence(self):
        result = request_sensitive_action(
            action_type="extraction_review",
            patient_id="PT-8829",
            details="Field extraction complete",
            confidence=0.95,
            affected_records=1,
        )
        assert result["status"] == "approved"

    def test_pending_review_low_confidence(self):
        result = request_sensitive_action(
            action_type="extraction_review",
            patient_id="PT-8829",
            details="Low confidence on lesion measurement",
            confidence=0.60,
            affected_records=1,
        )
        assert result["status"] == "pending_review"

    def test_pending_review_bulk_modification(self):
        result = request_sensitive_action(
            action_type="bulk_modification",
            patient_id="PT-8829",
            details="Updating 10 patient records",
            confidence=1.0,
            affected_records=10,
        )
        assert result["status"] == "pending_review"

    def test_pending_review_treatment_data_change(self):
        result = request_sensitive_action(
            action_type="treatment_data_change",
            patient_id="PT-1044",
            details="Modifying medication dosage",
            confidence=0.99,
            affected_records=1,
        )
        assert result["status"] == "pending_review"

    def test_auto_approve_routine_action(self):
        result = request_sensitive_action(
            action_type="routine_query",
            patient_id="PT-5510",
            details="Read-only patient lookup",
            confidence=0.99,
            affected_records=1,
        )
        assert result["status"] == "approved"

    def test_confidence_threshold_boundary(self):
        at_threshold = request_sensitive_action(
            action_type="extraction_review",
            patient_id="PT-8829",
            details="Exactly at threshold",
            confidence=CONFIDENCE_THRESHOLD,
            affected_records=1,
        )
        assert at_threshold["status"] == "approved"

        below_threshold = request_sensitive_action(
            action_type="extraction_review",
            patient_id="PT-8829",
            details="Just below threshold",
            confidence=CONFIDENCE_THRESHOLD - 0.01,
            affected_records=1,
        )
        assert below_threshold["status"] == "pending_review"

    def test_bulk_threshold_boundary(self):
        at_threshold = request_sensitive_action(
            action_type="routine_query",
            patient_id="PT-8829",
            details="At bulk limit",
            confidence=1.0,
            affected_records=BULK_RECORD_THRESHOLD,
        )
        assert at_threshold["status"] == "approved"

        above_threshold = request_sensitive_action(
            action_type="routine_query",
            patient_id="PT-8829",
            details="Above bulk limit",
            confidence=1.0,
            affected_records=BULK_RECORD_THRESHOLD + 1,
        )
        assert above_threshold["status"] == "pending_review"

    def test_result_includes_patient_id(self):
        result = request_sensitive_action(
            action_type="extraction_review",
            patient_id="PT-1044",
            details="test",
            confidence=0.99,
        )
        assert result["patient_id"] == "PT-1044"

    def test_result_includes_action_type(self):
        result = request_sensitive_action(
            action_type="extraction_review",
            patient_id="PT-8829",
            details="test",
            confidence=0.99,
        )
        assert result["action_type"] == "extraction_review"
