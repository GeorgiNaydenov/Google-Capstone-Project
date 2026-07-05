"""Session-isolated mutable repository for deterministic product demos."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from collections import OrderedDict
from pathlib import Path
from time import monotonic
from threading import Lock
from typing import Any

from clinical_app.tenancy import TENANTS, TenantConfig, TenantKind
from clinical_app import system as system_module


PATIENTS = [
    {"patient_id": "PT-8829", "name": "Jonathan Doe", "age": 62, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Non-small cell lung cancer (NSCLC)", "assigned_clinician": "Dr. Sarah Chen", "last_session_date": "2026-06-15", "data_completeness_score": 0.92, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-1044", "name": "Sarah Smith", "age": 45, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Type 2 Diabetes Mellitus with complications", "assigned_clinician": "Dr. Michael Torres", "last_session_date": "2026-06-12", "data_completeness_score": 0.78, "open_tasks": 3, "ai_review_status": "needs_review"},
    {"patient_id": "PT-5510", "name": "Wei Chen", "age": 38, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Major depressive disorder, recurrent", "assigned_clinician": "Dr. Emily Nakamura", "last_session_date": "2026-06-18", "data_completeness_score": 0.95, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-9921", "name": "Maria Garcia", "age": 71, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Congestive heart failure", "assigned_clinician": "Dr. Sarah Chen", "last_session_date": "2026-06-10", "data_completeness_score": 0.65, "open_tasks": 4, "ai_review_status": "needs_review"},
]

PATIENTS += [
    {"patient_id": "PT-1029", "name": "Eleanor Kim", "age": 67, "sex": "Female", "risk_level": "high", "primary_diagnosis": "Chronic kidney disease, stage 4", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-22", "data_completeness_score": 0.88, "open_tasks": 3, "ai_review_status": "needs_review"},
    {"patient_id": "PT-3842", "name": "David Okafor", "age": 59, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Acute coronary syndrome follow-up", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-21", "data_completeness_score": 0.84, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-7714", "name": "Amelia Rossi", "age": 73, "sex": "Female", "risk_level": "high", "primary_diagnosis": "Aortic stenosis, severe", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-20", "data_completeness_score": 0.91, "open_tasks": 2, "ai_review_status": "verified"},
    {"patient_id": "PT-2388", "name": "Noah Williams", "age": 52, "sex": "Male", "risk_level": "needs_review", "primary_diagnosis": "Crohn disease with recent flare", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-19", "data_completeness_score": 0.76, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-6503", "name": "Priya Nair", "age": 41, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Systemic lupus erythematosus", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-17", "data_completeness_score": 0.81, "open_tasks": 1, "ai_review_status": "needs_review"},
    {"patient_id": "PT-4337", "name": "Lucas Martin", "age": 64, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "COPD, GOLD stage II", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-16", "data_completeness_score": 0.96, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-8195", "name": "Aisha Rahman", "age": 36, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Multiple sclerosis, relapsing-remitting", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-15", "data_completeness_score": 0.93, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-2971", "name": "Henry Brooks", "age": 70, "sex": "Male", "risk_level": "needs_review", "primary_diagnosis": "Parkinson disease", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-14", "data_completeness_score": 0.79, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-5602", "name": "Sofia Alvarez", "age": 28, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Ulcerative colitis", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-13", "data_completeness_score": 0.97, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-1448", "name": "Owen Hughes", "age": 55, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Hypertension with left ventricular hypertrophy", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-12", "data_completeness_score": 0.90, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-9064", "name": "Mei Tan", "age": 48, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Rheumatoid arthritis", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-11", "data_completeness_score": 0.94, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-3256", "name": "Samuel Reed", "age": 62, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Prostate cancer in remission", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-10", "data_completeness_score": 0.92, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-6841", "name": "Fatima Hassan", "age": 44, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Graves disease", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-09", "data_completeness_score": 0.89, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-4720", "name": "Jack Thompson", "age": 33, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Epilepsy, focal onset", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-08", "data_completeness_score": 0.95, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-7539", "name": "Isabella Costa", "age": 57, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Nonalcoholic steatohepatitis", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-07", "data_completeness_score": 0.87, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-2186", "name": "Robert Lewis", "age": 69, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Osteoarthritis, bilateral knees", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-06", "data_completeness_score": 0.98, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-5368", "name": "Grace Li", "age": 31, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Hashimoto thyroiditis", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-05", "data_completeness_score": 0.96, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-8650", "name": "Mateo Silva", "age": 46, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Obstructive sleep apnea", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-04", "data_completeness_score": 0.86, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-3492", "name": "Nora Evans", "age": 50, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Migraine with aura", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-03", "data_completeness_score": 0.93, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-6177", "name": "Adam Kowalski", "age": 39, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Psoriatic arthritis", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-02", "data_completeness_score": 0.91, "open_tasks": 0, "ai_review_status": "verified"},
]

SESSIONS = [
    {"session_id": "SES-8829-003", "patient_id": "PT-8829", "date": "2026-06-15", "uploaded_image_count": 2, "extraction_confidence": 0.87, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "primary_tumor_size", "value": "4.2cm", "confidence": 0.91}, {"field_name": "hepatic_lesion_count", "value": "3", "confidence": 0.88}]},
    {"session_id": "SES-1044-001", "patient_id": "PT-1044", "date": "2026-06-12", "uploaded_image_count": 1, "extraction_confidence": 0.72, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "retinopathy_grade", "value": "Moderate NPDR", "confidence": 0.79}]},
    {"session_id": "SES-5510-001", "patient_id": "PT-5510", "date": "2026-06-18", "uploaded_image_count": 1, "extraction_confidence": 0.94, "clinician_verification_status": "verified", "extracted_fields": [{"field_name": "phq9_score", "value": "8", "confidence": 0.96}]},
    {"session_id": "SES-9921-001", "patient_id": "PT-9921", "date": "2026-06-10", "uploaded_image_count": 1, "extraction_confidence": 0.85, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "cardiothoracic_ratio", "value": "0.62", "confidence": 0.89}]},
]

SESSIONS += [
    {"session_id": f"SES-{patient_id[3:]}-001", "patient_id": patient_id, "date": date, "uploaded_image_count": images, "extraction_confidence": confidence, "clinician_verification_status": status, "extracted_fields": []}
    for patient_id, date, images, confidence, status in (
        ("PT-1029", "2026-06-22", 2, 0.76, "pending"),
        ("PT-3842", "2026-06-21", 1, 0.82, "pending"),
        ("PT-7714", "2026-06-20", 3, 0.94, "verified"),
        ("PT-2388", "2026-06-19", 1, 0.79, "pending"),
        ("PT-6503", "2026-06-17", 2, 0.81, "pending"),
        ("PT-4337", "2026-06-16", 1, 0.96, "verified"),
        ("PT-8195", "2026-06-15", 2, 0.93, "verified"),
        ("PT-2971", "2026-06-14", 1, 0.74, "pending"),
    )
]

EVIDENCE = {
    "PT-8829": [{"source_id": "NOTE-8829-005", "source_type": "text", "date": "2026-06-15", "text": "CT shows RUL mass increased from 3.8cm to 4.2cm and three hepatic lesions, largest 3.5cm."}, {"source_id": "SES-8829-003", "source_type": "image", "date": "2026-06-15", "text": "CT abdomen shows three hepatic lesions."}],
    "PT-1044": [{"source_id": "NOTE-1044-002", "source_type": "text", "date": "2026-06-12", "text": "HbA1c is 8.2% with moderate non-proliferative diabetic retinopathy."}],
    "PT-5510": [{"source_id": "NOTE-5510-002", "source_type": "text", "date": "2026-06-18", "text": "PHQ-9 improved from 14 to 8; no suicidal ideation."}],
    "PT-9921": [{"source_id": "NOTE-9921-002", "source_type": "text", "date": "2026-06-10", "text": "CHF exacerbation with EF 35%, BNP 890, weight gain, and bilateral effusions."}],
}

RESEARCH_NOTIFICATIONS = [
    {"id": "NTF-001", "title": "Diuretic change below confidence", "detail": "PT-1029 extraction scored 76%; clinician verification required.", "severity": "critical", "agent": "Validation Agent", "read": False, "route": "/app/inbox"},
    {"id": "NTF-002", "title": "High-risk cohort increased", "detail": "Four patients crossed the high-risk threshold this week.", "severity": "info", "agent": "Database Intelligence Agent", "read": False, "route": "/app/overview"},
    {"id": "NTF-003", "title": "Re-run extraction with high resolution OCR", "detail": "PT-8829 has a prior extraction below the preferred confidence target.", "severity": "warning", "agent": "Image Quality Agent", "read": False, "route": "/app/extraction?patient=PT-8829"},
]

NORTHSTAR_PATIENTS = [
    {"patient_id": "PT-7301", "name": "Marcus Webb", "age": 58, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Hepatocellular carcinoma, BCLC stage B", "assigned_clinician": "Dr. Ingrid Falk", "last_session_date": "2026-06-14", "data_completeness_score": 0.89, "open_tasks": 3, "ai_review_status": "needs_review"},
    {"patient_id": "PT-4185", "name": "Linnea Sorensen", "age": 47, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Atrial fibrillation, paroxysmal", "assigned_clinician": "Dr. Kwame Mensah", "last_session_date": "2026-06-13", "data_completeness_score": 0.77, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-9077", "name": "Tomas Herrera", "age": 66, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Idiopathic pulmonary fibrosis", "assigned_clinician": "Dr. Ingrid Falk", "last_session_date": "2026-06-12", "data_completeness_score": 0.86, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-2560", "name": "Amara Diallo", "age": 34, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Asthma, moderate persistent", "assigned_clinician": "Dr. Yuki Sato", "last_session_date": "2026-06-11", "data_completeness_score": 0.93, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-6934", "name": "Viktor Petrov", "age": 71, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Abdominal aortic aneurysm, 5.1cm", "assigned_clinician": "Dr. Kwame Mensah", "last_session_date": "2026-06-10", "data_completeness_score": 0.82, "open_tasks": 3, "ai_review_status": "needs_review"},
    {"patient_id": "PT-3408", "name": "Hana Kobayashi", "age": 29, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Celiac disease", "assigned_clinician": "Dr. Yuki Sato", "last_session_date": "2026-06-09", "data_completeness_score": 0.95, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-8216", "name": "Declan Murphy", "age": 54, "sex": "Male", "risk_level": "needs_review", "primary_diagnosis": "Chronic hepatitis C, treatment-naive", "assigned_clinician": "Dr. Ingrid Falk", "last_session_date": "2026-06-08", "data_completeness_score": 0.74, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-5723", "name": "Rosa Mendes", "age": 62, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Osteoporosis with prior vertebral fracture", "assigned_clinician": "Dr. Kwame Mensah", "last_session_date": "2026-06-07", "data_completeness_score": 0.81, "open_tasks": 1, "ai_review_status": "needs_review"},
    {"patient_id": "PT-1892", "name": "Elias Lindqvist", "age": 43, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Ankylosing spondylitis", "assigned_clinician": "Dr. Yuki Sato", "last_session_date": "2026-06-06", "data_completeness_score": 0.90, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-7645", "name": "Chioma Okeke", "age": 51, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Iron deficiency anemia, resolved", "assigned_clinician": "Dr. Ingrid Falk", "last_session_date": "2026-06-05", "data_completeness_score": 0.88, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-4029", "name": "Bruno Costa", "age": 39, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Gout, chronic tophaceous", "assigned_clinician": "Dr. Kwame Mensah", "last_session_date": "2026-06-04", "data_completeness_score": 0.85, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-9518", "name": "Ingrid Halvorsen", "age": 76, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Mild cognitive impairment", "assigned_clinician": "Dr. Yuki Sato", "last_session_date": "2026-06-03", "data_completeness_score": 0.72, "open_tasks": 2, "ai_review_status": "needs_review"},
]

NORTHSTAR_SESSIONS = [
    {"session_id": "SES-7301-002", "patient_id": "PT-7301", "date": "2026-06-14", "uploaded_image_count": 2, "extraction_confidence": 0.84, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "lesion_count", "value": "4", "confidence": 0.86}, {"field_name": "afp_level", "value": "412 ng/mL", "confidence": 0.90}]},
    {"session_id": "SES-4185-001", "patient_id": "PT-4185", "date": "2026-06-13", "uploaded_image_count": 1, "extraction_confidence": 0.78, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "ecg_rhythm", "value": "Atrial fibrillation with rapid ventricular response", "confidence": 0.83}]},
    {"session_id": "SES-9077-001", "patient_id": "PT-9077", "date": "2026-06-12", "uploaded_image_count": 2, "extraction_confidence": 0.88, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "fvc_percent_predicted", "value": "64%", "confidence": 0.90}]},
    {"session_id": "SES-6934-001", "patient_id": "PT-6934", "date": "2026-06-10", "uploaded_image_count": 1, "extraction_confidence": 0.91, "clinician_verification_status": "verified", "extracted_fields": [{"field_name": "aneurysm_diameter", "value": "5.1cm", "confidence": 0.93}]},
    {"session_id": "SES-8216-001", "patient_id": "PT-8216", "date": "2026-06-08", "uploaded_image_count": 1, "extraction_confidence": 0.71, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "fibrosis_stage", "value": "F2", "confidence": 0.75}]},
    {"session_id": "SES-9518-001", "patient_id": "PT-9518", "date": "2026-06-03", "uploaded_image_count": 1, "extraction_confidence": 0.76, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "moca_score", "value": "23", "confidence": 0.80}]},
]

NORTHSTAR_EVIDENCE = {
    "PT-7301": [{"source_id": "NOTE-7301-004", "source_type": "text", "date": "2026-06-14", "text": "MRI liver shows four LI-RADS 5 lesions, largest 3.1cm in segment VII; AFP 412 ng/mL, up from 260."}, {"source_id": "SES-7301-002", "source_type": "image", "date": "2026-06-14", "text": "MRI abdomen with contrast shows multifocal hepatic lesions."}],
    "PT-4185": [{"source_id": "NOTE-4185-002", "source_type": "text", "date": "2026-06-13", "text": "Holter confirms paroxysmal AF burden of 11%; CHA2DS2-VASc score 3, anticoagulation started."}],
    "PT-6934": [{"source_id": "NOTE-6934-003", "source_type": "text", "date": "2026-06-10", "text": "CT angiogram shows infrarenal AAA at 5.1cm, growth of 4mm in six months; vascular surgery referral placed."}],
    "PT-9518": [{"source_id": "NOTE-9518-001", "source_type": "text", "date": "2026-06-03", "text": "MoCA score 23/30 with deficits in delayed recall; B12 and TSH normal, MRI ordered."}],
}

NORTHSTAR_NOTIFICATIONS = [
    {"id": "NTF-N01", "title": "Hepatitis staging below confidence", "detail": "PT-8216 fibrosis staging scored 71%; clinician verification required.", "severity": "critical", "agent": "Validation Agent", "read": False, "route": "/app/inbox"},
    {"id": "NTF-N02", "title": "AAA surveillance interval exceeded", "detail": "PT-6934 aneurysm grew 4mm in six months; vascular review recommended.", "severity": "warning", "agent": "Database Intelligence Agent", "read": False, "route": "/app/overview"},
    {"id": "NTF-N03", "title": "Weekly cohort export completed", "detail": "Northstar Health population export finished with 12 patient records.", "severity": "info", "agent": "Database Intelligence Agent", "read": False, "route": "/app/database"},
]


RESEARCH_USERS = [
    {"id": "USR-001", "name": "Dr. Sarah Miller", "email": "sarah.miller@research.demo", "roles": ["Admin", "Clinician", "Reviewer"], "scope": "Organization", "status": "Active"},
    {"id": "USR-002", "name": "Dr. Elena Park", "email": "elena.park@research.demo", "roles": ["Clinician"], "scope": "Assigned patients", "status": "Active"},
    {"id": "USR-003", "name": "Dr. James Patel", "email": "james.patel@research.demo", "roles": ["Clinician", "Reviewer"], "scope": "Assigned patients", "status": "Active"},
    {"id": "USR-004", "name": "Alex Morgan", "email": "alex.morgan@research.demo", "roles": ["Data Manager"], "scope": "Data platform", "status": "Active"},
    {"id": "USR-005", "name": "Jordan Ellis", "email": "jordan.ellis@research.demo", "roles": ["Read-only Viewer"], "scope": "Audit and reports", "status": "Active"},
    {"id": "USR-006", "name": "Dr. Sarah Chen", "email": "sarah.chen@research.demo", "roles": ["Clinician"], "scope": "Assigned patients", "status": "Active"},
]

NORTHSTAR_USERS = [
    {"id": "USR-101", "name": "Dr. Ingrid Falk", "email": "ingrid.falk@northstar.demo", "roles": ["Admin", "Clinician"], "scope": "Organization", "status": "Active"},
    {"id": "USR-102", "name": "Dr. Kwame Mensah", "email": "kwame.mensah@northstar.demo", "roles": ["Clinician", "Reviewer"], "scope": "Assigned patients", "status": "Active"},
    {"id": "USR-103", "name": "Dr. Yuki Sato", "email": "yuki.sato@northstar.demo", "roles": ["Clinician"], "scope": "Assigned patients", "status": "Active"},
    {"id": "USR-104", "name": "Noor Haddad", "email": "noor.haddad@northstar.demo", "roles": ["Data Manager"], "scope": "Data platform", "status": "Active"},
    {"id": "USR-105", "name": "Sam Whitaker", "email": "sam.whitaker@northstar.demo", "roles": ["Read-only Viewer"], "scope": "Audit and reports", "status": "Active"},
]

# Plausible steady-state agent statistics for demo tenants; merged with the
# session's real runs by agent_monitoring() so demo screens stay lively while
# the real tenant reports only what actually executed.
MONITOR_BASELINE = [
    {"agent": "Image Quality Agent", "pipeline": "extraction", "lastRun": "2m ago", "status": "healthy", "avgConfidence": 0.96, "failureRate": 0.008, "reviewRate": 0.12, "avgDurationMs": 800, "linkedPatients": 18},
    {"agent": "Vision Agent", "pipeline": "extraction", "lastRun": "2m ago", "status": "healthy", "avgConfidence": 0.92, "failureRate": 0.011, "reviewRate": 0.18, "avgDurationMs": 4200, "linkedPatients": 18},
    {"agent": "Evidence Retrieval Agent", "pipeline": "qa", "lastRun": "8m ago", "status": "healthy", "avgConfidence": 0.89, "failureRate": 0.004, "reviewRate": 0.06, "avgDurationMs": 1700, "linkedPatients": 24},
    {"agent": "SQL Generation Agent", "pipeline": "database", "lastRun": "12m ago", "status": "healthy", "avgConfidence": 0.94, "failureRate": 0.002, "reviewRate": 1.0, "avgDurationMs": 2100, "linkedPatients": 24},
    {"agent": "Vector Indexing Agent", "pipeline": "extraction", "lastRun": "1m ago", "status": "degraded", "avgConfidence": 0.97, "failureRate": 0.024, "reviewRate": 0.0, "avgDurationMs": 3800, "linkedPatients": 24},
]


@dataclass(frozen=True)
class DemoDataset:
    """Deterministic fixture bundle backing one demo tenant."""

    key: str
    patients: list[dict[str, Any]]
    sessions: list[dict[str, Any]]
    evidence: dict[str, list[dict[str, Any]]]
    notifications: list[dict[str, Any]]
    users: list[dict[str, Any]]
    monitor_baseline: list[dict[str, Any]]


RESEARCH_CLINIC = DemoDataset("research_clinic", PATIENTS, SESSIONS, EVIDENCE, RESEARCH_NOTIFICATIONS, RESEARCH_USERS, MONITOR_BASELINE)
NORTHSTAR = DemoDataset("northstar", NORTHSTAR_PATIENTS, NORTHSTAR_SESSIONS, NORTHSTAR_EVIDENCE, NORTHSTAR_NOTIFICATIONS, NORTHSTAR_USERS, MONITOR_BASELINE)
DATASETS = {dataset.key: dataset for dataset in (RESEARCH_CLINIC, NORTHSTAR)}

import os

# Real-tenant databases and uploads follow CLINICAL_DATA_DIR when set (e.g. a
# mounted Docker volume) so they persist across restarts; otherwise they sit
# beside the project for local development. Demo tenants keep no files.
PROJECT_ROOT = Path(os.environ["CLINICAL_DATA_DIR"]).resolve() if os.environ.get("CLINICAL_DATA_DIR") else Path(__file__).resolve().parents[1]


def now() -> str:
    """Return stable-format UTC timestamp."""

    return datetime.now(UTC).isoformat()


def derive_monitoring(runs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate per-agent statistics from the runs that actually executed.

    Each run step names the agent stage that produced it, so grouping steps
    by name yields honest per-agent rows: last run time, error and review
    ratios, and the mean confidence of the runs the agent participated in.
    """

    stats: dict[str, dict[str, Any]] = {}
    for run in runs.values():
        for step in run.get("steps", []):
            name = str(step.get("name", "")).strip()
            if not name:
                continue
            row = stats.setdefault(name, {
                "agent": name, "pipeline": run.get("workflow", ""), "steps": 0,
                "errors": 0, "reviews": 0, "confidences": [], "lastRun": "",
            })
            row["steps"] += 1
            row["errors"] += step.get("status") == "error"
            row["reviews"] += step.get("status") == "review"
            confidence = float(run.get("confidence") or 0)
            if confidence:
                row["confidences"].append(confidence)
            row["lastRun"] = max(row["lastRun"], str(step.get("timestamp", "")))
    rows = []
    for row in stats.values():
        confidences = row.pop("confidences")
        steps = row.pop("steps")
        errors = row.pop("errors")
        reviews = row.pop("reviews")
        rows.append({
            **row,
            "status": "degraded" if errors else "healthy",
            "avgConfidence": round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
            "failureRate": round(errors / steps, 3),
            "reviewRate": round(reviews / steps, 3),
            "avgDurationMs": 0,
            "linkedPatients": 0,
        })
    rows.sort(key=lambda item: item["lastRun"], reverse=True)
    return rows


