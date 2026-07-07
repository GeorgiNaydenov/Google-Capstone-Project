"""Frontend contract tests for deterministic clinician product API."""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from clinical_app.app import create_app


def poll_until_settled(api: TestClient, headers: dict[str, str], run_id: str, timeout: float = 2.0) -> dict[str, object]:
    """Poll a live run until its background task moves it off "running".

    Live endpoints return immediately with status "running" and finish the
    real ADK call in a background asyncio task (see app.py's run_in_background
    closures) so the frontend can poll for incremental progress instead of
    blocking on a multi-minute request; tests need the same poll to observe
    the settled result.
    """

    deadline = time.monotonic() + timeout
    run = api.get(f"/api/runs/{run_id}", headers=headers).json()
    while run.get("status") == "running" and time.monotonic() < deadline:
        time.sleep(0.02)
        run = api.get(f"/api/runs/{run_id}", headers=headers).json()
    return run

# Seeded provenance rows (AUD-SEED-*, SEED-RCP-*) only exist after a generated
# showcase dataset has been loaded; without one the demo tenant falls back to
# the built-in fixtures, so these contracts cannot be exercised.
requires_generated_dataset = pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "showcase_data" / "database" / "app_manifest.json").is_file(),
    reason="generated showcase dataset not present; run scripts/generate_database_showcase.py --replace",
)


def client() -> TestClient:
    """Create API client with isolated repository registry."""

    return TestClient(create_app())


def clinician(session: str = "clinical-test") -> dict[str, str]:
    """Build clinician browser headers."""

    return {"X-Demo-Session": session, "X-Clinical-Role": "clinician", "X-User": "Dr. Test"}


def admin(session: str = "clinical-test") -> dict[str, str]:
    """Build admin browser headers."""

    return {"X-Demo-Session": session, "X-Clinical-Role": "admin", "X-User": "Admin Test"}


def upload_asset(api: TestClient, headers: dict[str, str], patient_id: str | None = None) -> str:
    """Upload real multipart bytes and return browser asset identifier."""

    patients = api.get("/api/patients", headers=headers).json()
    patient_ids = {patient["id"] for patient in patients}
    if patient_id not in patient_ids:
        patient_id = patients[0]["id"]
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
    readiness = api.get("/readyz")
    assert readiness.status_code == 200 and readiness.json()["status"] == "ready"
    assert any(component["name"] == "Clinical database" for component in readiness.json()["components"])
    created = api.post("/api/demo/session")
    assert created.status_code == 201
    headers = clinician(created.json()["sessionId"])
    dashboard = api.get("/api/dashboard", headers=headers, params={"role": "clinician"}).json()
    assert dashboard["metrics"]["patients"] > 0
    assert dashboard["patients"] and all(patient["id"] for patient in dashboard["patients"])
    first = api.get("/api/patients", headers=headers).json()[0]
    matches = api.get("/api/patients", headers=headers, params={"query": first["name"].split()[0]}).json()
    assert any(patient["id"] == first["id"] for patient in matches)
    profile = api.get(f"/api/patients/{first['id']}", headers=headers).json()
    assert profile["mrn"] == f"MRN-{first['id'][3:]}"
    sessions = api.get("/api/sessions", headers=headers).json()
    assert sessions and sessions[0]["patientId"]
    assert api.get(f"/api/sessions/{sessions[0]['id']}", headers=headers).json()["occurredAt"] == sessions[0]["occurredAt"]


