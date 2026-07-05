"""Generate a large governed SQLite cohort for the database agent.

The script creates the project schema, inserts at least 10,000 patient records
across the past four years by default, and emits reusable natural-language
query examples with SQL, textual insights, Plotly specs, and Matplotlib chart
images.
"""

from __future__ import annotations

import argparse
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
from capstone_agent.clinical_schemas import SCHEMA_DDL


DEFAULT_OUTPUT = Path("showcase_data/database")
DEFAULT_DB = DEFAULT_OUTPUT / "clinical_showcase.db"
DEFAULT_ANCHOR_DATE = date(2026, 7, 5)
DEFAULT_PATIENT_COUNT = 10000
DEFAULT_YEARS = 4
FIRST_NAMES = (
    "Avery",
    "Jordan",
    "Morgan",
    "Riley",
    "Casey",
    "Taylor",
    "Sofia",
    "Noah",
    "Priya",
    "Mei",
    "Lucas",
    "Amelia",
)
LAST_NAMES = (
    "Chen",
    "Garcia",
    "Okafor",
    "Rossi",
    "Nair",
    "Brooks",
    "Kim",
    "Patel",
    "Lewis",
    "Martin",
    "Silva",
    "Hassan",
)
DIAGNOSES = (
    "Metastatic NSCLC",
    "Heart failure with reduced EF",
    "Type 2 diabetes with complications",
    "Chronic kidney disease stage 4",
    "Crohn disease flare",
    "Aortic stenosis, severe",
    "Rheumatoid arthritis",
    "COPD GOLD stage II",
)
CLINICIANS = ("Dr. Sarah Miller", "Dr. Elena Park", "Dr. James Patel", "Dr. Priya Rao", "Dr. Miguel Torres")
LAB_COMPONENTS = (
    ("CBC", "Hemoglobin", "g/dL", "13.5-17.5"),
    ("CBC", "WBC", "K/uL", "4.5-11.0"),
    ("CMP", "Creatinine", "mg/dL", "0.6-1.2"),
    ("CMP", "eGFR", "mL/min", ">60"),
    ("Cardiac", "BNP", "pg/mL", "<100"),
    ("Inflammation", "CRP", "mg/L", "<5"),
)
FIELD_NAMES = (
    "primary_finding",
    "tumor_size_cm",
    "ejection_fraction_pct",
    "hba1c_pct",
    "egfr",
    "bnp",
    "crp",
    "medication_conflict",
)


def _sqlite_ddl(ddl: str) -> str:
    """Convert portable demo DDL to SQLite-compatible DDL."""

    return ddl.replace("SERIAL", "INTEGER").replace("JSONB", "TEXT")