class DemoRepository:
    """Mutable state belonging to exactly one browser demo session."""

    def __init__(self, dataset: DemoDataset = RESEARCH_CLINIC) -> None:
        self.session_id = ""
        self.is_demo = True
        self._dataset = dataset
        self.reset()

    def reset(self) -> None:
        """Restore deterministic seed state for this repository's dataset."""

        self.patients = {item["patient_id"]: item for item in deepcopy(self._dataset.patients)}
        self.sessions = {item["session_id"]: item for item in deepcopy(self._dataset.sessions)}
        self.evidence = deepcopy(self._dataset.evidence)
        self.source_assets: dict[str, tuple[bytes, str]] = {}
        for patient_id, evidence_rows in self.evidence.items():
            for evidence in evidence_rows:
                if evidence["source_type"] == "image":
                    asset_id = evidence["source_id"]
                    self.source_assets[asset_id] = (f"DEMO IMAGE {patient_id} {asset_id}".encode(), "image/png")
                    evidence["asset_id"] = asset_id
        self.uploads: dict[str, dict[str, Any]] = {}
        self.asset_contents: dict[str, bytes] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.query_history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.agent_config: dict[str, Any] = {
            "version": 1,
            "autoApprovalThreshold": 90,
            "reviewThreshold": 75,
            "maxConcurrentRuns": 8,
            "databaseEnabled": True,
        }
        self.notifications = [dict(item, createdAt=now()) for item in deepcopy(self._dataset.notifications)]
        self.users = deepcopy(self._dataset.users)
        self.permissions = {"roles": list(system_module.ROLES), "matrix": deepcopy(system_module.DEFAULT_PERMISSIONS), "version": 1}
        self.sequence = 0

    def identifier(self, prefix: str) -> str:
        """Create deterministic identifier within session state."""

        self.sequence += 1
        return f"{prefix}-{self.sequence:04d}"

    def log(self, action: str, actor: str, role: str, **details: Any) -> dict[str, Any]:
        """Append auditable product event."""

        event = {"audit_id": self.identifier("AUD"), "timestamp": now(), "action": action, "actor": actor, "role": role, "details": details}
        self.audit.append(event)
        return event

    def list_users(self) -> list[dict[str, Any]]:
        """Return the seeded demo user directory."""

        return self.users

    def agent_monitoring(self) -> list[dict[str, Any]]:
        """Merge the plausible demo baseline with this session's real runs."""

        derived = derive_monitoring(self.runs)
        baseline_names = {row["agent"] for row in self._dataset.monitor_baseline}
        merged = deepcopy(self._dataset.monitor_baseline)
        merged.extend(row for row in derived if row["agent"] not in baseline_names)
        return merged

    def load_permissions(self) -> dict[str, Any]:
        """Return the session-scoped permission matrix."""

        return self.permissions

    def save_permissions(self, matrix: list[dict[str, Any]], actor: str) -> dict[str, Any]:
        """Update the session-scoped permission matrix (demo tenants only)."""

        self.permissions["matrix"] = deepcopy(matrix)
        self.permissions["version"] = int(self.permissions["version"]) + 1
        return self.permissions

    def build_notifications(self) -> list[dict[str, Any]]:
        """Demo notifications are seeded; return them unchanged."""

        return self.notifications


