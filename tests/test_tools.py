"""Clinical tool validation tests — ensures consistent I/O contracts.

Tests Pydantic input validation, structured error responses,
and successful tool response format across all clinical tools.
No API key required — these test pure functions and mock data.
"""

import json

import pytest

from capstone_agent.models import (
    AuditEventInput,
    AuditTrailInput,
    ChartSpecInput,
    CitationBuildInput,
    ClinicalAnswerInput,
    ClinicalImageInput,
    GcsFetchInput,
    GcsStoreInput,
    ClinicalNotesSearchInput,
    ImageQualityInput,
    ImagingEvidenceInput,
    MemorySaveInput,
    MultiImageAnalysisInput,
    PatientRecordInput,
    ReviewFlagInput,
    SchemaInput,
    SqlExecutionInput,
    SqlGenerationInput,
    SqlValidationInput,
    StructuringInput,
    ToolError,
    ToolResponse,
    VectorSearchInput,
)
from capstone_agent.tools import (
    assess_image_quality,
    analyze_clinical_image,
    structure_clinical_findings,
    store_to_gcs,
    flag_for_review,
    lookup_patient_record,
    search_clinical_notes,
    search_vector_store,
    retrieve_imaging_evidence,
    fetch_image_from_gcs,
    analyze_evidence_images,
    build_citations,
    compose_clinical_answer,
    save_qa_to_memory,
    get_database_schema,
    generate_sql,
    validate_sql_safety,
    execute_clinical_query,
    generate_chart_spec,
    save_query_to_memory,
    log_audit_event,
    get_audit_trail,
)


# ---------------------------------------------------------------------------
# Output contract tests
# ---------------------------------------------------------------------------

class TestOutputContracts:
    def test_tool_response_format(self):
        resp = ToolResponse(message="Done", data={"key": "value"})
        d = resp.to_dict()
        assert d["status"] == "success"
        assert d["message"] == "Done"
        assert d["data"]["key"] == "value"

    def test_tool_error_format(self):
        err = ToolError(error_code="TEST_ERROR", message="Something broke")
        d = err.to_dict()
        assert d["status"] == "error"
        assert d["error_code"] == "TEST_ERROR"
        assert d["message"] == "Something broke"

    def test_tool_response_excludes_none_data(self):
        resp = ToolResponse(message="No data")
        d = resp.to_dict()
        assert "data" not in d


# ---------------------------------------------------------------------------
# Image Extraction Pipeline — Pydantic input validation
# ---------------------------------------------------------------------------

class TestImageExtractionInputs:
    def test_image_quality_input_valid(self):
        inp = ImageQualityInput(image_uri="gs://bucket/img.png", patient_id="PT-8829")
        assert inp.image_uri == "gs://bucket/img.png"

    def test_image_quality_input_empty_uri_rejected(self):
        with pytest.raises(Exception):
            ImageQualityInput(image_uri="", patient_id="PT-8829")

    def test_image_quality_input_empty_patient_rejected(self):
        with pytest.raises(Exception):
            ImageQualityInput(image_uri="gs://bucket/img.png", patient_id="")

    def test_clinical_image_input_valid(self):
        inp = ClinicalImageInput(image_uri="gs://x/y.png", quality_report="passed")
        assert inp.quality_report == "passed"

    def test_structuring_input_valid(self):
        inp = StructuringInput(vision_findings="findings text", patient_id="PT-1044")
        assert inp.patient_id == "PT-1044"

    def test_gcs_store_input_valid(self):
        inp = GcsStoreInput(patient_id="PT-8829", session_id="S-001", data='{"a":1}')
        assert inp.content_type == "application/json"

    def test_review_flag_input_valid(self):
        inp = ReviewFlagInput(field_name="lesion_size", value="3.5cm", confidence=0.65)
        assert inp.confidence == 0.65

    def test_review_flag_confidence_out_of_range(self):
        with pytest.raises(Exception):
            ReviewFlagInput(field_name="test", value="x", confidence=1.5)


# ---------------------------------------------------------------------------
# Patient Q&A Pipeline — Pydantic input validation
# ---------------------------------------------------------------------------

