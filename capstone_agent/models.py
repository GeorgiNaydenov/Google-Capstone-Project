"""Pydantic models for tool input/output contracts.

Every tool in the harness returns either a ToolResponse (success) or
ToolError (failure). This gives the LLM a consistent, parseable
contract regardless of which tool was called.

ADK expects tool functions to return plain dicts, so each model
has a to_dict() method for the return value.

Design decisions:
- Pydantic validates inputs at the boundary (fail fast, clear errors).
- Consistent status/message/data structure across all tools.
- Input models per tool enforce type safety before any logic runs.
- Clinical models map to SNOMED CT, LOINC, and ICD ontologies.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Output contracts (shared by ALL tools)
# ---------------------------------------------------------------------------

class ToolResponse(BaseModel):
    """Successful tool result. All tools return this on success."""
    status: Literal["success"] = "success"
    message: str = Field(description="Human-readable summary of what happened")
    data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Structured result data, if any",
    )

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


class ToolError(BaseModel):
    """Failed tool result. All tools return this on error."""
    status: Literal["error"] = "error"
    error_code: str = Field(description="Machine-readable error category")
    message: str = Field(description="Human-readable error description")
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error context for debugging",
    )

    def to_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# Image Extraction Pipeline — input/output models
# ---------------------------------------------------------------------------

class ImageQualityInput(BaseModel):
    """Input for the assess_image_quality tool."""
    image_uri: str = Field(min_length=1, description="GCS URI of the clinical image")
    patient_id: str = Field(min_length=1, max_length=20, description="Patient identifier")


class ClinicalImageInput(BaseModel):
    """Input for the analyze_clinical_image tool."""
    image_uri: str = Field(min_length=1, description="GCS URI of the clinical image")
    quality_report: str = Field(min_length=1, description="Quality assessment from prior stage")


class StructuringInput(BaseModel):
    """Input for the structure_clinical_findings tool."""
    vision_findings: str = Field(min_length=1, description="Vision analysis from prior stage")
    patient_id: str = Field(min_length=1, max_length=20, description="Patient identifier")


class GcsStoreInput(BaseModel):
    """Input for the store_to_gcs tool."""
    patient_id: str = Field(min_length=1, max_length=20)
    session_id: str = Field(min_length=1, max_length=20)
    data: str = Field(min_length=1, description="JSON string or image bytes reference")
    content_type: str = Field(default="application/json", max_length=50)


class OcrInput(BaseModel):
    """Input for deterministic OCR metadata extraction."""
    image_uri: str = Field(min_length=1, description="GCS URI of the clinical image")
    patient_id: str = Field(min_length=1, max_length=20)
    session_id: str = Field(min_length=1, max_length=20)


class ReviewTransitionInput(BaseModel):
    """Input for a clinician-controlled extraction review transition."""
    patient_id: str = Field(min_length=1, max_length=20)
    session_id: str = Field(min_length=1, max_length=20)
    current_status: Literal["needs_review", "approved", "rejected"]
    action: Literal["approve", "reject"]
    reviewer_id: str = Field(min_length=1, max_length=100)
    reason: str = Field(default="", max_length=1000)


class ExtractionPersistenceInput(BaseModel):
    """Input for post-review relational or vector persistence."""
    patient_id: str = Field(min_length=1, max_length=20)
    session_id: str = Field(min_length=1, max_length=20)
    structured_data: str = Field(min_length=1, description="Validated JSON extraction payload")
    review_receipt: str = Field(min_length=1, max_length=200)


class ReviewFlagInput(BaseModel):
    """Input for the flag_for_review tool."""
    field_name: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractionField(BaseModel):
    """A single field extracted from a clinical image."""
    field_name: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    needs_review: bool = False
    ontology_code: Optional[str] = None


class ExtractionResult(BaseModel):
    """Complete extraction output from the image pipeline."""
    session_id: str
    patient_id: str
    fields: list[ExtractionField]
    pipeline_status: str
    review_items: list[str] = []


# ---------------------------------------------------------------------------
# Patient Q&A Pipeline — input/output models
# ---------------------------------------------------------------------------

class PatientRecordInput(BaseModel):
    """Input for the lookup_patient_record tool."""
    patient_id: str = Field(min_length=1, max_length=20)


class QARequestInput(BaseModel):
    """Validated patient-scoped clinical question request."""
    patient_id: str = Field(min_length=1, max_length=20)
    question: str = Field(min_length=3, max_length=2000)
    source_types: str = Field(default="all")
    date_range_days: int = Field(default=180, ge=1, le=3650)


class ClinicalNotesSearchInput(BaseModel):
    """Input for the search_clinical_notes tool."""
    patient_id: str = Field(min_length=1, max_length=20)
    query: str = Field(min_length=1, max_length=2000)
    date_range_days: int = Field(default=180, ge=1, le=3650)


class VectorSearchInput(BaseModel):
    """Input for the search_vector_store tool."""
    query: str = Field(min_length=1, max_length=2000)
    patient_id: str = Field(min_length=1, max_length=20)
    source_types: str = Field(default="all", description="Comma-separated: text,image,structured or 'all'")


class ImagingEvidenceInput(BaseModel):
    """Input for the retrieve_imaging_evidence tool."""
    patient_id: str = Field(min_length=1, max_length=20)
    query: str = Field(min_length=1, max_length=2000)


class GcsFetchInput(BaseModel):
    """Input for the fetch_image_from_gcs tool."""
    gcs_uri: str = Field(min_length=1, description="GCS URI starting with gs://")


class MultiImageAnalysisInput(BaseModel):
    """Input for the analyze_evidence_images tool."""
    image_uris: str = Field(min_length=1, description="Comma-separated GCS URIs")
    clinical_question: str = Field(min_length=1, max_length=2000)


class CitationBuildInput(BaseModel):
    """Input for the build_citations tool."""
    evidence_items: str = Field(min_length=1, description="JSON string of evidence items")


class ClinicalAnswerInput(BaseModel):
    """Input for the compose_clinical_answer tool."""
    question: str = Field(min_length=1, max_length=2000)
    patient_context: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    image_analysis: str = Field(min_length=1)
    citations: str = Field(min_length=1)


class MemorySaveInput(BaseModel):
    """Input for the save_qa_to_memory and save_query_to_memory tools."""
    patient_id: str = Field(default="", max_length=20)
    question: str = Field(min_length=1, max_length=2000)
    answer_summary: str = Field(min_length=1)


class EvidenceItem(BaseModel):
    """A single piece of evidence retrieved for Q&A."""
    source_type: str
    source_id: str
    date: str
    text: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    gcs_uri: Optional[str] = None


class ImageEvidence(BaseModel):
    """Image-specific evidence with analysis results."""
    gcs_uri: str
    modality: str
    description: str
    findings: str
    comparison_notes: Optional[str] = None


class CitedSource(BaseModel):
    """A numbered citation in the Q&A answer."""
    ref: int
    source_type: str
    document_name: str
    date: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    snippet: str = ""
    gcs_uri: Optional[str] = None


class QAResult(BaseModel):
    """Complete Q&A response with citations and image references."""
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[CitedSource]
    image_references: list[str] = []
    agents_used: list[str]
    recommended_action: str = ""


# ---------------------------------------------------------------------------
# DB Intelligence Pipeline — input/output models
# ---------------------------------------------------------------------------

class SchemaInput(BaseModel):
    """Input for the get_database_schema tool."""
    tables: str = Field(default="all", description="Comma-separated table names or 'all'")


class SqlGenerationInput(BaseModel):
    """Input for the generate_sql tool."""
    question: str = Field(min_length=1, max_length=1000)
    schema_context: str = Field(min_length=1)


class SqlValidationInput(BaseModel):
    """Input for the validate_sql_safety tool."""
    sql: str = Field(min_length=1, max_length=5000)


class SqlExecutionInput(BaseModel):
    """Input for the execute_clinical_query tool."""
    sql: str = Field(min_length=1, max_length=5000)


class SqlApprovalInput(BaseModel):
    """Input for approving a safe SQL preview before execution."""
    sql: str = Field(min_length=1, max_length=5000)
    approver_id: str = Field(min_length=1, max_length=100)


class ApprovedSqlExecutionInput(SqlExecutionInput):
    """Input for execution with a matching SQL approval receipt."""
    approval_receipt: str = Field(min_length=1, max_length=200)


class ChartSpecInput(BaseModel):
    """Input for the generate_chart_spec tool."""
    query_results: str = Field(min_length=1, description="JSON string of query results")
    question: str = Field(min_length=1, max_length=1000)


class VisualGenerationInput(BaseModel):
    """Input for the generate_clinical_visual tool."""
    description: str = Field(min_length=10, max_length=2000, description="What the visual should show")
    patient_id: str = Field(default="", max_length=20)
    session_id: str = Field(default="", max_length=40)


class ChartSpec(BaseModel):
    """Chart specification for frontend rendering."""
    chart_type: str
    title: str
    x_axis: str
    y_axis: str
    data: list[dict[str, Any]]
    library: str = "plotly"


class SQLResult(BaseModel):
    """Complete DB intelligence response."""
    sql: str
    is_safe: bool
    safety_reason: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    insight_summary: str = ""
    chart_spec: Optional[ChartSpec] = None


# ---------------------------------------------------------------------------
# Audit — shared across all pipelines
# ---------------------------------------------------------------------------

class AuditEventInput(BaseModel):
    """Input for the log_audit_event tool."""
    agent_name: str = Field(min_length=1, max_length=50)
    action: str = Field(min_length=1, max_length=50)
    patient_id: str = Field(default="", max_length=20)
    details: str = Field(default="{}", description="JSON string of event details")


class AuditTrailInput(BaseModel):
    """Input for the get_audit_trail tool."""
    patient_id: str = Field(min_length=1, max_length=20)
    limit: int = Field(default=20, ge=1, le=100)


class AuditEntry(BaseModel):
    """A single audit log entry."""
    timestamp: str
    agent_name: str
    action: str
    patient_id: Optional[str] = None
    details: dict[str, Any] = {}
    user_role: str = "clinician"


# ---------------------------------------------------------------------------
# Document Upload & Search — input/output models
# ---------------------------------------------------------------------------

class DocumentUploadInput(BaseModel):
    """Input for the upload_document tool."""
    file_path: str = Field(min_length=1, description="Absolute or relative path to the file to process")
    patient_id: str = Field(default="", max_length=20, description="Optional patient ID to associate with")

class DocumentSearchInput(BaseModel):
    """Input for the search_documents tool."""
    query: str = Field(min_length=1, max_length=2000, description="Search query")
    patient_id: str = Field(default="", max_length=20)
    limit: int = Field(default=20, ge=1, le=100)

class DocumentListInput(BaseModel):
    """Input for the list_documents tool."""
    patient_id: str = Field(default="", max_length=20)
    limit: int = Field(default=50, ge=1, le=100)

class GeminiAnalysisInput(BaseModel):
    """Input for running Gemini analysis on a document."""
    document_id: str = Field(min_length=1, max_length=50)
    analysis_type: str = Field(default="clinical", description="clinical | summary | qa_context")