class LiveRepository:
    """Mutable per-session view over the real clinical database plus agent runs."""

    def __init__(self, db_path: Path | None = None, uploads_root: Path | None = None) -> None:
        self.session_id = ""
        self.is_demo = False
        # None keeps the legacy clinical.db store; a real tenant passes its
        # own SQLite file so its data never mixes with the seeded demo DB.
        self.db_path = db_path
        self.uploads_root = uploads_root
        self.patients: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, list[dict[str, Any]]] = {}
        self.source_assets: dict[str, tuple[bytes, str]] = {}
        self.uploads: dict[str, dict[str, Any]] = {}
        self.asset_contents: dict[str, bytes] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.query_history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.agent_config: dict[str, Any] = {
            "version": 1,
            "autoApprovalThreshold": 90,
            "reviewThreshold": 75,
            "maxConcurrentRuns": 8,
            "databaseEnabled": True,
        }
        self.notifications: list[dict[str, Any]] = []
        self.sequence = 0
        self._hydrate_from_database()

    def _hydrate_from_database(self) -> None:
        """Load patients, sessions, and note evidence from clinical.db.

        Live sessions must reflect the persisted store so uploads validate
        against real patients, dashboards show real counts, and Q&A grounds
        answers in stored clinical notes instead of an empty registry.
        Import stays local so demo tenants never touch the agent package.
        """

        system_module.seed_users(self._governance_db())

        try:
            from capstone_agent import database
        except Exception:
            return

        if self.db_path is not None:
            with database.tenant_storage(self.db_path, self.uploads_root):
                self._load_rows(database)
        else:
            self._load_rows(database)

    def _governance_db(self) -> Path:
        """Return the SQLite file holding this tenant's users and permissions."""

        return Path(self.db_path) if self.db_path is not None else PROJECT_ROOT / "clinical.db"

    def _load_rows(self, database: Any) -> None:
        """Read patients, sessions, and notes from the active database file."""

        patients = database.execute_sql(
            "SELECT patient_id, name, age, sex, risk_level, primary_diagnosis, "
            "assigned_clinician, last_session_date, data_completeness_score, "
            "open_tasks, ai_review_status FROM patients_core"
        )
        for row in patients.get("rows", []):
            item = dict(row)
            item["data_completeness_score"] = float(item.get("data_completeness_score") or 0)
            item["open_tasks"] = int(item.get("open_tasks") or 0)
            self.patients[item["patient_id"]] = item

        sessions = database.execute_sql(
            "SELECT session_id, patient_id, session_date AS date, uploaded_image_count, "
            "extraction_confidence, clinician_verification AS clinician_verification_status "
            "FROM sessions"
        )
        for row in sessions.get("rows", []):
            item = dict(row)
            item["uploaded_image_count"] = int(item.get("uploaded_image_count") or 0)
            item["extraction_confidence"] = float(item.get("extraction_confidence") or 0)
            item.setdefault("extracted_fields", [])
            self.sessions[item["session_id"]] = item

        # Join persisted extracted fields into their sessions so SessionDetail
        # shows what the extraction pipeline actually stored, not placeholders.
        fields = database.execute_sql(
            "SELECT session_id, field_name, field_value AS value, confidence FROM extracted_fields"
        )
        for row in fields.get("rows", []):
            session = self.sessions.get(row["session_id"])
            if session is not None:
                session["extracted_fields"].append({
                    "field_name": row["field_name"],
                    "value": row["value"],
                    "confidence": float(row.get("confidence") or 0),
                })

        notes = database.execute_sql(
            "SELECT note_id, patient_id, note_date, note_text FROM clinical_notes"
        )
        for row in notes.get("rows", []):
            self.evidence.setdefault(row["patient_id"], []).append({
                "source_id": row["note_id"],
                "source_type": "text",
                "date": row["note_date"],
                "text": row["note_text"],
            })

    def reset(self) -> None:
        """Clear session data while keeping tenant storage paths."""

        self.__init__(db_path=self.db_path, uploads_root=self.uploads_root)  # type: ignore[misc]

    def identifier(self, prefix: str) -> str:
        """Create identifier within session state."""

        self.sequence += 1
        return f"{prefix}-{self.sequence:04d}"

    def log(self, action: str, actor: str, role: str, **details: Any) -> dict[str, Any]:
        """Append auditable event."""

        event = {"audit_id": self.identifier("AUD"), "timestamp": now(), "action": action, "actor": actor, "role": role, "details": details}
        self.audit.append(event)
        return event

    def add_patient(self, patient_id: str, name: str, **kwargs: Any) -> dict[str, Any]:
        """Register a patient from extraction results."""

        patient = {
            "patient_id": patient_id, "name": name,
            "age": kwargs.get("age"), "sex": kwargs.get("sex"),
            "risk_level": kwargs.get("risk_level", "needs_review"),
            "primary_diagnosis": kwargs.get("diagnosis", ""),
            "assigned_clinician": kwargs.get("clinician", ""),
            "last_session_date": now()[:10],
            "data_completeness_score": 0.0,
            "open_tasks": 1,
            "ai_review_status": "needs_review",
        }
        self.patients[patient_id] = patient
        return patient

    def list_users(self) -> list[dict[str, Any]]:
        """Return the read-only user directory persisted in the tenant DB."""

        return system_module.load_users(self._governance_db())

    def agent_monitoring(self) -> list[dict[str, Any]]:
        """Return only agents that actually ran — empty before any runs."""

        return derive_monitoring(self.runs)

    def load_permissions(self) -> dict[str, Any]:
        """Return the permission matrix persisted in the tenant DB."""

        return system_module.load_permissions(self._governance_db())

    def save_permissions(self, matrix: list[dict[str, Any]], actor: str) -> dict[str, Any]:
        """Persist an admin's permission matrix edit to the tenant DB."""

        return system_module.save_permissions(self._governance_db(), matrix, actor)

    def build_notifications(self) -> list[dict[str, Any]]:
        """Derive real-tenant notifications from actual run state.

        Runs awaiting clinician review surface as critical items and failed
        runs as warnings; nothing is invented when the session has no runs.
        """

        derived: list[dict[str, Any]] = []
        for run in self.runs.values():
            patient_id = run.get("result", {}).get("patientId", "")
            if run.get("status") == "review":
                route = "/app/inbox" if run.get("workflow") == "extraction" else "/app/database"
                derived.append({
                    "id": f"NTF-{run['id']}", "title": f"{run.get('workflow', 'run').title()} awaiting review",
                    "detail": f"Run {run['id']}{f' for {patient_id}' if patient_id else ''} needs an explicit clinician decision.",
                    "severity": "critical", "agent": run.get("agentName", "pipeline"),
                    "read": any(n["id"] == f"NTF-{run['id']}" and n.get("read") for n in self.notifications),
                    "route": route, "createdAt": run.get("createdAt", now()),
                })
            elif run.get("status") == "error":
                derived.append({
                    "id": f"NTF-{run['id']}", "title": f"{run.get('workflow', 'run').title()} run failed",
                    "detail": f"Run {run['id']} ended in an error; inspect the run steps and retry.",
                    "severity": "warning", "agent": run.get("agentName", "pipeline"),
                    "read": any(n["id"] == f"NTF-{run['id']}" and n.get("read") for n in self.notifications),
                    "route": "/app/inbox",
                    "createdAt": run.get("createdAt", now()),
                })
        self.notifications = derived
        return derived