class TestPatientQAInputs:
    def test_patient_record_input_valid(self):
        inp = PatientRecordInput(patient_id="PT-8829")
        assert inp.patient_id == "PT-8829"

    def test_patient_record_input_empty_rejected(self):
        with pytest.raises(Exception):
            PatientRecordInput(patient_id="")

    def test_clinical_notes_search_valid(self):
        inp = ClinicalNotesSearchInput(patient_id="PT-8829", query="hepatic lesion")
        assert inp.date_range_days == 180

    def test_clinical_notes_search_long_query_rejected(self):
        with pytest.raises(Exception):
            ClinicalNotesSearchInput(patient_id="PT-8829", query="x" * 2001)

    def test_vector_search_input_valid(self):
        inp = VectorSearchInput(query="progression", patient_id="PT-8829")
        assert inp.source_types == "all"

    def test_gcs_fetch_input_valid(self):
        inp = GcsFetchInput(gcs_uri="gs://clinical/PT-8829/img.png")
        assert "gs://" in inp.gcs_uri

    def test_multi_image_analysis_input_valid(self):
        inp = MultiImageAnalysisInput(
            image_uris="gs://a/1.png,gs://a/2.png",
            clinical_question="progression?"
        )
        assert "," in inp.image_uris

    def test_citation_build_input_valid(self):
        inp = CitationBuildInput(evidence_items='[{"type":"text"}]')
        assert inp.evidence_items

    def test_memory_save_input_valid(self):
        inp = MemorySaveInput(question="What labs?", answer_summary="Normal range")
        assert inp.patient_id == ""


# ---------------------------------------------------------------------------
# DB Intelligence Pipeline — Pydantic input validation
# ---------------------------------------------------------------------------

class TestDBIntelligenceInputs:
    def test_schema_input_default(self):
        inp = SchemaInput()
        assert inp.tables == "all"

    def test_sql_generation_input_valid(self):
        inp = SqlGenerationInput(question="count patients", schema_context="CREATE TABLE...")
        assert inp.question == "count patients"

    def test_sql_validation_input_valid(self):
        inp = SqlValidationInput(sql="SELECT * FROM patients_core")
        assert "SELECT" in inp.sql

    def test_sql_validation_input_empty_rejected(self):
        with pytest.raises(Exception):
            SqlValidationInput(sql="")

    def test_sql_execution_input_valid(self):
        inp = SqlExecutionInput(sql="SELECT count(*) FROM patients_core")
        assert inp.sql

    def test_chart_spec_input_valid(self):
        inp = ChartSpecInput(query_results='{"rows":[]}', question="trend?")
        assert inp.question == "trend?"


# ---------------------------------------------------------------------------
# Audit — Pydantic input validation
# ---------------------------------------------------------------------------

class TestAuditInputs:
    def test_audit_event_input_valid(self):
        inp = AuditEventInput(agent_name="qa_audit", action="query")
        assert inp.patient_id == ""

    def test_audit_event_input_empty_agent_rejected(self):
        with pytest.raises(Exception):
            AuditEventInput(agent_name="", action="query")

    def test_audit_trail_input_valid(self):
        inp = AuditTrailInput(patient_id="PT-8829")
        assert inp.limit == 20

    def test_audit_trail_limit_bounds(self):
        with pytest.raises(Exception):
            AuditTrailInput(patient_id="PT-8829", limit=0)


# ---------------------------------------------------------------------------
# Image Extraction Pipeline — tool function tests
# ---------------------------------------------------------------------------

