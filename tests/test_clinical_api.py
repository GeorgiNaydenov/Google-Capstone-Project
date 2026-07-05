"""Frontend contract tests for deterministic clinician product API."""

from fastapi.testclient import TestClient

from clinical_app.app import create_app


def client() -> TestClient:
    """Create API client with isolated repository registry."""

    return TestClient(create_app())


def clinician(session: str = "clinical-test") -> dict[str, str]:
    """Build clinician browser headers."""

    return {"X-Demo-Session": session, "X-Clinical-Role": "clinician", "X-User": "Dr. Test"}


def admin(session: str = "clinical-test") -> dict[str, str]:
    """Build admin browser headers."""

    return {"X-Demo-Session": session, "X-Clinical-Role": "admin", "X-User": "Admin Test"}


def upload_asset(api: TestClient, headers: dict[str, str], patient_id: str = "PT-8829") -> str:
    """Upload real multipart bytes and return browser asset identifier."""

    contents = b"\x89PNG\r\n\x1a\nsynthetic"
    response = api.post(
        "/api/assets", headers=headers, data={"patient_id": patient_id},
        files={"file": ("scan.png", contents, "image/png")},
    )
    assert response.status_code == 201
    assert response.json()["previewUrl"].startswith("/api/assets/")
    return response.json()["assetId"]


def test_health_demo_and_camel_case_read_contracts() -> None:
    """Health, demo, dashboard, patient, and session shapes match frontend."""

    api = client()
    assert api.get("/healthz").json() == {"status": "ok", "mode": "local"}
    assert api.get("/readyz").json() == {"status": "ready"}
    created = api.post("/api/demo/session")
    assert created.status_code == 201
    headers = clinician(created.json()["sessionId"])
    dashboard = api.get("/api/dashboard", headers=headers, params={"role": "clinician"}).json()
    assert dashboard["metrics"]["patients"] == 24
    assert dashboard["patients"][0]["id"] == "PT-8829"
    matches = api.get("/api/patients", headers=headers, params={"query": "lung"}).json()
    assert [patient["id"] for patient in matches] == ["PT-8829"]
    profile = api.get("/api/patients/PT-8829", headers=headers).json()
    assert profile["mrn"] == "MRN-8829"
    sessions = api.get("/api/sessions", headers=headers, params={"patient_id": "PT-8829"}).json()
    assert sessions[0]["patientId"] == "PT-8829"
    assert api.get(f"/api/sessions/{sessions[0]['id']}", headers=headers).json()["occurredAt"] == "2026-06-15"


def test_extraction_is_review_gated_and_approval_persists() -> None:
    """Storage stays pending until clinician approval then becomes synced."""

    api = client()
    headers = clinician("approval")
    asset_id = upload_asset(api, headers)
    assert api.get(f"/api/assets/{asset_id}", headers=headers).content == b"\x89PNG\r\n\x1a\nsynthetic"
    response = api.post("/api/runs/extraction", headers=headers, json={"assetId": asset_id, "patientId": "PT-8829"})
    assert response.status_code == 201
    run = response.json()
    assert run["workflow"] == "extraction" and run["status"] == "review"
    assert run["steps"] and run["evidence"] and run["result"]
    assert {receipt["status"] for receipt in run["result"]["storageReceipts"]} == {"pending"}
    assert run["result"]["persisted"] is False
    assert api.get("/api/storage", headers=headers).json()["persistedCount"] == 0
    assert api.get("/api/reviews", headers=headers).json()[0]["id"] == run["id"]
    approved = api.post(
        f"/api/runs/{run['id']}/review", headers=headers,
        json={"decision": "approved", "fields": {"documentType": "Verified CT", "patientMatch": "PT-8829"}},
    ).json()
    assert approved["status"] == "completed"
    assert approved["result"]["persisted"] is True
    assert {receipt["status"] for receipt in approved["result"]["storageReceipts"]} == {"synced"}
    assert api.get("/api/storage", headers=headers).json()["persistedCount"] == 1
    assert api.get("/api/reviews", headers=headers).json() == []
    patient = api.get("/api/patients/PT-8829", headers=headers).json()
    assert patient["aiStatus"] == "verified"
    sessions = api.get("/api/sessions", headers=headers, params={"patient_id": "PT-8829"}).json()
    assert sessions[-1]["id"] == approved["result"]["sessionId"]
    image_qa = api.post(
        "/api/runs/qa", headers=headers,
        json={"patientId": "PT-8829", "question": "Show approved imaging", "filters": {"source": "image", "dateRange": "30d"}},
    ).json()
    assert image_qa["evidence"][0]["sourceUrl"].startswith("/api/assets/")
    assert api.get(image_qa["evidence"][0]["sourceUrl"]).status_code == 200
    assert api.get(image_qa["evidence"][0]["sourceUrl"].replace("approval", "expired")).status_code == 403


