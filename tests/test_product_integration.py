"""End-to-end contracts joining the clinical UI API to product state."""

from importlib import import_module
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_app.app import create_app
from clinical_app.repository import RepositoryRegistry

product_app = import_module("clinical_app.app")


PATIENT_ID = "PT-8829"


def headers(role: str = "clinician", session: str = "integration") -> dict[str, str]:
    """Build browser-equivalent headers for one isolated demo session."""

    return {
        "X-Demo-Session": session,
        "X-Clinical-Role": role,
        "X-User": "Integration Tester",
    }


@pytest.fixture
def api() -> TestClient:
    """Return an application client with a fresh repository registry."""

    return TestClient(create_app())


def first_patient_id(api: TestClient, request_headers: dict[str, str]) -> str:
    """Return a real patient id from the tenant's loaded roster."""

    return api.get("/api/patients", headers=request_headers).json()[0]["id"]


def upload_image(api: TestClient, request_headers: dict[str, str], patient_id: str) -> str:
    """Upload a small, browser-renderable image and return its asset ID."""

    response = api.post(
        "/api/assets",
        headers=request_headers,
        data={"patient_id": patient_id},
        files={"file": ("evidence.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    assert response.status_code == 201
    return response.json()["assetId"]


def start_extraction(api: TestClient, request_headers: dict[str, str], patient_id: str) -> dict[str, Any]:
    """Upload evidence and start the review-gated extraction workflow."""

    asset_id = upload_image(api, request_headers, patient_id)
    response = api.post(
        "/api/runs/extraction",
        headers=request_headers,
        json={"assetId": asset_id, "patientId": patient_id},
    )
    assert response.status_code == 201
    run = response.json()
    assert "extract_clinical_text" in {item["tool"] for item in run["result"]["toolCalls"]}
    return run


@pytest.mark.parametrize(
    ("query", "role", "needs_patient", "workflow", "route"),
    [
        ("Extract this uploaded image", "clinician", True, "extraction", "/app/extraction"),
        ("What changed in recent evidence?", "clinician", True, "qa", "/app/qa"),
        ("Count patients by risk", "clinician", False, "database", "/app/database"),
    ],
)
def test_orchestration_returns_browser_routes(
    api: TestClient,
    query: str,
    role: str,
    needs_patient: bool,
    workflow: str,
    route: str,
) -> None:
    """Auto orchestration must navigate to UI screens, never POST-only API URLs."""

    payload: dict[str, str] = {"query": query}
    if needs_patient:
        payload["patientId"] = first_patient_id(api, headers(role))
    response = api.post("/api/orchestrate", headers=headers(role), json=payload)
    assert response.status_code == 201
    assert response.json()["workflow"] == workflow
    assert response.json()["route"] == route


def test_clinician_can_preview_and_execute_database_query(api: TestClient) -> None:
    """Database intelligence remains usable from the clinician sidebar."""

    request_headers = headers("clinician", "clinician-database")
    preview = api.post(
        "/api/runs/database/preview",
        headers=request_headers,
        json={"question": "Count patients by risk"},
    )
    assert preview.status_code == 201
    preview_body = preview.json()
    assert preview_body["status"] == "review"
    assert preview_body["result"]["safe"] is True
    assert "validate_sql_safety" in {item["tool"] for item in preview_body["result"]["toolCalls"]}

    executed = api.post(
        f"/api/runs/database/{preview_body['id']}/execute",
        headers=request_headers,
    )
    assert executed.status_code == 200
    assert "approve_sql_preview" in {item["tool"] for item in executed.json()["result"]["toolCalls"]}
    assert executed.json()["status"] == "completed"
    assert executed.json()["result"]["rows"]
    assert executed.json()["result"]["chart"]


def test_extraction_approval_preserves_fields_and_updates_patient_state(api: TestClient) -> None:
    """Approval persists only edited fields and creates linked clinical evidence."""

    request_headers = headers(session="approved-extraction")
    sessions_before = api.get(
        "/api/sessions", headers=request_headers, params={"patient_id": PATIENT_ID}
    ).json()
    run = start_extraction(api, request_headers, PATIENT_ID)
    reviewed_fields = {
        "documentType": "Verified CT",
        "patientMatch": PATIENT_ID,
        "finding": "Three hepatic lesions",
    }

    reviewed = api.post(
        f"/api/runs/{run['id']}/review",
        headers=request_headers,
        json={"decision": "approved", "fields": reviewed_fields},
    )
    assert reviewed.status_code == 200
    result = reviewed.json()["result"]
    assert result["fields"] == reviewed_fields
    assert set(result["fields"]) == set(reviewed_fields)
    assert result["persisted"] is True
    assert {receipt["target"] for receipt in result["storageReceipts"]} == {
        "json",
        "relational",
        "vector",
    }
    assert {receipt["status"] for receipt in result["storageReceipts"]} == {"synced"}

    sessions_after = api.get(
        "/api/sessions", headers=request_headers, params={"patient_id": PATIENT_ID}
    ).json()
    new_sessions = {item["id"]: item for item in sessions_after} | {}
    for item in sessions_before:
        new_sessions.pop(item["id"], None)
    assert len(new_sessions) == 1
    assert next(iter(new_sessions.values()))["status"] == "verified"

    qa = api.post(
        "/api/runs/qa",
        headers=request_headers,
        json={
            "patientId": PATIENT_ID,
            "question": "Show the newly verified evidence",
            "filters": {"source": "structured", "dateRange": "all"},
        },
    )
    assert qa.status_code == 201
    assert qa.json()["evidence"]


def test_extraction_rejection_does_not_persist_or_create_records(api: TestClient) -> None:
    """Rejected output must not create sessions, evidence, or storage receipts."""

    request_headers = headers(session="rejected-extraction")
    sessions_before = api.get(
        "/api/sessions", headers=request_headers, params={"patient_id": PATIENT_ID}
    ).json()
    run = start_extraction(api, request_headers, PATIENT_ID)
    rejected = api.post(
        f"/api/runs/{run['id']}/review",
        headers=request_headers,
        json={"decision": "rejected"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["result"]["persisted"] is False
    assert not any(
        receipt["status"] == "synced"
        for receipt in rejected.json()["result"]["storageReceipts"]
    )
    assert api.get(
        "/api/sessions", headers=request_headers, params={"patient_id": PATIENT_ID}
    ).json() == sessions_before
    assert api.get("/api/storage", headers=request_headers).json()["persistedCount"] == 0


def test_qa_image_citation_reopens_authorized_asset(api: TestClient) -> None:
    """Image evidence citations must resolve to bytes in the same demo session."""

    request_headers = headers(session="image-citation")
    response = api.post(
        "/api/runs/qa",
        headers=request_headers,
        json={
            "patientId": PATIENT_ID,
            "question": "Show image evidence for the latest abnormal result",
            "filters": {"source": "image", "dateRange": "all"},
        },
    )
    assert response.status_code == 201
    images = [item for item in response.json()["evidence"] if item["kind"] == "image"]
    assert images
    assert images[0]["sourceUrl"].startswith("/api/assets/")

    source = api.get(images[0]["sourceUrl"], headers=request_headers)
    assert source.status_code == 200
    assert source.content
    assert source.headers["content-type"].startswith("image/")


def test_frontend_agent_configuration_keys_save_version_and_audit(api: TestClient) -> None:
    """Every visible runtime control must round-trip through the API contract."""

    request_headers = headers("admin", "config-contract")
    current = api.get("/api/agent-config", headers=request_headers).json()
    payload = {
        **current,
        "autoApprovalThreshold": 91,
        "reviewThreshold": 74,
        "maxConcurrentRuns": 12,
        "databaseEnabled": False,
    }
    response = api.put("/api/agent-config", headers=request_headers, json=payload)
    assert response.status_code == 200
    saved = response.json()
    assert saved["version"] == current["version"] + 1
    for key in ("autoApprovalThreshold", "reviewThreshold", "maxConcurrentRuns", "databaseEnabled"):
        assert saved[key] == payload[key]

    audit = api.get("/api/audit", headers=request_headers).json()
    assert any(event["event"] == "agent_config_saved" for event in audit)


def test_dashboard_and_users_match_rendered_frontend_contract(api: TestClient) -> None:
    """Dashboard metrics and role records provide every field rendered by the UI."""

    clinician_metrics = api.get(
        "/api/dashboard", headers=headers("clinician", "view-contract")
    ).json()["metrics"]
    assert {"patients", "highRisk", "pendingReview", "syncRate"} <= set(clinician_metrics)
    assert clinician_metrics["highRisk"] > 0
    assert 0 <= clinician_metrics["syncRate"] <= 100

    admin_headers = headers("admin", "view-contract")
    admin_metrics = api.get("/api/dashboard", headers=admin_headers).json()["metrics"]
    assert {"activeUsers", "agentRuns", "syncRate", "reviewSla"} <= set(admin_metrics)

    users = api.get("/api/users", headers=admin_headers).json()
    assert users
    assert all({"id", "name", "email", "roles", "scope", "status"} <= set(user) for user in users)
    assert any({"Clinician", "Admin"} <= set(user["roles"]) for user in users)


def test_repository_registry_evicts_oldest_session_at_capacity() -> None:
    """Attacker-controlled session IDs cannot grow process state without bound."""

    registry = RepositoryRegistry(max_count=2, ttl_seconds=3600)
    first = registry.get("first")
    first.uploads["sentinel"] = {"assetId": "sentinel"}
    registry.get("second")
    registry.get("third")
    assert registry.get("first").uploads == {}


def test_upload_limit_rejects_oversized_body(api: TestClient) -> None:
    """Public upload endpoint enforces its documented process-memory boundary."""

    response = api.post(
        "/api/assets",
        headers=headers(session="upload-limit"),
        data={"patient_id": PATIENT_ID},
        files={"file": ("too-large.pdf", b"x" * 10_000_001, "application/pdf")},
    )
    assert response.status_code == 413
    assert api.get("/api/storage", headers=headers(session="upload-limit")).json()["assetCount"] == 0


def test_upload_rejects_unsupported_file_type(api: TestClient) -> None:
    """Unsupported documents should never be stored as unknown assets."""

    response = api.post(
        "/api/assets",
        headers=headers(session="unsupported-upload"),
        data={"patient_id": PATIENT_ID},
        files={"file": ("note.txt", b"plain clinical text", "text/plain")},
    )
    assert response.status_code == 415
    assert api.get("/api/storage", headers=headers(session="unsupported-upload")).json()["assetCount"] == 0


def test_upload_rejects_mismatched_content_type(api: TestClient) -> None:
    """Declared media type, extension, and signature must agree."""

    response = api.post(
        "/api/assets",
        headers=headers(session="mismatch-upload"),
        data={"patient_id": PATIENT_ID},
        files={"file": ("scan.pdf", b"\x89PNG\r\n\x1a\nsynthetic", "application/pdf")},
    )
    assert response.status_code == 422
    assert api.get("/api/storage", headers=headers(session="mismatch-upload")).json()["assetCount"] == 0


def test_knowledge_base_upload_indexes_document_for_qa(api: TestClient) -> None:
    """Knowledge-base documents become patient-scoped Q&A evidence."""

    request_headers = headers(session="kb-upload")
    uploaded = api.post(
        "/api/knowledge-base/assets",
        headers=request_headers,
        data={"patient_id": PATIENT_ID},
        files={"file": ("care-plan.md", b"# Care plan\nBNP rising; repeat echo recommended.", "text/markdown")},
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["evidenceId"].startswith("KB-")

    qa = api.post(
        "/api/runs/qa",
        headers=request_headers,
        json={"patientId": PATIENT_ID, "question": "What does the uploaded knowledge base say about BNP?", "source_types": ["document"], "filters": {}},
    )

    assert qa.status_code == 201
    assert any(item["kind"] == "document" and "BNP rising" in item["excerpt"] for item in qa.json()["evidence"])


def test_database_execute_rejects_unsafe_agent_sql(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Agent-generated SQL must be re-validated server-side before execution."""

    async def fake_execute_live(query: str, user_id: str, **_: Any) -> dict[str, Any]:
        return {
            "finalResponse": "DELETE FROM patients_core",
            "authorSteps": [],
            "toolCalls": [],
            "stateOutputs": {},
            "fields": {},
            "confidence": 0.9,
            "sql": "DELETE FROM patients_core",
        }

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(product_app, "execute_live", fake_execute_live)
    live_api = TestClient(product_app.create_app())
    request_headers = {**headers(session="unsafe-sql"), "X-Tenant": "capstone"}
    preview = live_api.post(
        "/api/runs/database/preview",
        headers=request_headers,
        json={"question": "Delete all patient rows"},
    )
    assert preview.status_code == 201
    preview_body = preview.json()
    assert preview_body["result"]["safe"] is False

    executed = live_api.post(
        f"/api/runs/database/{preview_body['id']}/execute", headers=request_headers
    )
    assert executed.status_code == 400
    run = live_api.get(f"/api/runs/{preview_body['id']}", headers=request_headers).json()
    assert run["status"] == "review"
    assert "rows" not in run["result"]


def test_database_execute_completes_with_empty_result(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Zero-row result sets are valid completions, not execution failures."""

    request_headers = headers("clinician", "empty-result")
    preview = api.post(
        "/api/runs/database/preview",
        headers=request_headers,
        json={"question": "Count patients with an unmatched diagnosis"},
    )
    assert preview.status_code == 201
    monkeypatch.setattr(
        "capstone_agent.clinical_schemas.execute_query",
        lambda sql: {"columns": ["risk_level", "patient_count"], "rows": [], "row_count": 0, "table": "query_result"},
    )
    executed = api.post(
        f"/api/runs/database/{preview.json()['id']}/execute", headers=request_headers
    )
    assert executed.status_code == 200
    body = executed.json()
    assert body["status"] == "completed"
    assert body["result"]["rows"] == []
    assert body["result"]["chart"] is None


def test_database_execute_surfaces_sql_errors(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Database errors return an actionable failure and re-open the review gate."""

    request_headers = headers("clinician", "sql-error")
    preview = api.post(
        "/api/runs/database/preview",
        headers=request_headers,
        json={"question": "Count patients by risk"},
    )
    assert preview.status_code == 201
    monkeypatch.setattr(
        "capstone_agent.clinical_schemas.execute_query",
        lambda sql: {"columns": [], "rows": [], "row_count": 0, "error": "no such column: nope"},
    )
    executed = api.post(
        f"/api/runs/database/{preview.json()['id']}/execute", headers=request_headers
    )
    assert executed.status_code == 422
    run = api.get(f"/api/runs/{preview.json()['id']}", headers=request_headers).json()
    assert run["status"] == "review"


def test_visuals_route_rejects_unknown_document(api: TestClient) -> None:
    """Unknown visual ids must 404 without leaking storage details."""

    response = api.get("/api/visuals/VIS-does-not-exist")
    assert response.status_code == 404


def test_visuals_route_rejects_paths_outside_uploads(api: TestClient, tmp_path) -> None:
    """A forged document row must not let the API serve arbitrary files."""

    from capstone_agent import database

    outside = tmp_path / "secret.png"
    outside.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    database.store_document(
        document_id="VIS-test-outside-uploads",
        filename="secret.png",
        content_type="image/png",
        file_path=str(outside),
        raw_text="",
        page_count=1,
    )
    response = api.get("/api/visuals/VIS-test-outside-uploads")
    assert response.status_code == 404


def test_live_execution_mode_invokes_lazy_agent_bridge(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The real (Capstone) tenant delegates to the ADK bridge, no model call."""

    calls: list[tuple[str, str]] = []

    async def fake_execute_live(query: str, user_id: str, **_: Any) -> dict[str, Any]:
        calls.append((query, user_id))
        return {
            "finalResponse": "Synthetic live response",
            "authorSteps": [{"author": "patient_qa_pipeline", "eventId": "event-1"}],
        }

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(product_app, "execute_live", fake_execute_live)
    live_api = TestClient(product_app.create_app())
    response = live_api.post(
        "/api/runs/qa",
        headers={**headers(session="live-bridge"), "X-Tenant": "capstone"},
        json={"patientId": PATIENT_ID, "question": "What changed?", "filters": {}},
    )
    assert response.status_code == 201
    assert calls and calls[0][1] == "Integration Tester"
    assert PATIENT_ID in calls[0][0]
    assert response.json()["result"]["liveResponse"] == "Synthetic live response"
    assert response.json()["result"]["authorSteps"] == [
        {"author": "patient_qa_pipeline", "eventId": "event-1"}
    ]
    assert any(step["name"] == "Patient Qa Pipeline" for step in response.json()["steps"])


def capstone_headers(session: str = "capstone-int") -> dict[str, str]:
    """Build headers targeting the real Capstone tenant."""

    return {
        "X-Demo-Session": session,
        "X-Clinical-Role": "clinician",
        "X-User": "Integration Tester",
        "X-Tenant": "capstone",
    }


def test_capstone_tenant_starts_empty(api: TestClient, tmp_path, monkeypatch) -> None:
    """The real tenant serves zero seeded data and a schema-only database."""

    import sqlite3

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)
    request_headers = capstone_headers("capstone-empty")
    assert api.get("/api/patients", headers=request_headers).json() == []
    assert api.get("/api/sessions", headers=request_headers).json() == []
    assert api.get("/api/notifications", headers=request_headers).json() == []
    dashboard = api.get("/api/dashboard", headers=request_headers).json()
    assert dashboard["metrics"]["patients"] == 0
    assert dashboard["metrics"]["agentRuns24h"] == 0
    assert dashboard["metrics"]["openAiAlerts"] == 0
    db_file = tmp_path / "capstone.db"
    assert db_file.exists()
    with sqlite3.connect(db_file) as conn:
        assert conn.execute("SELECT COUNT(*) FROM patients_core").fetchone()[0] == 0


def test_capstone_writes_isolated_from_clinical_db(tmp_path) -> None:
    """Writes scoped by tenant_storage never reach the default clinical.db."""

    from uuid import uuid4

    from capstone_agent import database

    probe_id = f"PT-ISO-{uuid4().hex[:8]}"
    with database.tenant_storage(tmp_path / "capstone.db", tmp_path / "uploads"):
        database.ensure_patient(probe_id, "Isolation Probe")
        assert database.get_patient(probe_id) is not None
    assert database.get_patient(probe_id) is None


def test_capstone_database_preview_has_no_static_fallback(api: TestClient, tmp_path, monkeypatch) -> None:
    """A live SQL failure surfaces a 502 instead of canned fallback SQL."""

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)

    async def failing_execute_live(*_: Any, **__: Any) -> dict[str, Any]:
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(product_app, "execute_live", failing_execute_live)
    response = api.post(
        "/api/runs/database/preview",
        headers=capstone_headers("capstone-fallback"),
        json={"question": "How many patients per risk level?"},
    )
    assert response.status_code == 502
    assert "SQL generation failed" in response.json()["detail"]
    assert "SELECT risk_level" not in response.text


def test_capstone_preview_rejects_empty_sql(api: TestClient, tmp_path, monkeypatch) -> None:
    """An agent response without SQL is a surfaced error, not comment SQL."""

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)

    async def sqlless_execute_live(*_: Any, **__: Any) -> dict[str, Any]:
        return {
            "finalResponse": "I could not derive a query.",
            "authorSteps": [], "toolCalls": [], "stateOutputs": {},
            "fields": {}, "confidence": 0.9, "sql": "",
        }

    monkeypatch.setattr(product_app, "execute_live", sqlless_execute_live)
    response = api.post(
        "/api/runs/database/preview",
        headers=capstone_headers("capstone-empty-sql"),
        json={"question": "How many patients per risk level?"},
    )
    assert response.status_code == 502
    assert "did not return SQL" in response.json()["detail"]


def test_capstone_users_and_permissions_persist_across_sessions(api: TestClient, tmp_path, monkeypatch) -> None:
    """The real tenant's directory is DB-seeded and matrix edits survive new sessions."""

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)
    first = {**capstone_headers("capstone-perms-a"), "X-Clinical-Role": "admin"}
    users = api.get("/api/users", headers=first).json()
    assert len(users) >= 5
    assert any("Admin" in user["roles"] for user in users)

    matrix = api.get("/api/permissions", headers=first).json()
    edited = matrix["matrix"]
    edited[1]["grants"]["Reviewer"] = True
    saved = api.put("/api/permissions", headers=first, json={"matrix": edited}).json()
    assert saved["version"] == matrix["version"] + 1

    # A fresh session on the same tenant sees the persisted edit — proof the
    # matrix lives in capstone.db, not in per-session memory.
    second = {**capstone_headers("capstone-perms-b"), "X-Clinical-Role": "admin"}
    persisted = api.get("/api/permissions", headers=second).json()
    assert persisted["version"] == saved["version"]
    row = next(item for item in persisted["matrix"] if item["permission"] == edited[1]["permission"])
    assert row["grants"]["Reviewer"] is True


def test_capstone_monitoring_and_notifications_derive_from_runs(api: TestClient, tmp_path, monkeypatch) -> None:
    """The real tenant reports no agent activity until something actually runs."""

    monkeypatch.setattr("clinical_app.repository.PROJECT_ROOT", tmp_path)
    request_headers = {**capstone_headers("capstone-honest"), "X-Clinical-Role": "admin"}
    assert api.get("/api/agents/monitoring", headers=request_headers).json() == []
    assert api.get("/api/notifications", headers=request_headers).json() == []
    summary = api.get("/api/summary", headers=request_headers).json()
    assert summary["patients"] == 0 and summary["runs"] == 0
