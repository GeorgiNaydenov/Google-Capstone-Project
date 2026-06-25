"""Clinical database schema definitions and query engine.

Provides the SQL schema metadata and query execution for the
Database Intelligence pipeline. All queries run against the real
SQLite database via database.execute_sql().

Design decisions:
- Schema DDL is stored as strings so the nl_to_sql_agent can read
  table structures and generate appropriate queries.
- execute_query() delegates to database.execute_sql() for real SQL execution.
- All queries are read-only (SELECT). The validator rejects mutations.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Schema DDL (Cloud SQL / BigQuery table definitions)
# ---------------------------------------------------------------------------

SCHEMA_DDL: dict[str, str] = {
    "patients_core": """CREATE TABLE patients_core (
    patient_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL,
    sex VARCHAR(10) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,       -- 'high', 'needs_review', 'stable'
    primary_diagnosis VARCHAR(200),
    assigned_clinician VARCHAR(100),
    last_session_date DATE,
    data_completeness_score FLOAT,         -- 0.0 to 1.0
    open_tasks INTEGER DEFAULT 0,
    ai_review_status VARCHAR(20),          -- 'verified', 'needs_review', 'pending'
    extended_data TEXT                      -- JSON: demographics, medications, allergies, care_team
);""",

    "sessions": """CREATE TABLE sessions (
    session_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    session_date DATE NOT NULL,
    uploaded_image_count INTEGER DEFAULT 0,
    extraction_confidence FLOAT,           -- 0.0 to 1.0
    clinician_verification VARCHAR(20),    -- 'verified', 'pending', 'rejected'
    json_sync_status VARCHAR(20),          -- 'synced', 'pending', 'failed'
    relational_sync_status VARCHAR(20),
    vector_sync_status VARCHAR(20),
    audit_status VARCHAR(20)
);""",

    "extracted_fields": """CREATE TABLE extracted_fields (
    field_id SERIAL PRIMARY KEY,
    session_id VARCHAR(20) REFERENCES sessions(session_id),
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    field_name VARCHAR(100) NOT NULL,
    field_value VARCHAR(500),
    confidence FLOAT,                      -- 0.0 to 1.0
    ontology_code VARCHAR(50),             -- SNOMED CT or LOINC code
    needs_review BOOLEAN DEFAULT FALSE
);""",

    "clinical_notes": """CREATE TABLE clinical_notes (
    note_id VARCHAR(20) PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    note_date DATE NOT NULL,
    author VARCHAR(100),
    note_type VARCHAR(50),                 -- 'Progress Note', 'Consult', etc.
    note_text TEXT,
    vector_chunk_id VARCHAR(30)            -- Link to Vertex AI Vector Search
);""",

    "lab_results": """CREATE TABLE lab_results (
    result_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    result_date DATE NOT NULL,
    test_name VARCHAR(50),
    component VARCHAR(50),
    value VARCHAR(20),
    unit VARCHAR(20),
    reference_range VARCHAR(30),
    flag VARCHAR(10)                       -- 'normal', 'high', 'low'
);""",

    "imaging_studies": """CREATE TABLE imaging_studies (
    study_id SERIAL PRIMARY KEY,
    session_id VARCHAR(20) REFERENCES sessions(session_id),
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    gcs_uri VARCHAR(200) NOT NULL,         -- gs://clinical-data/...
    modality VARCHAR(30),                  -- 'CT', 'X-Ray', 'MRI', etc.
    body_region VARCHAR(50),
    description VARCHAR(200),
    quality_score FLOAT,
    resolution VARCHAR(20),
    bit_depth INTEGER,
    contrast VARCHAR(20),
    artifacts VARCHAR(50),
    dicom_compliant BOOLEAN DEFAULT FALSE,
    file_size_kb INTEGER
);""",

    "audit_log": """CREATE TABLE audit_log (
    event_id SERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP NOT NULL,
    agent_name VARCHAR(50),
    action VARCHAR(50),
    patient_id VARCHAR(10),
    session_id VARCHAR(20),
    details JSONB,
    user_role VARCHAR(20)
);""",

    "documents": """CREATE TABLE documents (
    document_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(10),
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(50),
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP NOT NULL,
    raw_text TEXT,
    page_count INTEGER DEFAULT 1,
    processing_status VARCHAR(20) DEFAULT 'processed',
    gemini_analysis TEXT
);""",

    "document_chunks": """CREATE TABLE document_chunks (
    chunk_id SERIAL PRIMARY KEY,
    document_id VARCHAR(50) REFERENCES documents(document_id),
    patient_id VARCHAR(10),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    source_page INTEGER
);""",

    "qa_memory": """CREATE TABLE qa_memory (
    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id VARCHAR(10),
    question TEXT NOT NULL,
    answer_summary TEXT NOT NULL,
    sql_query TEXT,
    created_at TIMESTAMP NOT NULL,
    memory_type VARCHAR(20) DEFAULT 'qa'   -- 'qa' or 'query_pattern'
);""",
}

# Full schema as a single string for the agent's context window
FULL_SCHEMA = "\n\n".join(SCHEMA_DDL.values())

# Table names for allowlisting
ALLOWED_TABLES = set(SCHEMA_DDL.keys())


def get_schema(tables: str = "all") -> str:
    """Return schema DDL for the requested tables.

    Args:
        tables: Comma-separated table names, or 'all' for everything.

    Returns:
        DDL string the NL-to-SQL agent reads to generate queries.
    """
    if tables == "all":
        return FULL_SCHEMA

    requested = [t.strip() for t in tables.split(",")]
    parts = []
    for table in requested:
        if table in SCHEMA_DDL:
            parts.append(SCHEMA_DDL[table])
    return "\n\n".join(parts) if parts else f"No schemas found for: {tables}"


# ---------------------------------------------------------------------------
# SQL safety validation
# ---------------------------------------------------------------------------

BLOCKED_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL",
}


def validate_sql(sql: str) -> dict[str, Any]:
    """Validate SQL for safety — read-only, no system tables, within schema.

    Returns:
        Dict with 'safe' bool, 'reason' string, and 'tables_referenced' list.
    """
    upper_sql = sql.upper().strip()

    if not upper_sql.startswith("SELECT"):
        return {"safe": False, "reason": "Query must start with SELECT.", "tables_referenced": []}

    for keyword in BLOCKED_KEYWORDS:
        if keyword in upper_sql.split():
            return {"safe": False, "reason": f"Blocked keyword: {keyword}", "tables_referenced": []}

    if "INFORMATION_SCHEMA" in upper_sql or "PG_CATALOG" in upper_sql:
        return {"safe": False, "reason": "System catalog access not allowed.", "tables_referenced": []}

    tables_found = []
    for table in ALLOWED_TABLES:
        if table.upper() in upper_sql:
            tables_found.append(table)

    if not tables_found:
        return {"safe": False, "reason": "No recognized tables in query.", "tables_referenced": []}

    return {"safe": True, "reason": "Query passed safety checks.", "tables_referenced": tables_found}


# ---------------------------------------------------------------------------
# Mock query executor (simulates Cloud SQL / BigQuery)
# ---------------------------------------------------------------------------

def execute_query(sql: str) -> dict[str, Any]:
    """Execute a read-only SQL query against the real SQLite database."""
    from . import database
    return database.execute_sql(sql)