def test_rejection_never_persists_extraction() -> None:
    """Rejected extraction remains absent from persisted storage."""

    api = client()
    headers = clinician("rejection")
    asset_id = upload_asset(api, headers, "PT-1044")
    run = api.post("/api/runs/extraction", headers=headers, json={"assetId": asset_id, "patientId": "PT-1044"}).json()
    rejected = api.post(f"/api/runs/{run['id']}/review", headers=headers, json={"decision": "rejected"}).json()
    assert rejected["result"]["persisted"] is False
    assert {receipt["status"] for receipt in rejected["result"]["storageReceipts"]} == {"pending"}
    assert api.get("/api/storage", headers=headers).json()["persistedCount"] == 0


def test_qa_database_admin_and_configuration_contracts() -> None:
    """Q&A, database aliases, audit, users, and config match browser API."""

    api = client()
    clinical_headers = clinician("workflows")
    qa = api.post(
        "/api/runs/qa", headers=clinical_headers,
        json={"patientId": "PT-9921", "question": "What changed?", "filters": {"source": "text"}},
    )
    assert qa.status_code == 201
    qa_run = qa.json()
    assert qa_run["workflow"] == "qa" and qa_run["evidence"][0]["kind"] == "text"
    assert api.get(f"/api/runs/{qa_run['id']}", headers=clinical_headers).json()["result"]["answer"]
    clinician_preview = api.post("/api/runs/database/preview", headers=clinical_headers, json={"question": "Count risk groups"})
    assert clinician_preview.status_code == 201
    assert api.post(f"/api/runs/database/{clinician_preview.json()['id']}/execute", headers=clinical_headers).status_code == 200
    admin_headers = admin("workflows")
    preview = api.post("/api/runs/database/preview", headers=admin_headers, json={"question": "Count risk groups"}).json()
    assert preview["status"] == "review" and preview["result"]["safe"] is True
    executed = api.post(f"/api/runs/database/{preview['id']}/execute", headers=admin_headers).json()
    assert executed["status"] == "completed" and executed["result"]["chart"]["type"] == "bar"
    assert sum(row["patient_count"] for row in executed["result"]["rows"]) == 24
    assert len(api.get("/api/users", headers=admin_headers).json()) >= 5
    config = api.get("/api/agent-config", headers=admin_headers).json()
    saved = api.put("/api/agent-config", headers=admin_headers, json={"autoApprovalThreshold": 94, "reviewThreshold": 70, "maxConcurrentRuns": 12, "databaseEnabled": False}).json()
    assert saved["version"] == config["version"] + 1 and saved["autoApprovalThreshold"] == 94
    users = api.get("/api/users", headers=admin_headers).json()
    assert any("Admin" in user["roles"] for user in users) and all(user["scope"] for user in users)
    metrics = api.get("/api/dashboard", headers=admin_headers, params={"role": "admin"}).json()["metrics"]
    assert {"activeUsers", "agentRuns", "syncRate", "reviewSla", "highRisk", "pendingReview", "completeness"} <= set(metrics)
    audit = api.get("/api/audit", headers=admin_headers).json()
    assert {"id", "timestamp", "event", "actor", "entity", "result"} <= set(audit[0])


def test_agent_catalog_and_notifications_are_actionable() -> None:
    """The shell discovers ADK pipelines and persists notification reads."""

    api = client()
    request_headers = clinician("shell-contracts")
    catalog = api.get("/api/agents", headers=request_headers).json()
    assert catalog["framework"] == "Google ADK"
    assert catalog["orchestrator"] == "clinical_orchestrator"
    assert {pipeline["id"] for pipeline in catalog["pipelines"]} == {"extraction", "qa", "database"}
    assert all(pipeline["agents"] for pipeline in catalog["pipelines"])
    notices = api.get("/api/notifications", headers=request_headers).json()
    assert len(notices) == 3 and all(not notice["read"] for notice in notices)
    updated = api.post(f"/api/notifications/{notices[0]['id']}/read", headers=request_headers)
    assert updated.status_code == 200 and updated.json()["read"] is True
    assert api.get("/api/notifications", headers=request_headers).json()[0]["read"] is True


def test_demo_session_state_isolation_and_reset() -> None:
    """Uploads and mutable config never cross demo sessions."""

    api = client()
    upload_asset(api, clinician("one"))
    assert api.get("/api/storage", headers=clinician("one")).json()["assetCount"] == 1
    assert api.get("/api/storage", headers=clinician("two")).json()["assetCount"] == 0
    assert api.post("/api/demo/reset", headers=clinician("one")).status_code == 204
    assert api.get("/api/storage", headers=clinician("one")).json()["assetCount"] == 0


