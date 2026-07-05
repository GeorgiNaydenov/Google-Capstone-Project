"""Pydantic contracts for the clinician product API."""

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from clinical_app.document import MAX_UPLOAD_BYTES


Role = Literal["clinician", "admin"]


class UploadRequest(BaseModel):
    """Metadata for a clinical file selected by a user."""

    filename: str = Field(min_length=1, max_length=255, description="Name of the file to be uploaded")
    content_type: str = Field(default="application/octet-stream", max_length=100, description="MIME content type of the file")
    size_bytes: int = Field(ge=1, le=MAX_UPLOAD_BYTES, description="File size in bytes")
    modality: str = Field(default="Document", max_length=50, description="Imaging modality or clinical report category")


class RunRequest(BaseModel):
    """Request to start deterministic extraction for uploaded evidence."""

    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(validation_alias=AliasChoices("patientId", "patient_id"), description="Target Patient ID, e.g. PT-8829")
    upload_ids: list[str] = Field(default_factory=list, validation_alias=AliasChoices("uploadIds", "upload_ids"), description="List of source asset IDs to extract from")
    asset_id: str | None = Field(default=None, validation_alias=AliasChoices("assetId", "asset_id"), description="Single asset ID helper (compatibility)")


class ReviewRequest(BaseModel):
    """Clinician decision on an extraction run."""

    decision: Literal["approved", "rejected"] = Field(description="Clinician's gate decision to either approve and persist or reject and discard")
    comment: str = Field(default="", max_length=1000, description="Optional clinician notes or rejection reasons")
    field_updates: dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("fields", "field_updates"), description="Modified clinical fields to override agent structuring output")


class QuestionRequest(BaseModel):
    """Patient-grounded clinical question."""

    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(validation_alias=AliasChoices("patientId", "patient_id"), description="Scoped Patient ID for context grounding")
    question: str = Field(min_length=3, max_length=2000, description="Natural language question, e.g. 'What is the PHQ-9 progress?'")
    source_types: list[Literal["text", "image", "lab", "document", "pdf", "json", "knowledge_base"]] = Field(default_factory=list, description="Filter citations by source evidence categories")
    filters: dict[str, Any] = Field(default_factory=dict, description="Custom criteria, e.g. dateRange: '30d'")


class DatabaseRequest(BaseModel):
    """Natural-language database intelligence request."""

    question: str = Field(min_length=3, max_length=1000, description="Cohort-wide natural language query, e.g. 'Count patients grouped by risk'")


class OrchestrateRequest(BaseModel):
    """Natural-language workflow routing request."""

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(min_length=3, max_length=2000, description="Natural language user request to route")
    patient_id: str | None = Field(default=None, validation_alias=AliasChoices("patientId", "patient_id"), description="Optional Patient ID context")


class ExecuteRequest(BaseModel):
    """Approved preview identifier for deterministic execution."""

    preview_id: str = Field(description="Temporary execution ID previewed and approved by the developer")


class ApiMessage(BaseModel):
    """Simple API status message."""

    status: str = Field(description="Liveness status, e.g. 'ok'")
    details: dict[str, Any] = Field(default_factory=dict, description="Metadata key-value audit map")


class PatientResponse(BaseModel):
    """Structured patient response contract."""

    id: str = Field(description="Unique patient identifier matching repository, e.g. PT-8829")
    name: str = Field(description="Patient's full legal name")
    mrn: str = Field(description="Medical Record Number for compliance lookup")
    age: int | None = Field(default=None, description="Patient age in years")
    sex: str | None = Field(default=None, description="Biological sex")
    condition: str | None = Field(default=None, description="Primary clinical diagnosis or oncological stage")
    risk: str = Field(description="Risk categorization level: 'high', 'medium', 'low'")
    aiStatus: str | None = Field(default=None, description="Review verification status: 'needs_review', 'verified'")
    completeness: float | None = Field(default=None, description="Ratio of required evidence uploaded (0.0 to 1.0)")
    lastEncounter: str | None = Field(default=None, description="Date of the last record update in ISO 8601 format")
    assignedClinician: str | None = Field(default=None, description="Assigned primary care clinician")
    openIssues: int = Field(default=0, description="Number of unresolved clinical tasks or warnings")
    dataSources: int = Field(default=0, description="Number of indexed evidence files associated with the patient")
    lastAiReview: str | None = Field(default=None, description="Timestamp of last agent structured evaluation")