def _value_for(component: str, rng: random.Random) -> tuple[str, str]:
    """Return synthetic lab value and abnormal flag."""

    if component == "Hemoglobin":
        value = round(rng.uniform(8.4, 15.8), 1)
        flag = "low" if value < 12 else "normal"
    elif component == "WBC":
        value = round(rng.uniform(2.0, 13.5), 1)
        flag = "low" if value < 4.5 else "high" if value > 11 else "normal"
    elif component == "Creatinine":
        value = round(rng.uniform(0.6, 3.1), 1)
        flag = "high" if value > 1.2 else "normal"
    elif component == "eGFR":
        value = round(rng.uniform(18, 96), 0)
        flag = "low" if value < 60 else "normal"
    elif component == "BNP":
        value = round(rng.uniform(40, 1400), 0)
        flag = "high" if value > 100 else "normal"
    else:
        value = round(rng.uniform(0.8, 48), 1)
        flag = "high" if value > 5 else "normal"
    return str(value), flag


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all clinical tables plus helpful read indexes."""

    for ddl in SCHEMA_DDL.values():
        conn.execute(_sqlite_ddl(ddl))
    conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_risk ON patients_core(risk_level)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_patient ON sessions(patient_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_patient_date ON clinical_notes(patient_id, note_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_labs_patient_date ON lab_results(patient_id, result_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent_name, action)")


def seed_database(conn: sqlite3.Connection, patient_count: int, seed: int, anchor_date: date, years: int) -> dict[str, int]:
    """Insert deterministic cohort rows."""

    rng = random.Random(seed)
    today = anchor_date
    lookback_days = max(365, years * 365)
    session_total = max(4, years)
    lab_points = max(4, years * 2)
    note_total = max(2, years)
    row_counts: dict[str, int] = {}

    patients = []
    for index in range(1, patient_count + 1):
        patient_id = f"PT-D{index:05d}"
        diagnosis = DIAGNOSES[index % len(DIAGNOSES)]
        risk = rng.choices(("high", "needs_review", "stable"), weights=(18, 32, 50))[0]
        open_tasks = rng.randint(1, 6) if risk != "stable" else rng.randint(0, 1)
        completeness = round(rng.uniform(0.62, 0.99), 2)
        patients.append(
            (
                patient_id,
                f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                rng.randint(21, 89),
                rng.choice(("Female", "Male")),
                risk,
                diagnosis,
                rng.choice(CLINICIANS),
                (today - timedelta(days=rng.randint(0, lookback_days))).isoformat(),
                completeness,
                open_tasks,
                "needs_review" if risk != "stable" and rng.random() < 0.75 else "verified",
                json.dumps(
                    {
                        "synthetic": True,
                        "insurance": rng.choice(("Medicare", "Aetna PPO", "BCBS", "Self-pay")),
                        "care_gap_count": open_tasks,
                        "risk_drivers": rng.sample(("labs", "imaging", "notes", "medications", "utilization"), 3),
                    }
                ),
            )
        )
    conn.executemany(
        """
        INSERT INTO patients_core (
            patient_id, name, age, sex, risk_level, primary_diagnosis,
            assigned_clinician, last_session_date, data_completeness_score,
            open_tasks, ai_review_status, extended_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        patients,
    )
    row_counts["patients_core"] = len(patients)

    sessions = []
    extracted_fields = []
    imaging = []
    notes = []
    labs = []
    audits = []
    session_index = 0
    for patient in patients:
        patient_id, name, _age, _sex, risk, diagnosis, clinician, *_rest = patient
        for offset in range(session_total):
            session_index += 1
            session_id = f"SES-D{session_index:06d}"
            spread_days = round(offset * lookback_days / max(1, session_total - 1))
            session_date = today - timedelta(days=min(lookback_days, spread_days + rng.randint(0, 24)))
            confidence = round(rng.uniform(0.68, 0.98), 2)
            verification = "pending" if confidence < 0.82 or risk != "stable" and rng.random() < 0.35 else "verified"
            sessions.append(
                (
                    session_id,
                    patient_id,
                    session_date.isoformat(),
                    rng.randint(1, 4),
                    confidence,
                    verification,
                    "synced",
                    "synced" if verification == "verified" else "pending",
                    "synced" if verification == "verified" else "pending",
                    "recorded",
                )
            )
            for field_name in rng.sample(FIELD_NAMES, 5):
                value = round(rng.uniform(0.8, 1400), 1) if field_name in {"bnp", "crp"} else rng.choice(("present", "absent", "worsening", "stable", "improved"))
                field_confidence = round(rng.uniform(0.64, 0.99), 2)
                extracted_fields.append((session_id, patient_id, field_name, str(value), field_confidence, "SYNTHETIC", field_confidence < 0.8))
            for modality in rng.sample(("CT", "MRI", "X-Ray", "Fundoscopy", "Document"), 2):
                imaging.append(
                    (
                        session_id,
                        patient_id,
                        f"gs://clinical-data/{patient_id}/{session_id}/{modality.lower()}-{offset}.png",
                        modality,
                        rng.choice(("Chest", "Abdomen", "Brain", "Eye", "Cardiac")),
                        f"{modality} evidence for {diagnosis}",
                        round(rng.uniform(0.72, 0.98), 2),
                        rng.choice(("512x512", "1024x1024", "2048x2048")),
                        rng.choice((8, 12, 16)),
                        rng.choice(("adequate", "low", "high")),
                        rng.choice(("none", "motion", "reflection", "low_contrast")),
                        modality in {"CT", "MRI", "X-Ray"},
                        rng.randint(280, 4200),
                    )
                )
            audits.extend(
                [
                    (
                        datetime.combine(session_date, datetime.min.time()).isoformat(),
                        "image_extraction_pipeline",
                        "extraction_complete",
                        patient_id,
                        session_id,
                        json.dumps({"confidence": confidence, "verification": verification}),
                        "system",
                    ),
                    (
                        datetime.combine(session_date, datetime.min.time()).isoformat(),
                        "database_intelligence_pipeline",
                        "cohort_row_indexed",
                        patient_id,
                        session_id,
                        json.dumps({"risk_level": risk}),
                        "admin",
                    ),
                ]
            )
        for note_index in range(note_total):
            spread_days = round(note_index * lookback_days / max(1, note_total - 1))
            note_date = today - timedelta(days=min(lookback_days, spread_days + rng.randint(0, 30)))
            notes.append(
                (
                    f"NOTE-D{len(notes) + 1:07d}",
                    patient_id,
                    note_date.isoformat(),
                    clinician,
                    rng.choice(("Progress Note", "Consult", "Care Plan", "Radiology Summary")),
                    f"{name} has {diagnosis}. Risk={risk}. Agent review state includes labs, imaging, medications, and care gaps.",
                    f"VEC-D{len(notes) + 1:07d}",
                )
            )
        for lab_index in range(lab_points):
            spread_days = round(lab_index * lookback_days / max(1, lab_points - 1))
            result_date = today - timedelta(days=min(lookback_days, spread_days + rng.randint(0, 18)))
            for test, component, unit, reference in LAB_COMPONENTS:
                value, flag = _value_for(component, rng)
                labs.append((patient_id, result_date.isoformat(), test, component, value, unit, reference, flag))

    conn.executemany(
        """
        INSERT INTO sessions (
            session_id, patient_id, session_date, uploaded_image_count,
            extraction_confidence, clinician_verification, json_sync_status,
            relational_sync_status, vector_sync_status, audit_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sessions,
    )
    conn.executemany(
        """
        INSERT INTO extracted_fields (
            session_id, patient_id, field_name, field_value, confidence, ontology_code, needs_review
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        extracted_fields,
    )
    conn.executemany(
        """
        INSERT INTO imaging_studies (
            session_id, patient_id, gcs_uri, modality, body_region, description,
            quality_score, resolution, bit_depth, contrast, artifacts, dicom_compliant, file_size_kb
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        imaging,
    )
    conn.executemany(
        """
        INSERT INTO clinical_notes (
            note_id, patient_id, note_date, author, note_type, note_text, vector_chunk_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        notes,
    )
    conn.executemany(
        """
        INSERT INTO lab_results (
            patient_id, result_date, test_name, component, value, unit, reference_range, flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        labs,
    )
    conn.executemany(
        """
        INSERT INTO audit_log (
            event_timestamp, agent_name, action, patient_id, session_id, details, user_role
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        audits,
    )
    conn.commit()

    row_counts.update(
        {
            "sessions": len(sessions),
            "extracted_fields": len(extracted_fields),
            "imaging_studies": len(imaging),
            "clinical_notes": len(notes),
            "lab_results": len(labs),
            "audit_log": len(audits),
        }
    )
    return row_counts


def _fetch(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    """Execute read-only SQL and return dictionaries."""

    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def _plotly_spec(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a simple Plotly-compatible bar spec."""

    if not rows:
        return {"data": [], "layout": {"title": title}}
    first, second = list(rows[0])[:2]
    return {
        "data": [{"type": "bar", "x": [row[first] for row in rows], "y": [row[second] for row in rows]}],
        "layout": {"title": title, "xaxis": {"title": first}, "yaxis": {"title": second}},
    }


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


def write_query_showcase(conn: sqlite3.Connection, output: Path) -> list[dict[str, Any]]:
    """Write example questions, SQL, Plotly specs, and Matplotlib charts."""

    chart_dir = output / "charts"
    chart_dir.mkdir(exist_ok=True)
    queries = [
        {
            "question": "Count patients by risk level.",
            "sql": "SELECT risk_level, COUNT(*) AS patient_count FROM patients_core GROUP BY risk_level ORDER BY patient_count DESC",
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
            "question": "Which lab components are most often abnormal?",
            "sql": "SELECT component, COUNT(*) AS abnormal_results FROM lab_results WHERE flag != 'normal' GROUP BY component ORDER BY abnormal_results DESC",
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
    specs = []
    for index, item in enumerate(queries, 1):
        rows = _fetch(conn, item["sql"])
        chart_path = chart_dir / f"query_{index:02d}.png"
        if rows:
            first, second = list(rows[0])[:2]
            plt.figure(figsize=(8, 4))
            plt.bar([str(row[first]) for row in rows], [float(row[second]) for row in rows])
            plt.xticks(rotation=25, ha="right")
            plt.title(item["question"])
            plt.tight_layout()
            plt.savefig(chart_path)
            plt.close()
        specs.append({**item, "insight": _textual_insight(item["question"], rows), "rows": rows[:25], "row_count": len(rows), "plotly": _plotly_spec(item["question"], rows), "matplotlib_png": str(chart_path)})
    (output / "query_showcase.json").write_text(json.dumps(specs, indent=2), encoding="utf-8")
    return specs


def generate(db_path: Path, output: Path, patient_count: int, seed: int, replace: bool, years: int = DEFAULT_YEARS, anchor_date: date = DEFAULT_ANCHOR_DATE) -> dict[str, Any]:
    """Create database and artifacts."""

    output.mkdir(parents=True, exist_ok=True)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        if not replace:
            raise FileExistsError(f"{db_path} already exists. Pass --replace to recreate it.")
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        create_schema(conn)
        row_counts = seed_database(conn, patient_count, seed, anchor_date, years)
        specs = write_query_showcase(conn, output)

    manifest = {
        "module": "database_intelligence",
        "db_path": str(db_path),
        "total_rows": sum(row_counts.values()),
        "row_counts": row_counts,
        "minimum_required_patients": 10000,
        "minimum_required_rows": 17000,
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
    }
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
    args = parser.parse_args()
    manifest = generate(args.db_path, args.output, args.patient_count, args.seed, args.replace, args.years, args.anchor_date)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