def test_orchestration_classifies_context_and_audits_plan() -> None:
    """Planner routes three workflows only with required context and permission."""

    api = client()
    headers = clinician("orchestration")
    extraction = api.post(
        "/api/orchestrate", headers=headers,
        json={"query": "Extract findings from this uploaded CT scan", "patientId": "PT-8829"},
    )
    assert extraction.status_code == 201
    assert extraction.json()["workflow"] == "extraction"
    assert extraction.json()["route"] == "/app/extraction"
    assert extraction.json()["agents"] and extraction.json()["dataSources"]
    qa = api.post(
        "/api/orchestrate", headers=headers,
        json={"query": "What changed in recent evidence?", "patientId": "PT-9921"},
    ).json()
    assert qa["intent"] == "answer_patient_question" and qa["workflow"] == "qa"
    assert api.post("/api/orchestrate", headers=headers, json={"query": "Summarize recent evidence"}).status_code == 422
    database = api.post("/api/orchestrate", headers=headers, json={"query": "Count population risk cohorts"}).json()
    assert database["workflow"] == "database" and database["route"] == "/app/database"
    audit = api.get("/api/audit", headers=admin("orchestration")).json()
    plans = [event for event in audit if event["event"] == "orchestration_plan_created"]
    assert len(plans) == 3


def test_upload_limit_and_repository_eviction() -> None:
    """Uploads cap at 10 MB and registry evicts least-recent session."""

    from clinical_app.repository import RepositoryRegistry

    api = client()
    oversized = api.post(
        "/api/assets", headers=clinician("upload-limit"), data={"patient_id": "PT-8829"},
        files={"file": ("large.pdf", b"x" * 10_000_001, "application/pdf")},
    )
    assert oversized.status_code == 413
    registry = RepositoryRegistry(max_count=2, ttl_seconds=3600)
    first = registry.get("first")
    first.uploads["sentinel"] = {"assetId": "sentinel"}
    registry.get("second")
    registry.get("third")
    assert "sentinel" not in registry.get("first").uploads


def test_live_mode_uses_lazy_bridge_and_persists_metadata(tmp_path, monkeypatch) -> None:
    """The real (Capstone) tenant invokes the bridge while demo stays offline."""

    import importlib

    app_module = importlib.import_module("clinical_app.app")
    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)

    async def fake_live(query: str, user_id: str, **_: object) -> dict[str, object]:
        assert query and user_id
        return {"finalResponse": "Safe live response", "authorSteps": [{"author": "root_agent", "eventId": "EV-1"}]}

    original_bridge = app_module.execute_live
    try:
        app_module.execute_live = fake_live
        api = TestClient(app_module.create_app())
        capstone = {**clinician("live"), "X-Tenant": "capstone"}
        run = api.post(
            "/api/runs/qa", headers=capstone,
            json={"patientId": "PT-9921", "question": "Summarize recent status"},
        ).json()
        assert run["result"]["liveResponse"] == "Safe live response"
        assert run["result"]["authorSteps"][0]["author"] == "root_agent"
        assert any(step["name"] == "Root Agent" for step in run["steps"])
        # Demo tenants never touch the model even when the bridge is patched.
        demo_run = api.post(
            "/api/runs/qa", headers=clinician("demo-live"),
            json={"patientId": "PT-9921", "question": "Summarize recent status"},
        ).json()
        assert "liveResponse" not in demo_run["result"]
    finally:
        app_module.execute_live = original_bridge


def test_tenant_header_selects_distinct_demo_datasets() -> None:
    """Same browser session sees different data per tenant with full isolation."""

    api = client()
    research = {**clinician("tenants"), "X-Tenant": "research-clinic"}
    northstar = {**clinician("tenants"), "X-Tenant": "northstar-health"}
    research_patients = api.get("/api/patients", headers=research).json()
    northstar_patients = api.get("/api/patients", headers=northstar).json()
    assert len(research_patients) == 24 and research_patients[0]["id"] == "PT-8829"
    assert len(northstar_patients) == 12 and northstar_patients[0]["id"] == "PT-7301"
    assert not {p["id"] for p in research_patients} & {p["id"] for p in northstar_patients}
    northstar_notices = api.get("/api/notifications", headers=northstar).json()
    assert {n["id"] for n in northstar_notices} == {"NTF-N01", "NTF-N02", "NTF-N03"}
    assert api.post("/api/notifications/NTF-001/read", headers=research).status_code == 200
    assert sum(not n["read"] for n in api.get("/api/notifications", headers=research).json()) == 2
    assert sum(not n["read"] for n in api.get("/api/notifications", headers=northstar).json()) == 3