class TestImageExtractionTools:
    def test_assess_image_quality_valid(self):
        result = assess_image_quality("gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-chest-axial.png", "PT-8829")
        assert result["status"] == "success"
        assert "data" in result
        assert "quality_score" in result["data"]

    def test_assess_image_quality_empty_uri(self):
        result = assess_image_quality("", "PT-8829")
        assert result["status"] == "error"
        assert result["error_code"] == "VALIDATION_ERROR"

    def test_assess_image_quality_unknown_image(self):
        result = assess_image_quality("gs://unknown/img.png", "PT-8829")
        assert result["status"] == "error"
        assert result["error_code"] == "IMAGE_NOT_FOUND"

    def test_analyze_clinical_image_valid(self):
        result = analyze_clinical_image("gs://clinical/PT-8829/session-3/ct-abdomen.png", "quality: passed")
        assert result["status"] == "success"
        assert "data" in result

    def test_analyze_clinical_image_empty_uri(self):
        result = analyze_clinical_image("", "quality: passed")
        assert result["status"] == "error"

    def test_structure_clinical_findings_valid(self):
        result = structure_clinical_findings("findings: mass in RUL", "PT-8829")
        assert result["status"] == "success"
        assert "data" in result
        assert "fields" in result["data"]

    def test_store_to_gcs_valid(self):
        result = store_to_gcs("PT-8829", "S-001", '{"test": true}')
        assert result["status"] == "success"
        assert "storage_uri" in result["data"] or "gcs_uri" in result["data"]

    def test_store_to_gcs_empty_data(self):
        result = store_to_gcs("PT-8829", "S-001", "")
        assert result["status"] == "error"

    def test_flag_for_review_valid(self):
        result = flag_for_review("lesion_size", "3.5cm", 0.65)
        assert result["status"] == "success"
        assert "flagged" in result["message"].lower() or "review" in result["message"].lower()

    def test_flag_for_review_high_confidence(self):
        result = flag_for_review("modality", "CT", 0.98)
        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# Patient Q&A Pipeline — tool function tests
# ---------------------------------------------------------------------------

class TestPatientQATools:
    def test_lookup_patient_record_exists(self):
        result = lookup_patient_record("PT-8829")
        assert result["status"] == "success"
        assert result["data"]["patient_id"] == "PT-8829"

    def test_lookup_patient_record_not_found(self):
        result = lookup_patient_record("PT-XXXX")
        assert result["status"] == "error"
        assert result["error_code"] == "PATIENT_NOT_FOUND"

    def test_lookup_patient_record_empty_id(self):
        result = lookup_patient_record("")
        assert result["status"] == "error"
        assert result["error_code"] == "VALIDATION_ERROR"

    def test_search_clinical_notes_valid(self):
        result = search_clinical_notes("PT-8829", "hepatic lesion")
        assert result["status"] == "success"
        assert "data" in result

    def test_search_clinical_notes_empty_query(self):
        result = search_clinical_notes("PT-8829", "")
        assert result["status"] == "error"

    def test_search_vector_store_valid(self):
        result = search_vector_store("hepatic progression", "PT-8829")
        assert result["status"] == "success"
        assert "results" in result["data"]

    def test_retrieve_imaging_evidence_valid(self):
        result = retrieve_imaging_evidence("PT-8829", "CT abdomen")
        assert result["status"] == "success"

    def test_fetch_image_from_gcs_valid(self):
        result = fetch_image_from_gcs("gs://clinical/PT-8829/session-3/ct-abdomen.png")
        assert result["status"] == "success"
        assert "gcs_uri" in result["data"]

    def test_fetch_image_from_gcs_empty_uri(self):
        result = fetch_image_from_gcs("")
        assert result["status"] == "error"

    def test_analyze_evidence_images_single(self):
        result = analyze_evidence_images(
            "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-chest-axial.png",
            "Any progression?"
        )
        assert result["status"] == "success"
        assert "per_image_analysis" in result["data"]

    def test_analyze_evidence_images_multiple(self):
        uris = "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-chest-axial.png,gs://clinical-data/PT-8829/sessions/SES-8829-002/ct-chest-axial.png"
        result = analyze_evidence_images(uris, "Compare lesion sizes")
        assert result["status"] == "success"
        assert "comparison_notes" in result["data"]

    def test_build_citations_valid(self):
        items = json.dumps([
            {"source_type": "text", "source_id": "note-1", "date": "2026-06-15",
             "text": "Findings text", "relevance_score": 0.9},
        ])
        result = build_citations(items)
        assert result["status"] == "success"
        assert "citations" in result["data"]

    def test_build_citations_invalid_json(self):
        result = build_citations("not valid json")
        assert result["status"] == "error"

    def test_compose_clinical_answer_valid(self):
        result = compose_clinical_answer(
            question="Is there progression?",
            patient_context="PT-8829, NSCLC, high risk",
            evidence="text evidence here",
            image_analysis="CT shows growth",
            citations="[1] CT scan, [2] Radiology note"
        )
        assert result["status"] == "success"
        assert "answer" in result["data"]
        assert "confidence" in result["data"]

    def test_save_qa_to_memory_valid(self):
        result = save_qa_to_memory("PT-8829", "What is the status?", "Stable condition")
        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# DB Intelligence Pipeline — tool function tests