class SessionResponse(BaseModel):
    """Structured session response contract."""

    id: str = Field(description="Unique session ID, e.g. SES-8829-003")
    patientId: str = Field(description="Associated Patient ID")
    title: str = Field(description="Descriptive session title")
    occurredAt: str = Field(description="Session date in YYYY-MM-DD format")
    status: str = Field(description="Gate status: 'pending', 'verified'")
    summary: str | None = Field(default=None, description="Brief extraction content summary")
    uploadedImageCount: int = Field(default=0, description="Number of image files processed during ingestion")
    extractionConfidence: float = Field(default=0.0, description="Agent consensus model confidence score (0.0 to 1.0)")
    jsonSyncStatus: str = Field(default="synced", description="Object storage status: 'pending', 'synced', 'failed'")
    relationalSyncStatus: str = Field(default="synced", description="Relational database sync status")
    vectorSyncStatus: str = Field(default="synced", description="Vector index sync status")
    auditStatus: str = Field(default="recorded", description="Compliance audit trail logging status")


class AuditEventResponse(BaseModel):
    """Structured audit event response contract."""

    id: str = Field(description="Unique compliance log entry ID, e.g. AUD-001")
    timestamp: str = Field(description="Audited event creation timestamp")
    event: str = Field(description="Audited clinical action code")
    actor: str = Field(description="User or agent ID performing the action")
    entity: str = Field(description="Target ID affected by the event")
    result: str = Field(description="Verification result: 'recorded', 'blocked'")


class DashboardResponse(BaseModel):
    """Structured dashboard data response contract."""

    metrics: dict[str, Any] = Field(description="Global operational metrics (patients, High Risk counts, stored assets, active run limits)")
    patients: list[PatientResponse] = Field(description="List of patients requiring immediate attention")
    sessions: list[SessionResponse] = Field(description="List of recent image extraction sessions")
    activity: list[AuditEventResponse] = Field(description="Latest compliance audit trail logs")


class NotificationResponse(BaseModel):
    """Structured notification response contract."""

    id: str = Field(description="Unique notification ID")
    title: str = Field(description="Descriptive notification title")
    detail: str = Field(description="Detailed event description")
    severity: str = Field(description="Severity flag: 'critical', 'warning', 'info'")
    agent: str = Field(description="Issuing agent identifier")
    read: bool = Field(description="Indicates if the notification has been marked read")
    route: str = Field(description="Target workspace navigation route link")


class StorageResponse(BaseModel):
    """Structured storage metadata response contract."""

    assets: list[dict[str, Any]] = Field(description="Metadata of all raw uploaded files")
    persistedExtractions: list[dict[str, Any]] = Field(description="Persisted session structured receipts")
    assetCount: int = Field(description="Total uploaded assets")
    persistedCount: int = Field(description="Total approved and synced session extractions")
    cloudCount: int = Field(description="Cloud Storage object count")
    jsonCount: int = Field(description="JSON record document count")
    sqlCount: int = Field(description="Relational database row count")
    vectorCount: int = Field(description="Vector index embedding count")
    auditCount: int = Field(description="Immutable compliance audit log count")


class AgentPipelineInfo(BaseModel):
    """Structure describing an agent pipeline."""

    id: str = Field(description="Pipeline category: 'extraction', 'qa', 'database'")
    name: str = Field(description="Descriptive pipeline title")
    route: str = Field(description="Workspace workflow route URL")
    agents: list[str] = Field(description="List of specialist agent IDs deployed in the sequential sequence")


class AgentCatalogResponse(BaseModel):
    """Structured agent catalog response contract."""

    executionMode: str = Field(description="Active execution engine mode: 'local' (deterministic demo), 'live' (Vertex AI)")
    orchestrator: str = Field(description="Primary intent classification agent identifier")
    framework: str = Field(description="Agent orchestrator platform framework name")
    pipelines: list[AgentPipelineInfo] = Field(description="List of available multi-agent pipeline sequential sequence workflows")