def test_extraction_is_review_gated_and_approval_persists() -> None:
    """Storage stays pending until clinician approval then becomes synced."""

    api = client()
    headers = clinician("approval")
    patient_id = api.get("/api/patients", headers=headers).json()[0]["id"]
    asset_id = upload_asset(api, headers, patient_id)
    assert api.get(f"/api/assets/{asset_id}", headers=headers).content == b"\x89PNG\r\n\x1a\nsynthetic"
    baseline_persisted = len(api.get("/api/storage", headers=headers).json()["persistedExtractions"])
    response = api.post("/api/runs/extraction", headers=headers, json={"assetId": asset_id, "patientId": patient_id})
    assert response.status_code == 201
    run = response.json()
    assert run["workflow"] == "extraction" and run["status"] == "review"
    assert run["steps"] and run["evidence"] and run["result"]
    assert {receipt["status"] for receipt in run["result"]["storageReceipts"]} == {"pending"}
    assert run["result"]["persisted"] is False
    assert len(api.get("/api/storage", headers=headers).json()["persistedExtractions"]) == baseline_persisted
    assert api.get("/api/reviews", headers=headers).json()[0]["id"] == run["id"]
    approved = api.post(
        f"/api/runs/{run['id']}/review", headers=headers,
        json={"decision": "approved", "fields": {"documentType": "Verified CT", "patientMatch": patient_id}},
    ).json()
    assert approved["status"] == "completed"
    assert approved["result"]["persisted"] is True
    assert {receipt["status"] for receipt in approved["result"]["storageReceipts"]} == {"synced"}
    persisted = api.get("/api/storage", headers=headers).json()["persistedExtractions"]
    assert len(persisted) == baseline_persisted + 1
    mine = next(entry for entry in persisted if entry["runId"] == run["id"])
    assert mine["jsonReceipt"] and mine["confidence"]
    assert mine["patientId"] == patient_id and mine["sessionId"] == approved["result"]["sessionId"]
    assert api.get("/api/reviews", headers=headers).json() == []
    patient = api.get(f"/api/patients/{patient_id}", headers=headers).json()
    assert patient["aiStatus"] == "verified"
    sessions = api.get("/api/sessions", headers=headers, params={"patient_id": patient_id}).json()
    assert sessions[-1]["id"] == approved["result"]["sessionId"]
    image_qa = api.post(
        "/api/runs/qa", headers=headers,
        json={"patientId": patient_id, "question": "Show approved imaging", "filters": {"source": "image", "dateRange": "30d"}},
    ).json()
    assert image_qa["evidence"][0]["sourceUrl"].startswith("/api/assets/")
    assert api.get(image_qa["evidence"][0]["sourceUrl"]).status_code == 200
    assert api.get(image_qa["evidence"][0]["sourceUrl"].replace("approval", "expired")).status_code == 403


def test_rejection_never_persists_extraction() -> None:
    """Rejected extraction remains absent from persisted storage."""

    api = client()
    headers = clinician("rejection")
    patient_id = api.get("/api/patients", headers=headers).json()[0]["id"]
    asset_id = upload_asset(api, headers, patient_id)
    baseline_persisted = len(api.get("/api/storage", headers=headers).json()["persistedExtractions"])
    run = api.post("/api/runs/extraction", headers=headers, json={"assetId": asset_id, "patientId": patient_id}).json()
    rejected = api.post(f"/api/runs/{run['id']}/review", headers=headers, json={"decision": "rejected"}).json()
    assert rejected["result"]["persisted"] is False
    assert {receipt["status"] for receipt in rejected["result"]["storageReceipts"]} == {"pending"}
    assert len(api.get("/api/storage", headers=headers).json()["persistedExtractions"]) == baseline_persisted


def test_qa_database_admin_and_configuration_contracts() -> None:
    """Q&A, database aliases, audit, users, and config match browser API."""

    api = client()
    clinical_headers = clinician("workflows")
    patient_id = api.get("/api/patients", headers=clinical_headers).json()[0]["id"]
    qa = api.post(
        "/api/runs/qa", headers=clinical_headers,
        json={"patientId": patient_id, "question": "What changed?", "filters": {"source": "text"}},
    )
    assert qa.status_code == 201
    qa_run = qa.json()
    assert qa_run["workflow"] == "qa" and isinstance(qa_run["evidence"], list)
    assert api.get(f"/api/runs/{qa_run['id']}", headers=clinical_headers).json()["result"]["answer"]
    clinician_preview = api.post("/api/runs/database/preview", headers=clinical_headers, json={"question": "Count risk groups"})
    assert clinician_preview.status_code == 201
    assert api.post(f"/api/runs/database/{clinician_preview.json()['id']}/execute", headers=clinical_headers).status_code == 200
    admin_headers = admin("workflows")
    preview = api.post("/api/runs/database/preview", headers=admin_headers, json={"question": "Count risk groups"}).json()
    assert preview["status"] == "review" and preview["result"]["safe"] is True
    executed = api.post(f"/api/runs/database/{preview['id']}/execute", headers=admin_headers).json()
    assert executed["status"] == "completed" and executed["result"]["chart"]["type"] == "bar"
    assert sum(row["patient_count"] for row in executed["result"]["rows"]) > 0
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


