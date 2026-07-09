"""FastAPI routes for clinician-facing deterministic application."""

import asyncio
import csv
import io
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Response, UploadFile, APIRouter, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from time import monotonic

# Load .env before any request handling so GOOGLE_API_KEY and Vertex settings
# reach the environment without requiring the lazy agent import.
load_dotenv()

from clinical_app.models import (
    DatabaseRequest, OrchestrateRequest, QuestionRequest, ReviewRequest, Role, RunRequest,
    PatientResponse, SessionResponse, AuditEventResponse, AuditEventDetailResponse, DashboardResponse, NotificationResponse,
    StorageResponse, AgentCatalogResponse, AgentConfigResponse, UserResponse,
    McpToolsListResponse, McpExecuteRequest, McpExecuteResponse, A2aCardResponse, V2HealthResponse,
    OrchestrationPlan, ErrorResponse,
    SystemHealthResponse, AgentMonitorRow, PermissionsResponse, PermissionsUpdateRequest,
    SchemaTable, WorkspaceSummaryResponse, EvidenceItemResponse,
    ReportScheduleResponse, ReportScheduleUpdateRequest,
)
from clinical_app.system import component_checks
from clinical_app.live_bridge import execute_live
from clinical_app.agent_runtime import database_execution_tools, database_preview_tools, extraction_review_tools, extraction_tools, qa_tools
from clinical_app.document import UploadPolicyError, detect_patient_id, detect_patient_id_from_parsed, parse_knowledge_base_upload, parse_upload, validate_knowledge_base_upload, validate_upload
from clinical_app.repository import DemoRepository, LiveRepository, RepositoryRegistry, now
from clinical_app.tenancy import TenantConfig, TenantKind, resolve_tenant


def patient_view(item: dict[str, Any], data_sources: int | None = None) -> dict[str, Any]:
    """Map repository patient to browser contract.

    Demo tenants keep the illustrative data-source count; real tenants pass
    the actual number of evidence sources so nothing is embellished.
    """

    risks = {"high": "high", "needs_review": "medium", "stable": "low"}
    return {
        "id": item["patient_id"], "name": item["name"],
        "mrn": f"MRN-{item['patient_id'][3:]}", "age": item.get("age"),
        "sex": item.get("sex"), "condition": item.get("primary_diagnosis"),
        "risk": risks.get(item.get("risk_level"), "medium"),
        "aiStatus": item.get("ai_review_status"),
        "completeness": item.get("data_completeness_score"),
        "lastEncounter": item.get("last_session_date"),
        "assignedClinician": item.get("assigned_clinician"),
        "openIssues": item.get("open_tasks", 0),
        "dataSources": data_sources if data_sources is not None else 3 + int(item.get("open_tasks", 0) > 0),
        "lastAiReview": item.get("last_session_date"),
    }


def tenant_patient_view(repo: Any, item: dict[str, Any]) -> dict[str, Any]:
    """Patient view honoring the repository's demo/real reporting rules."""

    if repo.is_demo:
        return patient_view(item)
    return patient_view(item, data_sources=len(repo.evidence.get(item["patient_id"], [])))


def session_view(item: dict[str, Any]) -> dict[str, Any]:
    """Map repository session to browser contract."""

    return {
        "id": item["session_id"], "patientId": item["patient_id"],
        "title": f"Clinical evidence review - {item['date']}",
        "occurredAt": item["date"],
        "status": item.get("clinician_verification_status", "pending"),
        "summary": f"{item.get('uploaded_image_count', 0)} assets; extraction confidence {item.get('extraction_confidence', 0):.0%}",
        "uploadedImageCount": item.get("uploaded_image_count", 0),
        "extractionConfidence": item.get("extraction_confidence", 0),
        "extractedFields": [
            {"name": field.get("field_name", ""), "value": str(field.get("value", "")), "confidence": float(field.get("confidence") or 0)}
            for field in item.get("extracted_fields", [])
        ],
        "jsonSyncStatus": "synced",
        "relationalSyncStatus": "synced",
        "vectorSyncStatus": "synced",
        "auditStatus": "recorded",
    }


def audit_view(item: dict[str, Any]) -> dict[str, Any]:
    """Map internal audit entry to browser contract."""

    details = item.get("details", {})
    entity = details.get("run_id") or details.get("patient_id") or details.get("query_id") or "system"
    return {"id": item["audit_id"], "timestamp": item["timestamp"], "event": item["action"], "actor": item["actor"], "entity": entity, "result": details.get("result", "recorded")}



API_DESCRIPTION = """
## Clinical AI Command Center API & Agent Hub

This API serves as the clinician-facing product backend and orchestration layer for the Clinician AI Kit, bridging the React/Vite frontend with Google ADK agent execution environments.

### Core Architecture

- **Agent Engine**: Managed via Google ADK (`google-adk`). Wires a root orchestrator with 22 specialist agents.
- **Multimodal Ingest**: Supports quality inspection, OCR, vision analysis, and clinical structuring.
- **Persistent Compliance Log**: Real Persisted SQLite persistence (`clinical.db`) under an immutable audit trail.
- **Multi-Tenant Scoping**: Dynamic tenant switching between demo settings (`research-clinic`) and live mode (`capstone`).

### Versioned Operations

1. **V1 API (`/api/v1`)**: Exposes core clinical entities (Patients, Sessions, Assets, Runs, Admin settings, Audit trail).
2. **V2 API (`/api/v2`)**: Advanced services integration, exposing MCP server tool catalogs (`/api/v2/mcp/tools`), remote agent cards (`/api/v2/a2a/card`), and system diagnostics.

### Documentation Surfaces

- **Swagger UI (`/docs`)**: styled interactive API console for `/api/v1` and `/api/v2`.
- **ReDoc (`/redoc`)**: readable OpenAPI reference for the same schema.
- **OpenAPI JSON (`/openapi.json`)**: raw contract consumed by the in-app Developer Console.
- **Frontend Diagram Atlas**: architecture SVG/PNG assets are served by the frontend bundle and documented in the Project Wiki; they are intentionally not modeled as API operations.

### 3-Layer Security Callbacks
- **Input Guardrails**: unicode normalization, prompt injection prevention.
- **Tool Authorization**: parameter verification, rate limits, secret token sanitization.
- **Output Redaction**: PII detection, security leaks blocking.
"""