class AgentConfigResponse(BaseModel):
    """Structured agent config response contract."""

    version: int = Field(description="Monotonically increasing configuration schema version")
    autoApprovalThreshold: int = Field(description="Confidence threshold for automatic session approval (0 to 100)")
    reviewThreshold: int = Field(description="Confidence threshold prompting mandatory clinical review (0 to 100)")
    maxConcurrentRuns: int = Field(description="Maximum parallel agent runs rate limit")
    databaseEnabled: bool = Field(description="Flag to enable execution of approved SELECT queries")


class UserResponse(BaseModel):
    """Structured user response contract."""

    id: str = Field(description="Unique corporate user identifier, e.g. USR-001")
    name: str = Field(description="User full legal name")
    email: str = Field(description="Verified workspace email address")
    roles: list[str] = Field(description="Assigned role access groups: 'clinician', 'reviewer', 'admin'")
    scope: str = Field(description="Access permission scope boundaries")
    status: str = Field(description="Account operational state: 'Active', 'Suspended'")


# --- V2 Service & Developer Console Schemas ---

class McpToolInfo(BaseModel):
    """Model context protocol tool definition."""

    name: str = Field(description="Unique programmatic tool identifier, e.g. 'get_patient_status'")
    description: str | None = Field(default=None, description="Detailed tool instruction guidelines and parameter references")
    inputSchema: dict[str, Any] | None = Field(default=None, alias="inputSchema", description="JSON schema describing expected arguments")
    outputSchema: dict[str, Any] | None = Field(default=None, alias="outputSchema", description="JSON schema describing tool output structure")


class McpToolsListResponse(BaseModel):
    """Response containing a list of MCP tools."""

    tools: list[McpToolInfo] = Field(description="List of dynamic database and search tools registered on the FastMCP server")
    total: int = Field(description="Total count of active FastMCP tools")


class McpExecuteRequest(BaseModel):
    """Request payload to execute an MCP tool."""

    model_config = ConfigDict(populate_by_name=True)

    tool_name: str = Field(validation_alias=AliasChoices("toolName", "tool_name"), description="Programmatic tool identifier")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Parameters matching tool inputSchema")


class McpExecuteResponse(BaseModel):
    """Execution output from an MCP tool."""

    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(description="Execution result status: 'success', 'failed'")
    result: Any = Field(description="Raw structured result returned by the SQLite or document processor tool execution")
    duration_ms: float = Field(default=0.0, validation_alias=AliasChoices("durationMs", "duration_ms"), description="Tool execution duration in milliseconds")


class A2aCardResponse(BaseModel):
    """Agent card payload for Agent-to-Agent discovery."""

    name: str = Field(description="Orchestration root agent identifier")
    description: str | None = Field(default=None, description="Root orchestrator capabilities statement")
    instruction: str | None = Field(default=None, description="System prompt instructions summary excerpt")
    pipelines: list[str] = Field(default_factory=list, description="Sub-agent sequential sequence pipelines names list")
    tools: list[str] = Field(default_factory=list, description="Native and MCP tools registered directly on the orchestrator")


class V2HealthResponse(BaseModel):
    """Advanced system health information."""

    status: str = Field(description="System liveness state, e.g. 'ok'")
    mode: str = Field(description="Active execution engine mode: 'local' (demo), 'live' (Vertex AI)")
    timestamp: str = Field(description="ISO 8601 current local server time")
    databaseConnected: bool = Field(description="SQLite clinical database persistence liveness connection check")
    storageAccessible: bool = Field(description="Local uploads storage read-write permission access check")


class OrchestrationPlan(BaseModel):
    """Workflow classification and orchestration plan."""

    model_config = ConfigDict(populate_by_name=True)

    intent: str = Field(description="Classified user query intent category, e.g. 'query_clinical_population'")
    workflow: str = Field(description="Routed agent sequence name: 'extraction', 'qa', 'database'")
    route: str = Field(description="Workspace navigation view route link")
    agents: list[str] = Field(description="Deployed specialist sub-agents deployed for the task")
    dataSources: list[str] = Field(default_factory=list, validation_alias=AliasChoices("dataSources", "data_sources"), description="Grounded persistent stores queried during execution")
    permissions: list[str] = Field(default_factory=list, description="Access security scopes validated before tool execution")
    expectedOutput: str = Field(validation_alias=AliasChoices("expectedOutput", "expected_output"), description="Descriptive expected result statement")


class ErrorResponse(BaseModel):
    """Standard error response structure returned by the API."""

    detail: str = Field(description="Explanation of the error message detailing the reason for failure")
