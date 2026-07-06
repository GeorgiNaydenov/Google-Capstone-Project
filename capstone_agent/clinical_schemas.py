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
    birth_date DATE,
    gender_identity VARCHAR(50),
    race_ethnicity VARCHAR(80),
    preferred_language VARCHAR(60),
    zip3 VARCHAR(3),
    risk_level VARCHAR(20) NOT NULL,       -- 'high', 'needs_review', 'stable'
    primary_diagnosis VARCHAR(200),
    assigned_clinician VARCHAR(100),
    last_session_date DATE,
    data_completeness_score FLOAT,         -- 0.0 to 1.0
    open_tasks INTEGER DEFAULT 0,
    ai_review_status VARCHAR(20),          -- 'verified', 'needs_review', 'pending'
    extended_data TEXT,                     -- JSON: demographics, medications, allergies, care_team
    blood_type VARCHAR(5),
    marital_status VARCHAR(30),
    smoking_status VARCHAR(20),            -- 'Never', 'Former', 'Current', 'Unknown'
    alcohol_use VARCHAR(20),               -- 'None', 'Social', 'Moderate', 'Heavy'
    bmi FLOAT,
    care_archetype VARCHAR(40),            -- e.g. 'cardiometabolic', 'renal', 'complex_multimorbidity'
    privacy_class VARCHAR(30),             -- 'PII' or 'DEIDENTIFIED'
    consent_status VARCHAR(30),            -- 'full', 'limited_research', 'treatment_only'
    record_quality VARCHAR(30),            -- 'high', 'mixed', 'requires_reconciliation'
    primary_provider_id INTEGER            -- REFERENCES providers(provider_id)
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
    vector_chunk_id VARCHAR(30),           -- Link to Vertex AI Vector Search
    is_signed BOOLEAN DEFAULT TRUE,
    signed_at TIMESTAMP
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
    flag VARCHAR(10),                      -- 'normal', 'high', 'low', 'critical_high', 'critical_low'
    panel_id INTEGER,                      -- REFERENCES lab_panels(panel_id)
    loinc_code VARCHAR(20),
    reference_low FLOAT,
    reference_high FLOAT,
    is_abnormal BOOLEAN DEFAULT FALSE,
    result_status VARCHAR(20)              -- 'Normal', 'High', 'Low', 'Critical High', 'Critical Low'
);""",

    "lab_panels": """CREATE TABLE lab_panels (
    panel_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    panel_name VARCHAR(80),                -- e.g. 'Lipid Panel', 'Comprehensive Metabolic Panel'
    ordered_by VARCHAR(100),
    ordered_date DATE,
    collected_date DATE,
    resulted_date DATE,
    lab_facility VARCHAR(120),
    accession_number VARCHAR(20),
    status VARCHAR(20)                     -- 'Final', 'Preliminary', 'Corrected'
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

    "patient_conditions": """CREATE TABLE patient_conditions (
    condition_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    diagnosis_code VARCHAR(20),            -- ICD-10 code, e.g. 'E11.9'
    condition_name VARCHAR(200) NOT NULL,
    category VARCHAR(60),
    onset_date DATE,
    status VARCHAR(30),                    -- 'Active', 'Chronic', 'Resolved', 'In Remission'
    severity VARCHAR(30),
    is_primary BOOLEAN DEFAULT FALSE,
    diagnosing_provider VARCHAR(100),
    notes TEXT,
    resolved_date DATE
);""",

    "medications": """CREATE TABLE medications (
    medication_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    medication_name VARCHAR(120) NOT NULL,
    medication_class VARCHAR(80),          -- e.g. 'Biguanide', 'ACE inhibitor', 'Statin'
    dose VARCHAR(80),
    route VARCHAR(40),
    frequency VARCHAR(60),
    start_date DATE,
    status VARCHAR(30),                    -- 'active', 'held', 'stopped'
    adherence_score FLOAT,
    generic_name VARCHAR(120),
    brand_name VARCHAR(120),
    indication VARCHAR(160),               -- condition the medication treats
    prescribing_provider VARCHAR(100),
    end_date DATE,
    refills_remaining INTEGER,
    pharmacy_name VARCHAR(80),
    ndc_code VARCHAR(20)
);""",

    "allergies": """CREATE TABLE allergies (
    allergy_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    allergen VARCHAR(120) NOT NULL,
    reaction VARCHAR(200),
    severity VARCHAR(30),                  -- 'Mild', 'Moderate', 'Severe', 'Life-Threatening'
    recorded_date DATE,
    allergen_category VARCHAR(40),         -- 'Drug', 'Food', 'Environmental', 'Contrast', 'Latex'
    onset_date DATE,
    verified_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);""",

    "encounters": """CREATE TABLE encounters (
    encounter_id VARCHAR(30) PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    encounter_date DATE NOT NULL,
    encounter_type VARCHAR(60),
    department VARCHAR(80),
    clinician VARCHAR(100),
    reason VARCHAR(200),
    disposition VARCHAR(80)
);""",

    "vital_signs": """CREATE TABLE vital_signs (
    vital_id SERIAL PRIMARY KEY,
    encounter_id VARCHAR(30) REFERENCES encounters(encounter_id),
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    measured_at TIMESTAMP NOT NULL,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    respiratory_rate INTEGER,
    oxygen_saturation FLOAT,
    temperature_c FLOAT,
    weight_kg FLOAT,
    bmi FLOAT,
    pain_score INTEGER,                    -- 0 to 10
    blood_glucose_mgdl FLOAT,
    recorded_by VARCHAR(100)
);""",

    "care_gaps": """CREATE TABLE care_gaps (
    gap_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    gap_type VARCHAR(80),
    description VARCHAR(300),
    priority VARCHAR(30),
    due_date DATE,
    status VARCHAR(30),
    owner VARCHAR(100)
);""",

    "procedures": """CREATE TABLE procedures (
    procedure_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    procedure_date DATE NOT NULL,
    procedure_name VARCHAR(160),
    procedure_code VARCHAR(30),            -- CPT code, e.g. '45378'
    body_site VARCHAR(80),
    outcome VARCHAR(120),
    performer VARCHAR(100),
    facility_name VARCHAR(120),
    indication VARCHAR(200),
    duration_minutes INTEGER,
    anesthesia_type VARCHAR(60),
    complications VARCHAR(200),
    status VARCHAR(30)                     -- 'Completed', 'Scheduled', 'Cancelled'
);""",

    "social_determinants": """CREATE TABLE social_determinants (
    sdoh_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    assessed_date DATE,
    housing_status VARCHAR(80),
    transportation_access VARCHAR(80),
    food_security VARCHAR(80),
    financial_strain VARCHAR(80),
    living_situation VARCHAR(120),
    smoking_status VARCHAR(20),
    packs_per_day FLOAT,
    smoking_years INTEGER,
    alcohol_use VARCHAR(20),
    drinks_per_week INTEGER,
    drug_use VARCHAR(20),
    exercise_frequency VARCHAR(40),
    diet_type VARCHAR(40),
    education_level VARCHAR(60),
    employment_status VARCHAR(40),
    occupation VARCHAR(80)
);""",

    "providers": """CREATE TABLE providers (
    provider_id SERIAL PRIMARY KEY,
    first_name VARCHAR(60),
    last_name VARCHAR(60),
    full_name VARCHAR(140),                -- display name matching assigned_clinician values
    title VARCHAR(20),                     -- 'MD', 'DO', 'MD, PhD'
    specialty VARCHAR(60),
    department VARCHAR(60),
    npi_number VARCHAR(10),
    email VARCHAR(120),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE
);""",

    "icd10_codes": """CREATE TABLE icd10_codes (
    icd10_id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE,               -- e.g. 'E11.9'
    description VARCHAR(200),
    category VARCHAR(60)                   -- e.g. 'Endocrine', 'Cardiovascular'
);""",

    "cpt_codes": """CREATE TABLE cpt_codes (
    cpt_id SERIAL PRIMARY KEY,
    code VARCHAR(10),                      -- e.g. '99214'
    description VARCHAR(200),
    category VARCHAR(60)                   -- e.g. 'Office Visit', 'Surgery'
);""",

    "insurance_policies": """CREATE TABLE insurance_policies (
    policy_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    insurance_provider VARCHAR(80),
    plan_name VARCHAR(120),
    policy_number VARCHAR(20),
    group_number VARCHAR(20),
    member_id VARCHAR(20),
    coverage_type VARCHAR(20),             -- 'HMO', 'PPO', 'Medicare', 'Medicaid', 'Self-Pay'
    subscriber_name VARCHAR(120),
    subscriber_relation VARCHAR(20),
    coverage_start_date DATE,
    coverage_end_date DATE,
    deductible FLOAT,
    copay FLOAT,
    out_of_pocket_max FLOAT,
    is_primary BOOLEAN,
    is_active BOOLEAN DEFAULT TRUE
);""",

    "emergency_contacts": """CREATE TABLE emergency_contacts (
    contact_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    contact_order INTEGER,
    full_name VARCHAR(120),
    relationship VARCHAR(40),
    phone_primary VARCHAR(20),
    phone_secondary VARCHAR(20),
    email VARCHAR(120),
    is_primary BOOLEAN
);""",

    "immunizations": """CREATE TABLE immunizations (
    immunization_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    vaccine_name VARCHAR(80),
    vaccine_abbreviation VARCHAR(20),
    cvx_code VARCHAR(10),
    administered_date DATE,
    administered_by VARCHAR(100),
    lot_number VARCHAR(20),
    manufacturer VARCHAR(60),
    site VARCHAR(40),
    route VARCHAR(10),                     -- 'IM', 'SC'
    dose_number INTEGER,
    series_complete BOOLEAN,
    expiration_date DATE
);""",

    "appointments": """CREATE TABLE appointments (
    appointment_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    provider VARCHAR(100),
    appointment_date DATE,
    start_time VARCHAR(5),
    end_time VARCHAR(5),
    appointment_type VARCHAR(60),
    department VARCHAR(60),
    facility_name VARCHAR(120),
    status VARCHAR(20),                    -- 'Completed', 'Cancelled', 'No-Show', 'Scheduled'
    reason_for_visit VARCHAR(200),
    follow_up_required BOOLEAN,
    follow_up_date DATE
);""",

    "medical_history": """CREATE TABLE medical_history (
    history_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    condition_name VARCHAR(160),
    icd10_code VARCHAR(10),
    onset_year INTEGER,
    resolution_year INTEGER,
    is_chronic BOOLEAN
);""",

    "surgical_history": """CREATE TABLE surgical_history (
    surgery_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    procedure_name VARCHAR(160),
    cpt_code VARCHAR(10),
    surgery_date DATE,
    facility_name VARCHAR(120),
    surgeon_name VARCHAR(100),
    indication VARCHAR(200),
    outcome VARCHAR(200),
    anesthesia_type VARCHAR(60)
);""",

    "family_history": """CREATE TABLE family_history (
    family_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(10) REFERENCES patients_core(patient_id),
    relation VARCHAR(40),                  -- 'Mother', 'Father', 'Sibling', ...
    condition_name VARCHAR(160),
    icd10_code VARCHAR(10),
    age_of_onset INTEGER,
    is_deceased BOOLEAN,
    cause_of_death VARCHAR(160)
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
