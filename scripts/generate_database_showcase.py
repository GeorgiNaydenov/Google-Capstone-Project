"""Generate a large governed SQLite cohort for the database agent.

The script builds the full 29-table clinical schema and seeds it with a
clinically coherent enterprise cohort (default 10,000 patients across four
years): archetype-driven diagnoses, condition-forced medications, biased lab
values with LOINC codes, longitudinal vitals, payer/SDoH context, narrative
notes, and a synthetic-PII / de-identified privacy mix. It also emits reusable
natural-language query examples with SQL, textual insights, Plotly specs, and
Matplotlib chart images.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import showcase_clinical_core as core


def _load_schema_ddl() -> dict[str, str]:
    """Load the clinical schema module without importing capstone_agent.__init__."""
    schema_path = Path(__file__).resolve().parents[1] / "capstone_agent" / "clinical_schemas.py"
    spec = importlib.util.spec_from_file_location("clinical_schemas_for_showcase", schema_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load schema module from {schema_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.SCHEMA_DDL)


SCHEMA_DDL = _load_schema_ddl()

# Categorical chart palette mirroring the frontend ChartPanel colors so the
# static matplotlib exports and live Plotly renders stay visually consistent.
CHART_PALETTE = ("#2563eb", "#16a34a", "#b45309", "#dc2626", "#0284c7", "#7c3aed", "#0f766e")


DEFAULT_OUTPUT = Path("showcase_data/database")
DEFAULT_DB = DEFAULT_OUTPUT / "clinical_showcase.db"
DEFAULT_ANCHOR_DATE = date(2026, 7, 5)
DEFAULT_PATIENT_COUNT = 1500
DEFAULT_YEARS = 4
PATIENT_BATCH = 250

EXTRACTION_FIELD_METRICS = ("hba1c", "egfr", "bnp", "crp", "ldl_cholesterol", "creatinine", "hemoglobin", "inr")


def _sqlite_ddl(ddl: str) -> str:
    """Convert portable demo DDL to SQLite-compatible DDL."""

    return ddl.replace("SERIAL", "INTEGER").replace("JSONB", "TEXT")


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all clinical tables plus helpful read indexes."""

    for ddl in SCHEMA_DDL.values():
        conn.execute(_sqlite_ddl(ddl))
    conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_risk ON patients_core(risk_level)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_patient ON sessions(patient_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_patient_date ON clinical_notes(patient_id, note_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_labs_patient_date ON lab_results(patient_id, result_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_labs_component ON lab_results(component, flag)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent_name, action)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_conditions_patient ON patient_conditions(patient_id, category, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_encounters_patient_date ON encounters(patient_id, encounter_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vitals_patient_date ON vital_signs(patient_id, measured_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_care_gaps_status ON care_gaps(status, priority)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_social_patient ON social_determinants(patient_id, assessed_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id, status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_immunizations_patient ON immunizations(patient_id, vaccine_abbreviation)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_policies_patient ON insurance_policies(patient_id, is_primary)")


def _seed_reference_tables(conn: sqlite3.Connection, providers: list[dict[str, Any]]) -> dict[str, int]:
    """Insert the provider directory and ICD-10/CPT terminology tables."""

    conn.executemany(
        "INSERT INTO providers (provider_id, first_name, last_name, full_name, title, specialty, department, npi_number, email, phone, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
        [(p["provider_id"], p["first_name"], p["last_name"], p["full_name"], p["title"], p["specialty"], p["department"], p["npi"], p["email"], p["phone"]) for p in providers],
    )
    conn.executemany(
        "INSERT INTO icd10_codes (code, description, category) VALUES (?, ?, ?)",
        core.ICD10_CATALOG,
    )
    conn.executemany(
        "INSERT INTO cpt_codes (code, description, category) VALUES (?, ?, ?)",
        core.CPT_CATALOG,
    )
    return {"providers": len(providers), "icd10_codes": len(core.ICD10_CATALOG), "cpt_codes": len(core.CPT_CATALOG)}


class _RowBuffer:
    """Accumulate per-table rows and flush them to SQLite in batches."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.rows: dict[str, list[tuple]] = {}
        self.sql: dict[str, str] = {}
        self.counts: dict[str, int] = {}

    def add(self, table: str, sql: str, row: tuple) -> None:
        """Queue one row for the named table."""
        self.sql[table] = sql
        self.rows.setdefault(table, []).append(row)
        self.counts[table] = self.counts.get(table, 0) + 1

    def flush(self) -> None:
        """Write all queued rows and clear the buffers."""
        for table, rows in self.rows.items():
            if rows:
                self.conn.executemany(self.sql[table], rows)
        self.rows = {}


def _extraction_fields_for(record: dict[str, Any], rng: random.Random) -> list[tuple[str, str, str | None]]:
    """Derive session extraction fields from the patient's actual lab values.

    Returns (field_name, field_value, ontology_code) tuples so the extraction
    pipeline's structured output stays consistent with the SQL cohort.
    """

    fields: list[tuple[str, str, str | None]] = []
    metrics = record.get("key_metrics", {})
    for metric_name in EXTRACTION_FIELD_METRICS:
        entry = metrics.get(metric_name)
        if entry is not None:
            loinc = next((test["loinc"] for test in core.LAB_CATALOG if test["name"].lower().replace(" ", "_").replace(",", "") == metric_name), None)
            fields.append((f"{metric_name}_value", str(entry["value"]), loinc))
        if len(fields) >= 4:
            break
    fields.append(("primary_finding", record["conditions"][0]["name"], record["conditions"][0]["code"]))
    fields.append(("medication_conflict", rng.choice(("present", "absent", "absent", "requires pharmacist review")), None))
    return fields


def seed_database(conn: sqlite3.Connection, patient_count: int, seed: int, anchor_date: date, years: int, patient_prefix: str = "PT-D", demo_platform: str = "primary") -> dict[str, int]:
    """Insert the deterministic clinically coherent cohort."""

    providers = core.build_providers(seed, demo_platform)
    row_counts = _seed_reference_tables(conn, providers)
    theme = core.TENANT_THEMES.get(demo_platform, core.TENANT_THEMES["primary"])
    lookback_days = max(365, years * 365)
    session_total = max(4, years)
    buffer = _RowBuffer(conn)
    session_index = 0
    encounter_index = 0
    panel_index = 0
    note_index = 0

    for index in range(1, patient_count + 1):
        record = core.build_patient(index, seed, patient_prefix, anchor_date, years, providers, demo_platform)
        rng = core.patient_rng(seed, f"{patient_prefix}-app", index)
        patient_id = record["patient_id"]
        clinician = record["provider"]["full_name"]

        extended = {
            "synthetic": True,
            "insurance": record["insurance"][0]["provider"] if record["insurance"] else None,
            "care_gap_count": len(record["care_gaps"]),
            "risk_drivers": rng.sample(("labs", "imaging", "notes", "medications", "utilization", "social_determinants"), 3),
            "care_archetype": record["archetype"],
            "privacy_class": record["privacy_class"],
            "demographics": {
                "dob": record["birth_date"],
                "mrn": record["mrn"],
                "insurance": record["insurance"][0]["plan_name"] if record["insurance"] else None,
                "primary_language": record["language"],
                "emergency_contact": f"{record['contacts'][0]['name']} ({record['contacts'][0]['relationship'].lower()})" if record["contacts"] else None,
            },
            "medications": [
                {"name": med["name"], "dose": f"{med['dose']} {med['frequency']}", "status": med["status"]}
                for med in record["medications"] if med["status"] == "active"
            ][:6],
            "allergies": [allergy["allergen"] for allergy in record["allergies"]] or ["No known allergies"],
            "care_team": record["care_team"],
            "diagnoses": [
                {"code": condition["code"], "description": condition["name"], "date": condition["onset_date"], "status": condition["status"].lower()}
                for condition in record["conditions"]
            ],
        }
        buffer.add(
            "patients_core",
            """INSERT INTO patients_core (
                patient_id, name, age, sex, birth_date, gender_identity, race_ethnicity,
                preferred_language, zip3, risk_level, primary_diagnosis, assigned_clinician,
                last_session_date, data_completeness_score, open_tasks, ai_review_status,
                extended_data, blood_type, marital_status, smoking_status, alcohol_use, bmi,
                care_archetype, privacy_class, consent_status, record_quality, primary_provider_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                patient_id, record["name"], record["age"], record["sex"], record["birth_date"],
                record["gender_identity"], record["race"], record["language"], record["zip3"],
                record["risk_level"], record["primary_diagnosis"], clinician,
                record["last_session_date"], record["completeness"], record["open_tasks"],
                record["ai_review_status"], json.dumps(extended), record["blood_type"],
                record["marital_status"], record["smoking"], record["alcohol"], record["bmi"],
                record["archetype"], record["privacy_class"], record["consent_status"],
                record["record_quality"], record["provider"]["provider_id"],
            ),
        )

        for condition in record["conditions"]:
            buffer.add(
                "patient_conditions",
                "INSERT INTO patient_conditions (patient_id, diagnosis_code, condition_name, category, onset_date, status, severity, is_primary, diagnosing_provider, notes, resolved_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, condition["code"], condition["name"], condition["category"], condition["onset_date"], condition["status"], condition["severity"], condition["is_primary"], condition["provider"], condition["notes"], condition["resolved_date"]),
            )
        for med in record["medications"]:
            buffer.add(
                "medications",
                "INSERT INTO medications (patient_id, medication_name, medication_class, dose, route, frequency, start_date, status, adherence_score, generic_name, brand_name, indication, prescribing_provider, end_date, refills_remaining, pharmacy_name, ndc_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, med["name"], med["class"], med["dose"], med["route"], med["frequency"], med["start_date"], med["status"], med["adherence"], med["generic"], med["brand"], med["indication"], med["prescriber"], med["end_date"], med["refills"], med["pharmacy"], med["ndc"]),
            )
        for allergy in record["allergies"]:
            buffer.add(
                "allergies",
                "INSERT INTO allergies (patient_id, allergen, reaction, severity, recorded_date, allergen_category, onset_date, verified_by, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, allergy["allergen"], allergy["reaction"], allergy["severity"], allergy["onset_date"] or record["last_session_date"], allergy["category"], allergy["onset_date"], allergy["verified_by"], allergy["active"]),
            )

        for vital in record["vitals"]:
            encounter_index += 1
            encounter_id = f"ENC-{patient_prefix.strip('PT-')}{encounter_index:07d}"
            buffer.add(
                "encounters",
                "INSERT INTO encounters (encounter_id, patient_id, encounter_date, encounter_type, department, clinician, reason, disposition) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (encounter_id, patient_id, vital["measured_at"][:10], rng.choice(("Primary care", "Specialty consult", "Telehealth", "Emergency follow-up", "Infusion visit")), record["provider"]["department"], clinician, f"Follow-up for {record['primary_diagnosis']}", rng.choice(("home", "follow-up scheduled", "medication adjusted", "referred"))),
            )
            buffer.add(
                "vital_signs",
                "INSERT INTO vital_signs (encounter_id, patient_id, measured_at, systolic_bp, diastolic_bp, heart_rate, respiratory_rate, oxygen_saturation, temperature_c, weight_kg, bmi, pain_score, blood_glucose_mgdl, recorded_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (encounter_id, patient_id, vital["measured_at"], vital["sbp"], vital["dbp"], vital["hr"], vital["rr"], vital["spo2"], vital["temp"], vital["weight"], vital["bmi"], vital["pain"], vital["glucose"], clinician),
            )

        for panel in record["panels"]:
            panel_index += 1
            buffer.add(
                "lab_panels",
                "INSERT INTO lab_panels (panel_id, patient_id, panel_name, ordered_by, ordered_date, collected_date, resulted_date, lab_facility, accession_number, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (panel_index, patient_id, panel["panel_name"], panel["ordered_by"], panel["ordered_date"], panel["collected_date"], panel["resulted_date"], panel["facility"], panel["accession"], panel["status"]),
            )
            for result in panel["results"]:
                buffer.add(
                    "lab_results",
                    "INSERT INTO lab_results (patient_id, result_date, test_name, component, value, unit, reference_range, flag, panel_id, loinc_code, reference_low, reference_high, is_abnormal, result_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (patient_id, panel["resulted_date"], panel["panel_name"], result["test"], str(result["value"]), result["unit"], f"{result['low']}-{result['high']}", result["flag"], panel_index, result["loinc"], result["low"], result["high"], result["is_abnormal"], result["status"]),
                )

        for gap_type, gap_description in record["care_gaps"]:
            buffer.add(
                "care_gaps",
                "INSERT INTO care_gaps (patient_id, gap_type, description, priority, due_date, status, owner) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (patient_id, gap_type, f"{gap_description} for {record['primary_diagnosis']}", "high" if record["risk_level"] == "high" else "medium", (anchor_date + timedelta(days=rng.randint(3, 120))).isoformat(), rng.choice(("open", "open", "scheduled", "deferred")), clinician),
            )
        for procedure in record["procedures"]:
            buffer.add(
                "procedures",
                "INSERT INTO procedures (patient_id, procedure_date, procedure_name, procedure_code, body_site, outcome, performer, facility_name, indication, duration_minutes, anesthesia_type, complications, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, procedure["date"], procedure["name"], procedure["code"], procedure["category"], procedure["outcome"], procedure["performer"], procedure["facility"], procedure["indication"], procedure["duration_minutes"], procedure["anesthesia"], None, procedure["status"]),
            )
        for immunization in record["immunizations"]:
            buffer.add(
                "immunizations",
                "INSERT INTO immunizations (patient_id, vaccine_name, vaccine_abbreviation, cvx_code, administered_date, administered_by, lot_number, manufacturer, site, route, dose_number, series_complete, expiration_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, immunization["name"], immunization["abbreviation"], immunization["cvx"], immunization["date"], immunization["administered_by"], immunization["lot"], immunization["manufacturer"], immunization["site"], immunization["route"], immunization["dose_number"], immunization["series_complete"], immunization["expiration"]),
            )
        for appointment in record["appointments"]:
            buffer.add(
                "appointments",
                "INSERT INTO appointments (patient_id, provider, appointment_date, start_time, end_time, appointment_type, department, facility_name, status, reason_for_visit, follow_up_required, follow_up_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, appointment["provider"], appointment["date"], appointment["start"], appointment["end"], appointment["type"], appointment["department"], appointment["facility"], appointment["status"], appointment["reason"], appointment["follow_up"], (date.fromisoformat(appointment["date"]) + timedelta(days=rng.randint(30, 90))).isoformat() if appointment["follow_up"] else None),
            )
        for history in record["medical_history"]:
            buffer.add(
                "medical_history",
                "INSERT INTO medical_history (patient_id, condition_name, icd10_code, onset_year, resolution_year, is_chronic) VALUES (?, ?, ?, ?, ?, ?)",
                (patient_id, history["condition"], None, history["onset_year"], history["resolution_year"], history["is_chronic"]),
            )
        for surgery in record["surgical_history"]:
            buffer.add(
                "surgical_history",
                "INSERT INTO surgical_history (patient_id, procedure_name, cpt_code, surgery_date, facility_name, surgeon_name, indication, outcome, anesthesia_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, surgery["procedure"], surgery["cpt"], surgery["date"], surgery["facility"], surgery["surgeon"], surgery["indication"], surgery["outcome"], surgery["anesthesia"]),
            )
        for relative in record["family_history"]:
            buffer.add(
                "family_history",
                "INSERT INTO family_history (patient_id, relation, condition_name, icd10_code, age_of_onset, is_deceased, cause_of_death) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (patient_id, relative["relation"], relative["condition"], None, relative["age_of_onset"], relative["is_deceased"], relative["cause_of_death"]),
            )
        social = record["social"]
        buffer.add(
            "social_determinants",
            "INSERT INTO social_determinants (patient_id, assessed_date, housing_status, transportation_access, food_security, financial_strain, living_situation, smoking_status, packs_per_day, smoking_years, alcohol_use, drinks_per_week, drug_use, exercise_frequency, diet_type, education_level, employment_status, occupation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (patient_id, (anchor_date - timedelta(days=rng.randint(0, 365))).isoformat(), social["housing"], social["transportation"], social["food_security"], social["financial_strain"], social["living_situation"], record["smoking"], social["packs_per_day"], social["smoking_years"], record["alcohol"], social["drinks_per_week"], record["drug_use"], social["exercise"], social["diet"], social["education"], social["employment"], record["occupation"]),
        )
        for policy in record["insurance"]:
            buffer.add(
                "insurance_policies",
                "INSERT INTO insurance_policies (patient_id, insurance_provider, plan_name, policy_number, group_number, member_id, coverage_type, subscriber_name, subscriber_relation, coverage_start_date, coverage_end_date, deductible, copay, out_of_pocket_max, is_primary, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                (patient_id, policy["provider"], policy["plan_name"], policy["policy_number"], policy["group_number"], policy["member_id"], policy["coverage_type"], policy["subscriber"], policy["relation"], policy["start_date"], policy["end_date"], policy["deductible"], policy["copay"], policy["oop_max"], policy["is_primary"]),
            )
        for contact in record["contacts"]:
            buffer.add(
                "emergency_contacts",
                "INSERT INTO emergency_contacts (patient_id, contact_order, full_name, relationship, phone_primary, phone_secondary, email, is_primary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (patient_id, contact["order"], contact["name"], contact["relationship"], contact["phone"], None, None, contact["is_primary"]),
            )
        for note in record["notes"]:
            note_index += 1
            buffer.add(
                "clinical_notes",
                "INSERT INTO clinical_notes (note_id, patient_id, note_date, author, note_type, note_text, vector_chunk_id, is_signed, signed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"NOTE-{patient_prefix.strip('PT-')}{note_index:07d}", patient_id, note["date"], note["author"], note["type"], note["text"], f"VEC-{patient_prefix.strip('PT-')}{note_index:07d}", True, note["signed_at"]),
            )

        # --- App pipeline artifacts: sessions, extracted fields, imaging, docs ---
        extraction_fields = _extraction_fields_for(record, rng)
        for offset in range(session_total):
            session_index += 1
            session_id = f"SES-{patient_prefix.strip('PT-')}{session_index:06d}"
            spread_days = round(offset * lookback_days / max(1, session_total - 1))
            session_date = anchor_date - timedelta(days=min(lookback_days - 1, spread_days + rng.randint(0, 24)))
            confidence = round(rng.uniform(0.68, 0.98), 2)
            verification = "pending" if confidence < 0.82 or (record["risk_level"] != "stable" and rng.random() < 0.35) else "verified"
            buffer.add(
                "sessions",
                "INSERT INTO sessions (session_id, patient_id, session_date, uploaded_image_count, extraction_confidence, clinician_verification, json_sync_status, relational_sync_status, vector_sync_status, audit_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, patient_id, session_date.isoformat(), rng.randint(1, 4), confidence, verification, "synced", "synced" if verification == "verified" else "pending", "synced" if verification == "verified" else "pending", "recorded"),
            )
            for field_name, field_value, ontology in extraction_fields:
                field_confidence = round(rng.uniform(0.64, 0.99), 2)
                buffer.add(
                    "extracted_fields",
                    "INSERT INTO extracted_fields (session_id, patient_id, field_name, field_value, confidence, ontology_code, needs_review) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (session_id, patient_id, field_name, field_value, field_confidence, ontology or "SYNTHETIC", field_confidence < 0.8),
                )
            for modality in rng.sample(("CT", "MRI", "X-Ray", "Fundoscopy", "Document"), 2):
                buffer.add(
                    "imaging_studies",
                    "INSERT INTO imaging_studies (session_id, patient_id, gcs_uri, modality, body_region, description, quality_score, resolution, bit_depth, contrast, artifacts, dicom_compliant, file_size_kb) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (session_id, patient_id, f"gs://{theme['gcs_bucket']}/{patient_id}/{session_id}/{modality.lower()}-{offset}.png", modality, rng.choice(("Chest", "Abdomen", "Brain", "Eye", "Cardiac")), f"{modality} evidence for {record['primary_diagnosis']}", round(rng.uniform(0.72, 0.98), 2), rng.choice(("512x512", "1024x1024", "2048x2048")), rng.choice((8, 12, 16)), rng.choice(("adequate", "low", "high")), rng.choice(("none", "motion", "reflection", "low_contrast")), modality in {"CT", "MRI", "X-Ray"}, rng.randint(280, 4200)),
                )
            timestamp = datetime.combine(session_date, datetime.min.time()).isoformat()
            buffer.add(
                "audit_log",
                "INSERT INTO audit_log (event_timestamp, agent_name, action, patient_id, session_id, details, user_role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (timestamp, "image_extraction_pipeline", "extraction_complete", patient_id, session_id, json.dumps({"confidence": confidence, "verification": verification}), "system"),
            )
            buffer.add(
                "audit_log",
                "INSERT INTO audit_log (event_timestamp, agent_name, action, patient_id, session_id, details, user_role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (timestamp, "database_intelligence_pipeline", "cohort_row_indexed", patient_id, session_id, json.dumps({"risk_level": record["risk_level"], "archetype": record["archetype"]}), "admin"),
            )

        doc_id = f"DOC-{patient_prefix.strip('PT-')}{index:05d}-01"
        raw_text = (f"CLINICAL EVIDENCE REPORT\nPatient: {record['name']} ({patient_id})\n"
                    f"Diagnosis: {record['primary_diagnosis']}\nRisk level: {record['risk_level']}\n"
                    f"Care archetype: {record['archetype']}\nSigned by {clinician}")
        buffer.add(
            "documents",
            "INSERT INTO documents (document_id, patient_id, filename, content_type, file_path, uploaded_at, raw_text, page_count, processing_status, gemini_analysis) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (doc_id, patient_id, f"report_{patient_id}.pdf", "application/pdf", f"uploads/report_{patient_id}.pdf", anchor_date.isoformat(), raw_text, 1, "processed", f"Analysis of report for {record['name']} with diagnosis {record['primary_diagnosis']}."),
        )
        buffer.add(
            "document_chunks",
            "INSERT INTO document_chunks (document_id, patient_id, chunk_index, chunk_text, source_page) VALUES (?, ?, ?, ?, ?)",
            (doc_id, patient_id, 0, raw_text.replace("\n", " "), 1),
        )
        buffer.add(
            "qa_memory",
            "INSERT INTO qa_memory (patient_id, question, answer_summary, sql_query, created_at, memory_type) VALUES (?, ?, ?, ?, ?, ?)",
            (patient_id, "What is the primary diagnosis?", f"The patient {record['name']} has a primary diagnosis of {record['primary_diagnosis']}.", f"SELECT primary_diagnosis FROM patients_core WHERE patient_id = '{patient_id}';", anchor_date.isoformat(), "qa"),
        )

        if index % PATIENT_BATCH == 0:
            buffer.flush()
            conn.commit()

    buffer.flush()
    conn.commit()
    row_counts.update(buffer.counts)
    return row_counts


def seed_database_from_template(conn: sqlite3.Connection, template_path: Path) -> dict[str, int]:
    """Insert cohort rows from a user-defined template JSON."""
    with open(template_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Database template must be a JSON object mapping table names to lists of rows.")

    row_counts = {}
    for table_name, rows in data.items():
        if table_name.startswith("_"):
            continue
        if not rows:
            row_counts[table_name] = 0
            continue

        valid_rows = [r for r in rows if isinstance(r, dict)]
        if not valid_rows:
            row_counts[table_name] = 0
            continue

        keys = [k for k in valid_rows[0].keys() if not k.startswith("_")]
        columns_str = ", ".join(keys)
        placeholders = ", ".join(["?"] * len(keys))
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        values = []
        for row in valid_rows:
            row_values = []
            for k in keys:
                val = row[k]
                if k in ("extended_data", "details") and (isinstance(val, dict) or isinstance(val, list)):
                    val = json.dumps(val)
                row_values.append(val)
            values.append(tuple(row_values))

        conn.executemany(sql, values)
        row_counts[table_name] = len(valid_rows)

    conn.commit()
    return row_counts


def _fetch(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    """Execute read-only SQL and return dictionaries."""

    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def _plotly_spec(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a Plotly-compatible spec with explicit categorical colors.

    Results exposing two or more numeric columns emit a heatmap matrix with a
    color scale so multi-metric comparisons (e.g. BMI vs blood pressure by
    risk level) are visually differentiated; single-metric results emit a bar
    chart with one palette color per category.
    """

    if not rows:
        return {"data": [], "layout": {"title": title}}
    first, second = _chart_columns(rows)
    numeric_keys = [key for key in rows[0] if key != first and all(_is_number(row.get(key)) for row in rows)]
    if len(numeric_keys) >= 2:
        return {
            "data": [{
                "type": "heatmap",
                "x": numeric_keys,
                "y": [str(row[first]) for row in rows],
                "z": [[float(row[key]) for key in numeric_keys] for row in rows],
                "colorscale": "Blues",
                "showscale": True,
            }],
            "layout": {"title": title, "xaxis": {"title": "metric"}, "yaxis": {"title": first}},
        }
    return {
        "data": [{
            "type": "bar",
            "x": [row[first] for row in rows],
            "y": [row[second] for row in rows],
            "marker": {"color": [CHART_PALETTE[index % len(CHART_PALETTE)] for index in range(len(rows))]},
        }],
        "layout": {"title": title, "xaxis": {"title": first}, "yaxis": {"title": second}},
    }


def _chart_columns(rows: list[dict[str, Any]]) -> tuple[str, str]:
    """Pick a categorical x column and numeric y column from a query result."""

    keys = list(rows[0])
    numeric = next((key for key in keys[1:] if all(_is_number(row.get(key)) for row in rows)), keys[-1])
    category = next((key for key in keys if key != numeric), keys[0])
    return category, numeric


def _is_number(value: Any) -> bool:
    """Return whether value can be plotted as a number."""

    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _textual_insight(question: str, rows: list[dict[str, Any]]) -> str:
    """Create a compact narrative answer alongside SQL and chart specs."""

    if not rows:
        return f"{question} No matching rows were returned for this synthetic cohort."
    first = rows[0]
    keys = list(first)
    if len(keys) < 2:
        return f"{question} Returned {len(rows)} rows for clinician review."
    label = first[keys[0]]
    value = first[keys[1]]
    return f"{question} Top segment is {label} with {value}; review table rows and chart before using this as demo evidence."


def _showcase_queries(anchor_date: date) -> list[dict[str, str]]:
    """Return the natural-language question and SQL library for the cohort.

    The library intentionally mixes population health, medication safety,
    preventive care, operations, and governance questions a clinical team
    could not answer without a purpose-built database over its own records.
    """

    inr_window = (anchor_date - timedelta(days=180)).isoformat()
    return [
        {
            "question": "Count patients by risk level.",
            "sql": "SELECT risk_level, COUNT(*) AS patient_count FROM patients_core GROUP BY risk_level ORDER BY patient_count DESC",
        },
        {
            "question": "Which diabetic patients have an HbA1c above 9 percent?",
            "sql": "SELECT p.patient_id, p.name, MAX(CAST(l.value AS REAL)) AS latest_hba1c, p.assigned_clinician FROM lab_results l JOIN patients_core p USING (patient_id) WHERE l.component = 'HbA1c' AND CAST(l.value AS REAL) > 9.0 AND EXISTS (SELECT 1 FROM patient_conditions c WHERE c.patient_id = p.patient_id AND c.condition_name LIKE '%diabetes%') GROUP BY p.patient_id ORDER BY latest_hba1c DESC LIMIT 15",
        },
        {
            "question": "Which anticoagulated patients have no recent INR result?",
            "sql": f"SELECT p.patient_id, p.name, p.age, p.risk_level FROM patients_core p JOIN medications m USING (patient_id) WHERE m.status = 'active' AND (m.medication_class LIKE '%anticoagulant%' OR m.medication_class = 'Vitamin K antagonist') AND NOT EXISTS (SELECT 1 FROM lab_results l WHERE l.patient_id = p.patient_id AND l.component = 'INR' AND l.result_date >= '{inr_window}') GROUP BY p.patient_id ORDER BY p.age DESC LIMIT 15",
        },
        {
            "question": "Which patients aged 65 and older are missing pneumococcal vaccination?",
            "sql": "SELECT p.patient_id, p.name, p.age, p.assigned_clinician FROM patients_core p WHERE p.age >= 65 AND NOT EXISTS (SELECT 1 FROM immunizations i WHERE i.patient_id = p.patient_id AND i.vaccine_abbreviation IN ('PPSV23', 'PCV13')) ORDER BY p.age DESC LIMIT 20",
        },
        {
            "question": "Which patients are on 8 or more active medications?",
            "sql": "SELECT p.patient_id, p.name, COUNT(*) AS active_medications, p.age, p.risk_level FROM medications m JOIN patients_core p USING (patient_id) WHERE m.status = 'active' GROUP BY p.patient_id HAVING COUNT(*) >= 8 ORDER BY active_medications DESC LIMIT 15",
        },
        {
            "question": "Compare uncontrolled hypertension rates by care archetype.",
            "sql": "SELECT p.care_archetype, ROUND(AVG(v.systolic_bp), 1) AS avg_systolic_bp, ROUND(100.0 * SUM(CASE WHEN v.systolic_bp >= 140 THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_readings_over_140 FROM vital_signs v JOIN patients_core p USING (patient_id) GROUP BY p.care_archetype ORDER BY pct_readings_over_140 DESC",
        },
        {
            "question": "How does appointment no-show rate vary with housing stability?",
            "sql": "SELECT s.housing_status, COUNT(*) AS past_appointments, ROUND(100.0 * SUM(CASE WHEN a.status = 'No-Show' THEN 1 ELSE 0 END) / COUNT(*), 1) AS no_show_pct FROM appointments a JOIN social_determinants s USING (patient_id) WHERE a.status IN ('Completed', 'Cancelled', 'No-Show', 'Rescheduled') GROUP BY s.housing_status ORDER BY no_show_pct DESC",
        },
        {
            "question": "Which payers cover the most high-risk patients with open care gaps?",
            "sql": "SELECT i.coverage_type, COUNT(DISTINCT p.patient_id) AS high_risk_patients_with_gaps FROM insurance_policies i JOIN patients_core p USING (patient_id) JOIN care_gaps g ON g.patient_id = p.patient_id AND g.status = 'open' WHERE p.risk_level = 'high' AND i.is_primary = 1 GROUP BY i.coverage_type ORDER BY high_risk_patients_with_gaps DESC",
        },
        {
            "question": "Which medication classes have the lowest adherence scores?",
            "sql": "SELECT medication_class, ROUND(AVG(adherence_score), 2) AS avg_adherence, COUNT(*) AS medication_count FROM medications WHERE status = 'active' GROUP BY medication_class HAVING COUNT(*) >= 5 ORDER BY avg_adherence ASC LIMIT 10",
        },
        {
            "question": "Which comorbidity categories are most common among high-risk patients?",
            "sql": "SELECT pc.category, COUNT(*) AS condition_count FROM patient_conditions pc JOIN patients_core p USING (patient_id) WHERE p.risk_level = 'high' AND pc.is_primary = 0 GROUP BY pc.category ORDER BY condition_count DESC",
        },
        {
            "question": "Compare average BMI and blood pressure by risk level.",
            "sql": "SELECT p.risk_level, ROUND(AVG(p.bmi), 1) AS avg_bmi, ROUND(AVG(v.systolic_bp), 1) AS avg_systolic_bp FROM vital_signs v JOIN patients_core p USING (patient_id) GROUP BY p.risk_level ORDER BY avg_systolic_bp DESC",
        },
        {
            "question": "Which lab components are most often abnormal?",
            "sql": "SELECT component, COUNT(*) AS abnormal_results FROM lab_results WHERE flag != 'normal' GROUP BY component ORDER BY abnormal_results DESC LIMIT 12",
        },
        {
            "question": "Show open care gaps by priority and owner.",
            "sql": "SELECT priority, owner, COUNT(*) AS open_gap_count FROM care_gaps WHERE status IN ('open', 'scheduled', 'deferred') GROUP BY priority, owner ORDER BY open_gap_count DESC LIMIT 12",
        },
        {
            "question": "How does evidence completeness vary by language?",
            "sql": "SELECT preferred_language, ROUND(AVG(data_completeness_score), 2) AS avg_completeness, COUNT(*) AS patient_count FROM patients_core GROUP BY preferred_language ORDER BY avg_completeness ASC",
        },
        {
            "question": "How is the cohort split between synthetic PII and de-identified records?",
            "sql": "SELECT privacy_class, consent_status, COUNT(*) AS patient_count FROM patients_core GROUP BY privacy_class, consent_status ORDER BY patient_count DESC",
        },
        {
            "question": "Which clinicians have the most pending reviews?",
            "sql": "SELECT assigned_clinician, COUNT(*) AS pending_reviews FROM patients_core WHERE ai_review_status = 'needs_review' GROUP BY assigned_clinician ORDER BY pending_reviews DESC LIMIT 10",
        },
        {
            "question": "Show average extraction confidence by imaging modality.",
            "sql": "SELECT i.modality, ROUND(AVG(s.extraction_confidence), 3) AS avg_confidence FROM imaging_studies i JOIN sessions s ON s.session_id = i.session_id GROUP BY i.modality ORDER BY avg_confidence DESC",
        },
        {
            "question": "Show high-risk extraction sessions by year.",
            "sql": "SELECT strftime('%Y', session_date) AS session_year, COUNT(*) AS high_risk_sessions FROM sessions JOIN patients_core USING (patient_id) WHERE risk_level = 'high' GROUP BY session_year ORDER BY session_year",
        },
        {
            "question": "How many agent audit events exist by pipeline?",
            "sql": "SELECT agent_name, COUNT(*) AS event_count FROM audit_log GROUP BY agent_name ORDER BY event_count DESC",
        },
    ]


def write_query_showcase(conn: sqlite3.Connection, output: Path, anchor_date: date = DEFAULT_ANCHOR_DATE) -> list[dict[str, Any]]:
    """Write example questions, SQL, Plotly specs, and Matplotlib charts."""

    chart_dir = output / "charts"
    chart_dir.mkdir(exist_ok=True)
    queries = _showcase_queries(anchor_date)
    specs = []
    for index, item in enumerate(queries, 1):
        try:
            rows = _fetch(conn, item["sql"])
        except Exception:
            rows = []
        chart_path = chart_dir / f"query_{index:02d}.png"
        if rows:
            first, second = _chart_columns(rows)
            try:
                plt.figure(figsize=(8, 4))
                plt.bar([str(row[first])[:24] for row in rows], [float(row[second]) for row in rows], color=[CHART_PALETTE[position % len(CHART_PALETTE)] for position in range(len(rows))])
                plt.xticks(rotation=25, ha="right")
                plt.ylabel(second.replace("_", " "))
                plt.grid(axis="y", alpha=0.3)
                plt.title(item["question"])
                plt.tight_layout()
                plt.savefig(chart_path, dpi=150, bbox_inches="tight")
                plt.close()
            except (TypeError, ValueError):
                plt.close()
        specs.append({**item, "insight": _textual_insight(item["question"], rows), "rows": rows[:25], "row_count": len(rows), "plotly": _plotly_spec(item["question"], rows), "matplotlib_png": str(chart_path)})
    (output / "query_showcase.json").write_text(json.dumps(specs, indent=2), encoding="utf-8")
    return specs


def _cohort_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    """Derive dashboard metrics from the generated cohort itself."""

    risk_counts = {
        str(row["risk_level"]): int(row["count"])
        for row in _fetch(conn, "SELECT risk_level, COUNT(*) AS count FROM patients_core GROUP BY risk_level")
    }
    pending = _fetch(conn, "SELECT COUNT(*) AS count FROM patients_core WHERE ai_review_status = 'needs_review'")[0]["count"]
    completeness = _fetch(conn, "SELECT ROUND(AVG(data_completeness_score), 2) AS avg_completeness FROM patients_core")[0]["avg_completeness"]
    return {
        "riskCounts": risk_counts,
        "pendingReview": int(pending or 0),
        "completeness": round(float(completeness or 0) * 100),
    }


def _app_contract(row_counts: dict[str, int], specs: list[dict[str, Any]], demo_platform: str, anchor_date: date, cohort_stats: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create dashboard, storage, and monitoring seed data from generated rows."""

    cohort_stats = cohort_stats or {}
    risk_counts = cohort_stats.get("riskCounts", {})
    patients = row_counts.get("patients_core", 0)
    sessions = row_counts.get("sessions", 0)
    documents = row_counts.get("documents", 0)
    persisted = row_counts.get("extracted_fields", 0)
    audits = row_counts.get("audit_log", 0)
    pending_review = int(cohort_stats.get("pendingReview", round(patients * 0.32)))
    agent_runs = max(12, round((sessions + len(specs) * 8) / 90))
    return {
        "demoPlatform": demo_platform,
        "dashboardSeed": {
            "patients": patients,
            "sessions": sessions,
            "highRiskEstimate": int(risk_counts.get("high", round(patients * 0.18))),
            "pendingReviewEstimate": pending_review,
            "pendingVerifications": pending_review,
            "storedAssets": documents,
            "agentRuns24h": agent_runs,
            "auditEvents": audits,
            "databaseRows": sum(row_counts.values()),
            "queryExamples": len(specs),
            "openAiAlerts": pending_review,
            "failedExtractions": 0,
            "completeness": int(cohort_stats.get("completeness", 90)),
            "syncRate": 100,
            "anchorDate": anchor_date.isoformat(),
        },
        "storageSeed": {
            "cloudObjects": documents,
            "jsonDocuments": persisted,
            "relationalRows": sum(row_counts.values()),
            "vectorRecords": row_counts.get("clinical_notes", 0) + row_counts.get("document_chunks", 0),
            "auditEvents": audits,
            "failedRecords": 0,
        },
        "agentMonitoringSeed": [
            {"pipeline": "database", "agent": "schema_discovery_agent", "runs": len(specs), "avgConfidence": 0.94, "failureRate": 0.0, "reviewRate": 0.0, "avgDurationMs": 510},
            {"pipeline": "database", "agent": "nl_to_sql_agent", "runs": len(specs), "avgConfidence": 0.91, "failureRate": 0.0, "reviewRate": 0.0, "avgDurationMs": 920},
            {"pipeline": "database", "agent": "sql_validator_agent", "runs": len(specs), "avgConfidence": 0.97, "failureRate": 0.0, "reviewRate": 0.0, "avgDurationMs": 340},
            {"pipeline": "database", "agent": "query_executor_agent", "runs": len(specs), "avgConfidence": 0.96, "failureRate": 0.0, "reviewRate": 0.0, "avgDurationMs": 680},
            {"pipeline": "database", "agent": "insight_chart_agent", "runs": len(specs), "avgConfidence": 0.93, "failureRate": 0.0, "reviewRate": 0.0, "avgDurationMs": 1210},
        ],
        "queryCards": [
            {"question": item["question"], "sql": item["sql"], "rowCount": item["row_count"], "chart": item["matplotlib_png"]}
            for item in specs
        ],
    }


def generate(db_path: Path, output: Path, patient_count: int, seed: int, replace: bool, years: int = DEFAULT_YEARS, anchor_date: date = DEFAULT_ANCHOR_DATE, template_path: Path | None = None, demo_platform: str = "primary", patient_prefix: str = "PT-D") -> dict[str, Any]:
    """Create database and artifacts."""

    output.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        if not replace:
            raise FileExistsError(f"{db_path} already exists. Pass --replace to recreate it.")
        try:
            db_path.unlink()
        except PermissionError as exc:
            raise SystemExit(
                f"Cannot replace {db_path}: another process is holding it open "
                f"(usually the clinical app backend). Stop the running uvicorn "
                f"server, then re-run this script. ({exc})"
            ) from exc
        for suffix in ("-shm", "-wal"):
            sidecar = db_path.with_name(db_path.name + suffix)
            if sidecar.exists():
                sidecar.unlink()

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=OFF")
        conn.execute("PRAGMA synchronous=OFF")
        create_schema(conn)
        if template_path:
            row_counts = seed_database_from_template(conn, template_path)
        else:
            row_counts = seed_database(conn, patient_count, seed, anchor_date, years, patient_prefix, demo_platform)
        specs = write_query_showcase(conn, output, anchor_date)
        cohort_stats = _cohort_stats(conn)

    app_contract = _app_contract(row_counts, specs, demo_platform, anchor_date, cohort_stats)
    manifest = {
        "module": "database_intelligence",
        "demo_platform": demo_platform,
        "db_path": str(db_path),
        "total_rows": sum(row_counts.values()),
        "row_counts": row_counts,
        "clinical_model": "archetype_coherent_v2",
        "minimum_required_patients": 1500,
        "minimum_required_rows": 150000,
        "coverage_years": years,
        "date_range": {
            "start": (anchor_date - timedelta(days=max(365, years * 365))).isoformat(),
            "end": anchor_date.isoformat(),
        },
        "query_count": len(specs),
        "backend_contract": {
            "preview": "/api/runs/database/preview",
            "execute": "/api/runs/database/{run_id}/execute",
            "export": "/api/database/queries/{run_id}/csv",
        },
        "frontend_contract": app_contract,
    }
    (output / "app_manifest.json").write_text(json.dumps(app_contract, indent=2), encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Generate large clinical SQLite showcase data.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB)
    parser.add_argument("--patient-count", type=int, default=DEFAULT_PATIENT_COUNT)
    parser.add_argument("--years", type=int, default=DEFAULT_YEARS)
    parser.add_argument("--anchor-date", type=date.fromisoformat, default=DEFAULT_ANCHOR_DATE)
    parser.add_argument("--seed", type=int, default=240624)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--demo-platform", default="primary")
    parser.add_argument("--patient-prefix", default="PT-D")
    args = parser.parse_args()
    manifest = generate(args.db_path, args.output, args.patient_count, args.seed, args.replace, args.years, args.anchor_date, args.template, args.demo_platform, args.patient_prefix)
    print(json.dumps({"db_path": manifest["db_path"], "total_rows": manifest["total_rows"], "patients": manifest["row_counts"].get("patients_core", 0), "queries": manifest["query_count"]}, indent=2))


if __name__ == "__main__":
    main()
