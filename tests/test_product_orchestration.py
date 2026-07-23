"""Contract tests for clinician-facing production workflow boundaries."""

from capstone_agent import orchestration
from capstone_agent.tools import (
    approve_sql_preview,
    execute_approved_clinical_query,
    extract_clinical_text,
    persist_extraction_relational,
    persist_extraction_vector,
    transition_extraction_review,
    validate_qa_request,
)


def test_extraction_pipeline_stops_at_external_human_review():
    """Autonomous extraction cannot impersonate a reviewer or persist data."""
    pipeline = orchestration.build_image_extraction_pipeline()
    assert [agent.name for agent in pipeline.sub_agents] == [
        "quality_assessor_agent",
        "ocr_processor_agent",
        "vision_analyzer_agent",
        "clinical_structuring_agent",
        "validation_gate",
        "clinical_review_request_agent",
    ]
    assert pipeline.sub_agents[-1].tools == []


def test_ocr_returns_stable_receipt():
    """OCR contract is deterministic for the same source operation."""
    args = ("gs://clinical-data/PT-8829/image.png", "PT-8829", "SES-8829-001")
    first = extract_clinical_text(*args)
    second = extract_clinical_text(*args)
    assert first["status"] == "success"
    assert first["data"]["ocr_receipt"] == second["data"]["ocr_receipt"]


def test_only_approved_review_receipt_unlocks_persistence():
    """Rejected extraction cannot enter relational or vector stores."""
    rejected = transition_extraction_review(
        "PT-8829", "SES-8829-001", "needs_review", "reject", "clinician-1"
    )
    blocked = persist_extraction_relational(
        "PT-8829", "SES-8829-001", "{}", rejected["data"]["review_receipt"]
    )
    approved = transition_extraction_review(
        "PT-8829", "SES-8829-001", "needs_review", "approve", "clinician-1"
    )
    relational = persist_extraction_relational(
        "PT-8829", "SES-8829-001", "{}", approved["data"]["review_receipt"]
    )
    vector = persist_extraction_vector(
        "PT-8829", "SES-8829-001", "{}", approved["data"]["review_receipt"]
    )
    assert blocked["error_code"] == "REVIEW_APPROVAL_REQUIRED"
    assert relational["data"]["target"] == "relational"
    assert vector["data"]["target"] == "vector"


def test_review_transition_cannot_be_replayed_from_terminal_state():
    """Terminal review states reject later transitions."""
    result = transition_extraction_review(
        "PT-8829", "SES-8829-001", "approved", "reject", "clinician-1"
    )
    assert result["error_code"] == "INVALID_REVIEW_TRANSITION"


def test_qa_pipeline_starts_with_explicit_request_validation():
    """Q&A never retrieves evidence before validating patient scope."""
    pipeline = orchestration.build_patient_qa_pipeline()
    assert pipeline.sub_agents[0].name == "qa_request_validation_agent"
    assert pipeline.sub_agents[-1].name == "qa_response_agent"
    valid = validate_qa_request("PT-8829", "What changed in recent imaging?")
    invalid = validate_qa_request("PT-8829", "What changed?", "email")
    assert valid["status"] == "success"
    assert invalid["error_code"] == "INVALID_SOURCE_TYPES"


def test_db_pipeline_has_preview_approval_before_execution():
    """Database construction places explicit approval before executor."""
    pipeline = orchestration.build_db_intelligence_pipeline()
    names = [agent.name for agent in pipeline.sub_agents]
    assert names.index("sql_preview_approval_agent") < names.index(
        "query_executor_agent"
    )


def test_sql_execution_requires_receipt_for_exact_preview():
    """Approval for one SQL preview cannot authorize a different query."""
    approved_sql = "SELECT * FROM patients_core"
    approval = approve_sql_preview(approved_sql, "clinician-1")
    receipt = approval["data"]["approval_receipt"]
    success = execute_approved_clinical_query(approved_sql, receipt)
    mismatch = execute_approved_clinical_query(
        "SELECT * FROM clinical_sessions", receipt
    )
    assert success["status"] == "success"
    assert mismatch["error_code"] == "SQL_APPROVAL_REQUIRED"


def test_unsafe_sql_cannot_receive_approval():
    """Mutation SQL is blocked at preview approval boundary."""
    result = approve_sql_preview("DROP TABLE patients_core", "clinician-1")
    assert result["error_code"] == "UNSAFE_SQL"
