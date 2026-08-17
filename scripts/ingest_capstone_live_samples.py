"""Ingest the corrected multi-patient live sample dataset into the real Capstone tenant database.

Reads the ready-made relational SQLite export (providers, patients, diagnoses,
medications, lab_results, vital_signs, procedures, clinical_notes,
live_sample_manifest) and maps it onto the production schema in
capstone_agent/clinical_schemas.py so the DB Intelligence pipeline can query
it live against capstone.db (the real "Capstone" tenant), exactly like any
other relational data that tenant persists.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from capstone_agent import database as capstone_db


def _severity_to_risk_level(severity: str | None) -> str:
    """Map a primary diagnosis severity to the patients_core risk_level enum."""
    return {"Severe": "high", "Moderate": "needs_review", "Mild": "stable"}.get(
        severity or "", "needs_review"
    )


def _normalize_flag(abnormal_flag: str | None) -> str:
    """Map the source's short lab flag codes to this system's documented
    lab_results.flag convention (see clinical_schemas.SCHEMA_DDL comment and
    the original mock_data.py seed rows: 'normal'/'low'/'high'/
    'critical_low'/'critical_high', not the raw H/HH/L/LL codes) — the
    NL-to-SQL agent reasons from that documented convention, so storing raw
    codes here would silently break every flag-based query.
    """
    return {"H": "high", "HH": "critical_high", "L": "low", "LL": "critical_low"}.get(
        abnormal_flag or "", "normal"
    )


def _care_archetype(sample_theme: str) -> str:
    return {
        "Cardiovascular Medicine": "cardiometabolic",
        "Pulmonology and Sleep Medicine": "pulmonary_sleep",
        "Rheumatology and Immunology": "rheumatology_immunology",
    }.get(sample_theme, "general")


def ingest(source_sqlite: Path, db_path: Path, uploads_dir: Path) -> dict[str, int]:
    """Load the live sample dataset into db_path, scoped via tenant_storage.

    Returns a dict of table -> rows inserted, for a final ingestion summary.
    """
    src = sqlite3.connect(str(source_sqlite))
    src.row_factory = sqlite3.Row

    providers = [dict(r) for r in src.execute("SELECT * FROM providers")]
    patients = [dict(r) for r in src.execute("SELECT * FROM patients")]
    diagnoses = [dict(r) for r in src.execute("SELECT * FROM diagnoses")]
    medications = [dict(r) for r in src.execute("SELECT * FROM medications")]
    lab_results = [dict(r) for r in src.execute("SELECT * FROM lab_results")]
    vital_signs = [dict(r) for r in src.execute("SELECT * FROM vital_signs")]
    procedures = [dict(r) for r in src.execute("SELECT * FROM procedures")]
    clinical_notes = [dict(r) for r in src.execute("SELECT * FROM clinical_notes")]
    manifest = [dict(r) for r in src.execute("SELECT * FROM live_sample_manifest")]
    src.close()

    provider_by_id = {p["provider_id"]: p for p in providers}
    theme_by_patient = {m["patient_id"]: m["sample_theme"] for m in manifest}
    pdf_by_patient = {m["patient_id"]: m["pdf_filename"] for m in manifest}
    diagnoses_by_patient: dict[int, list[dict]] = {}
    for d in diagnoses:
        diagnoses_by_patient.setdefault(d["patient_id"], []).append(d)
    notes_by_patient: dict[int, list[str]] = {}
    for n in clinical_notes:
        notes_by_patient.setdefault(n["patient_id"], []).append(n["note_date"])
    labs_by_patient: dict[int, list[str]] = {}
    for lr in lab_results:
        labs_by_patient.setdefault(lr["patient_id"], []).append(lr["resulted_date"])
    vitals_by_patient: dict[int, list[str]] = {}
    for v in vital_signs:
        vitals_by_patient.setdefault(v["patient_id"], []).append(v["recorded_at"])

    def provider_name(provider_id: int) -> str:
        p = provider_by_id.get(provider_id)
        if not p:
            return ""
        return f"Dr. {p['first_name']} {p['last_name']}"

    counts = {
        "providers": 0,
        "patients_core": 0,
        "patient_conditions": 0,
        "medications": 0,
        "lab_results": 0,
        "lab_panels": 0,
        "vital_signs": 0,
        "procedures": 0,
        "clinical_notes": 0,
    }

    with capstone_db.tenant_storage(db_path, uploads_dir):
        capstone_db.init_db(seed=False)
        with capstone_db.get_connection() as conn:
            for p in providers:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO providers (
                        provider_id, first_name, last_name, full_name, title,
                        specialty, department, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        p["provider_id"],
                        p["first_name"],
                        p["last_name"],
                        f"Dr. {p['first_name']} {p['last_name']}",
                        p["title"],
                        p["department"],
                        p["department"],
                    ),
                )
                counts["providers"] += 1

            for pt in patients:
                pid = str(pt["patient_id"])
                primary = next(
                    (
                        d
                        for d in diagnoses_by_patient.get(pt["patient_id"], [])
                        if d["is_primary"]
                    ),
                    None,
                )
                last_session = max(
                    notes_by_patient.get(pt["patient_id"], [])
                    + labs_by_patient.get(pt["patient_id"], [])
                    + [v[:10] for v in vitals_by_patient.get(pt["patient_id"], [])],
                    default=None,
                )
                theme = theme_by_patient.get(pt["patient_id"], "")
                extended = {
                    "demographics": {
                        "city": pt["city"],
                        "state": pt["state"],
                        "date_of_birth": pt["date_of_birth"],
                    },
                    "source_pdf": pdf_by_patient.get(pt["patient_id"], ""),
                    "sample_theme": theme,
                }
                name = " ".join(
                    part
                    for part in (pt["first_name"], pt["middle_name"], pt["last_name"])
                    if part
                )
                conn.execute(
                    """
                    INSERT OR REPLACE INTO patients_core (
                        patient_id, name, age, sex, birth_date, zip3, risk_level,
                        primary_diagnosis, assigned_clinician, last_session_date,
                        data_completeness_score, open_tasks, ai_review_status,
                        extended_data, smoking_status, alcohol_use, bmi,
                        care_archetype, privacy_class, consent_status,
                        record_quality, primary_provider_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pid,
                        name,
                        pt["age_computed"],
                        pt["gender"],
                        pt["date_of_birth"],
                        None,
                        _severity_to_risk_level(
                            primary["severity"] if primary else None
                        ),
                        primary["diagnosis_name"] if primary else "",
                        provider_name(pt["provider_id"]),
                        last_session,
                        1.0,
                        sum(
                            1
                            for lr in lab_results
                            if lr["patient_id"] == pt["patient_id"]
                            and lr["is_abnormal"]
                        ),
                        "verified",
                        json.dumps(extended),
                        pt["smoking_status"],
                        pt["alcohol_use"],
                        pt["bmi_computed"],
                        _care_archetype(theme),
                        "DEIDENTIFIED",
                        "full",
                        "high",
                        pt["provider_id"],
                    ),
                )
                counts["patients_core"] += 1

            for d in diagnoses:
                pid = str(d["patient_id"])
                patient = next(
                    p for p in patients if p["patient_id"] == d["patient_id"]
                )
                conn.execute(
                    """
                    INSERT INTO patient_conditions (
                        patient_id, diagnosis_code, condition_name, category,
                        onset_date, status, severity, is_primary,
                        diagnosing_provider, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pid,
                        d["icd_code"],
                        d["diagnosis_name"],
                        theme_by_patient.get(d["patient_id"], ""),
                        d["diagnosis_date"],
                        d["status"],
                        d["severity"],
                        bool(d["is_primary"]),
                        provider_name(patient["provider_id"]),
                        d["notes"],
                    ),
                )
                counts["patient_conditions"] += 1

            for m in medications:
                pid = str(m["patient_id"])
                patient = next(
                    p for p in patients if p["patient_id"] == m["patient_id"]
                )
                conn.execute(
                    """
                    INSERT INTO medications (
                        patient_id, medication_name, dose, route, frequency,
                        start_date, status, generic_name, brand_name, indication,
                        prescribing_provider, refills_remaining, pharmacy_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pid,
                        m["drug_name"],
                        f"{m['dosage_amount']} {m['dosage_unit']}",
                        m["route"],
                        m["frequency"],
                        m["start_date"],
                        "active" if m["is_active"] else "stopped",
                        m["generic_name"],
                        m["brand_name"],
                        m["indication"],
                        provider_name(patient["provider_id"]),
                        m["refills_remaining"],
                        m["pharmacy_name"],
                    ),
                )
                counts["medications"] += 1

            panel_ids: dict[tuple, int] = {}
            for lr in lab_results:
                pid = str(lr["patient_id"])
                panel_key = (lr["patient_id"], lr["panel_name"], lr["resulted_date"])
                if panel_key not in panel_ids:
                    cur = conn.execute(
                        """
                        INSERT INTO lab_panels (
                            patient_id, panel_name, ordered_date, collected_date,
                            resulted_date, status
                        ) VALUES (?, ?, ?, ?, ?, 'Final')
                        """,
                        (
                            pid,
                            lr["panel_name"],
                            lr["resulted_date"],
                            lr["resulted_date"],
                            lr["resulted_date"],
                        ),
                    )
                    panel_ids[panel_key] = cur.lastrowid
                    counts["lab_panels"] += 1
                conn.execute(
                    """
                    INSERT INTO lab_results (
                        patient_id, result_date, test_name, component, value, unit,
                        reference_range, flag, panel_id, reference_low,
                        reference_high, is_abnormal, result_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        # component mirrors test_name: this dataset has no separate
                        # panel-vs-analyte distinction, so both columns must resolve
                        # the same lab test regardless of which one a query picks.
                        pid,
                        lr["resulted_date"],
                        lr["test_name"],
                        lr["test_name"],
                        str(lr["result_value"]),
                        lr["result_unit"],
                        f"{lr['reference_range_low']}-{lr['reference_range_high']}",
                        _normalize_flag(lr["abnormal_flag"]),
                        panel_ids[panel_key],
                        lr["reference_range_low"],
                        lr["reference_range_high"],
                        bool(lr["is_abnormal"]),
                        lr["result_status"],
                    ),
                )
                counts["lab_results"] += 1

            for v in vital_signs:
                pid = str(v["patient_id"])
                height_m = (v["height_cm"] or 0) / 100
                bmi = (
                    round(v["weight_kg"] / (height_m**2), 1)
                    if v["weight_kg"] and height_m
                    else None
                )
                conn.execute(
                    """
                    INSERT INTO vital_signs (
                        encounter_id, patient_id, measured_at, systolic_bp,
                        diastolic_bp, heart_rate, respiratory_rate,
                        oxygen_saturation, temperature_c, weight_kg, bmi,
                        pain_score, blood_glucose_mgdl
                    ) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pid,
                        v["recorded_at"],
                        v["systolic_bp"],
                        v["diastolic_bp"],
                        v["heart_rate"],
                        v["respiratory_rate"],
                        v["spo2_percent"],
                        v["temperature_celsius"],
                        v["weight_kg"],
                        bmi,
                        v["pain_score"],
                        v["blood_glucose_mgdl"],
                    ),
                )
                counts["vital_signs"] += 1

            for pr in procedures:
                pid = str(pr["patient_id"])
                patient = next(
                    p for p in patients if p["patient_id"] == pr["patient_id"]
                )
                conn.execute(
                    """
                    INSERT INTO procedures (
                        patient_id, procedure_date, procedure_name, procedure_code,
                        outcome, performer, facility_name, indication, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pid,
                        pr["procedure_date"],
                        pr["procedure_name"],
                        pr["cpt_code"],
                        pr["outcome"],
                        provider_name(patient["provider_id"]),
                        pr["facility_name"],
                        pr["indication"],
                        pr["status"],
                    ),
                )
                counts["procedures"] += 1

            for n in clinical_notes:
                pid = str(n["patient_id"])
                patient = next(
                    p for p in patients if p["patient_id"] == n["patient_id"]
                )
                note_id = f"NOTE-{pid}-{n['note_date']}"
                conn.execute(
                    """
                    INSERT OR IGNORE INTO clinical_notes (
                        note_id, patient_id, note_date, author, note_type, note_text
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        note_id,
                        pid,
                        n["note_date"],
                        provider_name(patient["provider_id"]),
                        n["note_type"],
                        n["note_text"],
                    ),
                )
                counts["clinical_notes"] += 1

            conn.commit()

    return counts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest the live sample dataset into the real Capstone tenant DB."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            r"C:\Users\User\Downloads\New folder\live_samples_relational_seed.sqlite"
        ),
    )
    parser.add_argument("--db-path", type=Path, default=PROJECT_ROOT / "capstone.db")
    parser.add_argument(
        "--uploads-dir", type=Path, default=PROJECT_ROOT / "uploads_capstone"
    )
    args = parser.parse_args()

    print(f"Ingesting {args.source} into {args.db_path} (real Capstone tenant)...")
    counts = ingest(args.source, args.db_path, args.uploads_dir)
    for table, count in counts.items():
        print(f"  {table}: {count} rows")
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