# ---------------------------------------------------------------------------

class TestDBIntelligenceTools:
    def test_get_database_schema_all(self):
        result = get_database_schema()
        assert result["status"] == "success"
        assert "schema_ddl" in result["data"]

    def test_get_database_schema_specific_table(self):
        result = get_database_schema("patients_core")
        assert result["status"] == "success"

    def test_generate_sql_valid(self):
        result = generate_sql("count patients by risk", "CREATE TABLE patients_core...")
        assert result["status"] == "success"
        assert result["data"]["schema_loaded"] is True

    def test_generate_sql_empty_question(self):
        result = generate_sql("", "schema")
        assert result["status"] == "error"

    def test_validate_sql_safety_safe_query(self):
        result = validate_sql_safety("SELECT count(*) FROM patients_core WHERE risk_level = 'high'")
        assert result["status"] == "success"
        assert result["data"]["safe"] is True

    def test_validate_sql_safety_blocks_mutation(self):
        result = validate_sql_safety("DROP TABLE patients_core")
        assert result["status"] == "success"
        assert result["data"]["safe"] is False

    def test_validate_sql_safety_blocks_delete(self):
        result = validate_sql_safety("DELETE FROM patients_core WHERE id = 1")
        assert result["status"] == "success"
        assert result["data"]["safe"] is False

    def test_validate_sql_safety_empty_sql(self):
        result = validate_sql_safety("")
        assert result["status"] == "error"

    def test_execute_clinical_query_valid(self):
        result = execute_clinical_query("SELECT count(*) as cnt FROM patients_core WHERE risk_level = 'high'")
        assert result["status"] == "success"
        assert "rows" in result["data"]

    def test_execute_clinical_query_unrecognized_pattern(self):
        result = execute_clinical_query("SELECT * FROM unknown_table_xyz")
        assert result["status"] == "error"
        assert result["error_code"] == "QUERY_EXECUTION_ERROR"

    def test_generate_chart_spec_valid(self):
        query_results = json.dumps({
            "columns": ["risk_level", "count"],
            "rows": [{"risk_level": "high", "count": 2}, {"risk_level": "stable", "count": 1}],
            "row_count": 2
        })
        result = generate_chart_spec(query_results, "Patient risk distribution")
        assert result["status"] == "success"
        assert "chart_spec" in result["data"]
        assert "chart_type" in result["data"]["chart_spec"]

    def test_generate_chart_spec_bad_json_still_succeeds(self):
        result = generate_chart_spec("not json", "question")
        assert result["status"] == "success"

    def test_save_query_to_memory_valid(self):
        result = save_query_to_memory("count high risk", "SELECT...", "Found 2 patients")
        assert result["status"] == "success"


# ---------------------------------------------------------------------------
# Shared / Audit tools
# ---------------------------------------------------------------------------

class TestAuditTools:
    def test_log_audit_event_valid(self):
        result = log_audit_event("qa_audit", "patient_query", "PT-8829")
        assert result["status"] == "success"
        assert "timestamp" in result["data"]

    def test_log_audit_event_empty_agent(self):
        result = log_audit_event("", "query")
        assert result["status"] == "error"

    def test_log_audit_event_no_patient_id(self):
        result = log_audit_event("system", "startup")
        assert result["status"] == "success"

    def test_get_audit_trail_valid(self):
        result = get_audit_trail("PT-8829")
        assert result["status"] == "success"
        assert "events" in result["data"]

    def test_get_audit_trail_empty_patient(self):
        result = get_audit_trail("")
        assert result["status"] == "error"