def create_app() -> FastAPI:
    """Build API with fresh in-memory demo session registry."""

    api = FastAPI(title="Clinical AI Command Center API", version="0.3.0", docs_url=None, redoc_url=None, description=API_DESCRIPTION)
    registry = RepositoryRegistry()

    v1_router = APIRouter()

    COMMON_RESPONSES = {
        400: {"model": ErrorResponse, "description": "Bad Request: Parameter verification or query syntax error"},
        401: {"model": ErrorResponse, "description": "Unauthorized: Session key invalid or authorization headers missing"},
        403: {"model": ErrorResponse, "description": "Forbidden: User role does not possess permissions to write/read the target resource"},
        404: {"model": ErrorResponse, "description": "Not Found: The target patient, session, database run, or image asset does not exist"},
        422: {"model": ErrorResponse, "description": "Unprocessable Entity: Parameter validation constraints failed"},
        500: {"model": ErrorResponse, "description": "Internal Server Error: Persisted SQLite storage connection error or agent execution crash"}
    }

    v2_router = APIRouter()

    def effective_mode(tenant: TenantConfig) -> str:
        """Return the execution backend a tenant's requests use.

        Tenant kind is authoritative: real tenants execute live against their
        own database, demo tenants always serve deterministic fixtures. This
        is what keeps switching tenants switching data even when a live
        Capstone tenant coexists with the demo tenants in one deployment.
        """

        return "live" if tenant.kind == TenantKind.REAL else "local"

    async def context(
        demo_session: Annotated[str, Header(alias="X-Demo-Session")] = "public-demo",
        clinical_role: Annotated[Role | None, Header(alias="X-Clinical-Role")] = None,
        legacy_role: Annotated[Role | None, Header(alias="X-Role")] = None,
        user: Annotated[str, Header(alias="X-User")] = "demo-user",
        tenant: Annotated[str, Header(alias="X-Tenant")] = "local",
    ):
        active_tenant = resolve_tenant(tenant)
        repo = registry.get(demo_session, active_tenant)
        role = clinical_role or legacy_role or "clinician"
        if getattr(repo, "db_path", None) is not None:
            # Real tenants scope every database and upload access in this
            # request — including deep inside live agent tools — to their
            # own files via context-propagated storage state.
            from capstone_agent import database

            with database.tenant_storage(repo.db_path, getattr(repo, "uploads_root", None)):
                yield repo, role, user, active_tenant
        else:
            yield repo, role, user, active_tenant

    Context = Annotated[tuple[DemoRepository | LiveRepository, Role, str, TenantConfig], Depends(context)]

    def patient_or_404(repo: DemoRepository | LiveRepository, patient_id: str) -> dict[str, Any]:
        item = repo.patients.get(patient_id)
        if item is None and isinstance(repo, LiveRepository):
            # Live rosters are a session-start snapshot; a patient ingested or
            # registered after that moment exists only in the tenant database.
            item = repo.find_patient(patient_id)
        if not item:
            raise HTTPException(404, "Patient not found")
        return item

    def upload_patient_or_register(repo: DemoRepository | LiveRepository, patient_id: str) -> dict[str, Any]:
        """Resolve an upload's patient, registering unseen ids for live tenants.

        Demo rosters are fixed, so unknown ids stay a 404. Live evidence
        uploads (extraction source or Q&A knowledge base) are how a clinician
        first introduces a patient, so an unseen id creates a needs_review
        roster row — persisted through ensure_patient, mirroring what
        extraction approval already does — making the same patient immediately
        usable from both workflows and from future sessions.
        """

        if not patient_id or not patient_id.strip():
            raise HTTPException(422, "patientId is required")
        if not isinstance(repo, LiveRepository):
            return patient_or_404(repo, patient_id)
        item = repo.find_patient(patient_id)
        if item is not None:
            return item
        from capstone_agent import database as clinical_db

        clinical_db.ensure_patient(patient_id)
        return repo.add_patient(patient_id, f"Patient {patient_id}")

    def run_or_404(repo: DemoRepository | LiveRepository, run_id: str) -> dict[str, Any]:
        item = repo.runs.get(run_id)
        if not item:
            raise HTTPException(404, "Run not found")
        return item

    def author_steps_to_rows(run_id: str, author_steps: list[dict[str, Any]], running_last: bool = False) -> list[dict[str, Any]]:
        """Map ADK event authors to browser-visible step rows.

        running_last marks the most recent author as still "running" instead
        of "completed" — used for the on_step callback fired while the
        pipeline is mid-flight, so the frontend's PipelineBand shows the
        currently active agent instead of only a final all-completed snapshot.
        """

        rows = author_steps or [{"author": "root_agent"}]
        steps = [
            {"id": f"{run_id}-S{i}", "name": str(step.get("author", "root_agent")).replace("_", " ").title(), "status": "running" if running_last and i == len(rows) else "completed", "detail": "ADK event completed", "timestamp": now()}
            for i, step in enumerate(rows, 1)
        ]
        return steps

    def live_steps(run_id: str, live_result: dict[str, Any], terminal_name: str | None = None, terminal_status: str = "completed") -> list[dict[str, Any]]:
        """Map a finished live_result's author steps to browser-visible step rows, with an optional terminal gate row appended."""

        steps = author_steps_to_rows(run_id, live_result.get("authorSteps", []))
        if terminal_name:
            steps.append({"id": f"{run_id}-S{len(steps)+1}", "name": terminal_name, "status": terminal_status, "detail": "Awaiting explicit approval" if terminal_status == "review" else "Stage completed", "timestamp": now()})
        return steps

    def attach_live_metadata(result: dict[str, Any], live_result: dict[str, Any]) -> None:
        """Preserve live ADK response details for UI inspection and tests."""

        result["liveResponse"] = live_result.get("finalResponse", "")
        result["authorSteps"] = live_result.get("authorSteps", [])
        result["toolCalls"] = live_result.get("toolCalls", result.get("toolCalls", []))

    def last_tool_output(live_result: dict[str, Any], tool_name: str) -> dict[str, Any] | None:
        """Return the data payload of the last successful call to tool_name.

        citation_builder_agent's own output_key text is free-form prose, not
        reliable structured data — the deterministic build_citations tool
        return value (captured here from the event stream) is.
        """

        for call in reversed(live_result.get("toolCalls", [])):
            if call.get("tool") == tool_name and isinstance(call.get("output"), dict) and call["output"].get("status") == "success":
                return call["output"].get("data") or {}
        return None

    @api.get("/healthz")
    def healthz() -> dict[str, str]:
        """Report liveness for raw probes."""
        return {"status": "ok", "mode": effective_mode(resolve_tenant(None))}

    @v1_router.get("/health", response_model=dict[str, str], tags=["Health"], responses={200: {"description": "Report liveness for V1 API"}, **COMMON_RESPONSES})
    def health_v1() -> dict[str, str]:
        """Report liveness for V1 API."""
        return {"status": "ok", "mode": effective_mode(resolve_tenant(None))}

    @api.get("/readyz")
    def ready() -> dict[str, Any]:
        """Report readiness from real component checks.

        Returns 503 when the default-tenant database is unreachable so
        orchestrators (Cloud Run, Kubernetes) hold traffic until storage is
        writable; the frontend-bundle check is advisory and never fails
        readiness so API-only deployments stay ready.
        """

        default_repo = registry.get("readiness-probe", resolve_tenant(None))
        components = component_checks(default_repo)
        blocking = {"Clinical database", "Upload storage"}
        degraded = [c["name"] for c in components if c["status"] != "operational" and c["name"] in blocking]
        payload = {"status": "not-ready" if degraded else "ready", "components": components}
        if degraded:
            raise HTTPException(503, f"Not ready: {', '.join(degraded)}")
        return payload

    @v1_router.get("/agents", response_model=AgentCatalogResponse, tags=["Agents"], responses={200: {"description": "Expose the real ADK pipeline catalog and tenant execution mode"}, **COMMON_RESPONSES})
    def agents(ctx: Context) -> dict[str, Any]:
        """Expose the real ADK pipeline catalog and tenant execution mode."""

        return {
            "executionMode": effective_mode(ctx[3]),
            "orchestrator": "clinical_orchestrator",
            "framework": "Google ADK",
            "pipelines": [
                {"id": "extraction", "name": "Clinical Evidence Extraction", "route": "/app/extraction", "agents": ["quality_assessor_agent", "ocr_processor_agent", "vision_analyzer_agent", "clinical_structuring_agent", "extraction_critic_agent", "extraction_refiner_agent", "clinical_review_gate_agent", "extraction_persistence_agent", "extraction_audit_agent"]},
                {"id": "qa", "name": "Patient Q&A", "route": "/app/qa", "agents": ["qa_request_validation_agent", "context_assembly_agent", "evidence_retrieval_agent", "image_evidence_agent", "citation_builder_agent", "answer_synthesis_agent", "qa_audit_agent"]},
                {"id": "database", "name": "Population Insights", "route": "/app/database", "agents": ["schema_discovery_agent", "nl_to_sql_agent", "sql_validator_agent", "sql_preview_approval_agent", "query_executor_agent", "insight_chart_agent"]},
            ],
        }

    @v1_router.get("/notifications", response_model=list[NotificationResponse], tags=["Notifications"], responses={200: {"description": "List of unresolved notifications from agents"}, **COMMON_RESPONSES})
    def notifications(ctx: Context) -> list[dict[str, Any]]:
        """Return actionable notifications — seeded for demo, derived for real tenants."""

        return ctx[0].build_notifications()

    @v1_router.get("/system/health", response_model=SystemHealthResponse, tags=["Health"], responses={200: {"description": "Measured component health for the caller's tenant"}, **COMMON_RESPONSES})
    def system_health(ctx: Context) -> dict[str, Any]:
        """Measure real component health: database, agent runtime, MCP, storage, model, bundle."""

        return {"components": component_checks(ctx[0]), "checkedAt": now()}

    @v1_router.get("/agents/monitoring", response_model=list[AgentMonitorRow], tags=["Agents"], responses={200: {"description": "Per-agent runtime statistics"}, **COMMON_RESPONSES})
    def agents_monitoring(ctx: Context) -> list[dict[str, Any]]:
        """Return per-agent statistics — baseline+session for demo, run-derived for real tenants.

        Readable by every role: clinicians get the same read-only monitoring
        view admins see, and no mutation happens through this endpoint.
        """

        return ctx[0].agent_monitoring()

    @v1_router.get("/permissions", response_model=PermissionsResponse, tags=["Admin"], responses={200: {"description": "Role-permission matrix"}, **COMMON_RESPONSES})
    def permissions(ctx: Context) -> dict[str, Any]:
        """Return the tenant's permission matrix."""

        if ctx[1] != "admin":
            raise HTTPException(403, "Admin role required")
        return ctx[0].load_permissions()

    @v1_router.put("/permissions", response_model=PermissionsResponse, tags=["Admin"], responses={200: {"description": "Persisted the edited permission matrix"}, **COMMON_RESPONSES})
    def save_permissions(body: PermissionsUpdateRequest, ctx: Context) -> dict[str, Any]:
        """Persist an admin's permission matrix edit — durable for real tenants."""

        repo, role, user, _tenant = ctx
        if role != "admin":
            raise HTTPException(403, "Admin role required")
        saved = repo.save_permissions([row.model_dump() for row in body.matrix], user)
        repo.log("permissions_saved", user, role, version=saved["version"])
        return saved

    @v1_router.get("/database/schema", response_model=list[SchemaTable], tags=["Database"], responses={200: {"description": "Clinical database tables parsed from the governed DDL"}, **COMMON_RESPONSES})
    def database_schema() -> list[dict[str, Any]]:
        """Expose the real clinical schema the SQL pipeline queries against."""

        import re

        from capstone_agent.clinical_schemas import SCHEMA_DDL

        tables = []
        for table, ddl in SCHEMA_DDL.items():
            columns = []
            for line in ddl.splitlines()[1:]:
                text = line.split("--")[0].strip().rstrip(",")
                match = re.match(r"^(\w+)\s+([A-Za-z]+(?:\(\d+(?:,\s*\d+)?\))?)", text)
                if match and match.group(1).upper() not in {"PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "CONSTRAINT"}:
                    columns.append({"name": match.group(1), "type": match.group(2).upper()})
            tables.append({"table": table, "columns": columns})
        return tables

    @v1_router.get("/summary", response_model=WorkspaceSummaryResponse, tags=["Dashboard"], responses={200: {"description": "Live workspace counts for navigation badges"}, **COMMON_RESPONSES})
    def summary(ctx: Context) -> dict[str, Any]:
        """Return live counts for navigation badges and the role landing page."""

        repo = ctx[0]
        return {
            "queueCount": sum(item.get("ai_review_status") == "needs_review" for item in repo.patients.values()),
            "inboxCount": sum(item["workflow"] == "extraction" and item["status"] == "review" for item in repo.runs.values()),
            "unreadNotifications": sum(not item.get("read") for item in repo.build_notifications()),
            "patients": len(repo.patients),
            "runs": sum(not item.get("seeded") for item in repo.runs.values()),
        }

    @v1_router.get("/patients/{patient_id}/evidence", response_model=list[EvidenceItemResponse], tags=["Patients"], responses={200: {"description": "Evidence sources for one patient"}, **COMMON_RESPONSES})
    def patient_evidence(patient_id: str, ctx: Context) -> list[dict[str, Any]]:
        """Return the patient's evidence sources with viewable asset links."""

        repo = ctx[0]
        patient_or_404(repo, patient_id)
        return [
            {
                "id": item["source_id"], "kind": item["source_type"], "date": item["date"], "excerpt": item["text"],
                **({"sourceUrl": f"/api/assets/{item['asset_id']}?session={repo.session_id}"} if item.get("asset_id") else {}),
            }
            for item in repo.evidence.get(patient_id, [])
        ]

    @v1_router.post("/notifications/{notification_id}/read", response_model=NotificationResponse, tags=["Notifications"], responses={200: {"description": "Marked one notification as read"}, **COMMON_RESPONSES})
    def read_notification(notification_id: str, ctx: Context) -> dict[str, Any]:
        """Mark one notification read in the isolated demo session."""

        notification = next((item for item in ctx[0].notifications if item["id"] == notification_id), None)
        if not notification:
            raise HTTPException(404, "Notification not found")
        notification["read"] = True
        ctx[0].log("notification_read", ctx[2], ctx[1], notification_id=notification_id)
        return notification

    @v1_router.post("/demo/session", response_model=dict[str, str], status_code=201, tags=["Demo"], responses={201: {"description": "Created an isolated deterministic demo session"}, **COMMON_RESPONSES})
    def start_demo() -> dict[str, str]:
        """Create isolated demo state identifier."""

        session_id = f"demo-{uuid4().hex}"
        registry.get(session_id)
        return {"sessionId": session_id}

    @v1_router.post("/demo/reset", status_code=204, tags=["Demo"], responses={204: {"description": "Reset the caller's deterministic demo session"}, **COMMON_RESPONSES})
    def reset(ctx: Context) -> None:
        """Reset only caller demo session."""

        ctx[0].reset()

    @v1_router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"], responses={200: {"description": "Retrieved global metrics and recent activity dashboard details"}, **COMMON_RESPONSES})
    def dashboard(ctx: Context, role: Role | None = None) -> dict[str, Any]:
        """Return role-aware dashboard data."""

        repo, header_role, _user, _tenant = ctx
        active_role = role or header_role
        patients = [tenant_patient_view(repo, item) for item in repo.patients.values()]
        sessions = [session_view(item) for item in repo.sessions.values()]
        completeness = round(sum(float(p["completeness"] or 0) for p in patients) / max(1, len(patients)) * 100)
        pending = sum(p["aiStatus"] == "needs_review" for p in patients)
        persisted = sum(item["workflow"] == "extraction" and item["result"].get("persisted") for item in repo.runs.values())
        extraction_count = sum(item["workflow"] == "extraction" for item in repo.runs.values())
        sync_rate = round(persisted / extraction_count * 100) if extraction_count else 100
        # Demo tenants show illustrative platform activity; real tenants
        # report only what actually happened in this session.
        users = repo.list_users()
        clinician_count = sum("Clinician" in user.get("roles", []) for user in users)
        failed = sum(item["status"] == "error" for item in repo.runs.values())
        pending_actions = pending + sum(item["status"] == "review" for item in repo.runs.values()) + sum(not item.get("read") for item in repo.build_notifications())
        if getattr(repo, "dashboard_seed", None) is not None:
            ds = repo.dashboard_seed
            metrics: dict[str, int | str] = {
                "patients": ds.get("patients", len(patients)),
                "assignedPatients": ds.get("patients", len(patients)),
                "highRisk": ds.get("highRiskEstimate", sum(p["risk"] == "high" for p in patients)),
                "pendingReview": ds.get("pendingReviewEstimate", pending),
                "pendingVerifications": ds.get("pendingVerifications", ds.get("pendingReviewEstimate", pending)),
                "imageExtractionsToday": ds.get("imageExtractionsToday", ds.get("sourceImages", len(sessions))),
                "openAiAlerts": ds.get("openAiAlerts", len([item for item in repo.notifications if not item["read"]]) + 2),
                "agentRuns24h": ds.get("agentRuns24h", 214) + len(repo.runs),
                "syncRate": ds.get("syncRate", sync_rate),
                "completeness": ds.get("completeness", completeness),
                "sessions": ds.get("sessions", len(sessions)),
                "failedExtractions": ds.get("failedExtractions", failed),
                "totalUsers": len(users),
                "activeClinicians": clinician_count,
                "pendingActions": ds.get("pendingReviewEstimate", pending) + ds.get("failedExtractions", failed) + len(repo.runs) + len([item for item in repo.notifications if not item["read"]]),
                "storedAssets": ds.get("storedAssets", len(repo.uploads)),
                "databaseRows": ds.get("databaseRows", 0),
                "queryExamples": ds.get("queryExamples", 0),
                "qaPrompts": ds.get("qaPrompts", 0),
                "knowledgeBaseDocuments": ds.get("knowledgeBaseDocuments", 0),
                "citations": ds.get("citations", 0),
            }
            if active_role == "admin":
                metrics.update({
                    "activeUsers": len(users),
                    "agentRuns": ds.get("agentRuns24h", len(repo.runs)),
                    "reviewSla": "4m",
                    "auditEvents": ds.get("auditEvents", len(repo.audit)),
                    "storedAssets": ds.get("storedAssets", len(repo.uploads)),
                })
        else:
            alert_base = 2 if repo.is_demo else 0
            run_base = 214 if repo.is_demo else 0
            metrics = {"patients": len(patients), "assignedPatients": len(patients), "highRisk": sum(p["risk"] == "high" for p in patients), "pendingReview": pending, "pendingVerifications": pending, "imageExtractionsToday": len(sessions), "openAiAlerts": len([item for item in repo.notifications if not item["read"]]) + alert_base, "agentRuns24h": run_base + len(repo.runs), "syncRate": sync_rate, "completeness": completeness, "sessions": len(sessions), "failedExtractions": failed, "totalUsers": len(users), "activeClinicians": clinician_count, "pendingActions": pending_actions}
            if active_role == "admin":
                metrics.update({"activeUsers": len(users), "agentRuns": len(repo.runs), "reviewSla": "4m", "auditEvents": len(repo.audit), "storedAssets": len(repo.uploads)})
        return {"metrics": metrics, "patients": patients[:8], "sessions": sessions[:8], "activity": [audit_view(item) for item in reversed(repo.audit[-8:])]}

    @v1_router.get("/patients", response_model=list[PatientResponse], tags=["Patients"], responses={200: {"description": "List of matched patient profiles according to criteria"}, **COMMON_RESPONSES})
    def patients(ctx: Context, query: str = "", q: str = "", risk: str | None = None) -> list[dict[str, Any]]:
        """Search patients by identifier, name, diagnosis, or risk."""

        repo, _role, _user, _tenant = ctx
        needle = (query or q).casefold().strip()
        rows = list(repo.patients.values())
        if needle:
            rows = [p for p in rows if needle in " ".join((p["patient_id"], p["name"], p["primary_diagnosis"])).casefold()]
        views = [tenant_patient_view(repo, item) for item in rows]
        return [item for item in views if not risk or item["risk"] == risk]

    @v1_router.get("/patients/{patient_id}", response_model=PatientResponse, tags=["Patients"], responses={200: {"description": "Retrieved detailed patient profile and current risk metadata by ID"}, **COMMON_RESPONSES})
    def patient(patient_id: str, ctx: Context) -> dict[str, Any]:
        """Return patient profile."""

        return tenant_patient_view(ctx[0], patient_or_404(ctx[0], patient_id))

    @v1_router.get("/sessions", response_model=list[SessionResponse], tags=["Sessions"], responses={200: {"description": "List of recent clinical extraction sessions"}, **COMMON_RESPONSES})
    def sessions(ctx: Context, patient_id: str | None = None) -> list[dict[str, Any]]:
        """List clinical sessions, optionally for one patient."""

        rows = ctx[0].sessions.values()
        return [session_view(item) for item in rows if not patient_id or item["patient_id"] == patient_id]

    @v1_router.get("/patients/{patient_id}/sessions", response_model=list[SessionResponse], tags=["Sessions"], include_in_schema=False)
    def patient_sessions(patient_id: str, ctx: Context) -> list[dict[str, Any]]:
        """Compatibility route for patient sessions."""

        patient_or_404(ctx[0], patient_id)
        return sessions(ctx, patient_id)

    @v1_router.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"], responses={200: {"description": "Retrieved detailed session status and confidence scores"}, **COMMON_RESPONSES})
    def session(session_id: str, ctx: Context) -> dict[str, Any]:
        """Return one clinical session."""

        item = ctx[0].sessions.get(session_id)
        if not item:
            raise HTTPException(404, "Session not found")
        return session_view(item)

    @v1_router.post("/assets", status_code=201, tags=["Assets"], responses={201: {"description": "Asset uploaded and recorded successfully"}, **COMMON_RESPONSES})
    async def create_asset(ctx: Context, file: UploadFile = File(...), patient_id: str = Form("")) -> dict[str, Any]:
        """Store uploaded bytes inside caller demo session or process through live agent ETL.

        Live tenants may leave patient_id blank: the endpoint reads an id the
        document itself declares (local text for PDFs, one Gemini Vision pass
        for images) and registers it through upload_patient_or_register, so
        evidence carrying its own patient number processes without retyping.
        """

        repo, role, user, _tenant = ctx
        patient_id = patient_id.strip()
        if repo.is_demo or patient_id:
            # Blank live ids are resolved from the document text below,
            # after the upload has been validated and parsed.
            upload_patient_or_register(repo, patient_id)
        contents = await file.read()
        if not contents:
            raise HTTPException(422, "Uploaded file is empty")
        ct = file.content_type or "application/octet-stream"
        fn = file.filename or "upload"
        try:
            upload_meta = validate_upload(contents, ct, fn)
        except UploadPolicyError as exc:
            raise HTTPException(exc.status_code, str(exc)) from exc
        ct = str(upload_meta["contentType"])
        fn = str(upload_meta["filename"])
        asset_id = repo.identifier("AST")
        preview_url = f"/api/assets/{asset_id}?session={repo.session_id}"
        extracted = parse_upload(contents, ct, fn)
        detected_id = detect_patient_id_from_parsed(extracted)

        if not repo.is_demo:
            from capstone_agent import database as capstone_db
            from capstone_agent.document_processor import extract_text_from_image, process_document

            # Save file to uploads root on disk for live tenant
            uploads_dir = Path(capstone_db.active_uploads_root())
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_filename = f"{asset_id}_{fn}"
            dest_path = uploads_dir / dest_filename
            with open(dest_path, "wb") as f:
                f.write(contents)

            pre_extraction = None
            if not patient_id and not detected_id and str(extracted.get("type")) == "image":
                # Images carry no locally extractable text; one Gemini Vision
                # pass reads any on-image patient number, and process_document
                # below reuses the result instead of running OCR twice.
                try:
                    pre_extraction = extract_text_from_image(str(dest_path))
                    detected_id = detect_patient_id(str(pre_extraction.get("text") or ""))
                except Exception:
                    pre_extraction = None
            if not patient_id:
                if not detected_id:
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(422, "patientId is required: none was provided and none could be detected in the document")
                patient_id = detected_id
                upload_patient_or_register(repo, patient_id)

            # Run document processor ETL (parsing, chunking, Gemini structure)
            try:
                res = process_document(dest_path, patient_id, pre_extraction=pre_extraction)
                if "error" not in res:
                    extracted["textPreview"] = res.get("text_preview", extracted.get("textPreview", ""))
                    extracted["pageCount"] = res.get("page_count", extracted.get("pageCount", 1))
            except Exception:
                preview_text = extracted.get("textPreview") or f"Document text fallback for {fn}"
                capstone_db.store_document(
                    document_id=asset_id,
                    filename=fn,
                    content_type=ct,
                    file_path=str(dest_path),
                    raw_text=preview_text,
                    page_count=extracted.get("pageCount", 1),
                    patient_id=patient_id,
                    gemini_analysis="Mock clinical analysis fallback (no credentials)."
                )
                from capstone_agent.document_processor import chunk_text
                chunks = chunk_text(preview_text)
                chunk_dicts = [{"index": c["index"], "text": c["text"], "page": 1} for c in chunks]
                capstone_db.store_document_chunks(asset_id, chunk_dicts, patient_id)

            repo.asset_contents[asset_id] = contents
            repo.uploads[asset_id] = {"assetId": asset_id, "patientId": patient_id, "filename": fn, "contentType": ct, "sizeBytes": len(contents), "previewUrl": preview_url, "createdAt": now(), "extracted": extracted, "filePath": str(dest_path)}
        else:
            repo.asset_contents[asset_id] = contents
            repo.uploads[asset_id] = {"assetId": asset_id, "patientId": patient_id, "filename": fn, "contentType": ct, "sizeBytes": len(contents), "previewUrl": preview_url, "createdAt": now(), "extracted": extracted}

        repo.log("asset_uploaded", user, role, patient_id=patient_id, asset_id=asset_id)
        return {"assetId": asset_id, "patientId": patient_id, "detectedPatientId": detected_id, "previewUrl": preview_url, "extracted": extracted}

    @v1_router.post("/knowledge-base/assets", status_code=201, tags=["Assets"], responses={201: {"description": "Uploaded and indexed a patient-scoped knowledge-base document"}, **COMMON_RESPONSES})
    async def create_knowledge_base_asset(ctx: Context, file: UploadFile = File(...), patient_id: str = Form(...)) -> dict[str, Any]:
        """Store a patient-scoped document as searchable Q&A knowledge-base evidence."""

        repo, role, user, _tenant = ctx
        upload_patient_or_register(repo, patient_id)
        contents = await file.read()
        if not contents:
            raise HTTPException(422, "Uploaded file is empty")
        ct = file.content_type or "application/octet-stream"
        fn = file.filename or "upload"
        try:
            upload_meta = validate_knowledge_base_upload(contents, ct, fn)
        except UploadPolicyError as exc:
            raise HTTPException(exc.status_code, str(exc)) from exc

        ct = str(upload_meta["contentType"])
        fn = str(upload_meta["filename"])
        asset_id = repo.identifier("KB")
        preview_url = f"/api/assets/{asset_id}?session={repo.session_id}"
        extracted = parse_knowledge_base_upload(contents, ct, fn)

        if not repo.is_demo:
            from capstone_agent import database as capstone_db
            from capstone_agent.document_processor import process_document

            # Save file to uploads root on disk for live tenant
            uploads_dir = Path(capstone_db.active_uploads_root())
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_filename = f"{asset_id}_{fn}"
            dest_path = uploads_dir / dest_filename
            with open(dest_path, "wb") as f:
                f.write(contents)

            # Run document processor ETL
            try:
                res = process_document(dest_path, patient_id)
                if "error" not in res:
                    extracted["textPreview"] = res.get("text_preview", extracted.get("textPreview", ""))
                    extracted["pageCount"] = res.get("page_count", extracted.get("pageCount", 1))
            except Exception:
                preview_text = extracted.get("textPreview") or f"Document text fallback for {fn}"
                capstone_db.store_document(
                    document_id=asset_id,
                    filename=fn,
                    content_type=ct,
                    file_path=str(dest_path),
                    raw_text=preview_text,
                    page_count=extracted.get("pageCount", 1),
                    patient_id=patient_id,
                    gemini_analysis="Mock clinical analysis fallback (no credentials)."
                )
                from capstone_agent.document_processor import chunk_text
                chunks = chunk_text(preview_text)
                chunk_dicts = [{"index": c["index"], "text": c["text"], "page": 1} for c in chunks]
                capstone_db.store_document_chunks(asset_id, chunk_dicts, patient_id)

            repo.asset_contents[asset_id] = contents
            repo.uploads[asset_id] = {"assetId": asset_id, "patientId": patient_id, "filename": fn, "contentType": ct, "sizeBytes": len(contents), "previewUrl": preview_url, "createdAt": now(), "extracted": extracted, "knowledgeBase": True, "filePath": str(dest_path)}
        else:
            repo.asset_contents[asset_id] = contents
            repo.uploads[asset_id] = {"assetId": asset_id, "patientId": patient_id, "filename": fn, "contentType": ct, "sizeBytes": len(contents), "previewUrl": preview_url, "createdAt": now(), "extracted": extracted, "knowledgeBase": True}

        preview_text = str(extracted.get("textPreview") or "").strip()
        if not preview_text:
            pages = extracted.get("pages") if isinstance(extracted.get("pages"), list) else []
            preview_text = str(pages[0].get("text", "") if pages else "").strip()
        if not preview_text:
            preview_text = f"{fn} indexed without local text preview."

        repo.evidence.setdefault(patient_id, []).insert(0, {"source_id": asset_id, "source_type": "document", "date": now()[:10], "text": f"{fn}: {preview_text}", "asset_id": asset_id, "filename": fn})
        repo.log("knowledge_base_asset_uploaded", user, role, patient_id=patient_id, asset_id=asset_id)
        return {"assetId": asset_id, "patientId": patient_id, "previewUrl": preview_url, "evidenceId": asset_id, "extracted": extracted}

    @v1_router.post("/import", status_code=201, tags=["Admin"], responses={201: {"description": "Ingested and went through the ETL of a PDF, image, or database intelligence cohort"}, **COMMON_RESPONSES})
    async def import_data(
        ctx: Context,
        request: Request,
        import_type: str | None = Form(None),  # "document" or "database"
        patient_id: str = Form(""),
        file: UploadFile | None = File(None)
    ) -> dict[str, Any]:
        """Import PDF/image documents or seed database intelligence cohort."""

        repo, role, user, _tenant = ctx
        if repo.is_demo:
            raise HTTPException(400, "Import is only supported in live (real tenant) mode.")

        # If Content-Type is application/json, parse JSON body
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            import_type = body.get("import_type") or body.get("importType")
            patient_id = body.get("patient_id") or body.get("patientId", "")

        if not import_type:
            raise HTTPException(422, "import_type is required")

        from capstone_agent import database as capstone_db

        if import_type == "document":
            if not file:
                raise HTTPException(422, "File is required for document import")
            if not patient_id:
                raise HTTPException(422, "patientId is required for document import")
            
            contents = await file.read()
            if not contents:
                raise HTTPException(422, "Uploaded file is empty")
            
            ct = file.content_type or "application/octet-stream"
            fn = file.filename or "upload"
            
            try:
                upload_meta = validate_upload(contents, ct, fn)
            except UploadPolicyError:
                try:
                    upload_meta = validate_knowledge_base_upload(contents, ct, fn)
                except UploadPolicyError as exc2:
                    raise HTTPException(exc2.status_code, str(exc2)) from exc2
            
            ct = str(upload_meta["contentType"])
            fn = str(upload_meta["filename"])
            asset_id = repo.identifier("AST")
            
            # Save file to disk
            uploads_dir = Path(capstone_db.active_uploads_root())
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_filename = f"{asset_id}_{fn}"
            dest_path = uploads_dir / dest_filename
            with open(dest_path, "wb") as f:
                f.write(contents)
                
            # Process via document_processor ETL
            from capstone_agent.document_processor import process_document
            
            preview_url = f"/api/assets/{asset_id}?session={repo.session_id}"
            extracted = parse_upload(contents, ct, fn)
            
            try:
                res = process_document(dest_path, patient_id)
                if "error" in res:
                    raise RuntimeError(res["error"])
                doc_id = res.get("document_id")
                page_count = res.get("page_count")
                chunk_count = res.get("chunk_count")
                extracted["textPreview"] = res.get("text_preview", extracted.get("textPreview", ""))
                extracted["pageCount"] = res.get("page_count", extracted.get("pageCount", 1))
            except Exception:
                doc_id = asset_id
                page_count = extracted.get("pageCount", 1)
                chunk_count = 1
                preview_text = extracted.get("textPreview") or f"Document text fallback for {fn}"
                
                capstone_db.store_document(
                    document_id=doc_id,
                    filename=fn,
                    content_type=ct,
                    file_path=str(dest_path),
                    raw_text=preview_text,
                    page_count=page_count,
                    patient_id=patient_id,
                    gemini_analysis="Mock clinical analysis fallback (no credentials)."
                )
                from capstone_agent.document_processor import chunk_text
                chunks = chunk_text(preview_text)
                chunk_dicts = [{"index": c["index"], "text": c["text"], "page": 1} for c in chunks]
                capstone_db.store_document_chunks(doc_id, chunk_dicts, patient_id)
            
            repo.asset_contents[asset_id] = contents
            repo.uploads[asset_id] = {
                "assetId": asset_id,
                "patientId": patient_id,
                "filename": fn,
                "contentType": ct,
                "sizeBytes": len(contents),
                "previewUrl": preview_url,
                "createdAt": now(),
                "extracted": extracted,
                "filePath": str(dest_path),
            }
            repo.log("asset_imported", user, role, patient_id=patient_id, asset_id=asset_id)
            return {
                "status": "success",
                "message": f"Successfully imported and ran ETL on document '{fn}'",
                "assetId": asset_id,
                "documentId": doc_id,
                "pageCount": page_count,
                "chunkCount": chunk_count
            }
            
        elif import_type == "database":
            import sqlite3
            from datetime import date
            
            db_path = capstone_db.active_db_path()
            try:
                from scripts.generate_database_showcase import seed_database
                
                # Initialize the database schema if it doesn't exist
                capstone_db.init_db(seed=False)
                
                with sqlite3.connect(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    row_counts = seed_database(
                        conn=conn,
                        patient_count=5,
                        seed=12345,
                        anchor_date=date(2026, 7, 5),
                        years=4,
                        patient_prefix="PT-L",
                        demo_platform="primary"
                    )
                
                repo._hydrate_from_database()
                repo.log("database_intelligence_imported", user, role, details=json.dumps(row_counts))
                
                return {
                    "status": "success",
                    "message": "Successfully imported and ran ETL on database intelligence cohort",
                    "rowCounts": row_counts
                }
            except Exception as e:
                raise HTTPException(500, f"Database import failed: {e}")
        else:
            raise HTTPException(422, f"Unsupported import type: {import_type}")


    @v1_router.get("/knowledge-base/assets", tags=["Assets"], responses={200: {"description": "List indexed knowledge-base documents, optionally scoped to one patient"}, **COMMON_RESPONSES})
    def knowledge_base_assets(ctx: Context, patient_id: str | None = None) -> list[dict[str, Any]]:
        """List knowledge-base uploads powering the Q&A retrieval catalog.

        previewUrl is rewritten against the caller's session so seeded demo
        documents stay viewable, and dropped entirely when no bytes or disk
        file exist to serve — the UI then falls back to the parsed text.
        """

        repo = ctx[0]
        rows = []
        for item in repo.uploads.values():
            if not item.get("knowledgeBase"):
                continue
            if patient_id and item.get("patientId") != patient_id:
                continue
            view = {key: value for key, value in item.items() if key != "filePath"}
            servable = item["assetId"] in repo.asset_contents or bool(item.get("filePath"))
            view["previewUrl"] = f"/api/assets/{item['assetId']}?session={repo.session_id}" if servable else ""
            rows.append(view)
        return rows

    @v1_router.get("/extraction/sources", tags=["Assets"], responses={200: {"description": "List generated extraction packet sources for demo picking"}, **COMMON_RESPONSES})
    def extraction_sources(ctx: Context) -> list[dict[str, Any]]:
        """Return generated extraction PDF packets with patient-level previews."""

        repo, _role, _user, tenant = ctx
        rows = []
        for item in repo.uploads.values():
            if item.get("sourceUse") != "extraction":
                continue
            patient = repo.patients.get(str(item.get("patientId")), {})
            preview_url = ""
            if item.get("previewPath"):
                demo_platform = item.get("demoPlatform") or ("demo2" if tenant.id == "northstar" else "primary")
                preview_url = f"/demo-data/extraction/{demo_platform}/images/{Path(str(item['previewPath'])).name}"
            source_url = f"/api/assets/{item['assetId']}?session={repo.session_id}"
            rows.append({
                "id": item["assetId"],
                "assetId": item["assetId"],
                "label": f"{patient.get('primary_diagnosis', 'Clinical packet')} - {item.get('packetId', item['assetId'])}",
                "patientId": item.get("patientId", ""),
                "patientName": patient.get("name", ""),
                "filename": item.get("filename", ""),
                "packetFilename": item.get("filename", ""),
                "packetId": item.get("packetId", ""),
                "patientsInFile": item.get("patientCountInFile", 1),
                "batchPatientIds": item.get("packetPatientIds", []),
                "contentType": item.get("contentType", "application/pdf"),
                "sourceContentType": item.get("contentType", "application/pdf"),
                "previewContentType": item.get("previewContentType", "image/png"),
                "sourceUrl": source_url,
                "previewUrl": preview_url or source_url,
                "expectedFields": item.get("extracted", {}).get("fields", []),
                "reviewRequired": any(field.get("needs_review") for field in item.get("extracted", {}).get("fields", [])),
            })
        return rows

    @v1_router.get("/assets/{asset_id}", tags=["Assets"], response_model=None, responses={200: {"description": "Serve uploaded evidence bytes for authorized preview"}, **COMMON_RESPONSES})
    def asset(asset_id: str, ctx: Context, session: str | None = None) -> Response:
        """Return uploaded asset bytes for evidence preview."""

        repo = registry.find(session, asset_id) if session else ctx[0]
        if repo is None:
            raise HTTPException(403, "Asset capability expired or invalid")
        if asset_id in repo.asset_contents:
            metadata = repo.uploads[asset_id]
            return StreamingResponse(iter([repo.asset_contents[asset_id]]), media_type=metadata["contentType"])
        if asset_id in repo.source_assets:
            contents, content_type = repo.source_assets[asset_id]
            return StreamingResponse(iter([contents]), media_type=content_type)
        # Seeded knowledge-base documents carry a generated file on disk
        # instead of in-memory bytes; stream the real file for previews.
        metadata = repo.uploads.get(asset_id)
        if metadata and metadata.get("filePath"):
            candidate = Path(str(metadata["filePath"]))
            if candidate.is_file():
                return FileResponse(candidate, media_type=metadata["contentType"])
        raise HTTPException(404, "Asset not found")

    @v1_router.post("/runs/extraction", status_code=201, tags=["Extraction"], responses={201: {"description": "Began deterministic extraction pipeline on target report assets"}, **COMMON_RESPONSES})
    async def extraction(body: RunRequest, ctx: Context) -> dict[str, Any]:
        """Create extraction run — live agent execution or deterministic demo."""

        repo, role, user, tenant = ctx
        if not repo.is_demo:
            patient_id = body.patient_id
        else:
            patient_or_404(repo, body.patient_id)
            patient_id = body.patient_id
        asset_ids = [body.asset_id] if body.asset_id else body.upload_ids
        if not asset_ids or any(asset_id not in repo.uploads or repo.uploads[asset_id].get("patientId") != patient_id for asset_id in asset_ids):
            raise HTTPException(400, "Unknown asset for patient")
        run_id = repo.identifier("RUN")
        audit = repo.log("extraction_review_requested", user, role, patient_id=patient_id, run_id=run_id)

        def asset_kind(asset_meta: dict[str, Any]) -> str:
            return "document" if asset_meta.get("contentType") == "application/pdf" else "image"

        evidence_list = [
            {
                "id": aid,
                "label": repo.uploads[aid]["filename"],
                "kind": asset_kind(repo.uploads[aid]),
                "sourceUrl": f"/api/assets/{aid}?session={repo.session_id}",
            }
            for aid in asset_ids
        ]

        if not repo.is_demo:
            file_bytes = repo.asset_contents.get(asset_ids[0])
            file_mime = repo.uploads[asset_ids[0]].get("contentType", "application/octet-stream")
            extracted_meta = repo.uploads[asset_ids[0]].get("extracted", {})
            item = {"id": run_id, "workflow": "extraction", "status": "running", "agentName": "image_extraction_pipeline", "confidence": 0.0, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "running", "detail": "Routing to the clinical evidence extraction pipeline", "timestamp": now()}], "evidence": evidence_list, "result": {"patientId": patient_id, "fields": {}, "toolCalls": [], "storageReceipts": [], "persisted": False, "extractedContent": extracted_meta}, "review": None}
            repo.runs[run_id] = item

            async def run_in_background() -> None:
                try:
                    live_result = await execute_live(
                        f"Delegate to the image_extraction_pipeline sub-agent to run the full clinical "
                        f"extraction workflow (quality check, OCR, vision analysis, clinical structuring, "
                        f"and review gate) on the attached document for patient {patient_id}. Structure "
                        f"every field with a confidence score.",
                        user,
                        file_bytes=file_bytes,
                        file_mime=file_mime,
                        patient_context={"patient_id": patient_id},
                        on_step=lambda steps: item.update(steps=author_steps_to_rows(run_id, steps, running_last=True)),
                    )
                    fields = live_result.get("fields", {})
                    if not fields:
                        final_response = str(live_result.get("finalResponse", "")).strip()
                        if not final_response:
                            item["status"] = "error"
                            item["steps"].append({"id": f"{run_id}-S2", "name": "Agent Execution", "status": "error", "detail": "Extraction produced no structured fields or narrative response", "timestamp": now()})
                            return
                        fields = {"document_type": "Clinical evidence", "patient_match": patient_id, "finding": final_response}
                    item["steps"] = live_steps(run_id, live_result, "Clinical Review Gate", "review")
                    item["status"] = "review"
                    item["confidence"] = live_result.get("confidence", 0.88)
                    item["result"]["fields"] = fields
                    attach_live_metadata(item["result"], live_result)
                    item["result"]["stateOutputs"] = live_result.get("stateOutputs", {})
                    item["result"]["storageReceipts"] = [{"target": t, "status": "pending"} for t in ("json", "relational", "vector")]
                except Exception as exc:
                    item["status"] = "error"
                    item["steps"].append({"id": f"{run_id}-S2", "name": "Agent Execution", "status": "error", "detail": f"Execution failed: {exc}", "timestamp": now()})

            asyncio.create_task(run_in_background())
            return item

        primary_asset = repo.uploads[asset_ids[0]]
        extracted_meta = primary_asset.get("extracted", {})
        extracted_fields = extracted_meta.get("fields", []) if isinstance(extracted_meta.get("fields"), list) else []
        fields = {
            str(field.get("field_name") or field.get("label") or f"field_{index}"): (
                f"{field.get('value')} {field.get('unit')}".strip() if field.get("unit") else str(field.get("value", ""))
            )
            for index, field in enumerate(extracted_fields, 1)
        }
        if not fields:
            fields = {
                "document_type": extracted_meta.get("documentType", "Clinical evidence"),
                "patient_match": patient_id,
                "finding": str(extracted_meta.get("textPreview") or "Evidence ready for clinician verification"),
            }
        confidence = round(
            sum(float(field.get("confidence", 0.88)) for field in extracted_fields) / len(extracted_fields),
            2,
        ) if extracted_fields else 0.88
        # Extracted-field names are clinical data, not API parameters: they are
        # displayed verbatim in the inbox review workspace and mirrored into the
        # relational row, so every key here uses one convention (snake_case) to
        # match the extraction packets and the relational/session views.
        fields = {
            "document_type": extracted_meta.get("documentType", "Clinical evidence"),
            "patient_match": patient_id,
            "source_file": primary_asset.get("filename", ""),
            "packet_id": primary_asset.get("packetId", ""),
            "batch_patients": primary_asset.get("packetPatientIds", []),
            **fields,
            "finding": str(extracted_meta.get("textPreview") or "Evidence ready for clinician verification"),
        }
        tool_calls = extraction_tools(patient_id, asset_ids[0], run_id)
        step_names = ("Source Quality Agent", "PDF Packet Parser", "Vision Agent", "Clinical Structuring Agent", "Validation Agent", "Clinical Review Gate")
        steps = [{"id": f"{run_id}-S{i}", "name": name, "status": "completed" if i < 6 else "review", "detail": "Specialist stage completed" if i < 6 else "Awaiting clinician decision", "timestamp": now()} for i, name in enumerate(step_names, 1)]
        item = {"id": run_id, "workflow": "extraction", "status": "review", "agentName": "image_extraction_pipeline", "confidence": confidence, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": steps, "evidence": evidence_list, "result": {"patientId": patient_id, "fields": fields, "toolCalls": tool_calls, "storageReceipts": [{"target": target, "status": "pending"} for target in ("json", "relational", "vector")], "persisted": False, "extractedContent": extracted_meta}, "review": None}
        repo.runs[run_id] = item
        return item

    @v1_router.get("/runs/{run_id}", tags=["Runs"], responses={200: {"description": "Retrieved status, confidence scores, and current stage details of an active pipeline run"}, **COMMON_RESPONSES})
    def run(run_id: str, ctx: Context) -> dict[str, Any]:
        """Poll persisted agent run."""

        return run_or_404(ctx[0], run_id)

    @v1_router.get("/runs/{run_id}/events", tags=["Runs"], responses={200: {"description": "Retrieved list of completed run step execution events"}, **COMMON_RESPONSES})
    def run_events(run_id: str, ctx: Context) -> list[dict[str, Any]]:
        """Poll run steps."""

        return run_or_404(ctx[0], run_id).get("steps", [])

    @v1_router.get("/runs/{run_id}/events/stream", tags=["Runs"], responses={200: {"description": "Server-Sent Events (SSE) stream of run progress"}, **COMMON_RESPONSES})
    def event_stream(run_id: str, ctx: Context) -> StreamingResponse:
        """Stream run steps as server-sent events."""

        steps = run_or_404(ctx[0], run_id).get("steps", [])
        def generate():
            for index, step in enumerate(steps, 1):
                yield f"id: {index}\nevent: step\ndata: {json.dumps(step)}\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")

    @v1_router.post("/runs/{run_id}/review", tags=["Runs"], responses={200: {"description": "Recorded review decision to approve or reject structured extraction data"}, **COMMON_RESPONSES})
    def review(run_id: str, body: ReviewRequest, ctx: Context) -> dict[str, Any]:
        """Approve and persist extraction, or reject without persistence."""

        repo, role, user, _tenant = ctx
        if role != "clinician":
            raise HTTPException(403, "Clinician role required")
        item = run_or_404(repo, run_id)
        if item["workflow"] != "extraction" or item["status"] != "review":
            raise HTTPException(409, "Run is not awaiting extraction review")
        if body.field_updates:
            item["result"]["fields"] = body.field_updates.get("fields", body.field_updates)
        approved = body.decision == "approved"
        pid = item["result"]["patientId"]
        occurred_at = datetime.now(UTC).date().isoformat()
        session_id = repo.identifier("SES") if approved else None
        if approved and not repo.is_demo:
            # Live approvals write to clinical.db where foreign keys are
            # enforced: the patient and session rows must exist before
            # extracted fields can reference them.
            from capstone_agent import database as clinical_db

            clinical_db.ensure_patient(pid, repo.patients.get(pid, {}).get("name", ""))
            clinical_db.store_session(session_id, pid, occurred_at, len(item["evidence"]), float(item["confidence"] or 0), "verified")
        review_traces = extraction_review_tools(pid, run_id, body.decision, user, item["result"]["fields"], body.comment, persist_session_id=session_id)
        item["result"]["toolCalls"].extend(review_traces)
        if approved:
            if repo.is_demo:
                item["result"]["storageReceipts"] = [{"target": target, "status": "synced", "receiptId": repo.identifier("RCP")} for target in ("json", "relational", "vector")]
            else:
                # Live receipts reflect what the persistence tools actually did.
                trace_status = {trace["tool"]: trace.get("status") for trace in review_traces}
                receipt_tools = {"json": "store_to_gcs", "relational": "persist_extraction_relational", "vector": "persist_extraction_vector"}
                item["result"]["storageReceipts"] = [{"target": target, "status": "synced" if trace_status.get(tool) == "success" else "failed", "receiptId": repo.identifier("RCP")} for target, tool in receipt_tools.items()]
            item["result"]["persisted"] = all(receipt["status"] == "synced" for receipt in item["result"]["storageReceipts"])
            patient = repo.patients.get(pid)
            if not patient and not repo.is_demo:
                patient = repo.add_patient(pid, f"Patient {pid}")
            elif not patient:
                raise HTTPException(404, "Patient not found")
            patient["ai_review_status"] = "verified"
            patient["open_tasks"] = max(0, int(patient.get("open_tasks", 0)) - 1)
            patient["last_session_date"] = occurred_at
            repo.sessions[session_id] = {"session_id": session_id, "patient_id": patient["patient_id"], "date": occurred_at, "uploaded_image_count": len(item["evidence"]), "extraction_confidence": item["confidence"], "clinician_verification_status": "verified", "extracted_fields": [{"field_name": key, "value": str(value), "confidence": item["confidence"]} for key, value in item["result"]["fields"].items()]}
            evidence_rows = repo.evidence.setdefault(patient["patient_id"], [])
            evidence_rows.append({"source_id": session_id, "source_type": "structured", "date": occurred_at, "text": json.dumps(item["result"]["fields"], sort_keys=True)})
            for source in item["evidence"]:
                evidence_rows.append({"source_id": source["id"], "source_type": source.get("kind", "image"), "date": occurred_at, "text": f"Clinician-approved source: {source['label']}", "asset_id": source["id"]})
            item["result"]["sessionId"] = session_id
        item["result"]["decision"] = body.decision
        item["review"] = {"decision": body.decision, "comment": body.comment, "reviewedBy": user, "reviewedAt": now()}
        item["status"] = "completed"
        item["steps"].append({"id": f"{run_id}-S4", "name": "Clinical review", "status": "completed", "detail": "Approved and persisted" if approved else "Rejected; no extracted result persisted", "timestamp": now()})
        repo.log(f"extraction_{body.decision}", user, role, patient_id=item["result"]["patientId"], run_id=run_id, result="persisted" if approved else "not_persisted")
        return item

    @v1_router.get("/reviews", tags=["Runs"], responses={200: {"description": "List extraction runs awaiting clinician review"}, **COMMON_RESPONSES})
    def reviews(ctx: Context) -> list[dict[str, Any]]:
        """List extraction runs awaiting clinician review."""

        return [item for item in ctx[0].runs.values() if item["workflow"] == "extraction" and item["status"] == "review"]

    @v1_router.get("/runs", tags=["Runs"], responses={200: {"description": "List this session's agent runs for conversation-history restore"}, **COMMON_RESPONSES})
    def list_runs(ctx: Context, workflow: str | None = None, patient_id: str | None = None) -> list[dict[str, Any]]:
        """List the session's agent runs in creation order.

        Workflow screens call this on mount so a clinician who navigates away
        and returns sees the same conversation thread the backend already
        holds — runs are the durable record of every QA, extraction, and
        database exchange in this session.
        """

        rows = [item for item in ctx[0].runs.values() if not item.get("seeded") and (not workflow or item.get("workflow") == workflow)]
        if patient_id:
            rows = [item for item in rows if item.get("result", {}).get("patientId") == patient_id]
        return rows

    @v1_router.post("/orchestrate", response_model=OrchestrationPlan, status_code=201, tags=["Orchestration"], responses={201: {"description": "Classify user query and structure orchestrator execution route"}, **COMMON_RESPONSES})
    def orchestrate(body: OrchestrateRequest, ctx: Context) -> dict[str, Any]:
        """Classify a request and return an audited workflow execution plan."""

        repo, role, user, _tenant = ctx
        query = body.query.casefold()
        extraction_terms = ("extract", "upload", "image", "scan", "dicom", "document", "ocr")
        database_terms = ("sql", "database", "cohort", "population", "count", "analytics", "report", "across patients")
        if any(term in query for term in extraction_terms):
            intent = "extract_clinical_evidence"
            workflow = "extraction"
            route = "/app/extraction"
            agents = ["quality_assessor_agent", "vision_analyzer_agent", "clinical_structurer_agent"]
            data_sources = ["uploaded_asset", "patient_record"]
            permissions = ["patient:read", "asset:write", "clinical_review:write"]
            expected_output = "Review-gated structured clinical fields with evidence and pending storage receipts."
        elif any(term in query for term in database_terms):
            intent = "query_clinical_population"
            workflow = "database"
            route = "/app/database"
            agents = ["sql_generator_agent", "sql_safety_agent", "chart_generator_agent"]
            data_sources = ["clinical_relational_store"]
            permissions = ["database:read", "population_analytics:execute"]
            expected_output = "Read-only SQL preview requiring confirmation before tabular and chart execution."
        else:
            intent = "answer_patient_question"
            workflow = "qa"
            route = "/app/qa"
            agents = ["patient_context_agent", "evidence_retrieval_agent", "grounded_answer_agent"]
            data_sources = ["patient_record", "clinical_notes", "image_evidence", "lab_results"]
            permissions = ["patient:read", "clinical_evidence:read"]
            expected_output = "Patient-grounded answer with confidence and reopenable evidence citations."
        if workflow in {"extraction", "qa"}:
            if not body.patient_id:
                raise HTTPException(422, "patientId is required for patient-specific workflows")
            patient_or_404(repo, body.patient_id)
        plan = {"intent": intent, "workflow": workflow, "route": route, "agents": agents, "dataSources": data_sources, "permissions": permissions, "expectedOutput": expected_output}
        repo.log("orchestration_plan_created", user, role, patient_id=body.patient_id, workflow=workflow, route=route)
        return plan

    @v1_router.post("/runs/qa", status_code=201, tags=["QA"], responses={201: {"description": "Began patient-grounded QA retrieval pipeline execution"}, **COMMON_RESPONSES})
    @v1_router.post("/qa/runs", status_code=201, tags=["QA"], include_in_schema=False)
    async def question(body: QuestionRequest, ctx: Context) -> dict[str, Any]:
        """Execute evidence-grounded Q&A — live agent or deterministic demo."""

        repo, role, user, _tenant = ctx
        if repo.is_demo:
            # Validate before logging so a 404 never produces a fake
            # "question_answered" audit event for a request that never ran.
            patient_or_404(repo, body.patient_id)
        elif body.patient_id and not repo.find_patient(body.patient_id):
            # Live Q&A is often where a clinician first references a new
            # patient; register the id in the session roster (in-memory,
            # needs_review) so extraction uploads and the patient list see
            # the same patient without waiting for persisted evidence.
            repo.add_patient(body.patient_id, f"Patient {body.patient_id}")
        run_id = repo.identifier("RUN")
        audit = repo.log("question_answered", user, role, patient_id=body.patient_id, run_id=run_id)

        if not repo.is_demo:
            source_types_str = ",".join(body.source_types) if body.source_types else "all"
            local_evidence = repo.evidence.get(body.patient_id, [])
            evidence_views = [{"id": e["source_id"], "label": f"{e['source_type'].title()} evidence - {e['date']}", "kind": e["source_type"], "excerpt": e["text"], **({"sourceUrl": f"/api/assets/{e['asset_id']}?session={repo.session_id}"} if e.get("asset_id") else {})} for e in local_evidence[:5]]
            item = {"id": run_id, "workflow": "qa", "status": "running", "agentName": "patient_qa_pipeline", "confidence": 0.0, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "running", "detail": "Routing to the patient Q&A pipeline", "timestamp": now()}], "evidence": evidence_views, "result": {"answer": "", "question": body.question, "patientId": body.patient_id, "toolCalls": []}}
            repo.runs[run_id] = item
            patient_data = repo.patients.get(body.patient_id, {})
            evidence_text = "\n".join(e["text"] for e in local_evidence[:10])

            async def run_in_background() -> None:
                try:
                    live_result = await execute_live(
                        f"Answer this clinical question for patient {body.patient_id} with evidence citations: {body.question}\n\nPatient context: {json.dumps(patient_data)}\n\nAvailable evidence:\n{evidence_text}",
                        user,
                        patient_context={"patient_id": body.patient_id, "source_types": source_types_str},
                        # Patient-scoped session key keeps follow-up questions in the
                        # same ADK session without leaking state across patients.
                        session_key=f"{repo.session_id}-{body.patient_id}",
                        on_step=lambda steps: item.update(steps=author_steps_to_rows(run_id, steps, running_last=True)),
                    )
                    item["steps"] = live_steps(run_id, live_result)
                    item["status"] = "completed"
                    item["confidence"] = live_result.get("confidence", 0.85)
                    state_outputs = live_result.get("stateOutputs", {})
                    item["result"]["answer"] = state_outputs.get("qa_answer") or live_result.get("finalResponse", "No answer generated")
                    attach_live_metadata(item["result"], live_result)
                    item["result"]["stateOutputs"] = state_outputs
                    # citation_builder_agent's citations carry the image_evidence_agent's
                    # findings even when no locally-stored asset backs them (e.g. imaging
                    # studies referenced only by a synthetic GCS URI) — surface them as a
                    # structured table. imageEvidence intentionally stays unset here: an
                    # <img> pointed at a non-HTTP gs:// URI cannot render, so the frontend's
                    # existing fallback (first "image" kind entry in evidence, which only
                    # exists for real stored assets) remains the only inline image source.
                    citations = (last_tool_output(live_result, "build_citations") or {}).get("citations", [])
                    if citations:
                        item["result"]["summaryRows"] = [
                            {
                                "id": f"{run_id}-cite-{citation.get('ref', index)}",
                                "citation": f"[{citation.get('ref', index)}]",
                                "file": citation.get("document_name", "Evidence"),
                                "type": citation.get("source_type", "text"),
                                "finding": citation.get("snippet", ""),
                            }
                            for index, citation in enumerate(citations, 1)
                        ]
                except Exception as exc:
                    item["status"] = "error"
                    item["steps"].append({"id": f"{run_id}-S2", "name": "Agent Execution", "status": "error", "detail": f"Execution failed: {exc}", "timestamp": now()})

            asyncio.create_task(run_in_background())
            return item

        patient = repo.patients[body.patient_id]
        source_filter = list(body.source_types)
        requested_source = body.filters.get("source")
        if not source_filter and requested_source not in (None, "", "all"):
            source_filter = [{"note": "text", "structured": "structured", "image": "image", "pdf": "document", "json": "document", "knowledge_base": "document"}.get(requested_source, requested_source)]
        source_filter = [{"pdf": "document", "json": "document", "knowledge_base": "document"}.get(item, item) for item in source_filter]
        evidence = [e for e in repo.evidence.get(body.patient_id, []) if not source_filter or e["source_type"] in source_filter]
        date_range = body.filters.get("dateRange", "all")
        if date_range in {"30d", "1y"}:
            cutoff = datetime.now(UTC).date() - timedelta(days=30 if date_range == "30d" else 365)
            evidence = [e for e in evidence if datetime.fromisoformat(e["date"]).date() >= cutoff]
        kind_map = {"text": "text", "image": "image", "structured": "structured", "lab": "structured", "document": "document"}
        evidence_views = [{"id": e["source_id"], "label": f"{e['source_type'].title()} evidence - {e['date']}", "kind": kind_map[e["source_type"]], "excerpt": e["text"], **({"sourceUrl": f"/api/assets/{e['asset_id']}?session={repo.session_id}"} if e.get("asset_id") else {})} for e in evidence[:5]]
        answer = f"{patient['name']}: {evidence[0]['text']}" if evidence else "No evidence matched selected filters."
        tool_calls = qa_tools(body.patient_id, body.question, source_filter, date_range)
        qa_step_names = ("Request Validation Agent", "Patient Context Agent", "Retrieval Agent", "Image Evidence Agent", "Citation Agent", "Clinical Answer Agent", "Validation Agent", "Audit Agent")
        item = {"id": run_id, "workflow": "qa", "status": "completed", "agentName": "patient_qa_pipeline", "confidence": 0.88 if evidence else 0.0, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S{i}", "name": name, "status": "completed", "detail": f"Retrieved {len(evidence_views)} sources" if name == "Retrieval Agent" else "Stage completed", "timestamp": now()} for i, name in enumerate(qa_step_names, 1)], "evidence": evidence_views, "result": {"answer": answer, "question": body.question, "patientId": body.patient_id, "toolCalls": tool_calls}}
        repo.runs[run_id] = item
        return item

    @v1_router.post("/runs/database/preview", status_code=201, tags=["Database"], responses={201: {"description": "Began database cohort preview pipeline to classify intent and compile SQL query"}, **COMMON_RESPONSES})
    async def database_preview(body: DatabaseRequest, ctx: Context) -> dict[str, Any]:
        """Generate read-only SQL preview — live agent or deterministic demo."""

        repo, role, user, _tenant = ctx
        run_id = repo.identifier("RUN")
        audit = repo.log("database_preview_generated", user, role, run_id=run_id)

        if not repo.is_demo:
            item = {"id": run_id, "workflow": "database", "status": "running", "agentName": "db_intelligence_pipeline", "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "running", "detail": "Routing to the population insights pipeline", "timestamp": now()}], "evidence": [], "result": {"question": body.question, "sql": "", "safe": False, "readOnly": True, "tables": [], "toolCalls": []}}
            repo.runs[run_id] = item

            async def run_in_background() -> None:
                try:
                    live_result = await execute_live(
                        f"Generate a safe read-only SQL query for this clinical population question: {body.question}\n\nOnly generate SELECT statements.",
                        user,
                        patient_context={"workflow": "database"},
                        # One ADK session per browser session keeps database
                        # follow-up questions conversational, mirroring the
                        # patient-scoped session the Q&A pipeline already uses.
                        session_key=f"{repo.session_id}-database",
                        # Fast path: one schema-grounded model call drafts the
                        # SQL. validate_sql below plus database_execute's re-gate
                        # provide the safety guarantees deterministically, so the
                        # full six-stage pipeline would only add latency here.
                        target="sql_draft",
                        on_step=lambda steps: item.update(steps=author_steps_to_rows(run_id, steps, running_last=True)),
                    )
                    from capstone_agent.clinical_schemas import validate_sql

                    sql = live_result.get("sql", "")
                    if not sql:
                        item["status"] = "error"
                        item["steps"].append({"id": f"{run_id}-S2", "name": "SQL Generation", "status": "error", "detail": "Agent did not return SQL for this question", "timestamp": now()})
                        return
                    item["steps"] = live_steps(run_id, live_result, "SQL Approval Gate", "review")
                    item["status"] = "review"
                    item["result"]["sql"] = sql
                    item["result"]["safe"] = bool(validate_sql(sql)["safe"])
                    attach_live_metadata(item["result"], live_result)
                except Exception as exc:
                    # No canned fallback: a real tenant surfaces the failure so
                    # the clinician never approves SQL the agent did not write.
                    item["status"] = "error"
                    item["steps"] = [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "error", "detail": f"SQL generation failed: {type(exc).__name__}: {exc}", "timestamp": now()}]

            asyncio.create_task(run_in_background())
            return item

        query_cards = getattr(repo, "database_queries", []) or []
        submitted_words = {word.strip("?.!,").casefold() for word in body.question.split() if len(word.strip("?.!,")) > 3}
        selected_card = None
        if query_cards:
            scored = []
            for card in query_cards:
                card_words = {word.strip("?.!,").casefold() for word in str(card.get("question", "")).split() if len(word.strip("?.!,")) > 3}
                scored.append((len(submitted_words & card_words), card))
            selected_card = max(scored, key=lambda item: item[0])[1]
        sql = str((selected_card or {}).get("sql") or "SELECT risk_level, COUNT(*) AS patient_count FROM patients_core GROUP BY risk_level ORDER BY patient_count DESC")
        tool_calls = database_preview_tools(body.question, sql)
        from capstone_agent import clinical_schemas

        verdict = clinical_schemas.validate_sql(sql)
        item = {"id": run_id, "workflow": "database", "status": "review", "agentName": "db_intelligence_pipeline", "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Schema Understanding Agent", "status": "completed", "timestamp": now()}, {"id": f"{run_id}-S2", "name": "SQL Generation Agent", "status": "completed", "timestamp": now()}, {"id": f"{run_id}-S3", "name": "Query Validation Agent", "status": "completed", "timestamp": now()}, {"id": f"{run_id}-S4", "name": "SQL Approval Gate", "status": "review", "detail": "Awaiting explicit execution approval", "timestamp": now()}], "evidence": [], "result": {"question": body.question, "matchedQuestion": (selected_card or {}).get("question"), "sql": sql, "safe": bool(verdict["safe"]), "readOnly": True, "tables": verdict.get("tables_referenced", []), "toolCalls": tool_calls}}
        repo.runs[run_id] = item
        return item

    @v1_router.post("/runs/database/{run_id}/execute", tags=["Database"], responses={200: {"description": "Executed approved SQL query and saved result table and charts"}, **COMMON_RESPONSES})
    async def database_execute(run_id: str, ctx: Context) -> dict[str, Any]:
        """Execute reviewed database preview with a server-side safety gate."""

        repo, role, user, _tenant = ctx
        item = run_or_404(repo, run_id)
        if item["workflow"] != "database" or item["status"] != "review":
            raise HTTPException(409, "Database run is not awaiting execution")

        from capstone_agent import clinical_schemas

        # The agent validates SQL inside its own pipeline, but agent-generated
        # SQL must be re-gated here before touching the database.
        sql = item["result"].get("sql", "")
        verdict = clinical_schemas.validate_sql(sql)
        if not verdict["safe"]:
            item["steps"].append({"id": f"{run_id}-S{len(item['steps']) + 1}", "name": "Query execution", "status": "error", "detail": f"SQL rejected: {verdict['reason']}", "timestamp": now()})
            raise HTTPException(400, f"SQL rejected: {verdict['reason']}")

        item["status"] = "running"

        res = clinical_schemas.execute_query(sql)
        if res.get("error"):
            item["status"] = "review"
            item["steps"].append({"id": f"{run_id}-S{len(item['steps']) + 1}", "name": "Query execution", "status": "review", "detail": f"Execution failed: {res['error']}", "timestamp": now()})
            raise HTTPException(422, f"Failed to execute query: {res['error']}")

        rows = res.get("rows", [])
        columns = res.get("columns", [])
        item["status"] = "completed"
        item["result"].update({
            "columns": columns,
            "rows": rows,
            "chart": {"type": "bar", "x": columns[0], "y": columns[1]} if rows and len(columns) >= 2 else None,
        })
        item["result"]["toolCalls"].extend(database_execution_tools(item["result"].get("question", ""), sql, rows, user))
        item["steps"].append({"id": f"{run_id}-S{len(item['steps']) + 1}", "name": "Query execution", "status": "completed", "detail": f"Returned {len(rows)} rows", "timestamp": now()})

        repo.query_history.append(item)
        repo.log("database_query_executed", user, role, run_id=run_id)
        return item

    @v1_router.get("/database/history", response_model=list[dict[str, Any]], tags=["Database"], responses={200: {"description": "Retrieved database cohort run history"}, **COMMON_RESPONSES})
    def history(ctx: Context) -> list[dict[str, Any]]:
        """Return completed database runs."""

        return ctx[0].query_history

    @v1_router.get("/database/examples", response_model=list[str], tags=["Database"], responses={200: {"description": "Example population questions grounded in the tenant's actual database contents"}, **COMMON_RESPONSES})
    def database_examples(ctx: Context) -> list[str]:
        """Return example questions derived from the tenant's real data.

        Demo tenants surface their curated query-card questions, which the
        deterministic preview matcher is guaranteed to answer. Live tenants
        probe the governed database for what is actually present — the top
        condition, critical lab flags, missed appointments, medication load —
        so every suggestion is answerable with real rows instead of being a
        generic template that returns nothing.
        """

        repo = ctx[0]
        fallback = [
            "Count patients by risk level",
            "Which patients have critical lab results, and for which tests?",
            "How many active medications is each patient taking?",
            "Which patients missed the most appointments?",
        ]
        if repo.is_demo:
            cards = getattr(repo, "database_queries", []) or []
            questions = [str(card.get("question")) for card in cards if card.get("question")]
            return questions[:7] or fallback

        from capstone_agent import clinical_schemas

        def probe(sql: str) -> list[dict[str, Any]]:
            """Run one read-only probe; any failure just drops the suggestion."""
            try:
                res = clinical_schemas.execute_query(sql)
                return res.get("rows", []) if not res.get("error") else []
            except Exception:
                return []

        examples: list[str] = []
        risk = probe("SELECT COUNT(DISTINCT risk_level) AS n FROM patients_core")
        if risk and int(risk[0].get("n") or 0) >= 2:
            examples.append("Count patients by risk level")
        condition = probe("SELECT condition_name, COUNT(DISTINCT patient_id) AS n FROM patient_conditions GROUP BY condition_name ORDER BY n DESC LIMIT 1")
        if condition and condition[0].get("condition_name"):
            examples.append(f"Which patients have {str(condition[0]['condition_name']).rstrip('.').lower()}, and how old are they?")
        critical = probe("SELECT COUNT(*) AS n FROM lab_results WHERE flag LIKE 'critical%'")
        if critical and int(critical[0].get("n") or 0):
            examples.append("Which patients have critical lab results, and for which tests?")
        panel = probe("SELECT test_name, COUNT(*) AS n FROM lab_results GROUP BY test_name ORDER BY n DESC LIMIT 1")
        if panel and panel[0].get("test_name"):
            examples.append(f"Show the most recent {panel[0]['test_name']} result date for each patient")
        noshow = probe("SELECT COUNT(*) AS n FROM appointments WHERE status = 'No-Show'")
        if noshow and int(noshow[0].get("n") or 0):
            examples.append("Which patients missed the most appointments?")
        meds = probe("SELECT COUNT(*) AS n FROM medications")
        if meds and int(meds[0].get("n") or 0):
            examples.append("How many active medications is each patient taking?")
        vitals = probe("SELECT COUNT(*) AS n FROM vital_signs")
        if vitals and int(vitals[0].get("n") or 0):
            examples.append("What is the average systolic blood pressure by risk level?")
        return examples[:7] or fallback

    @v1_router.get("/database/queries/{run_id}/csv", tags=["Database"], responses={200: {"description": "Retrieved query results exported as a CSV stream"}, **COMMON_RESPONSES})
    def export_csv(run_id: str, ctx: Context) -> StreamingResponse:
        """Export database run rows as CSV."""

        item = run_or_404(ctx[0], run_id)
        rows = item.get("result", {}).get("rows")
        if not rows:
            raise HTTPException(409, "Query has no result rows")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="{run_id}.csv"'})

    @v1_router.get("/storage", response_model=StorageResponse, tags=["Storage"], responses={200: {"description": "Retrieved storage system metrics and totals"}, **COMMON_RESPONSES})
    def storage(ctx: Context) -> dict[str, Any]:
        """Return uploaded assets, approved storage receipts, and derived pipeline records."""

        repo = ctx[0]

        def persisted_view(item: dict[str, Any]) -> dict[str, Any]:
            # The JSON records tab renders patient, session, receipt, and
            # confidence per persisted extraction, so surface the run result
            # fields the frontend contract expects instead of receipts alone.
            receipts = item["result"].get("storageReceipts", [])
            return {
                "runId": item["id"],
                "patientId": item["result"].get("patientId", ""),
                "sessionId": item["result"].get("sessionId", ""),
                "confidence": item.get("confidence"),
                "jsonReceipt": next((receipt.get("receiptId") for receipt in receipts if receipt.get("target") == "json"), None),
                "receipts": receipts,
                "fields": item["result"].get("fields", {}),
            }

        persisted = [persisted_view(item) for item in repo.runs.values() if item["workflow"] == "extraction" and item["result"].get("persisted")]
        destinations = {"json": "JSON document store", "relational": "Relational database", "vector": "Vector search index"}
        records = [
            {"id": meta["assetId"], "source": meta["filename"], "destination": "Object storage", "status": "synced", "updated": meta["createdAt"], "owner": "Upload service", "patientId": meta.get("patientId", ""), "sessionId": "", "error": ""}
            for meta in repo.uploads.values()
        ]
        for item in repo.runs.values():
            if item["workflow"] != "extraction":
                continue
            for receipt in item["result"].get("storageReceipts", []):
                records.append({
                    "id": receipt.get("receiptId") or f"{item['id']}-{receipt['target']}",
                    "source": f"Extraction {item['id']}",
                    "destination": destinations.get(receipt["target"], receipt["target"]),
                    "status": receipt.get("status", "pending"),
                    "updated": item.get("createdAt", now()),
                    "owner": "Storage Agent",
                    "patientId": item["result"].get("patientId", ""),
                    "sessionId": item["result"].get("sessionId", ""),
                    "error": "" if receipt.get("status") != "failed" else "Persistence tool reported failure",
                })
        if getattr(repo, "storage_seed", None) is not None:
            ss = repo.storage_seed
            # Surface a sample of real loaded showcase sessions as per-record
            # rows so the JSON/relational/vector tabs show traceable records
            # (patient, session, receipt, confidence) instead of one opaque
            # rollup counter; aggregate counts still flow through jsonCount etc.
            sample_sessions = sorted(repo.sessions.values(), key=lambda item: str(item.get("date", "")), reverse=True)[:10]
            receipt_targets = (("JSON", "json", "JSON document store", "Structuring agents"), ("SQL", "relational", "Relational database", "Database generator"), ("VECTOR", "vector", "Vector search index", "Embedding agents"))
            for index, session in enumerate(sample_sessions, 1):
                for tag, _target, destination, owner in receipt_targets:
                    records.append({
                        "id": f"SEED-RCP-{tag}-{index:03d}",
                        "source": f"Session {session.get('session_id', '')}",
                        "destination": destination,
                        "status": "synced",
                        "updated": str(session.get("date", now())),
                        "owner": owner,
                        "patientId": session.get("patient_id", ""),
                        "sessionId": session.get("session_id", ""),
                        "error": "",
                    })
                persisted.append({
                    "runId": f"RUN-SEED-{session.get('session_id', index)}",
                    "patientId": session.get("patient_id", ""),
                    "sessionId": session.get("session_id", ""),
                    "confidence": session.get("extraction_confidence"),
                    "jsonReceipt": f"SEED-RCP-JSON-{index:03d}",
                    "receipts": [{"target": target, "status": "synced", "receiptId": f"SEED-RCP-{tag}-{index:03d}"} for tag, target, _destination, _owner in receipt_targets],
                    "fields": {str(field.get("field_name", f"field_{position}")): str(field.get("value", "")) for position, field in enumerate(session.get("extracted_fields", []), 1)},
                })
            seeded_records = [
                ("SEED-CLOUD", f"Provisioned: {ss.get('cloudObjects', 0)} generated evidence files", "Object storage", "Showcase data generator"),
                ("SEED-AUDIT", f"Provisioned: {ss.get('auditEvents', 0)} generated audit events", "Audit log", "Audit service"),
            ]
            for record_id, source, destination, owner in seeded_records:
                if not any(item["id"] == record_id for item in records):
                    records.append({
                        "id": record_id,
                        "source": source,
                        "destination": destination,
                        "status": "synced",
                        "updated": now(),
                        "owner": owner,
                        "patientId": "",
                        "sessionId": "",
                        "error": "",
                    })
            if ss.get("failedRecords", 0):
                records.append({
                    "id": "SEED-FAILED",
                    "source": f"Provisioned: {ss.get('failedRecords', 0)} generated failed records",
                    "destination": "Provider failover queue",
                    "status": "failed",
                    "updated": now(),
                    "owner": "Storage monitor",
                    "patientId": "",
                    "sessionId": "",
                    "error": "Synthetic provider failure record",
                })
            return {
                "assets": list(repo.uploads.values()),
                "persistedExtractions": persisted,
                "records": records,
                "assetCount": ss.get("cloudObjects", len(repo.uploads)),
                "persistedCount": ss.get("jsonDocuments", len(persisted)),
                "cloudCount": ss.get("cloudObjects", len(repo.uploads)),
                "jsonCount": ss.get("jsonDocuments", len(persisted)),
                "sqlCount": ss.get("relationalRows", len(persisted)),
                "vectorCount": ss.get("vectorRecords", len(persisted)),
                "auditCount": ss.get("auditEvents", len(repo.audit)),
                "failedCount": ss.get("failedRecords", 0),
            }
        return {"assets": list(repo.uploads.values()), "persistedExtractions": persisted, "records": records, "assetCount": len(repo.uploads), "persistedCount": len(persisted), "cloudCount": len(repo.uploads), "jsonCount": len(persisted), "sqlCount": len(persisted), "vectorCount": len(persisted), "auditCount": len(repo.audit)}

    @v1_router.get("/users", response_model=list[UserResponse], tags=["Admin"], responses={200: {"description": "Retrieved corporate user directory"}, **COMMON_RESPONSES})
    def users(ctx: Context) -> list[dict[str, Any]]:
        """Return the tenant's user directory — seeded fixtures for demo, persisted rows for real."""

        if ctx[1] != "admin":
            raise HTTPException(403, "Admin role required")
        return ctx[0].list_users()

    @v1_router.get("/agent-config", response_model=AgentConfigResponse, tags=["Admin"], responses={200: {"description": "Retrieved current agent validation thresholds and concurrent limits"}, **COMMON_RESPONSES})
    def agent_config(ctx: Context) -> dict[str, Any]:
        """Return current session-scoped agent configuration.

        Readable by every role so clinicians can inspect the thresholds that
        govern their reviews; only the PUT endpoint is admin-gated.
        """

        return ctx[0].agent_config

    @v1_router.put("/agent-config", response_model=AgentConfigResponse, tags=["Admin"], responses={200: {"description": "Updated and persisted new agent thresholds configuration"}, **COMMON_RESPONSES})
    def save_agent_config(config: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Validate and save session-scoped agent configuration."""

        repo, role, user, _tenant = ctx
        if role != "admin":
            raise HTTPException(403, "Admin role required")
        allowed = {"autoApprovalThreshold", "reviewThreshold", "maxConcurrentRuns", "databaseEnabled"}
        unknown = set(config) - allowed - {"version"}
        if unknown:
            raise HTTPException(422, f"Unknown configuration keys: {', '.join(sorted(unknown))}")
        repo.agent_config.update({key: value for key, value in config.items() if key != "version"})
        repo.agent_config["version"] += 1
        repo.log("agent_config_saved", user, role, version=repo.agent_config["version"])
        return repo.agent_config

    @v1_router.get("/report-schedules", response_model=list[ReportScheduleResponse], tags=["Reports"], responses={200: {"description": "List every report with its recurring generation schedule"}, **COMMON_RESPONSES})
    def report_schedules(ctx: Context) -> list[dict[str, Any]]:
        """List every workspace report with its recurring generation schedule."""

        return list(ctx[0].report_schedules.values())

    @v1_router.put("/report-schedules/{report_id}", response_model=ReportScheduleResponse, tags=["Reports"], responses={200: {"description": "Updated the report's recurring generation frequency"}, **COMMON_RESPONSES})
    def save_report_schedule(report_id: str, body: ReportScheduleUpdateRequest, ctx: Context) -> dict[str, Any]:
        """Set how often a report is generated (off, daily, weekly, or monthly).

        The schedule is session-scoped like the rest of the demo state; every
        change is audit-logged so governance sees who altered report cadence.
        """

        repo, role, user, _tenant = ctx
        item = repo.report_schedules.get(report_id)
        if item is None:
            raise HTTPException(404, "Report not found")
        interval_days = {"daily": 1, "weekly": 7, "monthly": 30}.get(body.frequency)
        item["frequency"] = body.frequency
        item["updatedAt"] = now()
        item["nextRun"] = (datetime.now(UTC) + timedelta(days=interval_days)).strftime("%Y-%m-%d") if interval_days else None
        repo.log("report_schedule_updated", user, role, report_id=report_id, frequency=body.frequency)
        return item

    @v1_router.get("/visuals/{document_id}", tags=["Storage"], responses={200: {"description": "Serve patient structured visual image binary data"}, **COMMON_RESPONSES})
    def visual(document_id: str, ctx: Context) -> FileResponse:
        """Serve an agent-generated visual recorded in the documents table.

        Only image documents whose stored path resolves inside the tenant's
        uploads directory are served, so a forged document row cannot read
        arbitrary files.
        """

        from capstone_agent import database as clinical_db

        doc = clinical_db.get_document(document_id)
        if not doc or not str(doc.get("content_type", "")).startswith("image/"):
            raise HTTPException(404, "Visual not found")
        uploads_root = Path(clinical_db.active_uploads_root()).resolve()
        candidate = Path(doc.get("file_path") or "").resolve()
        if not candidate.is_file() or uploads_root not in candidate.parents:
            raise HTTPException(404, "Visual not found")
        return FileResponse(candidate, media_type=doc["content_type"])

    @v1_router.get("/audit", response_model=list[AuditEventResponse], tags=["Admin"], responses={200: {"description": "Immutable compliance activity and security log history"}, **COMMON_RESPONSES})
    def audit(ctx: Context, patient_id: str | None = None) -> list[dict[str, Any]]:
        """Return camelCase-compatible audit trail."""

        repo, role, _user, _tenant = ctx
        if role != "admin" and not patient_id:
            return [audit_view(item) for item in reversed(repo.audit)]
        rows = [item for item in repo.audit if not patient_id or item["details"].get("patient_id") == patient_id]
        return [audit_view(item) for item in reversed(rows)]

    @v1_router.get("/audit/{audit_id}", response_model=AuditEventDetailResponse, tags=["Admin"], responses={200: {"description": "Retrieved one audit event with its linked run and patient context"}, **COMMON_RESPONSES})
    def audit_event(audit_id: str, ctx: Context) -> dict[str, Any]:
        """Return one audit event enriched with the run and patient it references."""

        repo = ctx[0]
        item = next((entry for entry in repo.audit if entry["audit_id"] == audit_id), None)
        if item is None:
            raise HTTPException(404, "Audit event not found")
        details = item.get("details", {})
        view = audit_view(item)
        view["details"] = details
        run_item = repo.runs.get(str(details.get("run_id", "")))
        view["run"] = {
            "id": run_item["id"],
            "workflow": run_item["workflow"],
            "status": run_item["status"],
            "agentName": run_item.get("agentName", ""),
            "confidence": run_item.get("confidence"),
            "steps": [{"name": step.get("name", ""), "status": step.get("status", ""), "detail": step.get("detail", "")} for step in run_item.get("steps", [])],
        } if run_item else None
        patient = repo.patients.get(str(details.get("patient_id", "")))
        view["patient"] = {"id": patient.get("patient_id", ""), "name": patient.get("name", "")} if patient else None
        return view


    # --- V2 Service & Developer Console Endpoints ---

    @v2_router.get("/health", response_model=V2HealthResponse, tags=["System V2"], responses={200: {"description": "Retrieve health diagnostic metrics including database connection check"}, **COMMON_RESPONSES})
    def v2_health(ctx: Context) -> dict[str, Any]:
        """Report extended V2 health, including DB connectivity."""
        repo = ctx[0]
        db_connected = False
        if getattr(repo, "db_path", None) is not None:
            try:
                from capstone_agent import database as db
                res = db.execute_sql("SELECT 1")
                db_connected = bool(res.get("rows"))
            except Exception:
                pass
        else:
            db_connected = True  # demo repository has no file database but is healthy
        
        uploads_accessible = True
        if getattr(repo, "uploads_root", None) is not None:
            try:
                uploads_accessible = Path(repo.uploads_root).exists()
            except Exception:
                uploads_accessible = False

        return {
            "status": "ok",
            "mode": effective_mode(ctx[3]),
            "timestamp": now(),
            "databaseConnected": db_connected,
            "storageAccessible": uploads_accessible,
        }

    @v2_router.get("/mcp/tools", response_model=McpToolsListResponse, tags=["MCP V2"], responses={200: {"description": "Expose all database tools available over MCP"}, **COMMON_RESPONSES})
    async def list_mcp_tools() -> dict[str, Any]:
        """List all dynamic tools registered on the FastMCP clinical server."""
        try:
            from mcp_server.server import mcp
            tools_list = await mcp.list_tools()
            formatted = []
            for t in tools_list:
                formatted.append({
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                    "outputSchema": t.outputSchema,
                })
            return {"tools": formatted, "total": len(formatted)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list MCP tools: {e}")

    @v2_router.post("/mcp/execute", response_model=McpExecuteResponse, tags=["MCP V2"], responses={200: {"description": "Gated dynamic execution of an MCP tool"}, **COMMON_RESPONSES})
    async def execute_mcp_tool(body: McpExecuteRequest, ctx: Context) -> dict[str, Any]:
        """Run an MCP tool on the clinical server on behalf of the user/session."""
        repo, role, user, _tenant = ctx
        start_time = monotonic()
        try:
            from mcp_server.server import mcp
            if body.tool_name == "query_clinical_database":
                sql_query = body.arguments.get("sql", "")
                from capstone_agent.clinical_schemas import validate_sql
                safety = validate_sql(sql_query)
                if not safety["safe"]:
                    raise HTTPException(status_code=400, detail=f"SQL Blocked: {safety['reason']}")

            res = await mcp.call_tool(body.tool_name, body.arguments)
            duration = (monotonic() - start_time) * 1000.0
            
            repo.log(
                f"mcp_tool_execution_{body.tool_name}",
                user,
                role,
                arguments=body.arguments,
                duration_ms=duration,
            )
            
            return {
                "status": "success",
                "result": res,
                "durationMs": duration,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MCP execution failed: {e}")

    @v2_router.get("/a2a/card", response_model=A2aCardResponse, tags=["A2A V2"], responses={200: {"description": "Expose the Agent Card metadata for Agent-to-Agent discovery"}, **COMMON_RESPONSES})
    def a2a_card() -> dict[str, Any]:
        """Expose the Agent Card metadata for Agent-to-Agent discovery."""
        try:
            from capstone_agent.agent import root_agent
            pipelines_list = [p.name for p in root_agent.sub_agents]
            tools_list = []
            for t in root_agent.tools:
                if hasattr(t, "name"):
                    tools_list.append(t.name)
                elif hasattr(t, "tool_name"):
                    tools_list.append(t.tool_name)
                else:
                    tools_list.append(str(t))
            return {
                "name": root_agent.name,
                "description": root_agent.description,
                "instruction": root_agent.instruction[:500] + "..." if root_agent.instruction else None,
                "pipelines": pipelines_list,
                "tools": tools_list,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve A2A card: {e}")

    # Wiki folders live at the repository root; anchor them there instead of
    # trusting the server process working directory.
    wiki_root = Path(__file__).resolve().parents[1]

    @v2_router.get("/docs/list", tags=["System V2"], responses={200: {"description": "Expose a list of categories and files for both the Obsidian wiki and Karpathy LLM Wiki"}, **COMMON_RESPONSES})
    def docs_list() -> dict[str, Any]:
        """Expose a list of categories and files for both the Obsidian wiki and Karpathy LLM Wiki."""
        def get_wiki_files(base_dir: str) -> list[dict[str, str]]:
            files_list = []
            if not os.path.exists(base_dir):
                return files_list
            for root, dirs, files in os.walk(base_dir):
                if ".obsidian" in root or "_generated" in root:
                    continue
                for file in files:
                    if not file.endswith(".md"):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, base_dir)
                    title = os.path.splitext(file)[0]
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if content.startswith("---"):
                                parts = content.split("---", 2)
                                if len(parts) >= 3:
                                    for line in parts[1].split("\n"):
                                        if ":" in line:
                                            k, v = line.split(":", 1)
                                            if k.strip() == "title":
                                                title = v.strip().strip("'\"")
                                                break
                    except Exception:
                        pass
                    files_list.append({
                        "path": rel_path.replace("\\", "/"),
                        "title": title
                    })
            return files_list

        try:
            return {
                "obsidian": get_wiki_files(str(wiki_root / "Project Wiki")),
                "karpathy": get_wiki_files(str(wiki_root / "wiki"))
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list documentation files: {e}")

    @v2_router.get("/docs/file", tags=["System V2"], responses={200: {"description": "Retrieve content of an Obsidian or Karpathy wiki file"}, **COMMON_RESPONSES})
    def docs_file(type: str, path: str) -> dict[str, Any]:
        """Retrieve content of an Obsidian or Karpathy wiki file."""
        if type == "obsidian":
            base_dir = str(wiki_root / "Project Wiki")
        elif type == "karpathy":
            base_dir = str(wiki_root / "wiki")
        else:
            raise HTTPException(status_code=400, detail="Invalid doc type")
            
        clean_path = os.path.normpath(path).replace("..", "")
        resolved_base = os.path.abspath(base_dir)
        resolved_file = os.path.abspath(os.path.join(base_dir, clean_path))
        if not resolved_file.startswith(resolved_base):
            raise HTTPException(status_code=403, detail="Access denied")
            
        if not os.path.exists(resolved_file) or not os.path.isfile(resolved_file):
            raise HTTPException(status_code=404, detail="File not found")
            
        try:
            with open(resolved_file, "r", encoding="utf-8") as f:
                return {"content": f.read()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Register routers on api app instance
    api.include_router(v1_router, prefix="/api/v1")
    api.include_router(v2_router, prefix="/api/v2")
    api.include_router(v1_router, prefix="/api", include_in_schema=False)

    @api.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        from fastapi.openapi.docs import get_swagger_ui_html
        from fastapi.responses import HTMLResponse
        
        response = get_swagger_ui_html(
            openapi_url=api.openapi_url,
            title="Clinician AI Kit - API & Swagger Console",
            oauth2_redirect_url=api.swagger_ui_oauth2_redirect_url,
        )
        
        custom_css = """
        body {
            background-color: #0b0f19 !important;
            color: #f3f4f6 !important;
            font-family: 'Outfit', 'Inter', sans-serif !important;
            margin: 0;
            padding: 0;
        }
        .swagger-ui {
            background-color: #0b0f19 !important;
            color: #f3f4f6 !important;
        }
        .swagger-ui .info .title {
            color: #f3f4f6 !important;
            font-size: 2.2em !important;
            font-weight: 800 !important;
        }
        .swagger-ui .info p, .swagger-ui .info li, .swagger-ui .info td, .swagger-ui .info th {
            color: #9ca3af !important;
            font-size: 1.05em !important;
            line-height: 1.6 !important;
        }
        .swagger-ui .info a {
            color: #3b82f6 !important;
            text-decoration: none !important;
        }
        .swagger-ui .info a:hover {
            text-decoration: underline !important;
        }
        .swagger-ui .scheme-container {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
            border-radius: 12px !important;
            margin: 20px 0 !important;
            padding: 20px !important;
        }
        .swagger-ui select {
            background-color: #1f2937 !important;
            color: #f3f4f6 !important;
            border: 1px solid #374151 !important;
            border-radius: 6px !important;
            padding: 8px !important;
        }
        .swagger-ui input[type=text] {
            background-color: #1f2937 !important;
            color: #f3f4f6 !important;
            border: 1px solid #374151 !important;
            border-radius: 6px !important;
            padding: 8px !important;
        }
        .swagger-ui .opblock {
            border-radius: 10px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            border: 1px solid #1f2937 !important;
            margin-bottom: 12px !important;
            overflow: hidden !important;
        }
        .swagger-ui .opblock .opblock-summary {
            padding: 12px 20px !important;
        }
        .swagger-ui .opblock.opblock-get {
            background-color: rgba(59, 130, 246, 0.08) !important;
            border-color: rgba(59, 130, 246, 0.3) !important;
        }
        .swagger-ui .opblock.opblock-get .opblock-summary-method {
            background-color: #3b82f6 !important;
            color: #fff !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
        }
        .swagger-ui .opblock.opblock-post {
            background-color: rgba(16, 185, 129, 0.08) !important;
            border-color: rgba(16, 185, 129, 0.3) !important;
        }
        .swagger-ui .opblock.opblock-post .opblock-summary-method {
            background-color: #10b981 !important;
            color: #fff !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
        }
        .swagger-ui .opblock.opblock-put {
            background-color: rgba(245, 158, 11, 0.08) !important;
            border-color: rgba(245, 158, 11, 0.3) !important;
        }
        .swagger-ui .opblock.opblock-put .opblock-summary-method {
            background-color: #f59e0b !important;
            color: #fff !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
        }
        .swagger-ui .opblock .opblock-section-header {
            background-color: #111827 !important;
            border-bottom: 1px solid #1f2937 !important;
            padding: 10px 20px !important;
        }
        .swagger-ui .opblock .opblock-section-header h4 {
            color: #f3f4f6 !important;
        }
        .swagger-ui .tabli button {
            color: #9ca3af !important;
            font-weight: 600 !important;
        }
        .swagger-ui .tabli.active button {
            color: #f3f4f6 !important;
            border-bottom: 2px solid #3b82f6 !important;
        }
        .swagger-ui .responses-inner h4, .swagger-ui .responses-inner h5 {
            color: #f3f4f6 !important;
        }
        .swagger-ui .response-col_status {
            color: #f3f4f6 !important;
            font-weight: 700 !important;
        }
        .swagger-ui .response-col_description {
            color: #9ca3af !important;
        }
        .swagger-ui .parameter__name {
            color: #f3f4f6 !important;
            font-weight: 600 !important;
        }
        .swagger-ui .parameter__type {
            color: #9ca3af !important;
        }
        .swagger-ui .parameter__in {
            color: #6b7280 !important;
            font-style: italic !important;
        }
        .swagger-ui .model-box {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 8px !important;
            padding: 10px !important;
        }
        .swagger-ui .model {
            color: #f3f4f6 !important;
        }
        .swagger-ui .model-title {
            color: #3b82f6 !important;
            font-weight: 700 !important;
        }
        .swagger-ui .opblock-summary-path {
            color: #f3f4f6 !important;
            font-weight: 600 !important;
            font-size: 1.1em !important;
        }
        .swagger-ui .opblock-summary-description {
            color: #9ca3af !important;
        }
        .swagger-ui .btn.execute {
            background-color: #3b82f6 !important;
            border-color: #2563eb !important;
            color: #fff !important;
            border-radius: 6px !important;
            font-weight: 700 !important;
            padding: 8px 24px !important;
            transition: all 0.2s ease !important;
        }
        .swagger-ui .btn.execute:hover {
            background-color: #2563eb !important;
        }
        .swagger-ui .btn {
            border-radius: 6px !important;
            color: #9ca3af !important;
            border-color: #374151 !important;
            background-color: #1f2937 !important;
        }
        .swagger-ui .btn:hover {
            color: #f3f4f6 !important;
            background-color: #374151 !important;
        }
        .swagger-ui .model-toggle:after {
            filter: invert(1) !important;
        }
        .swagger-ui .dialog-ux .modal-ux {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 12px !important;
        }
        .swagger-ui .dialog-ux .modal-ux-header h3 {
            color: #f3f4f6 !important;
        }
        .swagger-ui .dialog-ux .modal-ux-content {
            color: #9ca3af !important;
        }
        .swagger-ui table thead tr td, .swagger-ui table thead tr th {
            border-bottom: 1px solid #1f2937 !important;
            color: #f3f4f6 !important;
            font-weight: 700 !important;
        }
        .swagger-ui .servers-title {
            color: #f3f4f6 !important;
        }
        .swagger-ui section.models {
            border: 1px solid #1f2937 !important;
            border-radius: 12px !important;
            background-color: #111827 !important;
        }
        .swagger-ui section.models h4 {
            color: #f3f4f6 !important;
            border-bottom: 1px solid #1f2937 !important;
            padding: 15px 20px !important;
        }
        """
        html = response.body.decode("utf-8")
        html_with_style = html.replace("</head>", f"<style>{custom_css}</style></head>")
        return HTMLResponse(content=html_with_style, status_code=200)

    @api.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        from fastapi.openapi.docs import get_redoc_html
        return get_redoc_html(
            openapi_url=api.openapi_url,
            title="Clinician AI Kit - ReDoc Specification"
        )

    # Standalone documentation hub — built into frontend/public/documentation by
    # scripts/build_docs_site.py and copied into dist/ by npm run build. Prefer
    # the built copy, but fall back to the committed source folder so the hub
    # serves without a frontend build (dev servers and the test client).
    project_root = Path(__file__).resolve().parents[1]
    for candidate in (project_root / "frontend" / "dist" / "documentation", project_root / "frontend" / "public" / "documentation"):
        if candidate.is_dir():
            api.mount("/documentation", StaticFiles(directory=candidate, html=True), name="documentation")
            break

    dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if dist.is_dir():
        assets = dist / "assets"
        if assets.is_dir():
            api.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

        @api.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            """Serve built frontend and fall back to SPA entry point."""

            if path in ("api", "docs", "redoc", "openapi.json") or path.startswith(("api/", "docs/", "redoc/")):
                raise HTTPException(404, "API route not found")
            candidate = (dist / path).resolve()
            if candidate.is_file() and dist.resolve() in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return api


app = create_app()