def test_run_history_and_knowledge_base_listing_restore_conversations() -> None:
    """GET /runs and GET /knowledge-base/assets rebuild workflow chat history."""

    api = client()
    headers = clinician("history-session")
    roster = api.get("/api/patients", headers=headers).json()
    patient_id, other_patient = roster[0]["id"], roster[1]["id"]
    qa = api.post(
        "/api/runs/qa", headers=headers,
        json={"patientId": patient_id, "question": "Trend since last session?", "filters": {}},
    )
    assert qa.status_code == 201
    preview = api.post("/api/runs/database/preview", headers=headers, json={"question": "Count patients by risk level"})
    assert preview.status_code == 201
    assert api.post(f"/api/runs/database/{preview.json()['id']}/execute", headers=headers).status_code == 200

    all_runs = api.get("/api/runs", headers=headers).json()
    assert [run["workflow"] for run in all_runs] == ["qa", "database"]
    qa_runs = api.get("/api/runs", headers=headers, params={"workflow": "qa", "patient_id": patient_id}).json()
    assert [run["id"] for run in qa_runs] == [qa.json()["id"]]
    assert qa_runs[0]["result"]["question"] == "Trend since last session?"
    assert api.get("/api/runs", headers=headers, params={"workflow": "qa", "patient_id": "PT-0000"}).json() == []
    assert api.get("/api/runs", headers=clinician("history-other")).json() == []

    kb = api.post(
        "/api/knowledge-base/assets", headers=headers, data={"patient_id": patient_id},
        files={"file": ("notes.txt", b"Patient baseline values.", "text/plain")},
    )
    assert kb.status_code == 201
    listed = api.get("/api/knowledge-base/assets", headers=headers, params={"patient_id": patient_id}).json()
    assert [item["assetId"] for item in listed] == [kb.json()["assetId"]]
    assert listed[0]["patientId"] == patient_id and listed[0]["filename"] == "notes.txt"
    assert api.get("/api/knowledge-base/assets", headers=headers, params={"patient_id": other_patient}).json() == []


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
    baseline = len(api.get("/api/storage", headers=clinician("one")).json()["assets"])
    upload_asset(api, clinician("one"))
    assert len(api.get("/api/storage", headers=clinician("one")).json()["assets"]) == baseline + 1
    assert len(api.get("/api/storage", headers=clinician("two")).json()["assets"]) == baseline
    assert api.post("/api/demo/reset", headers=clinician("one")).status_code == 204
    assert len(api.get("/api/storage", headers=clinician("one")).json()["assets"]) == baseline


