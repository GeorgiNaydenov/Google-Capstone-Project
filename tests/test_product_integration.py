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


def upload_image(api: TestClient, request_headers: dict[str, str]) -> str:
    """Upload a small, browser-renderable image and return its asset ID."""

    response = api.post(
        "/api/assets",
        headers=request_headers,
        data={"patient_id": PATIENT_ID},
        files={"file": ("evidence.png", b"\x89PNG\r\n\x1a\nsynthetic", "image/png")},
    )
    assert response.status_code == 201
    return response.json()["assetId"]


def start_extraction(api: TestClient, request_headers: dict[str, str]) -> dict[str, Any]:
    """Upload evidence and start the review-gated extraction workflow."""

    asset_id = upload_image(api, request_headers)
    response = api.post(
        "/api/runs/extraction",
        headers=request_headers,
        json={"assetId": asset_id, "patientId": PATIENT_ID},
    )
    assert response.status_code == 201
    run = response.json()
    assert "extract_clinical_text" in {item["tool"] for item in run["result"]["toolCalls"]}
    return run


@pytest.mark.parametrize(
    ("query", "role", "patient_id", "workflow", "route"),
    [
        ("Extract this uploaded image", "clinician", PATIENT_ID, "extraction", "/app/extraction"),
        ("What changed in recent evidence?", "clinician", PATIENT_ID, "qa", "/app/qa"),
        ("Count patients by risk", "clinician", None, "database", "/app/database"),
    ],
)
def test_orchestration_returns_browser_routes(
    api: TestClient,
    query: str,
    role: str,
    patient_id: str | None,
    workflow: str,
    route: str,
) -> None:
    """Auto orchestration must navigate to UI screens, never POST-only API URLs."""

    payload: dict[str, str] = {"query": query}
    if patient_id:
        payload["patientId"] = patient_id
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
    run = start_extraction(api, request_headers)
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
    run = start_extraction(api, request_headers)
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
    assert any({"clinician", "admin"} <= set(user["roles"]) for user in users)


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


def test_live_execution_mode_invokes_lazy_agent_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live mode delegates to ADK bridge while tests make no model call."""

    calls: list[tuple[str, str]] = []

    async def fake_execute_live(query: str, user_id: str, **_: Any) -> dict[str, Any]:
        calls.append((query, user_id))
        return {
            "finalResponse": "Synthetic live response",
            "authorSteps": [{"author": "patient_qa_pipeline", "eventId": "event-1"}],
        }

    monkeypatch.setenv("AGENT_EXECUTION_MODE", "live")
    monkeypatch.setattr(product_app, "execute_live", fake_execute_live)
    live_api = TestClient(product_app.create_app())
    response = live_api.post(
        "/api/runs/qa",
        headers=headers(session="live-bridge"),
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
