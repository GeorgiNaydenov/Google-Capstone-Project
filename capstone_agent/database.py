"""SQLite database layer — real persistence for all clinical data.

Provides connection management, schema initialization with seed data,
document CRUD, and full-text search across stored documents and notes.
"""

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import clinical_schemas
from . import mock_data

# CLINICAL_DATA_DIR relocates the default database and uploads onto a writable
# (optionally mounted) directory so real-tenant data survives container
# restarts; unset, both stay next to the project for local development.
_DATA_DIR = Path(os.environ["CLINICAL_DATA_DIR"]).resolve() if os.environ.get("CLINICAL_DATA_DIR") else Path(__file__).resolve().parent.parent
DB_PATH = _DATA_DIR / "clinical.db"
UPLOADS_ROOT = _DATA_DIR / "uploads"

# Tenant-scoped storage overrides. Contextvars propagate across await and
# into anyio/asyncio worker threads, so everything a live agent run touches
# inside one request sees the same tenant database and uploads directory.
_active_db_path: ContextVar[Path | None] = ContextVar("active_db_path", default=None)
_active_uploads_root: ContextVar[Path | None] = ContextVar("active_uploads_root", default=None)

_INITIALIZED_PATHS: set[str] = set()
_INIT_LOCK = threading.Lock()


def active_db_path() -> Path:
    """Return the SQLite file scoped to the current execution context."""
    return _active_db_path.get() or DB_PATH


def active_uploads_root() -> Path:
    """Return the uploads directory scoped to the current execution context."""
    return _active_uploads_root.get() or UPLOADS_ROOT


@contextmanager
def tenant_storage(db_path: Path | str | None, uploads_root: Path | str | None = None):
    """Scope all database and upload access in this context to a tenant.

    Passing None for either value keeps the legacy default (clinical.db and
    uploads/). Non-default databases are initialized schema-only so a real
    tenant starts empty instead of inheriting the demo seed.
    """
    db_token = _active_db_path.set(Path(db_path) if db_path else None)
    uploads_token = _active_uploads_root.set(Path(uploads_root) if uploads_root else None)
    try:
        if db_path is not None:
            init_db()
        yield
    finally:
        _active_db_path.reset(db_token)
        _active_uploads_root.reset(uploads_token)


