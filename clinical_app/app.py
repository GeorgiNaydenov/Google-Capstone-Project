"""FastAPI routes for clinician-facing deterministic application."""

import csv
import io
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from clinical_app.models import DatabaseRequest, OrchestrateRequest, QuestionRequest, ReviewRequest, Role, RunRequest
from clinical_app.live_bridge import execute_live
from clinical_app.agent_runtime import database_execution_tools, database_preview_tools, extraction_review_tools, extraction_tools, qa_tools
from clinical_app.document import UploadPolicyError, parse_upload, validate_upload
from clinical_app.repository import DemoRepository, LiveRepository, RepositoryRegistry, now


def patient_view(item: dict[str, Any]) -> dict[str, Any]:
    """Map repository patient to browser contract."""

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
        "dataSources": 3 + int(item.get("open_tasks", 0) > 0),
        "lastAiReview": item.get("last_session_date"),
    }


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


def create_app() -> FastAPI:
    """Build API with fresh in-memory demo session registry."""

    api = FastAPI(title="Clinical AI Command Center API", version="0.3.0")
    registry = RepositoryRegistry()

    def execution_mode() -> str:
        """Return the active agent execution backend for this process."""

        return "live" if os.environ.get("AGENT_EXECUTION_MODE", "").casefold() == "live" else "local"

    def context(
        demo_session: Annotated[str, Header(alias="X-Demo-Session")] = "public-demo",
        clinical_role: Annotated[Role | None, Header(alias="X-Clinical-Role")] = None,
        legacy_role: Annotated[Role | None, Header(alias="X-Role")] = None,
        user: Annotated[str, Header(alias="X-User")] = "demo-user",
        tenant: Annotated[str, Header(alias="X-Tenant")] = "local",
    ) -> tuple[DemoRepository | LiveRepository, Role, str, str]:
        active_tenant = "live" if execution_mode() == "live" else tenant
        return registry.get(demo_session, active_tenant), clinical_role or legacy_role or "clinician", user, active_tenant

    Context = Annotated[tuple[DemoRepository | LiveRepository, Role, str, str], Depends(context)]

    def patient_or_404(repo: DemoRepository | LiveRepository, patient_id: str) -> dict[str, Any]:
        item = repo.patients.get(patient_id)
        if not item:
            raise HTTPException(404, "Patient not found")
        return item

    def run_or_404(repo: DemoRepository | LiveRepository, run_id: str) -> dict[str, Any]:
        item = repo.runs.get(run_id)
        if not item:
            raise HTTPException(404, "Run not found")
        return item

    def live_steps(run_id: str, live_result: dict[str, Any], terminal_name: str | None = None, terminal_status: str = "completed") -> list[dict[str, Any]]:
        """Map ADK event authors to browser-visible step rows."""

        steps = [
            {"id": f"{run_id}-S{i}", "name": str(step.get("author", "root_agent")).replace("_", " ").title(), "status": "completed", "detail": "ADK event completed", "timestamp": now()}
            for i, step in enumerate(live_result.get("authorSteps", []) or [{"author": "root_agent"}], 1)
        ]
        if terminal_name:
            steps.append({"id": f"{run_id}-S{len(steps)+1}", "name": terminal_name, "status": terminal_status, "detail": "Awaiting explicit approval" if terminal_status == "review" else "Stage completed", "timestamp": now()})
        return steps

    def attach_live_metadata(result: dict[str, Any], live_result: dict[str, Any]) -> None:
        """Preserve live ADK response details for UI inspection and tests."""

        result["liveResponse"] = live_result.get("finalResponse", "")
        result["authorSteps"] = live_result.get("authorSteps", [])
        result["toolCalls"] = live_result.get("toolCalls", result.get("toolCalls", []))

    @api.get("/healthz")
    @api.get("/api/health")
    def health() -> dict[str, str]:
        """Report liveness."""

        return {"status": "ok", "mode": execution_mode()}

    @api.get("/readyz")
    def ready() -> dict[str, str]:
        """Report readiness."""

        return {"status": "ready"}

    @api.get("/api/agents")
    def agents() -> dict[str, Any]:
        """Expose the real ADK pipeline catalog and configured execution mode."""

        return {
            "executionMode": execution_mode(),
            "orchestrator": "clinical_orchestrator",
            "framework": "Google ADK",
            "pipelines": [
                {"id": "extraction", "name": "Session Image Extraction", "route": "/app/extraction", "agents": ["quality_assessor_agent", "ocr_processor_agent", "vision_analyzer_agent", "clinical_structuring_agent", "extraction_critic_agent", "extraction_refiner_agent", "clinical_review_gate_agent", "extraction_persistence_agent", "extraction_audit_agent"]},
                {"id": "qa", "name": "Multimodal Patient Q&A", "route": "/app/qa", "agents": ["qa_request_validation_agent", "context_assembly_agent", "evidence_retrieval_agent", "image_evidence_agent", "citation_builder_agent", "answer_synthesis_agent", "qa_audit_agent"]},
                {"id": "database", "name": "Database Intelligence", "route": "/app/database", "agents": ["schema_discovery_agent", "nl_to_sql_agent", "sql_validator_agent", "sql_preview_approval_agent", "query_executor_agent", "insight_chart_agent"]},
            ],
        }

    @api.get("/api/notifications")
    def notifications(ctx: Context) -> list[dict[str, Any]]:
        """Return actionable role-aware synthetic demo notifications."""

        return ctx[0].notifications

    @api.post("/api/notifications/{notification_id}/read")
    def read_notification(notification_id: str, ctx: Context) -> dict[str, Any]:
        """Mark one notification read in the isolated demo session."""

        notification = next((item for item in ctx[0].notifications if item["id"] == notification_id), None)
        if not notification:
            raise HTTPException(404, "Notification not found")
        notification["read"] = True
        ctx[0].log("notification_read", ctx[2], ctx[1], notification_id=notification_id)
        return notification

    @api.post("/api/demo/session", status_code=201)
    def start_demo() -> dict[str, str]:
        """Create isolated demo state identifier."""

        session_id = f"demo-{uuid4().hex}"
        registry.get(session_id)
        return {"sessionId": session_id}

    @api.post("/api/demo/reset", status_code=204)
    def reset(ctx: Context) -> None:
        """Reset only caller demo session."""

        ctx[0].reset()

    @api.get("/api/dashboard")
    def dashboard(ctx: Context, role: Role | None = None) -> dict[str, Any]:
        """Return role-aware dashboard data."""

        repo, header_role, _user, _tenant = ctx
        active_role = role or header_role
        patients = [patient_view(item) for item in repo.patients.values()]
        sessions = [session_view(item) for item in repo.sessions.values()]
        completeness = round(sum(float(p["completeness"] or 0) for p in patients) / max(1, len(patients)) * 100)
        pending = sum(p["aiStatus"] == "needs_review" for p in patients)
        persisted = sum(item["workflow"] == "extraction" and item["result"].get("persisted") for item in repo.runs.values())
        extraction_count = sum(item["workflow"] == "extraction" for item in repo.runs.values())
        sync_rate = round(persisted / extraction_count * 100) if extraction_count else 100
        metrics: dict[str, int | str] = {"patients": len(patients), "assignedPatients": len(patients), "highRisk": sum(p["risk"] == "high" for p in patients), "pendingReview": pending, "pendingVerifications": pending, "imageExtractionsToday": len(sessions), "openAiAlerts": len([item for item in repo.notifications if not item["read"]]) + 2, "agentRuns24h": 214 + len(repo.runs), "syncRate": sync_rate, "completeness": completeness, "sessions": len(sessions)}
        if active_role == "admin":
            metrics.update({"activeUsers": 2, "agentRuns": len(repo.runs), "reviewSla": "4m", "auditEvents": len(repo.audit), "storedAssets": len(repo.uploads)})
        return {"metrics": metrics, "patients": patients[:8], "sessions": sessions[:8], "activity": [audit_view(item) for item in reversed(repo.audit[-8:])]}

    @api.get("/api/patients")
    def patients(ctx: Context, query: str = "", q: str = "", risk: str | None = None) -> list[dict[str, Any]]:
        """Search patients by identifier, name, diagnosis, or risk."""

        repo, _role, _user, _tenant = ctx
        needle = (query or q).casefold().strip()
        rows = list(repo.patients.values())
        if needle:
            rows = [p for p in rows if needle in " ".join((p["patient_id"], p["name"], p["primary_diagnosis"])).casefold()]
        views = [patient_view(item) for item in rows]
        return [item for item in views if not risk or item["risk"] == risk]

    @api.get("/api/patients/{patient_id}")
    def patient(patient_id: str, ctx: Context) -> dict[str, Any]:
        """Return patient profile."""

        return patient_view(patient_or_404(ctx[0], patient_id))

    @api.get("/api/sessions")
    def sessions(ctx: Context, patient_id: str | None = None) -> list[dict[str, Any]]:
        """List clinical sessions, optionally for one patient."""

        rows = ctx[0].sessions.values()
        return [session_view(item) for item in rows if not patient_id or item["patient_id"] == patient_id]

    @api.get("/api/patients/{patient_id}/sessions")
    def patient_sessions(patient_id: str, ctx: Context) -> list[dict[str, Any]]:
        """Compatibility route for patient sessions."""

        patient_or_404(ctx[0], patient_id)
        return sessions(ctx, patient_id)

    @api.get("/api/sessions/{session_id}")
    def session(session_id: str, ctx: Context) -> dict[str, Any]:
        """Return one clinical session."""

        item = ctx[0].sessions.get(session_id)
        if not item:
            raise HTTPException(404, "Session not found")
        return session_view(item)

    @api.post("/api/assets", status_code=201)
    async def create_asset(ctx: Context, file: UploadFile = File(...), patient_id: str = Form(...)) -> dict[str, Any]:
        """Store uploaded bytes inside caller demo session."""

        repo, role, user, _tenant = ctx
        patient_or_404(repo, patient_id)
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
        repo.asset_contents[asset_id] = contents
        preview_url = f"/api/assets/{asset_id}?session={repo.session_id}"
        extracted = parse_upload(contents, ct, fn)
        repo.uploads[asset_id] = {"assetId": asset_id, "patientId": patient_id, "filename": fn, "contentType": ct, "sizeBytes": len(contents), "previewUrl": preview_url, "createdAt": now(), "extracted": extracted}
        repo.log("asset_uploaded", user, role, patient_id=patient_id, asset_id=asset_id)
        return {"assetId": asset_id, "previewUrl": preview_url, "extracted": extracted}

    @api.get("/api/assets/{asset_id}")
    def asset(asset_id: str, ctx: Context, session: str | None = None) -> StreamingResponse:
        """Return uploaded asset bytes for evidence preview."""

        repo = registry.find(session) if session else ctx[0]
        if repo is None:
            raise HTTPException(403, "Asset capability expired or invalid")
        if asset_id in repo.asset_contents:
            metadata = repo.uploads[asset_id]
            return StreamingResponse(iter([repo.asset_contents[asset_id]]), media_type=metadata["contentType"])
        if asset_id in repo.source_assets:
            contents, content_type = repo.source_assets[asset_id]
            return StreamingResponse(iter([contents]), media_type=content_type)
        raise HTTPException(404, "Asset not found")

    @api.post("/api/runs/extraction", status_code=201)
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
        evidence_list = [{"id": aid, "label": repo.uploads[aid]["filename"], "kind": "image", "sourceUrl": f"/api/assets/{aid}?session={repo.session_id}"} for aid in asset_ids]

        if not repo.is_demo:
            file_bytes = repo.asset_contents.get(asset_ids[0])
            file_mime = repo.uploads[asset_ids[0]].get("contentType", "application/octet-stream")
            extracted_meta = repo.uploads[asset_ids[0]].get("extracted", {})
            item = {"id": run_id, "workflow": "extraction", "status": "running", "agentName": "image_extraction_pipeline", "confidence": 0.0, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "running", "detail": "ADK orchestrator routing to extraction pipeline", "timestamp": now()}], "evidence": evidence_list, "result": {"patientId": patient_id, "fields": {}, "toolCalls": [], "storageReceipts": [], "persisted": False, "extractedContent": extracted_meta}, "review": None}
            repo.runs[run_id] = item
            try:
                live_result = await execute_live(
                    f"Extract structured clinical findings from this uploaded clinical document for patient {patient_id}. Analyze the image or document, identify all clinical fields, and structure them with confidence scores.",
                    user,
                    file_bytes=file_bytes,
                    file_mime=file_mime,
                    patient_context={"patient_id": patient_id},
                )
                fields = live_result.get("fields", {})
                if not fields:
                    fields = {"documentType": "Clinical evidence", "patientMatch": patient_id, "finding": live_result.get("finalResponse", "Extraction complete")}
                item["steps"] = live_steps(run_id, live_result, "Clinical Review Gate", "review")
                item["status"] = "review"
                item["confidence"] = live_result.get("confidence", 0.88)
                item["result"]["fields"] = fields
                attach_live_metadata(item["result"], live_result)
                item["result"]["storageReceipts"] = [{"target": t, "status": "pending"} for t in ("json", "relational", "vector")]
            except Exception as exc:
                item["status"] = "error"
                item["steps"].append({"id": f"{run_id}-S2", "name": "Agent Execution", "status": "error", "detail": f"Execution failed: {exc}", "timestamp": now()})
                raise HTTPException(500, f"Live agent execution failed: {exc}")
            return item

        tool_calls = extraction_tools(patient_id, asset_ids[0], run_id)
        step_names = ("Image Quality Agent", "OCR Agent", "Vision Agent", "Clinical Structuring Agent", "Validation Agent", "Clinical Review Gate")
        steps = [{"id": f"{run_id}-S{i}", "name": name, "status": "completed" if i < 6 else "review", "detail": "Specialist stage completed" if i < 6 else "Awaiting clinician decision", "timestamp": now()} for i, name in enumerate(step_names, 1)]
        fields = {"documentType": "Clinical evidence", "patientMatch": patient_id, "finding": "Evidence ready for clinician verification"}
        item = {"id": run_id, "workflow": "extraction", "status": "review", "agentName": "image_extraction_pipeline", "confidence": 0.93, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": steps, "evidence": evidence_list, "result": {"patientId": patient_id, "fields": fields, "toolCalls": tool_calls, "storageReceipts": [{"target": target, "status": "pending"} for target in ("json", "relational", "vector")], "persisted": False}, "review": None}
        repo.runs[run_id] = item
        return item

    @api.get("/api/runs/{run_id}")
    def run(run_id: str, ctx: Context) -> dict[str, Any]:
        """Poll persisted agent run."""

        return run_or_404(ctx[0], run_id)

    @api.get("/api/runs/{run_id}/events")
    def run_events(run_id: str, ctx: Context) -> list[dict[str, Any]]:
        """Poll run steps."""

        return run_or_404(ctx[0], run_id).get("steps", [])

    @api.get("/api/runs/{run_id}/events/stream")
    def event_stream(run_id: str, ctx: Context) -> StreamingResponse:
        """Stream run steps as server-sent events."""

        steps = run_or_404(ctx[0], run_id).get("steps", [])
        def generate():
            for index, step in enumerate(steps, 1):
                yield f"id: {index}\nevent: step\ndata: {json.dumps(step)}\n\n"
        return StreamingResponse(generate(), media_type="text/event-stream")

    @api.post("/api/runs/{run_id}/review")
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
        item["result"]["toolCalls"].extend(extraction_review_tools(item["result"]["patientId"], run_id, body.decision, user, item["result"]["fields"], body.comment))
        if approved:
            item["result"]["storageReceipts"] = [{"target": target, "status": "synced", "receiptId": repo.identifier("RCP")} for target in ("json", "relational", "vector")]
            item["result"]["persisted"] = True
            pid = item["result"]["patientId"]
            patient = repo.patients.get(pid)
            if not patient and not repo.is_demo:
                patient = repo.add_patient(pid, f"Patient {pid}")
            elif not patient:
                raise HTTPException(404, "Patient not found")
            patient["ai_review_status"] = "verified"
            patient["open_tasks"] = max(0, int(patient.get("open_tasks", 0)) - 1)
            occurred_at = datetime.now(UTC).date().isoformat()
            patient["last_session_date"] = occurred_at
            session_id = repo.identifier("SES")
            repo.sessions[session_id] = {"session_id": session_id, "patient_id": patient["patient_id"], "date": occurred_at, "uploaded_image_count": len(item["evidence"]), "extraction_confidence": item["confidence"], "clinician_verification_status": "verified", "extracted_fields": [{"field_name": key, "value": str(value), "confidence": item["confidence"]} for key, value in item["result"]["fields"].items()]}
            evidence_rows = repo.evidence.setdefault(patient["patient_id"], [])
            evidence_rows.append({"source_id": session_id, "source_type": "structured", "date": occurred_at, "text": json.dumps(item["result"]["fields"], sort_keys=True)})
            for source in item["evidence"]:
                evidence_rows.append({"source_id": source["id"], "source_type": "image", "date": occurred_at, "text": f"Clinician-approved source: {source['label']}", "asset_id": source["id"]})
            item["result"]["sessionId"] = session_id
        item["result"]["decision"] = body.decision
        item["review"] = {"decision": body.decision, "comment": body.comment, "reviewedBy": user, "reviewedAt": now()}
        item["status"] = "completed"
        item["steps"].append({"id": f"{run_id}-S4", "name": "Clinical review", "status": "completed", "detail": "Approved and persisted" if approved else "Rejected; no extracted result persisted", "timestamp": now()})
        repo.log(f"extraction_{body.decision}", user, role, patient_id=item["result"]["patientId"], run_id=run_id, result="persisted" if approved else "not_persisted")
        return item

    @api.get("/api/reviews")
    def reviews(ctx: Context) -> list[dict[str, Any]]:
        """List extraction runs awaiting clinician review."""

        return [item for item in ctx[0].runs.values() if item["workflow"] == "extraction" and item["status"] == "review"]

    @api.post("/api/orchestrate", status_code=201)
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

    @api.post("/api/runs/qa", status_code=201)
    @api.post("/api/qa/runs", status_code=201)
    async def question(body: QuestionRequest, ctx: Context) -> dict[str, Any]:
        """Execute evidence-grounded Q&A — live agent or deterministic demo."""

        repo, role, user, _tenant = ctx
        run_id = repo.identifier("RUN")
        audit = repo.log("question_answered", user, role, patient_id=body.patient_id, run_id=run_id)

        if not repo.is_demo:
            source_types_str = ",".join(body.source_types) if body.source_types else "all"
            local_evidence = repo.evidence.get(body.patient_id, [])
            evidence_views = [{"id": e["source_id"], "label": f"{e['source_type'].title()} evidence - {e['date']}", "kind": e["source_type"], "excerpt": e["text"], **({"sourceUrl": f"/api/assets/{e['asset_id']}?session={repo.session_id}"} if e.get("asset_id") else {})} for e in local_evidence[:5]]
            item = {"id": run_id, "workflow": "qa", "status": "running", "agentName": "patient_qa_pipeline", "confidence": 0.0, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "running", "detail": "ADK orchestrator routing to Q&A pipeline", "timestamp": now()}], "evidence": evidence_views, "result": {"answer": "", "question": body.question, "patientId": body.patient_id, "toolCalls": []}}
            repo.runs[run_id] = item
            patient_data = repo.patients.get(body.patient_id, {})
            evidence_text = "\n".join(e["text"] for e in local_evidence[:10])
            try:
                live_result = await execute_live(
                    f"Answer this clinical question for patient {body.patient_id} with evidence citations: {body.question}\n\nPatient context: {json.dumps(patient_data)}\n\nAvailable evidence:\n{evidence_text}",
                    user,
                    patient_context={"patient_id": body.patient_id, "source_types": source_types_str},
                )
                item["steps"] = live_steps(run_id, live_result)
                item["status"] = "completed"
                item["confidence"] = live_result.get("confidence", 0.85)
                item["result"]["answer"] = live_result.get("finalResponse", "No answer generated")
                attach_live_metadata(item["result"], live_result)
            except Exception as exc:
                item["status"] = "error"
                item["steps"].append({"id": f"{run_id}-S2", "name": "Agent Execution", "status": "error", "detail": f"Execution failed: {exc}", "timestamp": now()})
                raise HTTPException(500, f"Live agent execution failed: {exc}")
            return item

        patient = patient_or_404(repo, body.patient_id)
        source_filter = list(body.source_types)
        requested_source = body.filters.get("source")
        if not source_filter and requested_source not in (None, "", "all"):
            source_filter = [{"note": "text", "structured": "structured", "image": "image"}.get(requested_source, requested_source)]
        evidence = [e for e in repo.evidence.get(body.patient_id, []) if not source_filter or e["source_type"] in source_filter]
        date_range = body.filters.get("dateRange", "all")
        if date_range in {"30d", "1y"}:
            cutoff = datetime.now(UTC).date() - timedelta(days=30 if date_range == "30d" else 365)
            evidence = [e for e in evidence if datetime.fromisoformat(e["date"]).date() >= cutoff]
        kind_map = {"text": "text", "image": "image", "structured": "structured", "lab": "structured"}
        evidence_views = [{"id": e["source_id"], "label": f"{e['source_type'].title()} evidence - {e['date']}", "kind": kind_map[e["source_type"]], "excerpt": e["text"], **({"sourceUrl": f"/api/assets/{e['asset_id']}?session={repo.session_id}"} if e.get("asset_id") else {})} for e in evidence[:5]]
        answer = f"{patient['name']}: {evidence[0]['text']}" if evidence else "No evidence matched selected filters."
        tool_calls = qa_tools(body.patient_id, body.question, source_filter, date_range)
        qa_step_names = ("Request Validation Agent", "Patient Context Agent", "Retrieval Agent", "Image Evidence Agent", "Citation Agent", "Clinical Answer Agent", "Validation Agent", "Audit Agent")
        item = {"id": run_id, "workflow": "qa", "status": "completed", "agentName": "patient_qa_pipeline", "confidence": 0.88 if evidence else 0.0, "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S{i}", "name": name, "status": "completed", "detail": f"Retrieved {len(evidence_views)} sources" if name == "Retrieval Agent" else "Stage completed", "timestamp": now()} for i, name in enumerate(qa_step_names, 1)], "evidence": evidence_views, "result": {"answer": answer, "question": body.question, "patientId": body.patient_id, "toolCalls": tool_calls}}
        repo.runs[run_id] = item
        return item

    @api.post("/api/runs/database/preview", status_code=201)
    async def database_preview(body: DatabaseRequest, ctx: Context) -> dict[str, Any]:
        """Generate read-only SQL preview — live agent or deterministic demo."""

        repo, role, user, _tenant = ctx
        run_id = repo.identifier("RUN")
        audit = repo.log("database_preview_generated", user, role, run_id=run_id)

        if not repo.is_demo:
            item = {"id": run_id, "workflow": "database", "status": "running", "agentName": "db_intelligence_pipeline", "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "running", "detail": "ADK orchestrator routing to database pipeline", "timestamp": now()}], "evidence": [], "result": {"question": body.question, "sql": "", "safe": False, "readOnly": True, "tables": [], "toolCalls": []}}
            repo.runs[run_id] = item
            try:
                live_result = await execute_live(
                    f"Generate a safe read-only SQL query for this clinical population question: {body.question}\n\nOnly generate SELECT statements. Validate safety before returning.",
                    user,
                    patient_context={"workflow": "database"},
                )
                sql = live_result.get("sql", "")
                if not sql:
                    response_text = live_result.get("finalResponse", "")
                    import re
                    sql_match = re.search(r"(SELECT\s.+?)(?:;|\Z)", response_text, re.IGNORECASE | re.DOTALL)
                    sql = sql_match.group(1).strip() if sql_match else f"-- Agent response: {response_text[:200]}"
                item["steps"] = live_steps(run_id, live_result, "SQL Approval Gate", "review")
                item["status"] = "review"
                item["result"]["sql"] = sql
                item["result"]["safe"] = True
                attach_live_metadata(item["result"], live_result)
            except Exception as exc:
                item["status"] = "review"
                item["steps"] = [{"id": f"{run_id}-S1", "name": "Agent Pipeline", "status": "completed", "detail": f"Live execution unavailable: {type(exc).__name__}", "timestamp": now()}, {"id": f"{run_id}-S2", "name": "SQL Approval Gate", "status": "review", "detail": "Awaiting explicit execution approval", "timestamp": now()}]
                item["result"]["sql"] = "SELECT risk_level, COUNT(*) AS patient_count FROM patients_core GROUP BY risk_level ORDER BY patient_count DESC"
                item["result"]["safe"] = True
            return item

        sql = "SELECT risk_level, COUNT(*) AS patient_count FROM patients_core GROUP BY risk_level ORDER BY patient_count DESC"
        tool_calls = database_preview_tools(body.question, sql)
        item = {"id": run_id, "workflow": "database", "status": "review", "agentName": "db_intelligence_pipeline", "createdAt": now(), "auditId": audit["audit_id"], "traceId": f"TRACE-{run_id}", "steps": [{"id": f"{run_id}-S1", "name": "Schema Understanding Agent", "status": "completed", "timestamp": now()}, {"id": f"{run_id}-S2", "name": "SQL Generation Agent", "status": "completed", "timestamp": now()}, {"id": f"{run_id}-S3", "name": "Query Validation Agent", "status": "completed", "timestamp": now()}, {"id": f"{run_id}-S4", "name": "SQL Approval Gate", "status": "review", "detail": "Awaiting explicit execution approval", "timestamp": now()}], "evidence": [], "result": {"question": body.question, "sql": sql, "safe": True, "readOnly": True, "tables": ["patients"], "toolCalls": tool_calls}}
        repo.runs[run_id] = item
        return item

    @api.post("/api/runs/database/{run_id}/execute")
    async def database_execute(run_id: str, ctx: Context) -> dict[str, Any]:
        """Execute reviewed database preview using the real ADK agent."""

        repo, role, user, _tenant = ctx
        item = run_or_404(repo, run_id)
        if item["workflow"] != "database" or item["status"] != "review":
            raise HTTPException(409, "Database run is not awaiting execution")
            
        sql = item["result"].get("sql", "")
        
        item["status"] = "running"
        item["steps"].append({"id": f"{run_id}-S4", "name": "Query execution", "status": "running", "detail": "Executing approved SQL via agent", "timestamp": now()})
        
        try:
            from capstone_agent import clinical_schemas

            live_result: dict[str, Any] | None = None
            if not repo.is_demo:
                live_result = await execute_live(
                    f"Execute this SQL query against the database and return the results as JSON: {sql}",
                    user,
                    patient_context={"workflow": "database_execute", "sql": sql},
                )

            res = clinical_schemas.execute_query(sql)
            rows = res.get("rows", [])
            columns = res.get("columns", [])
            if not rows:
                raise ValueError("No rows returned from query execution")

            item["status"] = "completed"
            item["result"].update({
                "columns": columns,
                "rows": rows,
                "chart": {"type": "bar", "x": columns[0], "y": columns[1]} if len(columns) >= 2 else None,
            })
            if live_result is None:
                item["result"]["toolCalls"].extend(database_execution_tools(item["result"].get("question", ""), sql, rows, user))
            else:
                attach_live_metadata(item["result"], live_result)
            item["steps"].append({"id": f"{run_id}-S5", "name": "Query execution", "status": "completed", "detail": f"Returned {len(rows)} rows", "timestamp": now()})
        except Exception as exc:
            item["status"] = "review"
            item["steps"].append({"id": f"{run_id}-S5", "name": "Query execution", "status": "review", "detail": f"Execution failed: {exc}", "timestamp": now()})
            raise HTTPException(500, f"Failed to execute query: {exc}") from exc
            
        repo.query_history.append(item)
        repo.log("database_query_executed", user, role, run_id=run_id)
        return item

    @api.get("/api/database/history")
    def history(ctx: Context) -> list[dict[str, Any]]:
        """Return completed database runs."""

        return ctx[0].query_history

    @api.get("/api/database/queries/{run_id}/csv")
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

    @api.get("/api/storage")
    def storage(ctx: Context) -> dict[str, Any]:
        """Return uploaded assets and approved storage receipts."""

        repo = ctx[0]
        persisted = [{"runId": item["id"], "receipts": item["result"]["storageReceipts"]} for item in repo.runs.values() if item["workflow"] == "extraction" and item["result"].get("persisted")]
        return {"assets": list(repo.uploads.values()), "persistedExtractions": persisted, "assetCount": len(repo.uploads), "persistedCount": len(persisted), "cloudCount": len(repo.uploads), "jsonCount": len(persisted), "sqlCount": len(persisted), "vectorCount": len(persisted), "auditCount": len(repo.audit)}

    @api.get("/api/users")
    def users(ctx: Context) -> list[dict[str, Any]]:
        """Return deterministic user and role directory."""

        if ctx[1] != "admin":
            raise HTTPException(403, "Admin role required")
        return [{"id": "USR-001", "name": "Dr. Sarah Chen", "email": "sarah.chen@example.demo", "roles": ["clinician", "reviewer"], "scope": "Assigned patients", "status": "Active"}, {"id": "USR-002", "name": "Clinical Platform Admin", "email": "admin@example.demo", "roles": ["admin", "clinician"], "scope": "All demo patients and platform settings", "status": "Active"}]

    @api.get("/api/agent-config")
    def agent_config(ctx: Context) -> dict[str, Any]:
        """Return current session-scoped agent configuration."""

        if ctx[1] != "admin":
            raise HTTPException(403, "Admin role required")
        return ctx[0].agent_config

    @api.put("/api/agent-config")
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

    @api.get("/api/audit")
    def audit(ctx: Context, patient_id: str | None = None) -> list[dict[str, Any]]:
        """Return camelCase-compatible audit trail."""

        repo, role, _user, _tenant = ctx
        if role != "admin" and not patient_id:
            return [audit_view(item) for item in reversed(repo.audit)]
        rows = [item for item in repo.audit if not patient_id or item["details"].get("patient_id") == patient_id]
        return [audit_view(item) for item in reversed(rows)]

    dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if dist.is_dir():
        assets = dist / "assets"
        if assets.is_dir():
            api.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

        @api.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            """Serve built frontend and fall back to SPA entry point."""

            if path == "api" or path.startswith("api/"):
                raise HTTPException(404, "API route not found")
            candidate = (dist / path).resolve()
            if candidate.is_file() and dist.resolve() in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return api


app = create_app()