class RepositoryRegistry:
    """Thread-safe registry of isolated repositories, tenant-aware."""

    def __init__(self, max_count: int = 100, ttl_seconds: int = 3600) -> None:
        self._items: OrderedDict[str, tuple[DemoRepository | LiveRepository, float]] = OrderedDict()
        self._lock = Lock()
        self._max_count = max_count
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _build(tenant: TenantConfig) -> DemoRepository | LiveRepository:
        """Construct the repository type a tenant's requests must see.

        Tenant kind is authoritative: real tenants get a LiveRepository over
        their own database file, demo tenants get their deterministic dataset.
        """

        if tenant.kind == TenantKind.REAL:
            return LiveRepository(
                db_path=PROJECT_ROOT / (tenant.db_filename or "clinical.db"),
                uploads_root=PROJECT_ROOT / (tenant.uploads_dirname or "uploads"),
            )
        return DemoRepository(DATASETS[tenant.dataset or "research_clinic"])

    def get(self, session_id: str, tenant: TenantConfig | None = None) -> DemoRepository | LiveRepository:
        """Return existing repository or create tenant-appropriate session state."""

        active = tenant or TENANTS["research-clinic"]
        key = f"{active.id}::{session_id}"
        with self._lock:
            current = monotonic()
            expired = [item for item, (_, touched) in self._items.items() if current - touched > self._ttl_seconds]
            for item in expired:
                self._items.pop(item, None)
            if key in self._items:
                repository, _ = self._items.pop(key)
            else:
                repository = self._build(active)
            self._items[key] = (repository, current)
            repository.session_id = session_id
            while len(self._items) > self._max_count:
                self._items.popitem(last=False)
            return repository

    def find(self, session_id: str) -> DemoRepository | LiveRepository | None:
        """Find existing session without creating state for invalid capability URLs."""

        suffix = f"::{session_id}"
        with self._lock:
            current = monotonic()
            # Most-recently-used entries sit at the end of the OrderedDict, so
            # scan in reverse to prefer the tenant the caller last touched.
            for key in reversed(self._items):
                if not key.endswith(suffix):
                    continue
                repository, touched = self._items[key]
                if current - touched > self._ttl_seconds:
                    self._items.pop(key, None)
                    return None
                return repository
            return None
