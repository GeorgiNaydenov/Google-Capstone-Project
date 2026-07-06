"""Unit tests for the versioned API backend endpoints (V1 and V2)."""

from fastapi.testclient import TestClient
from clinical_app.app import create_app


def client() -> TestClient:
    """Create API client with isolated repository registry."""
    return TestClient(create_app())


def clinician(session: str = "versioned-test") -> dict[str, str]:
    """Build clinician browser headers."""
    return {"X-Demo-Session": session, "X-Clinical-Role": "clinician", "X-User": "Dr. Versioned"}


def test_health_v1_and_v2() -> None:
    """Verify health endpoints on V1 and V2."""
    api = client()
    headers = clinician()
    
    # Root healthz
    res = api.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    
    # V1 health
    res = api.get("/api/v1/health", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    
    # V2 health
    res = api.get("/api/v2/health", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "databaseConnected" in data
    assert "storageAccessible" in data


def test_v1_patients_and_compatibility() -> None:
    """Verify patients endpoint is identical on /api and /api/v1."""
    api = client()
    headers = clinician()
    
    # Create a demo session
    created = api.post("/api/v1/demo/session", headers=headers)
    assert created.status_code == 201
    session_id = created.json()["sessionId"]
    
    session_headers = clinician(session_id)
    
    # Fetch from /api/v1/patients
    res1 = api.get("/api/v1/patients", headers=session_headers)
    assert res1.status_code == 200
    patients_v1 = res1.json()
    
    # Fetch from compatibility /api/patients
    res2 = api.get("/api/patients", headers=session_headers)
    assert res2.status_code == 200
    patients_compat = res2.json()
    
    assert patients_v1 == patients_compat
    # The demo tenant now layers a generated cohort under the hand-authored
    # fixture patients, so the exact count depends on generator output; just
    # confirm the well-known fixture patient is still reachable at the front.
    assert len(patients_v1) >= 24
    assert patients_v1[0]["id"] == "PT-8829"


def test_v2_mcp_tools() -> None:
    """Verify MCP tools list endpoint on V2."""
    api = client()
    headers = clinician()
    
    res = api.get("/api/v2/mcp/tools", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert "total" in data
    assert isinstance(data["tools"], list)
    assert data["total"] > 0
    # verify at least one of our defined tools is present
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_patient_status" in tool_names


def test_v2_a2a_card() -> None:
    """Verify Agent Card discovery endpoint on V2."""
    api = client()
    headers = clinician()
    
    res = api.get("/api/v2/a2a/card", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert data["name"] == "clinical_orchestrator"
    assert "pipelines" in data
    assert "image_extraction_pipeline" in data["pipelines"]
    assert "tools" in data


def test_custom_swagger_ui() -> None:
    """Verify that the custom Swagger UI and ReDoc pages work and are styled correctly."""
    api = client()
    
    # Swagger docs
    res = api.get("/docs")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html = res.text
    assert "Clinician AI Kit - API & Swagger Console" in html
    assert "#0b0f19" in html
    
    # ReDoc specs
    res_redoc = api.get("/redoc")
    assert res_redoc.status_code == 200
    
    # OpenAPI JSON
    res_openapi = api.get("/openapi.json")
    assert res_openapi.status_code == 200
    openapi = res_openapi.json()
    paths = openapi.get("paths", {})
    # Check that compatibility alias routes (e.g. /api/patients) are omitted from schema (include_in_schema=False)
    assert "/api/patients" not in paths
    assert "/api/v1/patients" in paths
    # Verify that the schema is fully described and has COMMON_RESPONSES defined
    v1_patients = paths["/api/v1/patients"]["get"]
    assert "responses" in v1_patients
    assert "403" in v1_patients["responses"]
    assert "ErrorResponse" in openapi["components"]["schemas"]