def test_legacy_tenant_values_map_to_research_clinic() -> None:
    """Old header values and missing headers keep the original demo dataset."""

    api = client()
    for legacy in ("local", "demo", None):
        headers = clinician(f"legacy-{legacy}")
        if legacy is not None:
            headers["X-Tenant"] = legacy
        patients = api.get("/api/patients", headers=headers).json()
        assert len(patients) == 24 and patients[0]["id"] == "PT-8829"


def test_registry_keys_by_tenant() -> None:
    """One session id yields separate repositories per tenant; find() resolves MRU."""

    from clinical_app.repository import RepositoryRegistry
    from clinical_app.tenancy import TENANTS

    registry = RepositoryRegistry()
    research = registry.get("shared", TENANTS["research-clinic"])
    northstar = registry.get("shared", TENANTS["northstar-health"])
    assert research is not northstar
    assert registry.find("shared") is northstar
    assert registry.get("shared", TENANTS["research-clinic"]) is research
    assert registry.find("missing") is None


def test_system_health_reports_measured_components_without_model_key() -> None:
    """Component health rows are measured and well-formed even with no credentials."""

    api = client()
    payload = api.get("/api/system/health", headers=clinician()).json()
    names = {component["name"] for component in payload["components"]}
    assert {"Clinical database", "ADK agent runtime", "MCP tool server", "Upload storage", "Model credentials", "Frontend bundle"} <= names
    for component in payload["components"]:
        assert component["status"] in {"operational", "unavailable"}
        assert component["latencyMs"] >= 0
        assert component["detail"]
    assert payload["checkedAt"]


def test_database_schema_endpoint_lists_governed_tables() -> None:
    """Schema explorer data comes from the real governed DDL."""

    api = client()
    tables = api.get("/api/database/schema", headers=clinician()).json()
    by_name = {table["table"]: table for table in tables}
    assert "patients_core" in by_name
    columns = {column["name"] for column in by_name["patients_core"]["columns"]}
    assert {"patient_id", "risk_level", "primary_diagnosis"} <= columns


def test_permissions_matrix_default_and_admin_edit() -> None:
    """Permission matrix serves the default grants and accepts admin edits."""

    api = client()
    denied = api.get("/api/permissions", headers=clinician())
    assert denied.status_code == 403
    matrix = api.get("/api/permissions", headers=admin()).json()
    assert matrix["roles"][0] == "Admin"
    assert any(row["permission"] == "Run clinical agents" for row in matrix["matrix"])
    edited = dict(matrix)
    edited["matrix"][0]["grants"]["Data Manager"] = True
    saved = api.put("/api/permissions", headers=admin(), json={"matrix": edited["matrix"]}).json()
    assert saved["version"] == matrix["version"] + 1
    assert saved["matrix"][0]["grants"]["Data Manager"] is True


def test_agent_monitoring_merges_demo_baseline_with_session_runs() -> None:
    """Demo monitoring shows the plausible baseline plus real session runs."""

    api = client()
    assert api.get("/api/agents/monitoring", headers=clinician()).status_code == 403
    rows = api.get("/api/agents/monitoring", headers=admin()).json()
    assert any(row["agent"] == "Vision Agent" for row in rows)
    for row in rows:
        assert row["status"] in {"healthy", "degraded"}
        assert 0.0 <= row["avgConfidence"] <= 1.0


def test_summary_counts_reflect_repository_state() -> None:
    """Navigation badge counts derive from live repository state."""

    api = client()
    headers = clinician()
    summary = api.get("/api/summary", headers=headers).json()
    assert summary["patients"] == 24
    assert summary["queueCount"] > 0
    assert summary["runs"] == 0
    asset_id = upload_asset(api, headers)
    run = api.post("/api/runs/extraction", headers=headers, json={"patientId": "PT-8829", "uploadIds": [asset_id]}).json()
    assert run["status"] == "review"
    refreshed = api.get("/api/summary", headers=headers).json()
    assert refreshed["runs"] == 1
    assert refreshed["inboxCount"] == 1


def test_patient_evidence_endpoint_returns_sources() -> None:
    """Patient evidence rows expose kind, date, excerpt, and viewable links."""

    api = client()
    rows = api.get("/api/patients/PT-8829/evidence", headers=clinician()).json()
    assert rows and {"id", "kind", "date", "excerpt"} <= set(rows[0])
    assert any(row.get("sourceUrl") for row in rows)
    assert api.get("/api/patients/PT-0000/evidence", headers=clinician()).status_code == 404
