"""Unit tests for live mode ingestion, ETL, and database seeding."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from clinical_app.app import create_app


def client() -> TestClient:
    """Create API client with isolated registry."""
    return TestClient(create_app())


def live_headers(session: str = "live-test-session") -> dict[str, str]:
    """Headers targeting the real Capstone tenant (live mode)."""
    return {
        "X-Demo-Session": session,
        "X-Clinical-Role": "admin",
        "X-User": "Dr. IngestionTest",
        "X-Tenant": "capstone"
    }


def test_import_database_and_documents_etl() -> None:
    # Clear active database cache to force re-initialization
    from capstone_agent import database as capstone_db
    capstone_db._INITIALIZED_PATHS.clear()

    # Clean up any existing test DB/uploads to ensure test isolation
    db_path = Path("capstone.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass

    uploads_dir = Path("uploads_capstone")
    if uploads_dir.exists():
        import shutil
        try:
            shutil.rmtree(uploads_dir)
        except OSError:
            pass

    api = client()
    headers = live_headers()

    # 1. Database ETL Ingestion
    print("\n[Test] Importing database intelligence cohort...")
    response = api.post(
        "/api/import",
        headers=headers,
        data={"import_type": "database"}
    )
    assert response.status_code == 201, f"Import database failed: {response.text}"
    data = response.json()
    assert data["status"] == "success"
    assert "rowCounts" in data
    assert data["rowCounts"]["patients_core"] == 5

    # Verify patients exist in patient registry
    patients_response = api.get("/api/patients", headers=headers)
    assert patients_response.status_code == 200
    patients = patients_response.json()
    assert len(patients) >= 5
    assert any(p["id"].startswith("PT-L") for p in patients)

    patient_id = next(p["id"] for p in patients if p["id"].startswith("PT-L"))

    # 2. Document ETL Ingestion (PDF)
    print("[Test] Ingesting PDF document through ETL...")
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
    response = api.post(
        "/api/import",
        headers=headers,
        data={"import_type": "document", "patient_id": patient_id},
        files={"file": ("test_report.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 201, f"Import PDF failed: {response.text}"
    doc_data = response.json()
    assert doc_data["status"] == "success"
    assert "documentId" in doc_data
    assert doc_data["pageCount"] == 0 or doc_data["pageCount"] == 1  # fitz might return 0 on blank pdf signature, or 1

    # 3. Document ETL Ingestion (PNG Image)
    print("[Test] Ingesting PNG screenshot through ETL...")
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    response = api.post(
        "/api/import",
        headers=headers,
        data={"import_type": "document", "patient_id": patient_id},
        files={"file": ("screenshot.png", png_content, "image/png")}
    )
    assert response.status_code == 201, f"Import PNG failed: {response.text}"
    img_data = response.json()
    assert img_data["status"] == "success"
    assert "documentId" in img_data

    # 4. Verify uploads are populated in repository
    print("[Test] Verifying repository assets...")
    storage_response = api.get("/api/storage", headers=headers)
    assert storage_response.status_code == 200
    storage = storage_response.json()
    assert storage["assetCount"] >= 2
    assert any(a["filename"] == "test_report.pdf" for a in storage["assets"])


def test_upload_registers_unseen_live_patient_across_sessions() -> None:
    """Evidence uploads register unknown live patients instead of 404ing.

    A clinician can reference a brand-new patient from Q&A or extraction;
    the upload creates a needs_review roster row persisted in the tenant
    database, and a session whose roster snapshot predates the patient
    still resolves it through the database fallback.
    """
    from capstone_agent import database as capstone_db
    capstone_db._INITIALIZED_PATHS.clear()

    db_path = Path("capstone.db")
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass

    api = client()
    session_a = live_headers("live-register-session-a")
    session_b = live_headers("live-register-session-b")

    # Session B hydrates its roster now, before the patient exists, so a
    # later lookup can only succeed through the database fallback.
    assert api.get("/api/patients", headers=session_b).status_code == 200

    png_content = b"\x89PNG\r\n\x1a\nsynthetic"
    response = api.post(
        "/api/assets",
        headers=session_a,
        data={"patient_id": "900042"},
        files={"file": ("temperature_panel.png", png_content, "image/png")},
    )
    assert response.status_code == 201, f"Upload for unseen patient failed: {response.text}"
    assert "assetId" in response.json()

    # The uploading session sees the registered patient in its roster.
    patients = api.get("/api/patients", headers=session_a).json()
    registered = next((p for p in patients if p["id"] == "900042"), None)
    assert registered is not None
    assert registered["aiStatus"] == "needs_review"

    # The stale session resolves the same patient via the tenant database.
    detail = api.get("/api/patients/900042", headers=session_b)
    assert detail.status_code == 200


def test_asset_upload_detects_patient_id_from_document_text() -> None:
    """A blank patient id resolves from the number the document itself prints.

    Mirrors the clinician flow: a packet headed "Patient 990001" uploads
    without typing an id; the endpoint detects the identifier from the
    parsed text, registers the patient, and echoes the effective id so the
    UI can fill the field.
    """

    import fitz

    api = client()
    headers = live_headers("live-detect-session")

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Confidential - Patient 990001: Whiteside, Eleanor - Laboratory Results")
    pdf_bytes = doc.tobytes()
    doc.close()

    response = api.post(
        "/api/assets",
        headers=headers,
        data={"patient_id": ""},
        files={"file": ("temperature_history.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["patientId"] == "990001"
    assert payload["detectedPatientId"] == "990001"
    assert api.get("/api/patients/990001", headers=headers).status_code == 200

    # A document with no readable identifier and no typed id is rejected
    # with actionable detail instead of a silent fallback.
    response = api.post(
        "/api/assets",
        headers=headers,
        data={"patient_id": ""},
        files={"file": ("unlabeled.pdf", b"%PDF-1.4\n% no text\n", "application/pdf")},
    )
    assert response.status_code == 422
    assert "detected" in response.json()["detail"]

    # Q&A knowledge-base uploads register unseen patients the same way.
    kb_response = api.post(
        "/api/knowledge-base/assets",
        headers=headers,
        data={"patient_id": "900043"},
        files={"file": ("focus_notes.txt", b"Live sample focus panel notes.", "text/plain")},
    )
    assert kb_response.status_code == 201, f"KB upload for unseen patient failed: {kb_response.text}"
    assert any(p["id"] == "900043" for p in api.get("/api/patients", headers=headers).json())