def get_connection():
    """Get a connection to the context-active SQLite database.

    GCS FUSE (Cloud Run volume mount) does not support random writes required
    by SQLite WAL mode. Using DELETE journal mode ensures sequential writes to
    the single .db file, which is fully compatible with GCS FUSE semantics.
    """
    conn = sqlite3.connect(str(active_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(*, seed: bool | None = None):
    """Initialize the active database, seeding demo data only for clinical.db.

    The seed default keys off the active path so the legacy store keeps its
    deterministic demo rows while tenant databases (e.g. capstone.db) are
    created schema-only and stay empty until real workflows write to them.
    """
    path_key = str(active_db_path())
    if seed is None:
        seed = active_db_path() == DB_PATH
    with _INIT_LOCK:
        if path_key in _INITIALIZED_PATHS:
            return
        # Tenant databases may live in directories that do not exist yet
        # (e.g. showcase_data/ under a relocated data root); sqlite cannot
        # create missing parents itself.
        Path(path_key).parent.mkdir(parents=True, exist_ok=True)
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients_core'")
            if cursor.fetchone():
                _INITIALIZED_PATHS.add(path_key)
                return

            for ddl in clinical_schemas.SCHEMA_DDL.values():
                sqlite_ddl = ddl.replace("SERIAL", "INTEGER").replace("JSONB", "TEXT")
                cursor.execute(sqlite_ddl)

            if seed:
                _seed_demo_rows(cursor)

            conn.commit()

        _INITIALIZED_PATHS.add(path_key)


def _seed_demo_rows(cursor) -> None:
    """Insert the deterministic demo dataset into a freshly created schema."""
    for pt in mock_data.PATIENTS.values():
        extended = {}
        for key in ("demographics", "diagnoses", "medications", "allergies", "care_team", "diagnosis_codes"):
            if key in pt:
                extended[key] = pt[key]
        cursor.execute("""
            INSERT OR IGNORE INTO patients_core (
                patient_id, name, age, sex, risk_level, primary_diagnosis,
                assigned_clinician, last_session_date, data_completeness_score,
                open_tasks, ai_review_status, extended_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pt["patient_id"], pt["name"], pt["age"], pt["sex"], pt["risk_level"],
            pt["primary_diagnosis"], pt["assigned_clinician"], pt["last_session_date"],
            pt["data_completeness_score"], pt["open_tasks"], pt["ai_review_status"],
            json.dumps(extended) if extended else None,
        ))

    _EXTRA_PATIENTS = [
        ("PT-1029", "Eleanor Kim", 67, "Female", "high", "Chronic kidney disease, stage 4", "Dr. Sarah Miller", "2026-06-22", 0.88, 3, "needs_review"),
        ("PT-3842", "David Okafor", 59, "Male", "high", "Acute coronary syndrome follow-up", "Dr. Sarah Miller", "2026-06-21", 0.84, 2, "needs_review"),
        ("PT-7714", "Amelia Rossi", 73, "Female", "high", "Aortic stenosis, severe", "Dr. Sarah Miller", "2026-06-20", 0.91, 2, "verified"),
        ("PT-2388", "Noah Williams", 52, "Male", "needs_review", "Crohn disease with recent flare", "Dr. Elena Park", "2026-06-19", 0.76, 2, "needs_review"),
        ("PT-6503", "Priya Nair", 41, "Female", "needs_review", "Systemic lupus erythematosus", "Dr. Elena Park", "2026-06-17", 0.81, 1, "needs_review"),
        ("PT-4337", "Lucas Martin", 64, "Male", "stable", "COPD, GOLD stage II", "Dr. Sarah Miller", "2026-06-16", 0.96, 0, "verified"),
        ("PT-8195", "Aisha Rahman", 36, "Female", "stable", "Multiple sclerosis, relapsing-remitting", "Dr. Elena Park", "2026-06-15", 0.93, 1, "verified"),
        ("PT-2971", "Henry Brooks", 70, "Male", "needs_review", "Parkinson disease", "Dr. James Patel", "2026-06-14", 0.79, 2, "needs_review"),
        ("PT-5602", "Sofia Alvarez", 28, "Female", "stable", "Ulcerative colitis", "Dr. James Patel", "2026-06-13", 0.97, 0, "verified"),
        ("PT-1448", "Owen Hughes", 55, "Male", "stable", "Hypertension with left ventricular hypertrophy", "Dr. Sarah Miller", "2026-06-12", 0.90, 1, "verified"),
        ("PT-9064", "Mei Tan", 48, "Female", "stable", "Rheumatoid arthritis", "Dr. Elena Park", "2026-06-11", 0.94, 0, "verified"),
        ("PT-3256", "Samuel Reed", 62, "Male", "stable", "Prostate cancer in remission", "Dr. James Patel", "2026-06-10", 0.92, 0, "verified"),
        ("PT-6841", "Fatima Hassan", 44, "Female", "stable", "Graves disease", "Dr. Sarah Miller", "2026-06-09", 0.89, 1, "verified"),
        ("PT-4720", "Jack Thompson", 33, "Male", "stable", "Epilepsy, focal onset", "Dr. Elena Park", "2026-06-08", 0.95, 0, "verified"),
        ("PT-7539", "Isabella Costa", 57, "Female", "stable", "Nonalcoholic steatohepatitis", "Dr. James Patel", "2026-06-07", 0.87, 1, "verified"),
        ("PT-2186", "Robert Lewis", 69, "Male", "stable", "Osteoarthritis, bilateral knees", "Dr. Sarah Miller", "2026-06-06", 0.98, 0, "verified"),
        ("PT-5368", "Grace Li", 31, "Female", "stable", "Hashimoto thyroiditis", "Dr. Elena Park", "2026-06-05", 0.96, 0, "verified"),
        ("PT-8650", "Mateo Silva", 46, "Male", "stable", "Obstructive sleep apnea", "Dr. James Patel", "2026-06-04", 0.86, 1, "verified"),
        ("PT-3492", "Nora Evans", 50, "Female", "stable", "Migraine with aura", "Dr. Sarah Miller", "2026-06-03", 0.93, 0, "verified"),
        ("PT-6177", "Adam Kowalski", 39, "Male", "stable", "Psoriatic arthritis", "Dr. Elena Park", "2026-06-02", 0.91, 0, "verified"),
    ]
    for row in _EXTRA_PATIENTS:
        cursor.execute("""
            INSERT OR IGNORE INTO patients_core (
                patient_id, name, age, sex, risk_level, primary_diagnosis,
                assigned_clinician, last_session_date, data_completeness_score,
                open_tasks, ai_review_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    _EXTRA_SESSIONS = [
        ("SES-1029-001", "PT-1029", "2026-06-22", 2, 0.76, "pending"),
        ("SES-3842-001", "PT-3842", "2026-06-21", 1, 0.82, "pending"),
        ("SES-7714-001", "PT-7714", "2026-06-20", 3, 0.94, "verified"),
        ("SES-2388-001", "PT-2388", "2026-06-19", 1, 0.79, "pending"),
        ("SES-6503-001", "PT-6503", "2026-06-17", 2, 0.81, "pending"),
        ("SES-4337-001", "PT-4337", "2026-06-16", 1, 0.96, "verified"),
        ("SES-8195-001", "PT-8195", "2026-06-15", 2, 0.93, "verified"),
        ("SES-2971-001", "PT-2971", "2026-06-14", 1, 0.74, "pending"),
    ]
    for row in _EXTRA_SESSIONS:
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (
                session_id, patient_id, session_date, uploaded_image_count,
                extraction_confidence, clinician_verification, json_sync_status,
                relational_sync_status, vector_sync_status, audit_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'synced', 'synced', 'synced', 'recorded')
        """, row)

    for sessions in mock_data.SESSIONS.values():
        for session in sessions:
            cursor.execute("""
                INSERT OR IGNORE INTO sessions (
                    session_id, patient_id, session_date, uploaded_image_count,
                    extraction_confidence, clinician_verification, json_sync_status,
                    relational_sync_status, vector_sync_status, audit_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session["session_id"], session["patient_id"], session["date"],
                session["uploaded_image_count"], session["extraction_confidence"],
                session.get("clinician_verification_status", "pending"),
                "synced", "synced", "synced", "recorded"
            ))

            for field in session.get("extracted_fields", []):
                cursor.execute("""
                    INSERT OR IGNORE INTO extracted_fields (
                        session_id, patient_id, field_name, field_value, confidence,
                        ontology_code, needs_review
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session["session_id"], session["patient_id"], field["field_name"],
                    field["value"], field["confidence"], field.get("ontology_code"),
                    field["confidence"] < 0.8,
                ))

            for image in session.get("images", []):
                qm = mock_data.IMAGE_QUALITY_DB.get(image["gcs_uri"], {})
                cursor.execute("""
                    INSERT OR IGNORE INTO imaging_studies (
                        session_id, patient_id, gcs_uri, modality, body_region,
                        description, quality_score, resolution, bit_depth, contrast,
                        artifacts, dicom_compliant, file_size_kb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session["session_id"], session["patient_id"], image["gcs_uri"],
                    image["modality"], image["body_region"], image["description"],
                    qm.get("quality_score", 0.9), qm.get("resolution"),
                    qm.get("bit_depth"), qm.get("contrast"), qm.get("artifacts"),
                    qm.get("dicom_compliant", False), qm.get("file_size_kb"),
                ))

    for patient_id, notes in mock_data.CLINICAL_NOTES.items():
        for note in notes:
            cursor.execute("""
                INSERT OR IGNORE INTO clinical_notes (
                    note_id, patient_id, note_date, author, note_type, note_text, vector_chunk_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                note["note_id"], patient_id, note["date"], note["author"],
                note["type"], note["text"], note.get("vector_chunk_id")
            ))

    for patient_id, labs in mock_data.LAB_RESULTS.items():
        for lab in labs:
            cursor.execute("""
                INSERT OR IGNORE INTO lab_results (
                    patient_id, result_date, test_name, component, value, unit, reference_range, flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient_id, lab["date"], lab["test"], lab["component"],
                lab["value"], lab["unit"], lab["reference_range"], lab.get("flag")
            ))

    for audit in mock_data.AUDIT_EVENTS:
        cursor.execute("""
            INSERT OR IGNORE INTO audit_log (
                event_timestamp, agent_name, action, patient_id, session_id, details, user_role
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            audit["timestamp"], audit["agent_name"], audit["action"],
            audit.get("patient_id"), audit.get("session_id"),
            json.dumps(audit.get("details", {})), audit.get("user_role", "clinician")
        ))


def execute_sql(sql: str) -> dict[str, Any]:
    """Execute a read-only SQL query against the SQLite database."""
    init_db()
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [dict(row) for row in cursor.fetchall()]
            return {"columns": columns, "rows": rows, "row_count": len(rows), "table": "query_result"}
    except Exception as e:
        return {"columns": [], "rows": [], "row_count": 0, "error": str(e)}


# ---------------------------------------------------------------------------
# Document CRUD
# ---------------------------------------------------------------------------

def store_document(
    document_id: str,
    filename: str,
    content_type: str,
    file_path: str,
    raw_text: str,
    page_count: int,
    patient_id: str = "",
    gemini_analysis: str = "",
) -> dict[str, Any]:
    """Store a processed document in the database."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO documents (
                document_id, patient_id, filename, content_type, file_path,
                uploaded_at, raw_text, page_count, processing_status, gemini_analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'processed', ?)
        """, (document_id, patient_id or None, filename, content_type, file_path,
              now, raw_text, page_count, gemini_analysis))
        conn.commit()
    return {"document_id": document_id, "stored_at": now}


def store_document_chunks(document_id: str, chunks: list[dict], patient_id: str = "") -> int:
    """Store text chunks for a document. Returns chunk count."""
    init_db()
    with get_connection() as conn:
        for chunk in chunks:
            conn.execute("""
                INSERT INTO document_chunks (document_id, patient_id, chunk_index, chunk_text, source_page)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, patient_id or None, chunk["index"], chunk["text"], chunk.get("page")))
        conn.commit()
    return len(chunks)


def search_documents(query: str, patient_id: str = "", limit: int = 20) -> list[dict[str, Any]]:
    """Full-text search across document chunks and clinical notes."""
    init_db()
    results = []
    keywords = [kw.strip() for kw in query.split() if len(kw.strip()) >= 2]
    if not keywords:
        return results

    like_clauses = " OR ".join(["chunk_text LIKE ?"] * len(keywords))
    params = [f"%{kw}%" for kw in keywords]

    with get_connection() as conn:
        if patient_id:
            sql = f"""
                SELECT dc.chunk_id, dc.document_id, dc.chunk_text, dc.chunk_index, dc.source_page,
                       d.filename, d.content_type, d.uploaded_at, d.patient_id
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE dc.patient_id = ? AND ({like_clauses})
                LIMIT ?
            """
            rows = conn.execute(sql, [patient_id] + params + [limit]).fetchall()
        else:
            sql = f"""
                SELECT dc.chunk_id, dc.document_id, dc.chunk_text, dc.chunk_index, dc.source_page,
                       d.filename, d.content_type, d.uploaded_at, d.patient_id
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.document_id
                WHERE {like_clauses}
                LIMIT ?
            """
            rows = conn.execute(sql, params + [limit]).fetchall()

        for row in rows:
            row_dict = dict(row)
            hit_count = sum(1 for kw in keywords if kw.lower() in row_dict["chunk_text"].lower())
            row_dict["relevance_score"] = round(min(0.98, 0.50 + hit_count * 0.15), 2)
            row_dict["source_type"] = "document"
            results.append(row_dict)

    # Also search clinical notes
    note_like = " OR ".join(["note_text LIKE ?"] * len(keywords))
    with get_connection() as conn:
        if patient_id:
            sql = f"""
                SELECT note_id, patient_id, note_date, author, note_type, note_text
                FROM clinical_notes
                WHERE patient_id = ? AND ({note_like})
                LIMIT ?
            """
            rows = conn.execute(sql, [patient_id] + params + [limit]).fetchall()
        else:
            sql = f"""
                SELECT note_id, patient_id, note_date, author, note_type, note_text
                FROM clinical_notes
                WHERE {note_like}
                LIMIT ?
            """
            rows = conn.execute(sql, params + [limit]).fetchall()

        for row in rows:
            row_dict = dict(row)
            hit_count = sum(1 for kw in keywords if kw.lower() in row_dict["note_text"].lower())
            results.append({
                "chunk_id": row_dict["note_id"],
                "document_id": row_dict["note_id"],
                "chunk_text": row_dict["note_text"][:500],
                "chunk_index": 0,
                "source_page": None,
                "filename": f"{row_dict['note_type']} - {row_dict['author']}",
                "content_type": "clinical_note",
                "uploaded_at": row_dict["note_date"],
                "patient_id": row_dict["patient_id"],
                "relevance_score": round(min(0.98, 0.50 + hit_count * 0.15), 2),
                "source_type": "clinical_note",
            })

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:limit]