def test_orchestration_classifies_context_and_audits_plan() -> None:
    """Planner routes three workflows only with required context and permission."""

    api = client()
    headers = clinician("orchestration")
    roster = api.get("/api/patients", headers=headers).json()
    extraction = api.post(
        "/api/orchestrate", headers=headers,
        json={"query": "Extract findings from this uploaded CT scan", "patientId": roster[0]["id"]},
    )
    assert extraction.status_code == 201
    assert extraction.json()["workflow"] == "extraction"
    assert extraction.json()["route"] == "/app/extraction"
    assert extraction.json()["agents"] and extraction.json()["dataSources"]
    qa = api.post(
        "/api/orchestrate", headers=headers,
        json={"query": "What changed in recent evidence?", "patientId": roster[1]["id"]},
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
    patient_id = api.get("/api/patients", headers=clinician("upload-limit")).json()[0]["id"]
    oversized = api.post(
        "/api/assets", headers=clinician("upload-limit"), data={"patient_id": patient_id},
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
        run = poll_until_settled(api, capstone, run["id"])
        assert run["result"]["liveResponse"] == "Safe live response"
        assert run["result"]["authorSteps"][0]["author"] == "root_agent"
        assert any(step["name"] == "Root Agent" for step in run["steps"])
        # Demo tenants never touch the model even when the bridge is patched.
        demo_headers = clinician("demo-live")
        demo_patient = api.get("/api/patients", headers=demo_headers).json()[0]["id"]
        demo_run = api.post(
            "/api/runs/qa", headers=demo_headers,
            json={"patientId": demo_patient, "question": "Summarize recent status"},
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
    assert research_patients
    # Northstar serves either the static seed (12 patients, PT-7301 first) or
    # the generated demo2 dataset when showcase_data/demo2 exists; both are
    # valid — the contract under test is isolation, not the roster contents.
    assert northstar_patients and northstar_patients[0]["id"] != "PT-8829"
    assert research_patients[0]["condition"] != northstar_patients[0]["condition"] or research_patients[0]["id"] != northstar_patients[0]["id"]
    northstar_notices = api.get("/api/notifications", headers=northstar).json()
    assert {n["id"] for n in northstar_notices} == {"NTF-N01", "NTF-N02", "NTF-N03"}
    assert api.post("/api/notifications/NTF-001/read", headers=research).status_code == 200
    assert sum(not n["read"] for n in api.get("/api/notifications", headers=research).json()) == 2
    assert sum(not n["read"] for n in api.get("/api/notifications", headers=northstar).json()) == 3


def test_legacy_tenant_values_map_to_research_clinic() -> None:
    """Old header values and missing headers keep the Research Clinic dataset."""

    api = client()
    expected = api.get("/api/patients", headers={**clinician("legacy-reference"), "X-Tenant": "research-clinic"}).json()
    for legacy in ("local", "demo", None):
        headers = clinician(f"legacy-{legacy}")
        if legacy is not None:
            headers["X-Tenant"] = legacy
        patients = api.get("/api/patients", headers=headers).json()
        assert patients[0]["id"] == expected[0]["id"]
        assert len(patients) == len(expected)


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
    assert {"patient_id", "birth_date", "race_ethnicity", "preferred_language", "risk_level", "primary_diagnosis"} <= columns
    assert {"patient_conditions", "medications", "vital_signs", "care_gaps", "social_determinants"} <= set(by_name)


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
    assert any(row["pipeline"] in {"extraction", "qa", "database"} for row in rows)
    for row in rows:
        assert row["status"] in {"healthy", "degraded"}
        assert 0.0 <= row["avgConfidence"] <= 1.0


def test_summary_counts_reflect_repository_state() -> None:
    """Navigation badge counts derive from live repository state."""

    api = client()
    headers = clinician()
    patient_count = len(api.get("/api/patients", headers=headers).json())
    summary = api.get("/api/summary", headers=headers).json()
    assert summary["patients"] == patient_count
    assert summary["queueCount"] > 0
    assert summary["runs"] == 0
    patient_id = api.get("/api/patients", headers=headers).json()[0]["id"]
    asset_id = upload_asset(api, headers, patient_id)
    run = api.post("/api/runs/extraction", headers=headers, json={"patientId": patient_id, "uploadIds": [asset_id]}).json()
    assert run["status"] == "review"
    refreshed = api.get("/api/summary", headers=headers).json()
    assert refreshed["runs"] == 1
    assert refreshed["inboxCount"] == 1


def test_patient_evidence_endpoint_returns_sources() -> None:
    """Patient evidence rows expose kind, date, excerpt, and viewable links."""

    api = client()
    headers = clinician()
    roster = api.get("/api/patients", headers=headers).json()
    rows = next((items for items in (api.get(f"/api/patients/{patient['id']}/evidence", headers=headers).json() for patient in roster[:100]) if items), None)
    assert rows, "at least one demo patient exposes evidence sources"
    assert {"id", "kind", "date", "excerpt"} <= set(rows[0])
    assert api.get("/api/patients/PT-0000/evidence", headers=headers).status_code == 404


def test_documentation_hub_served_standalone() -> None:
    """The documentation hub serves readable pages outside the SPA shell."""

    api = client()
    hub = api.get("/documentation/")
    assert hub.status_code == 200
    assert "Nexus documentation" in hub.text
    assert "Enter the application" in hub.text
    assert 'href="/roles"' in hub.text
    wiki_page = api.get("/documentation/llm-wiki/index.html")
    assert wiki_page.status_code == 200
    assert "Documentation hub" in wiki_page.text
    obsidian_page = api.get("/documentation/project-wiki/Home.html")
    assert obsidian_page.status_code == 200
    assert "Back to main page" in obsidian_page.text


def test_storage_records_derive_from_upload_and_approval() -> None:
    """Storage pipeline records reflect real uploads and approved extractions."""

    api = client()
    headers = clinician("storage-records")
    patient_id = api.get("/api/patients", headers=headers).json()[0]["id"]
    before = {record["id"] for record in api.get("/api/storage", headers=headers).json()["records"]}
    asset_id = upload_asset(api, headers, patient_id)
    after_upload = api.get("/api/storage", headers=headers).json()["records"]
    assert any(record["destination"] == "Object storage" and record["source"] == "scan.png" and record["id"] not in before for record in after_upload)
    run = api.post("/api/runs/extraction", headers=headers, json={"assetId": asset_id, "patientId": patient_id}).json()
    api.post(f"/api/runs/{run['id']}/review", headers=headers, json={"decision": "approved", "fields": {"documentType": "CT"}})
    records = api.get("/api/storage", headers=headers).json()["records"]
    extraction_records = [record for record in records if record["source"] == f"Extraction {run['id']}"]
    assert {record["destination"] for record in extraction_records} == {"JSON document store", "Relational database", "Vector search index"}
    assert all(record["status"] == "synced" and record["patientId"] == patient_id for record in extraction_records)


@requires_generated_dataset
def test_audit_event_detail_links_seeded_run() -> None:
    """GET /audit/{id} returns the event with its linked bootstrap run."""

    api = client()
    detail = api.get("/api/audit/AUD-SEED-001", headers=admin("audit-detail")).json()
    assert detail["event"] == "showcase_database_loaded"
    assert detail["details"]["run_id"] == "RUN-SEED-DB"
    assert detail["run"]["id"] == "RUN-SEED-DB" and detail["run"]["status"] == "completed"
    assert api.get("/api/audit/AUD-UNKNOWN", headers=admin("audit-detail")).status_code == 404
    linked = api.get("/api/runs/RUN-SEED-DB", headers=clinician("audit-detail")).json()
    assert linked["workflow"] == "database" and linked["steps"]
    # Seeded bootstrap runs are provenance records, not conversation turns.
    assert api.get("/api/runs", headers=clinician("audit-detail")).json() == []


@requires_generated_dataset
def test_demo_storage_serves_sample_records_with_patient_context() -> None:
    """Seeded demo storage rows carry patient, session, and receipt context."""

    api = client()
    storage = api.get("/api/storage", headers=admin("storage-context")).json()
    sample = [record for record in storage["records"] if str(record["id"]).startswith("SEED-RCP-")]
    assert sample and all(record["patientId"] and record["sessionId"] for record in sample)
    seeded = [entry for entry in storage["persistedExtractions"] if str(entry["runId"]).startswith("RUN-SEED-")]
    assert seeded and all(entry["jsonReceipt"] and entry["patientId"] and entry["confidence"] is not None for entry in seeded)


def test_database_examples_are_grounded_and_answerable() -> None:
    """GET /database/examples returns questions the tenant can actually answer.

    Demo tenants surface their curated query-card questions, so the first
    suggestion must round-trip through preview and execution with real rows
    instead of being a generic template that matches nothing.
    """

    api = client()
    headers = clinician("examples-session")
    response = api.get("/api/database/examples", headers=headers)
    assert response.status_code == 200
    questions = response.json()
    assert questions and len(questions) <= 7
    assert all(isinstance(question, str) and question for question in questions)
    preview = api.post("/api/runs/database/preview", headers=headers, json={"question": questions[0]})
    assert preview.status_code == 201
    executed = api.post(f"/api/runs/database/{preview.json()['id']}/execute", headers=headers)
    assert executed.status_code == 200
    assert executed.json()["result"]["rows"]