def get_document(document_id: str) -> dict[str, Any] | None:
    """Retrieve a document by ID."""
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,)).fetchone()
        return dict(row) if row else None


def list_documents(patient_id: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """List documents, optionally filtered by patient."""
    init_db()
    with get_connection() as conn:
        if patient_id:
            rows = conn.execute(
                "SELECT document_id, patient_id, filename, content_type, uploaded_at, page_count, processing_status "
                "FROM documents WHERE patient_id = ? ORDER BY uploaded_at DESC LIMIT ?",
                (patient_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT document_id, patient_id, filename, content_type, uploaded_at, page_count, processing_status "
                "FROM documents ORDER BY uploaded_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(row) for row in rows]


def log_audit(agent_name: str, action: str, patient_id: str = "", session_id: str = "",
              details: str = "{}", user_role: str = "system") -> dict[str, Any]:
    """Insert an audit log entry and return it."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO audit_log (event_timestamp, agent_name, action, patient_id, session_id, details, user_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now, agent_name, action, patient_id or None, session_id or None, details, user_role))
        conn.commit()
        return {
            "event_id": cursor.lastrowid,
            "timestamp": now,
            "agent_name": agent_name,
            "action": action,
        }


# ---------------------------------------------------------------------------
# Patient helpers (replaces mock_data.get_patient)
# ---------------------------------------------------------------------------

def get_patient(patient_id: str) -> dict[str, Any] | None:
    """Retrieve a full patient record by ID, including extended JSON data."""
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM patients_core WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        extended_raw = result.pop("extended_data", None)
        if extended_raw:
            try:
                extended = json.loads(extended_raw) if isinstance(extended_raw, str) else extended_raw
                result.update(extended)
            except (json.JSONDecodeError, TypeError):
                pass
        return result


# ---------------------------------------------------------------------------
# Imaging helpers (replaces mock_data.get_image_quality, _find_image_context)
# ---------------------------------------------------------------------------

def get_imaging_quality(gcs_uri: str) -> dict[str, Any] | None:
    """Retrieve image quality metadata from the imaging_studies table."""
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT quality_score, resolution, bit_depth, contrast, artifacts, "
            "dicom_compliant, file_size_kb, modality "
            "FROM imaging_studies WHERE gcs_uri = ?", (gcs_uri,)
        ).fetchone()
        return dict(row) if row else None


def get_image_context(gcs_uri: str) -> dict[str, Any]:
    """Get full image context: modality, body_region, description, plus extracted_fields."""
    init_db()
    with get_connection() as conn:
        img_row = conn.execute(
            "SELECT session_id, patient_id, modality, body_region, description "
            "FROM imaging_studies WHERE gcs_uri = ?", (gcs_uri,)
        ).fetchone()
        if not img_row:
            return {
                "modality": "Unknown", "body_region": "Unknown",
                "description": "", "extracted_fields": [], "regions": [],
            }
        img = dict(img_row)
        fields = conn.execute(
            "SELECT field_name, field_value AS value, confidence, ontology_code "
            "FROM extracted_fields WHERE session_id = ?", (img["session_id"],)
        ).fetchall()
        field_list = [dict(f) for f in fields]
        return {
            "modality": img["modality"],
            "body_region": img["body_region"],
            "description": img["description"],
            "extracted_fields": field_list,
            "session_id": img["session_id"],
            "patient_id": img["patient_id"],
            "regions": [f["field_name"] for f in field_list],
        }


def search_imaging_studies(patient_id: str, keywords: list[str]) -> list[dict[str, Any]]:
    """Search imaging studies by patient and keyword matching on description."""
    init_db()
    if not keywords:
        return []
    like_clauses = " OR ".join(["description LIKE ?"] * len(keywords))
    params: list[Any] = [f"%{kw}%" for kw in keywords]
    with get_connection() as conn:
        if patient_id:
            sql = (
                f"SELECT study_id, session_id, patient_id, gcs_uri, modality, "
                f"body_region, description, quality_score "
                f"FROM imaging_studies WHERE patient_id = ? AND ({like_clauses})"
            )
            rows = conn.execute(sql, [patient_id] + params).fetchall()
        else:
            sql = (
                f"SELECT study_id, session_id, patient_id, gcs_uri, modality, "
                f"body_region, description, quality_score "
                f"FROM imaging_studies WHERE {like_clauses}"
            )
            rows = conn.execute(sql, params).fetchall()
    results = []
    for row in rows:
        d = dict(row)
        hit_count = sum(1 for kw in keywords if kw.lower() in (d.get("description") or "").lower())
        d["relevance_score"] = round(min(0.98, 0.50 + hit_count * 0.15), 2)
        results.append(d)
    return sorted(results, key=lambda x: x["relevance_score"], reverse=True)


# ---------------------------------------------------------------------------
# Session / extraction helpers
# ---------------------------------------------------------------------------

def get_sessions_with_fields(patient_id: str) -> list[dict[str, Any]]:
    """Get sessions for a patient with their extracted fields nested."""
    init_db()
    with get_connection() as conn:
        sessions = conn.execute(
            "SELECT session_id, patient_id, session_date, extraction_confidence, "
            "clinician_verification FROM sessions WHERE patient_id = ? "
            "ORDER BY session_date DESC", (patient_id,)
        ).fetchall()
        result = []
        for s in sessions:
            sd = dict(s)
            fields = conn.execute(
                "SELECT field_name, field_value AS value, confidence, ontology_code "
                "FROM extracted_fields WHERE session_id = ?", (sd["session_id"],)
            ).fetchall()
            sd["extracted_fields"] = [dict(f) for f in fields]
            result.append(sd)
        return result


def get_extracted_fields(session_id: str) -> list[dict[str, Any]]:
    """Return extracted fields for a session."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT field_name, field_value AS value, confidence, ontology_code, needs_review "
            "FROM extracted_fields WHERE session_id = ?", (session_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def ensure_patient(patient_id: str, name: str = "") -> dict[str, Any]:
    """Ensure a patients_core row exists so session inserts satisfy the FK.

    Live extraction can register a patient the store has never seen; the
    minimal row is created as needs_review so clinicians triage it later.
    """
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT patient_id FROM patients_core WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if row:
            return {"patient_id": patient_id, "created": False}
        conn.execute("""
            INSERT INTO patients_core (
                patient_id, name, age, sex, risk_level, primary_diagnosis,
                assigned_clinician, last_session_date, data_completeness_score,
                open_tasks, ai_review_status
            ) VALUES (?, ?, 0, 'Unknown', 'needs_review', '', '', NULL, 0.0, 1, 'needs_review')
        """, (patient_id, name or f"Patient {patient_id}"))
        conn.commit()
    return {"patient_id": patient_id, "created": True}


def store_session(
    session_id: str,
    patient_id: str,
    session_date: str,
    uploaded_image_count: int = 0,
    extraction_confidence: float = 0.0,
    clinician_verification: str = "verified",
) -> dict[str, Any]:
    """Insert a session row so extracted fields have a valid parent record.

    extracted_fields.session_id has an enforced foreign key (PRAGMA
    foreign_keys=ON), so persistence callers must create the session first.
    """
    init_db()
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO sessions (
                session_id, patient_id, session_date, uploaded_image_count,
                extraction_confidence, clinician_verification, json_sync_status,
                relational_sync_status, vector_sync_status, audit_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'synced', 'synced', 'synced', 'recorded')
        """, (session_id, patient_id, session_date, uploaded_image_count,
              extraction_confidence, clinician_verification))
        conn.commit()
    return {"session_id": session_id, "patient_id": patient_id}


def store_extraction_fields(
    session_id: str, patient_id: str, fields: list[dict]
) -> dict[str, Any]:
    """Insert extracted fields into the extracted_fields table."""
    init_db()
    inserted = 0
    with get_connection() as conn:
        for field in fields:
            if not isinstance(field, dict):
                continue
            conn.execute("""
                INSERT INTO extracted_fields (
                    session_id, patient_id, field_name, field_value, confidence,
                    ontology_code, needs_review
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, patient_id,
                field.get("field_name", field.get("name", "")),
                field.get("value", field.get("field_value", "")),
                field.get("confidence", 0.0),
                field.get("ontology_code"),
                field.get("confidence", 0.0) < 0.8,
            ))
            inserted += 1
        conn.commit()
    return {"rows_inserted": inserted, "session_id": session_id}


# ---------------------------------------------------------------------------
# Local storage (replaces fake GCS URIs)
# ---------------------------------------------------------------------------

def store_document_to_local(
    patient_id: str, session_id: str, data: str, content_type: str
) -> dict[str, Any]:
    """Write data to local filesystem and record in documents table."""
    init_db()
    upload_dir = active_uploads_root() / patient_id / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = ".json" if "json" in content_type else ".txt"
    filename = f"extraction-result{ext}"
    file_path = upload_dir / filename
    file_path.write_text(data, encoding="utf-8")

    import hashlib
    doc_id = f"STORE-{hashlib.sha256(data.encode()).hexdigest()[:16]}"
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO documents (
                document_id, patient_id, filename, content_type, file_path,
                uploaded_at, raw_text, page_count, processing_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'stored')
        """, (doc_id, patient_id or None, filename, content_type, str(file_path), now, data))
        conn.commit()

    return {
        "document_id": doc_id,
        "file_path": str(file_path),
        "stored_at": now,
        "size_bytes": len(data),
    }


# ---------------------------------------------------------------------------
# Q&A memory persistence
# ---------------------------------------------------------------------------

def save_qa_memory(
    patient_id: str, question: str, answer_summary: str,
    sql_query: str | None = None, memory_type: str = "qa",
) -> dict[str, Any]:
    """Persist a Q&A interaction or query pattern to the qa_memory table."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO qa_memory (patient_id, question, answer_summary, sql_query, created_at, memory_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (patient_id or None, question, answer_summary, sql_query, now, memory_type))
        conn.commit()
        return {"memory_id": cursor.lastrowid, "created_at": now, "memory_type": memory_type}


def search_qa_memory(patient_id: str = "", limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve recent Q&A memories, optionally filtered by patient."""
    init_db()
    with get_connection() as conn:
        if patient_id:
            rows = conn.execute(
                "SELECT * FROM qa_memory WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
                (patient_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM qa_memory ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


# Auto-initialize on import
init_db()
