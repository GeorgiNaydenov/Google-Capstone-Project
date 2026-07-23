"""Session-isolated mutable repository for deterministic product demos."""

import json
import os
import sqlite3
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
    {
        "patient_id": "PT-8829",
        "name": "Jonathan Doe",
        "age": 62,
        "sex": "Male",
        "risk_level": "high",
        "primary_diagnosis": "Non-small cell lung cancer (NSCLC)",
        "assigned_clinician": "Dr. Sarah Chen",
        "last_session_date": "2026-06-15",
        "data_completeness_score": 0.92,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-1044",
        "name": "Sarah Smith",
        "age": 45,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Type 2 Diabetes Mellitus with complications",
        "assigned_clinician": "Dr. Michael Torres",
        "last_session_date": "2026-06-12",
        "data_completeness_score": 0.78,
        "open_tasks": 3,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-5510",
        "name": "Wei Chen",
        "age": 38,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Major depressive disorder, recurrent",
        "assigned_clinician": "Dr. Emily Nakamura",
        "last_session_date": "2026-06-18",
        "data_completeness_score": 0.95,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-9921",
        "name": "Maria Garcia",
        "age": 71,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Congestive heart failure",
        "assigned_clinician": "Dr. Sarah Chen",
        "last_session_date": "2026-06-10",
        "data_completeness_score": 0.65,
        "open_tasks": 4,
        "ai_review_status": "needs_review",
    },
]

PATIENTS += [
    {
        "patient_id": "PT-1029",
        "name": "Eleanor Kim",
        "age": 67,
        "sex": "Female",
        "risk_level": "high",
        "primary_diagnosis": "Chronic kidney disease, stage 4",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-22",
        "data_completeness_score": 0.88,
        "open_tasks": 3,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-3842",
        "name": "David Okafor",
        "age": 59,
        "sex": "Male",
        "risk_level": "high",
        "primary_diagnosis": "Acute coronary syndrome follow-up",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-21",
        "data_completeness_score": 0.84,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-7714",
        "name": "Amelia Rossi",
        "age": 73,
        "sex": "Female",
        "risk_level": "high",
        "primary_diagnosis": "Aortic stenosis, severe",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-20",
        "data_completeness_score": 0.91,
        "open_tasks": 2,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-2388",
        "name": "Noah Williams",
        "age": 52,
        "sex": "Male",
        "risk_level": "needs_review",
        "primary_diagnosis": "Crohn disease with recent flare",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-19",
        "data_completeness_score": 0.76,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-6503",
        "name": "Priya Nair",
        "age": 41,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Systemic lupus erythematosus",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-17",
        "data_completeness_score": 0.81,
        "open_tasks": 1,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-4337",
        "name": "Lucas Martin",
        "age": 64,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "COPD, GOLD stage II",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-16",
        "data_completeness_score": 0.96,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-8195",
        "name": "Aisha Rahman",
        "age": 36,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Multiple sclerosis, relapsing-remitting",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-15",
        "data_completeness_score": 0.93,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-2971",
        "name": "Henry Brooks",
        "age": 70,
        "sex": "Male",
        "risk_level": "needs_review",
        "primary_diagnosis": "Parkinson disease",
        "assigned_clinician": "Dr. James Patel",
        "last_session_date": "2026-06-14",
        "data_completeness_score": 0.79,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-5602",
        "name": "Sofia Alvarez",
        "age": 28,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Ulcerative colitis",
        "assigned_clinician": "Dr. James Patel",
        "last_session_date": "2026-06-13",
        "data_completeness_score": 0.97,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-1448",
        "name": "Owen Hughes",
        "age": 55,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Hypertension with left ventricular hypertrophy",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-12",
        "data_completeness_score": 0.90,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-9064",
        "name": "Mei Tan",
        "age": 48,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Rheumatoid arthritis",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-11",
        "data_completeness_score": 0.94,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-3256",
        "name": "Samuel Reed",
        "age": 62,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Prostate cancer in remission",
        "assigned_clinician": "Dr. James Patel",
        "last_session_date": "2026-06-10",
        "data_completeness_score": 0.92,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-6841",
        "name": "Fatima Hassan",
        "age": 44,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Graves disease",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-09",
        "data_completeness_score": 0.89,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-4720",
        "name": "Jack Thompson",
        "age": 33,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Epilepsy, focal onset",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-08",
        "data_completeness_score": 0.95,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-7539",
        "name": "Isabella Costa",
        "age": 57,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Nonalcoholic steatohepatitis",
        "assigned_clinician": "Dr. James Patel",
        "last_session_date": "2026-06-07",
        "data_completeness_score": 0.87,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-2186",
        "name": "Robert Lewis",
        "age": 69,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Osteoarthritis, bilateral knees",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-06",
        "data_completeness_score": 0.98,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-5368",
        "name": "Grace Li",
        "age": 31,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Hashimoto thyroiditis",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-05",
        "data_completeness_score": 0.96,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-8650",
        "name": "Mateo Silva",
        "age": 46,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Obstructive sleep apnea",
        "assigned_clinician": "Dr. James Patel",
        "last_session_date": "2026-06-04",
        "data_completeness_score": 0.86,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-3492",
        "name": "Nora Evans",
        "age": 50,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Migraine with aura",
        "assigned_clinician": "Dr. Sarah Miller",
        "last_session_date": "2026-06-03",
        "data_completeness_score": 0.93,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-6177",
        "name": "Adam Kowalski",
        "age": 39,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Psoriatic arthritis",
        "assigned_clinician": "Dr. Elena Park",
        "last_session_date": "2026-06-02",
        "data_completeness_score": 0.91,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
]

SESSIONS = [
    {
        "session_id": "SES-8829-003",
        "patient_id": "PT-8829",
        "date": "2026-06-15",
        "uploaded_image_count": 2,
        "extraction_confidence": 0.87,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {"field_name": "primary_tumor_size", "value": "4.2cm", "confidence": 0.91},
            {"field_name": "hepatic_lesion_count", "value": "3", "confidence": 0.88},
        ],
    },
    {
        "session_id": "SES-1044-001",
        "patient_id": "PT-1044",
        "date": "2026-06-12",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.72,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {
                "field_name": "retinopathy_grade",
                "value": "Moderate NPDR",
                "confidence": 0.79,
            }
        ],
    },
    {
        "session_id": "SES-5510-001",
        "patient_id": "PT-5510",
        "date": "2026-06-18",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.94,
        "clinician_verification_status": "verified",
        "extracted_fields": [
            {"field_name": "phq9_score", "value": "8", "confidence": 0.96}
        ],
    },
    {
        "session_id": "SES-9921-001",
        "patient_id": "PT-9921",
        "date": "2026-06-10",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.85,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {"field_name": "cardiothoracic_ratio", "value": "0.62", "confidence": 0.89}
        ],
    },
]

SESSIONS += [
    {
        "session_id": f"SES-{patient_id[3:]}-001",
        "patient_id": patient_id,
        "date": date,
        "uploaded_image_count": images,
        "extraction_confidence": confidence,
        "clinician_verification_status": status,
        "extracted_fields": [],
    }
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
    "PT-8829": [
        {
            "source_id": "NOTE-8829-005",
            "source_type": "text",
            "date": "2026-06-15",
            "text": "CT shows RUL mass increased from 3.8cm to 4.2cm and three hepatic lesions, largest 3.5cm.",
        },
        {
            "source_id": "SES-8829-003",
            "source_type": "image",
            "date": "2026-06-15",
            "text": "CT abdomen shows three hepatic lesions.",
        },
    ],
    "PT-1044": [
        {
            "source_id": "NOTE-1044-002",
            "source_type": "text",
            "date": "2026-06-12",
            "text": "HbA1c is 8.2% with moderate non-proliferative diabetic retinopathy.",
        }
    ],
    "PT-5510": [
        {
            "source_id": "NOTE-5510-002",
            "source_type": "text",
            "date": "2026-06-18",
            "text": "PHQ-9 improved from 14 to 8; no suicidal ideation.",
        }
    ],
    "PT-9921": [
        {
            "source_id": "NOTE-9921-002",
            "source_type": "text",
            "date": "2026-06-10",
            "text": "CHF exacerbation with EF 35%, BNP 890, weight gain, and bilateral effusions.",
        }
    ],
}

RESEARCH_NOTIFICATIONS = [
    {
        "id": "NTF-001",
        "title": "Diuretic change below confidence",
        "detail": "PT-1029 extraction scored 76%; clinician verification required.",
        "severity": "critical",
        "agent": "Validation Agent",
        "read": False,
        "route": "/app/inbox",
    },
    {
        "id": "NTF-002",
        "title": "High-risk cohort increased",
        "detail": "Four patients crossed the high-risk threshold this week.",
        "severity": "info",
        "agent": "Population Insights Agent",
        "read": False,
        "route": "/app/overview",
    },
    {
        "id": "NTF-003",
        "title": "Re-run extraction with high resolution OCR",
        "detail": "PT-8829 has a prior extraction below the preferred confidence target.",
        "severity": "warning",
        "agent": "Image Quality Agent",
        "read": False,
        "route": "/app/extraction?patient=PT-8829",
    },
]

NORTHSTAR_PATIENTS = [
    {
        "patient_id": "PT-7301",
        "name": "Marcus Webb",
        "age": 58,
        "sex": "Male",
        "risk_level": "high",
        "primary_diagnosis": "Hepatocellular carcinoma, BCLC stage B",
        "assigned_clinician": "Dr. Ingrid Falk",
        "last_session_date": "2026-06-14",
        "data_completeness_score": 0.89,
        "open_tasks": 3,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-4185",
        "name": "Linnea Sorensen",
        "age": 47,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Atrial fibrillation, paroxysmal",
        "assigned_clinician": "Dr. Kwame Mensah",
        "last_session_date": "2026-06-13",
        "data_completeness_score": 0.77,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-9077",
        "name": "Tomas Herrera",
        "age": 66,
        "sex": "Male",
        "risk_level": "high",
        "primary_diagnosis": "Idiopathic pulmonary fibrosis",
        "assigned_clinician": "Dr. Ingrid Falk",
        "last_session_date": "2026-06-12",
        "data_completeness_score": 0.86,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-2560",
        "name": "Amara Diallo",
        "age": 34,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Asthma, moderate persistent",
        "assigned_clinician": "Dr. Yuki Sato",
        "last_session_date": "2026-06-11",
        "data_completeness_score": 0.93,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-6934",
        "name": "Viktor Petrov",
        "age": 71,
        "sex": "Male",
        "risk_level": "high",
        "primary_diagnosis": "Abdominal aortic aneurysm, 5.1cm",
        "assigned_clinician": "Dr. Kwame Mensah",
        "last_session_date": "2026-06-10",
        "data_completeness_score": 0.82,
        "open_tasks": 3,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-3408",
        "name": "Hana Kobayashi",
        "age": 29,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Celiac disease",
        "assigned_clinician": "Dr. Yuki Sato",
        "last_session_date": "2026-06-09",
        "data_completeness_score": 0.95,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-8216",
        "name": "Declan Murphy",
        "age": 54,
        "sex": "Male",
        "risk_level": "needs_review",
        "primary_diagnosis": "Chronic hepatitis C, treatment-naive",
        "assigned_clinician": "Dr. Ingrid Falk",
        "last_session_date": "2026-06-08",
        "data_completeness_score": 0.74,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-5723",
        "name": "Rosa Mendes",
        "age": 62,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Osteoporosis with prior vertebral fracture",
        "assigned_clinician": "Dr. Kwame Mensah",
        "last_session_date": "2026-06-07",
        "data_completeness_score": 0.81,
        "open_tasks": 1,
        "ai_review_status": "needs_review",
    },
    {
        "patient_id": "PT-1892",
        "name": "Elias Lindqvist",
        "age": 43,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Ankylosing spondylitis",
        "assigned_clinician": "Dr. Yuki Sato",
        "last_session_date": "2026-06-06",
        "data_completeness_score": 0.90,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-7645",
        "name": "Chioma Okeke",
        "age": 51,
        "sex": "Female",
        "risk_level": "stable",
        "primary_diagnosis": "Iron deficiency anemia, resolved",
        "assigned_clinician": "Dr. Ingrid Falk",
        "last_session_date": "2026-06-05",
        "data_completeness_score": 0.88,
        "open_tasks": 0,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-4029",
        "name": "Bruno Costa",
        "age": 39,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Gout, chronic tophaceous",
        "assigned_clinician": "Dr. Kwame Mensah",
        "last_session_date": "2026-06-04",
        "data_completeness_score": 0.85,
        "open_tasks": 1,
        "ai_review_status": "verified",
    },
    {
        "patient_id": "PT-9518",
        "name": "Ingrid Halvorsen",
        "age": 76,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Mild cognitive impairment",
        "assigned_clinician": "Dr. Yuki Sato",
        "last_session_date": "2026-06-03",
        "data_completeness_score": 0.72,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
    },
]

NORTHSTAR_SESSIONS = [
    {
        "session_id": "SES-7301-002",
        "patient_id": "PT-7301",
        "date": "2026-06-14",
        "uploaded_image_count": 2,
        "extraction_confidence": 0.84,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {"field_name": "lesion_count", "value": "4", "confidence": 0.86},
            {"field_name": "afp_level", "value": "412 ng/mL", "confidence": 0.90},
        ],
    },
    {
        "session_id": "SES-4185-001",
        "patient_id": "PT-4185",
        "date": "2026-06-13",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.78,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {
                "field_name": "ecg_rhythm",
                "value": "Atrial fibrillation with rapid ventricular response",
                "confidence": 0.83,
            }
        ],
    },
    {
        "session_id": "SES-9077-001",
        "patient_id": "PT-9077",
        "date": "2026-06-12",
        "uploaded_image_count": 2,
        "extraction_confidence": 0.88,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {"field_name": "fvc_percent_predicted", "value": "64%", "confidence": 0.90}
        ],
    },
    {
        "session_id": "SES-6934-001",
        "patient_id": "PT-6934",
        "date": "2026-06-10",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.91,
        "clinician_verification_status": "verified",
        "extracted_fields": [
            {"field_name": "aneurysm_diameter", "value": "5.1cm", "confidence": 0.93}
        ],
    },
    {
        "session_id": "SES-8216-001",
        "patient_id": "PT-8216",
        "date": "2026-06-08",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.71,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {"field_name": "fibrosis_stage", "value": "F2", "confidence": 0.75}
        ],
    },
    {
        "session_id": "SES-9518-001",
        "patient_id": "PT-9518",
        "date": "2026-06-03",
        "uploaded_image_count": 1,
        "extraction_confidence": 0.76,
        "clinician_verification_status": "pending",
        "extracted_fields": [
            {"field_name": "moca_score", "value": "23", "confidence": 0.80}
        ],
    },
]

NORTHSTAR_EVIDENCE = {
    "PT-7301": [
        {
            "source_id": "NOTE-7301-004",
            "source_type": "text",
            "date": "2026-06-14",
            "text": "MRI liver shows four LI-RADS 5 lesions, largest 3.1cm in segment VII; AFP 412 ng/mL, up from 260.",
        },
        {
            "source_id": "SES-7301-002",
            "source_type": "image",
            "date": "2026-06-14",
            "text": "MRI abdomen with contrast shows multifocal hepatic lesions.",
        },
    ],
    "PT-4185": [
        {
            "source_id": "NOTE-4185-002",
            "source_type": "text",
            "date": "2026-06-13",
            "text": "Holter confirms paroxysmal AF burden of 11%; CHA2DS2-VASc score 3, anticoagulation started.",
        }
    ],
    "PT-6934": [
        {
            "source_id": "NOTE-6934-003",
            "source_type": "text",
            "date": "2026-06-10",
            "text": "CT angiogram shows infrarenal AAA at 5.1cm, growth of 4mm in six months; vascular surgery referral placed.",
        }
    ],
    "PT-9518": [
        {
            "source_id": "NOTE-9518-001",
            "source_type": "text",
            "date": "2026-06-03",
            "text": "MoCA score 23/30 with deficits in delayed recall; B12 and TSH normal, MRI ordered.",
        }
    ],
}

NORTHSTAR_NOTIFICATIONS = [
    {
        "id": "NTF-N01",
        "title": "Hepatitis staging below confidence",
        "detail": "PT-8216 fibrosis staging scored 71%; clinician verification required.",
        "severity": "critical",
        "agent": "Validation Agent",
        "read": False,
        "route": "/app/inbox",
    },
    {
        "id": "NTF-N02",
        "title": "AAA surveillance interval exceeded",
        "detail": "PT-6934 aneurysm grew 4mm in six months; vascular review recommended.",
        "severity": "warning",
        "agent": "Population Insights Agent",
        "read": False,
        "route": "/app/overview",
    },
    {
        "id": "NTF-N03",
        "title": "Weekly cohort export completed",
        "detail": "Northstar Health population export finished with 12 patient records.",
        "severity": "info",
        "agent": "Population Insights Agent",
        "read": False,
        "route": "/app/database",
    },
]


RESEARCH_USERS = [
    {
        "id": "USR-001",
        "name": "Dr. Sarah Miller",
        "email": "sarah.miller@research.demo",
        "roles": ["Admin", "Clinician", "Reviewer"],
        "scope": "Organization",
        "status": "Active",
    },
    {
        "id": "USR-002",
        "name": "Dr. Elena Park",
        "email": "elena.park@research.demo",
        "roles": ["Clinician"],
        "scope": "Assigned patients",
        "status": "Active",
    },
    {
        "id": "USR-003",
        "name": "Dr. James Patel",
        "email": "james.patel@research.demo",
        "roles": ["Clinician", "Reviewer"],
        "scope": "Assigned patients",
        "status": "Active",
    },
    {
        "id": "USR-004",
        "name": "Alex Morgan",
        "email": "alex.morgan@research.demo",
        "roles": ["Data Manager"],
        "scope": "Data platform",
        "status": "Active",
    },
    {
        "id": "USR-005",
        "name": "Jordan Ellis",
        "email": "jordan.ellis@research.demo",
        "roles": ["Read-only Viewer"],
        "scope": "Audit and reports",
        "status": "Active",
    },
    {
        "id": "USR-006",
        "name": "Dr. Sarah Chen",
        "email": "sarah.chen@research.demo",
        "roles": ["Clinician"],
        "scope": "Assigned patients",
        "status": "Active",
    },
]

NORTHSTAR_USERS = [
    {
        "id": "USR-101",
        "name": "Dr. Ingrid Falk",
        "email": "ingrid.falk@northstar.demo",
        "roles": ["Admin", "Clinician"],
        "scope": "Organization",
        "status": "Active",
    },
    {
        "id": "USR-102",
        "name": "Dr. Kwame Mensah",
        "email": "kwame.mensah@northstar.demo",
        "roles": ["Clinician", "Reviewer"],
        "scope": "Assigned patients",
        "status": "Active",
    },
    {
        "id": "USR-103",
        "name": "Dr. Yuki Sato",
        "email": "yuki.sato@northstar.demo",
        "roles": ["Clinician"],
        "scope": "Assigned patients",
        "status": "Active",
    },
    {
        "id": "USR-104",
        "name": "Noor Haddad",
        "email": "noor.haddad@northstar.demo",
        "roles": ["Data Manager"],
        "scope": "Data platform",
        "status": "Active",
    },
    {
        "id": "USR-105",
        "name": "Sam Whitaker",
        "email": "sam.whitaker@northstar.demo",
        "roles": ["Read-only Viewer"],
        "scope": "Audit and reports",
        "status": "Active",
    },
]

# Plausible steady-state agent statistics for demo tenants; merged with the
# session's real runs by agent_monitoring() so demo screens stay lively while
# the real tenant reports only what actually executed.
MONITOR_BASELINE = [
    {
        "agent": "Image Quality Agent",
        "pipeline": "extraction",
        "lastRun": "2m ago",
        "status": "healthy",
        "avgConfidence": 0.96,
        "failureRate": 0.008,
        "reviewRate": 0.12,
        "avgDurationMs": 800,
        "linkedPatients": 18,
    },
    {
        "agent": "Vision Agent",
        "pipeline": "extraction",
        "lastRun": "2m ago",
        "status": "healthy",
        "avgConfidence": 0.92,
        "failureRate": 0.011,
        "reviewRate": 0.18,
        "avgDurationMs": 4200,
        "linkedPatients": 18,
    },
    {
        "agent": "Evidence Retrieval Agent",
        "pipeline": "qa",
        "lastRun": "8m ago",
        "status": "healthy",
        "avgConfidence": 0.89,
        "failureRate": 0.004,
        "reviewRate": 0.06,
        "avgDurationMs": 1700,
        "linkedPatients": 24,
    },
    {
        "agent": "SQL Generation Agent",
        "pipeline": "database",
        "lastRun": "12m ago",
        "status": "healthy",
        "avgConfidence": 0.94,
        "failureRate": 0.002,
        "reviewRate": 1.0,
        "avgDurationMs": 2100,
        "linkedPatients": 24,
    },
    {
        "agent": "Vector Indexing Agent",
        "pipeline": "extraction",
        "lastRun": "1m ago",
        "status": "degraded",
        "avgConfidence": 0.97,
        "failureRate": 0.024,
        "reviewRate": 0.0,
        "avgDurationMs": 3800,
        "linkedPatients": 24,
    },
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
    uploads: dict[str, dict[str, Any]] | None = None
    dashboard_seed: dict[str, Any] | None = None
    storage_seed: dict[str, Any] | None = None
    database_queries: list[dict[str, Any]] | None = None
    conversation_runs: list[dict[str, Any]] | None = None


RESEARCH_CLINIC = DemoDataset(
    "research_clinic",
    PATIENTS,
    SESSIONS,
    EVIDENCE,
    RESEARCH_NOTIFICATIONS,
    RESEARCH_USERS,
    MONITOR_BASELINE,
)
NORTHSTAR = DemoDataset(
    "northstar",
    NORTHSTAR_PATIENTS,
    NORTHSTAR_SESSIONS,
    NORTHSTAR_EVIDENCE,
    NORTHSTAR_NOTIFICATIONS,
    NORTHSTAR_USERS,
    MONITOR_BASELINE,
)
DATASETS = {dataset.key: dataset for dataset in (RESEARCH_CLINIC, NORTHSTAR)}

# Real-tenant databases and uploads follow CLINICAL_DATA_DIR when set (e.g. a
# mounted Docker volume) so they persist across restarts; otherwise they sit
# beside the project for local development. Demo tenants keep no files.
PROJECT_ROOT = (
    Path(os.environ["CLINICAL_DATA_DIR"]).resolve()
    if os.environ.get("CLINICAL_DATA_DIR")
    else Path(__file__).resolve().parents[1]
)

# Generated showcase assets (databases, PDFs, PNG previews, manifests) ship
# baked into the image beside the package and must resolve there regardless
# of CLINICAL_DATA_DIR — that variable relocates the *writable* real-tenant
# store, not these read-only demo fixtures. Reusing PROJECT_ROOT here made
# demo tenants look for showcase_data under the mounted volume (empty) and
# silently fall back to the tiny hardcoded dataset once CLINICAL_DATA_DIR was set.
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _read_app_manifest(directory: Path) -> dict[str, Any]:
    """Read a generated app manifest, falling back to manifest.frontend_contract."""

    app_manifest_path = directory / "app_manifest.json"
    if app_manifest_path.is_file():
        with open(app_manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    full_manifest_path = directory / "manifest.json"
    if full_manifest_path.is_file():
        with open(full_manifest_path, "r", encoding="utf-8") as f:
            full_manifest = json.load(f)
        return full_manifest.get("frontend_contract", {})
    return {}


def _generated_database_path(database_dir: Path) -> Path | None:
    """Resolve the SQLite file created by a database showcase generator."""

    manifest_path = database_dir / "manifest.json"
    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        raw = manifest.get("db_path")
        if raw:
            candidate = Path(str(raw))
            candidates = [candidate, PACKAGE_ROOT / candidate]
            for item in candidates:
                if item.is_file():
                    return item
    return next(database_dir.glob("*.db"), None)


def _generated_file_path(path_value: Any) -> Path:
    """Resolve generated manifest paths whether absolute or project-relative."""

    candidate = Path(str(path_value or "").replace("\\", "/"))
    if candidate.is_absolute():
        return candidate
    return PACKAGE_ROOT / candidate


def _monitor_row(baseline: dict[str, Any]) -> dict[str, Any]:
    """Normalize generated agent-monitoring seed rows for the app contract."""

    return {
        "agent": baseline["agent"],
        "pipeline": baseline["pipeline"],
        "lastRun": "2m ago",
        "status": "healthy"
        if float(baseline.get("failureRate", 0)) < 0.05
        else "degraded",
        "avgConfidence": float(baseline.get("avgConfidence", 0.9)),
        "failureRate": float(baseline.get("failureRate", 0)),
        "reviewRate": float(baseline.get("reviewRate", 0)),
        "avgDurationMs": int(baseline.get("avgDurationMs", 1500)),
        "linkedPatients": int(baseline.get("linkedPatients", 14)),
    }


def load_showcase_dataset(
    key: str,
    base_dir: Path,
    notifications: list[dict[str, Any]],
    users: list[dict[str, Any]],
    base_patients: list[dict[str, Any]] | None = None,
    base_sessions: list[dict[str, Any]] | None = None,
    base_evidence: dict[str, list[dict[str, Any]]] | None = None,
) -> DemoDataset | None:
    """Dynamically load a generated showcase dataset if files exist.

    base_patients/base_sessions/base_evidence are merged first so hand-authored
    demo anchors keep stable ordering while generated records add scale.
    """

    db_manifest_path = base_dir / "database" / "app_manifest.json"
    multimodal_manifest_path = base_dir / "multimodal" / "app_manifest.json"
    extraction_manifest_path = base_dir / "extraction" / "manifest.json"

    if (
        not db_manifest_path.is_file()
        and not (base_dir / "database" / "manifest.json").is_file()
    ):
        return None
    if (
        not multimodal_manifest_path.is_file()
        and not (base_dir / "multimodal" / "manifest.json").is_file()
    ):
        return None

    try:
        db_manifest = _read_app_manifest(base_dir / "database")
        mm_manifest = _read_app_manifest(base_dir / "multimodal")
        extraction_app_manifest = _read_app_manifest(base_dir / "extraction")
        if not db_manifest.get("dashboardSeed") or not mm_manifest.get("dashboardSeed"):
            return None
        extraction_manifest = {}
        if extraction_manifest_path.is_file():
            with open(extraction_manifest_path, "r", encoding="utf-8") as f:
                extraction_manifest = json.load(f)

        patients_by_id: dict[str, dict[str, Any]] = {
            item["patient_id"]: dict(item) for item in (base_patients or [])
        }
        sessions_by_id: dict[str, dict[str, Any]] = {
            item["session_id"]: dict(item) for item in (base_sessions or [])
        }
        evidence: dict[str, list[dict[str, Any]]] = {
            patient_id: list(items)
            for patient_id, items in (base_evidence or {}).items()
        }
        uploads = {}
        conversation_runs: list[dict[str, Any]] = []
        packet_records: dict[str, list[dict[str, Any]]] = {}
        for sample in extraction_manifest.get("samples", []):
            packet_id = str(sample.get("packet_id") or sample.get("sample_id") or "")
            packet_records.setdefault(packet_id, []).append(
                {
                    "patientId": sample.get("patient", {}).get("patient_id", ""),
                    "patientName": sample.get("patient", {}).get("name", ""),
                    "encounterDate": sample.get("encounter_date", ""),
                    "fields": sample.get("fields", []),
                    "note": sample.get("note", ""),
                }
            )
        db_path = _generated_database_path(base_dir / "database")
        if db_path and db_path.is_file():
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                for row in conn.execute(
                    """
                    SELECT patient_id, name, age, sex, risk_level, primary_diagnosis,
                           assigned_clinician, last_session_date, data_completeness_score,
                           open_tasks, ai_review_status
                    FROM patients_core
                    ORDER BY CASE risk_level WHEN 'high' THEN 0 WHEN 'needs_review' THEN 1 ELSE 2 END,
                             last_session_date DESC
                    LIMIT 750
                    """
                ):
                    patients_by_id[row["patient_id"]] = dict(row)
                for row in conn.execute(
                    """
                    SELECT s.session_id, s.patient_id, s.session_date AS date,
                           s.uploaded_image_count, s.extraction_confidence,
                           s.clinician_verification AS clinician_verification_status
                    FROM sessions s
                    JOIN patients_core p USING (patient_id)
                    ORDER BY s.session_date DESC
                    LIMIT 1200
                    """
                ):
                    item = dict(row)
                    item["extracted_fields"] = []
                    sessions_by_id[item["session_id"]] = item
                for row in conn.execute(
                    """
                    SELECT session_id, field_name, field_value AS value, confidence
                    FROM extracted_fields
                    WHERE session_id IN (SELECT session_id FROM sessions ORDER BY session_date DESC LIMIT 1200)
                    """
                ):
                    session = sessions_by_id.get(row["session_id"])
                    if session is not None:
                        session["extracted_fields"].append(
                            {
                                "field_name": row["field_name"],
                                "value": row["value"],
                                "confidence": float(row["confidence"] or 0),
                            }
                        )
                for row in conn.execute(
                    """
                    SELECT note_id, patient_id, note_date, note_text
                    FROM clinical_notes
                    WHERE patient_id IN (SELECT patient_id FROM patients_core LIMIT 750)
                    ORDER BY note_date DESC
                    LIMIT 1500
                    """
                ):
                    evidence.setdefault(row["patient_id"], []).append(
                        {
                            "source_id": row["note_id"],
                            "source_type": "text",
                            "date": row["note_date"],
                            "text": row["note_text"],
                        }
                    )
        for sample in extraction_manifest.get("samples", []):
            patient = sample.get("patient", {})
            patient_id = patient.get("patient_id")
            if not patient_id:
                continue
            patients_by_id.setdefault(
                patient_id,
                {
                    "patient_id": patient_id,
                    "name": patient.get("name", f"Patient {patient_id}"),
                    "age": patient.get("age", 0),
                    "sex": patient.get("sex", "Unknown"),
                    "risk_level": "needs_review"
                    if any(
                        field.get("needs_review") for field in sample.get("fields", [])
                    )
                    else "stable",
                    "primary_diagnosis": patient.get(
                        "diagnosis", "Synthetic extraction case"
                    ),
                    "assigned_clinician": patient.get("clinician", "Demo clinician"),
                    "last_session_date": sample.get("encounter_date", "2026-07-05"),
                    "data_completeness_score": 0.88,
                    "open_tasks": 1
                    if any(
                        field.get("needs_review") for field in sample.get("fields", [])
                    )
                    else 0,
                    "ai_review_status": "needs_review"
                    if any(
                        field.get("needs_review") for field in sample.get("fields", [])
                    )
                    else "verified",
                },
            )
            asset_path = _generated_file_path(sample.get("asset_path", ""))
            preview_path = _generated_file_path(sample.get("preview_path", ""))
            asset_id = sample.get("sample_id", f"EXT-{patient_id}")
            content_type = (
                sample.get("content_type")
                or sample.get("sourceContentType")
                or "application/pdf"
            )
            source_kind = "document" if content_type == "application/pdf" else "image"
            preview_url = f"/api/assets/{asset_id}"
            upload = {
                "assetId": asset_id,
                "patientId": patient_id,
                "filename": asset_path.name if asset_path.name else f"{asset_id}.png",
                "contentType": content_type,
                "sizeBytes": asset_path.stat().st_size
                if asset_path.is_file()
                else 102400,
                "previewUrl": preview_url,
                "createdAt": sample.get("encounter_date", "2026-07-05"),
                "knowledgeBase": False,
                "sourceUse": "extraction",
                "filePath": str(asset_path) if asset_path.is_file() else "",
                "previewPath": str(preview_path) if preview_path.is_file() else "",
                "previewContentType": sample.get("preview_content_type", "image/png"),
                "demoPlatform": extraction_manifest.get("demo_platform", "primary"),
                "packetId": sample.get("packet_id"),
                "packetPatientIds": sample.get("packet_patient_ids", []),
                "patientCountInFile": sample.get("patient_count_in_file", 1),
                "extracted": {
                    "type": source_kind,
                    "documentType": sample.get("expected_agent_output", {}).get(
                        "documentType", "Enterprise clinical packet"
                    ),
                    "textPreview": sample.get("note", ""),
                    "fields": sample.get("fields", []),
                    "visualization": sample.get("expected_agent_output", {}).get(
                        "visualization", {}
                    ),
                    "packetPatientIds": sample.get("packet_patient_ids", []),
                    "selectedPatientId": patient_id,
                    "patientRecordIndex": max(
                        1, sample.get("packet_patient_ids", []).index(patient_id) + 1
                    )
                    if patient_id in sample.get("packet_patient_ids", [])
                    else 1,
                    "pageCount": sample.get("patient_count_in_file", 1),
                    "packetRecords": packet_records.get(
                        str(sample.get("packet_id") or sample.get("sample_id") or ""),
                        [],
                    ),
                },
            }
            uploads[asset_id] = upload
            session_id = f"SES-{asset_id}"
            sessions_by_id[session_id] = {
                "session_id": session_id,
                "patient_id": patient_id,
                "date": sample.get("encounter_date", "2026-07-05"),
                "uploaded_image_count": 1,
                "extraction_confidence": round(
                    sum(
                        float(field.get("confidence", 0.85))
                        for field in sample.get("fields", [])
                    )
                    / max(1, len(sample.get("fields", []))),
                    2,
                ),
                "clinician_verification_status": "pending"
                if any(field.get("needs_review") for field in sample.get("fields", []))
                else "verified",
                "extracted_fields": [
                    {
                        "field_name": field.get("field_name", ""),
                        "value": field.get("value", ""),
                        "confidence": field.get("confidence", 0.0),
                    }
                    for field in sample.get("fields", [])
                ],
            }
            evidence.setdefault(patient_id, []).append(
                {
                    "source_id": asset_id,
                    "source_type": source_kind,
                    "date": sample.get("encounter_date", "2026-07-05"),
                    "text": sample.get("note", "Synthetic extraction packet evidence."),
                    "asset_id": asset_id,
                }
            )

        for item in mm_manifest.get("syntheticKnowledgeBase", []):
            patient_id = item["patientId"]
            bundle_rel_path = item["bundlePath"]
            bundle_path = PACKAGE_ROOT / bundle_rel_path.replace("\\", "/")
            if not bundle_path.is_file():
                continue

            with open(bundle_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)

            pt = bundle["patient"]
            patients_by_id[pt["patient_id"]] = {
                "patient_id": pt["patient_id"],
                "name": pt["name"],
                "age": pt["age"],
                "sex": pt["sex"],
                "risk_level": pt["risk_level"],
                "primary_diagnosis": pt["primary_diagnosis"],
                "assigned_clinician": pt["assigned_clinician"],
                "last_session_date": "2026-07-05",
                "data_completeness_score": pt.get("data_completeness_score", 0.95),
                "open_tasks": 2 if pt["risk_level"] in ("high", "needs_review") else 0,
                "ai_review_status": "needs_review"
                if pt["risk_level"] in ("high", "needs_review")
                else "verified",
            }

            evidence_list = evidence.setdefault(pt["patient_id"], [])
            for note in bundle.get("notes", []):
                evidence_list.append(
                    {
                        "source_id": note["note_id"],
                        "source_type": "text",
                        "date": note["date"],
                        "text": note["text"],
                    }
                )

            for pdf in bundle.get("pdf_documents", []):
                evidence_list.append(
                    {
                        "source_id": pdf["document_id"],
                        "source_type": "document",
                        "date": pdf["date"],
                        "text": f"PDF Clinical Evidence Document containing: {', '.join(pdf['contains'])}",
                    }
                )
            for pdf in bundle.get("pdf_documents", []):
                session_id = (
                    f"SES-{pt['patient_id'][3:]}-{pdf['document_id'].split('-')[-1]}"
                )
                sessions_by_id[session_id] = {
                    "session_id": session_id,
                    "patient_id": pt["patient_id"],
                    "date": pdf["date"],
                    "uploaded_image_count": 1
                    if "image_evidence_summary" in pdf["contains"]
                    or "trend_chart" in pdf["contains"]
                    else 0,
                    "extraction_confidence": 0.92,
                    "clinician_verification_status": "verified"
                    if pdf["date"] < "2026-07-01"
                    else "pending",
                    "extracted_fields": [],
                }

            for doc in bundle.get("knowledge_base_documents", []):
                doc_id = doc["document_id"]
                # The generated file exists on disk; keep its resolved path so
                # the asset route can stream real bytes for previews instead
                # of 404ing on a seeded upload with no in-memory contents.
                doc_path = PACKAGE_ROOT / doc["path"].replace("\\", "/")
                uploads[doc_id] = {
                    "assetId": doc_id,
                    "patientId": doc["patient_id"],
                    "filename": Path(doc["path"]).name,
                    "contentType": doc["content_type"],
                    "sizeBytes": doc_path.stat().st_size
                    if doc_path.is_file()
                    else 102400,
                    "previewUrl": f"/api/assets/{doc_id}",
                    "createdAt": datetime.now(UTC).isoformat(),
                    "knowledgeBase": True,
                    "filePath": str(doc_path) if doc_path.is_file() else "",
                    "extracted": {
                        "type": "pdf"
                        if doc["content_type"] == "application/pdf"
                        else "document",
                        "pageCount": doc.get("page_count", 1),
                        "textPreview": f"Synthetic knowledge base file {doc_id} for patient {doc['patient_id']}.",
                    },
                }

            chart_evidence: list[dict[str, Any]] = []
            chart_labels = {
                "metric_trends": "Longitudinal patient trend",
                "comparator_risk": "Comparator cohort risk distribution",
            }
            evidence_date = max(
                (str(note.get("date", "")) for note in bundle.get("notes", [])),
                default="2026-07-05",
            )
            for chart_value in bundle.get("matplotlib_pngs", []):
                chart_path = _generated_file_path(chart_value)
                if not chart_path.is_file():
                    continue
                chart_key = chart_path.stem
                chart_id = (
                    f"VIS-{pt['patient_id']}-{chart_key.upper().replace('_', '-')}"
                )
                chart_label = chart_labels.get(
                    chart_key, chart_key.replace("_", " ").title()
                )
                uploads[chart_id] = {
                    "assetId": chart_id,
                    "patientId": pt["patient_id"],
                    "filename": chart_path.name,
                    "contentType": "image/png",
                    "sizeBytes": chart_path.stat().st_size,
                    "previewUrl": f"/api/assets/{chart_id}",
                    "createdAt": evidence_date,
                    "knowledgeBase": True,
                    "sourceUse": "qa_visual",
                    "filePath": str(chart_path),
                    "extracted": {
                        "type": "image",
                        "imageCount": 1,
                        "textPreview": f"{chart_label} for {pt['name']} ({pt['patient_id']}).",
                    },
                }
                evidence_item = {
                    "source_id": chart_id,
                    "source_type": "image",
                    "date": evidence_date,
                    "text": f"{chart_label} for {pt['patient_id']}, derived from the generated longitudinal patient record.",
                    "asset_id": chart_id,
                }
                evidence_list.append(evidence_item)
                chart_evidence.append(evidence_item)

            qa_prompts = bundle.get("qa_prompts", [])
            if qa_prompts:
                prompt = qa_prompts[0]
                note_evidence = max(
                    bundle.get("notes", []),
                    key=lambda note: str(note.get("date", "")),
                    default={},
                )
                seeded_evidence = []
                if note_evidence:
                    seeded_evidence.append(
                        {
                            "id": note_evidence.get(
                                "note_id", f"NOTE-{pt['patient_id']}"
                            ),
                            "label": f"Clinical note - {note_evidence.get('date', evidence_date)}",
                            "kind": "text",
                            "excerpt": note_evidence.get("text", ""),
                        }
                    )
                if chart_evidence:
                    seeded_evidence.append(
                        {
                            "id": chart_evidence[0]["source_id"],
                            "label": f"Visual trend - {chart_evidence[0]['date']}",
                            "kind": "image",
                            "excerpt": chart_evidence[0]["text"],
                        }
                    )
                answer = (
                    f"{pt['name']} has {pt['primary_diagnosis']} with current risk status "
                    f"{str(pt['risk_level']).replace('_', ' ')}. Recent longitudinal evidence and the attached "
                    "trend visual should be reviewed together; the visual is supportive evidence, not a standalone diagnosis."
                )
                conversation_runs.append(
                    {
                        "id": f"RUN-DEMO-QA-{pt['patient_id']}",
                        "workflow": "qa",
                        "status": "completed",
                        "agentName": "patient_qa_pipeline",
                        "confidence": 0.9,
                        "createdAt": evidence_date,
                        "auditId": f"AUD-DEMO-QA-{pt['patient_id']}",
                        "traceId": f"TRACE-DEMO-QA-{pt['patient_id']}",
                        "seededConversation": True,
                        "steps": [
                            {
                                "id": f"RUN-DEMO-QA-{pt['patient_id']}-S1",
                                "name": "Evidence Retrieval Agent",
                                "status": "completed",
                                "detail": "Retrieved longitudinal text and visual evidence",
                                "timestamp": evidence_date,
                            },
                            {
                                "id": f"RUN-DEMO-QA-{pt['patient_id']}-S2",
                                "name": "Clinical Answer Agent",
                                "status": "completed",
                                "detail": "Synthesized clinician-facing answer",
                                "timestamp": evidence_date,
                            },
                        ],
                        "evidence": seeded_evidence,
                        "result": {
                            "question": prompt.get(
                                "question",
                                "What changed and which evidence supports it?",
                            ),
                            "patientId": pt["patient_id"],
                            "answer": answer,
                            "imageEvidence": seeded_evidence[-1]
                            if seeded_evidence
                            and seeded_evidence[-1].get("kind") == "image"
                            else None,
                            "summaryRows": [
                                {
                                    "id": f"{pt['patient_id']}-diagnosis",
                                    "citation": "[1]",
                                    "file": "Longitudinal record",
                                    "type": "structured",
                                    "finding": pt["primary_diagnosis"],
                                },
                                {
                                    "id": f"{pt['patient_id']}-risk",
                                    "citation": "[2]",
                                    "file": "Trend visual",
                                    "type": "image",
                                    "finding": f"Current risk status: {str(pt['risk_level']).replace('_', ' ')}",
                                },
                            ],
                            "answerSections": {
                                "keyEvidence": answer,
                                "recommendedAction": "Correlate the trend with the latest authored note and verify any material change before updating the care plan.",
                                "limitations": "Synthetic longitudinal evidence for product demonstration; clinician review remains required.",
                            },
                            "toolCalls": [],
                        },
                    }
                )

        monitor_baseline = []
        for manifest in (db_manifest, extraction_app_manifest, mm_manifest):
            monitor_baseline.extend(
                _monitor_row(baseline)
                for baseline in manifest.get("agentMonitoringSeed", [])
            )

        if not monitor_baseline:
            monitor_baseline = MONITOR_BASELINE

        db_dashboard = db_manifest.get("dashboardSeed", {})
        extraction_dashboard = extraction_app_manifest.get("dashboardSeed", {})
        mm_dashboard = mm_manifest.get("dashboardSeed", {})
        total_patients = int(db_dashboard.get("patients", 0)) or len(patients_by_id)
        total_sessions = (
            int(db_dashboard.get("sessions", 0))
            + int(extraction_dashboard.get("sessions", 0))
            + int(mm_dashboard.get("sessions", 0))
        ) or len(sessions_by_id)
        high_risk = max(
            int(db_dashboard.get("highRiskEstimate", 0)),
            int(extraction_dashboard.get("highRiskEstimate", 0)),
            int(mm_dashboard.get("highRiskEstimate", 0)),
            sum(
                1
                for patient in patients_by_id.values()
                if patient.get("risk_level") == "high"
            ),
        )
        pending_review = max(
            int(db_dashboard.get("pendingReviewEstimate", 0)),
            int(extraction_dashboard.get("pendingReviewEstimate", 0)),
            int(mm_dashboard.get("pendingReviewEstimate", 0)),
            sum(
                1
                for patient in patients_by_id.values()
                if patient.get("ai_review_status") == "needs_review"
                or patient.get("risk_level") in {"high", "needs_review"}
            ),
        )
        completeness_values = [
            float(patient.get("data_completeness_score") or 0)
            for patient in patients_by_id.values()
        ]
        storage_total = (
            db_manifest.get("storageSeed", {}).get("cloudObjects", 0)
            + extraction_app_manifest.get("storageSeed", {}).get("cloudObjects", 0)
            + mm_manifest.get("storageSeed", {}).get("cloudObjects", 0)
        )
        combined_dashboard = {
            **db_dashboard,
            "patients": total_patients,
            "sessions": total_sessions,
            "highRiskEstimate": high_risk,
            "pendingReviewEstimate": pending_review,
            "pendingVerifications": pending_review,
            "storedAssets": storage_total,
            "imageExtractionsToday": extraction_dashboard.get(
                "imageExtractionsToday", extraction_dashboard.get("sourceImages", 0)
            ),
            "agentRuns24h": db_dashboard.get("agentRuns24h", 0)
            + extraction_dashboard.get("agentRuns", 0)
            + mm_dashboard.get("agentRuns24h", 0),
            "auditEvents": db_dashboard.get("auditEvents", 0)
            + extraction_dashboard.get("auditEvents", 0)
            + mm_dashboard.get("auditEvents", 0),
            "databaseRows": db_dashboard.get("databaseRows", 0),
            "queryExamples": db_dashboard.get("queryExamples", 0),
            "sourcePackets": extraction_dashboard.get("sourcePackets", 0),
            "patientsPerFile": extraction_dashboard.get("patientsPerFile", 0),
            "qaPrompts": mm_dashboard.get("qaPrompts", 0),
            "knowledgeBaseDocuments": mm_dashboard.get("knowledgeBaseDocuments", 0),
            "citations": mm_dashboard.get("citations", 0),
            "openAiAlerts": db_dashboard.get("openAiAlerts", 0)
            + extraction_dashboard.get("openAiAlerts", 0)
            + mm_dashboard.get("openAiAlerts", 0),
            "failedExtractions": db_dashboard.get("failedExtractions", 0)
            + extraction_dashboard.get("failedExtractions", 0)
            + mm_dashboard.get("failedExtractions", 0),
            "completeness": round(
                sum(completeness_values) / max(1, len(completeness_values)) * 100
            ),
            "syncRate": 100,
        }
        db_storage = db_manifest.get("storageSeed", {})
        extraction_storage = extraction_app_manifest.get("storageSeed", {})
        mm_storage = mm_manifest.get("storageSeed", {})
        combined_storage = {
            "cloudObjects": db_storage.get("cloudObjects", 0)
            + extraction_storage.get("cloudObjects", 0)
            + mm_storage.get("cloudObjects", 0),
            "jsonDocuments": db_storage.get("jsonDocuments", 0)
            + extraction_storage.get("jsonDocuments", 0)
            + mm_storage.get("jsonDocuments", 0),
            "relationalRows": db_storage.get("relationalRows", 0)
            + extraction_storage.get("relationalRows", 0)
            + mm_storage.get("relationalRows", 0),
            "vectorRecords": db_storage.get("vectorRecords", 0)
            + extraction_storage.get("vectorRecords", 0)
            + mm_storage.get("vectorRecords", 0),
            "auditEvents": db_storage.get("auditEvents", 0)
            + mm_storage.get("auditEvents", 0),
            "failedRecords": db_storage.get("failedRecords", 0)
            + extraction_storage.get("failedRecords", 0)
            + mm_storage.get("failedRecords", 0),
        }
        return DemoDataset(
            key=key,
            patients=list(patients_by_id.values()),
            sessions=list(sessions_by_id.values()),
            evidence=evidence,
            notifications=notifications,
            users=users,
            monitor_baseline=monitor_baseline,
            uploads=uploads,
            dashboard_seed=combined_dashboard,
            storage_seed=combined_storage,
            database_queries=db_manifest.get("queryCards", []),
            conversation_runs=conversation_runs,
        )
    except Exception as exc:
        print(f"Error loading generated showcase dataset from {base_dir}: {exc}")
        return None


# Try loading generated showcase datasets for both demo tenants. The primary
# scripts feed Research Clinic; the demo2 scripts feed Northstar Health.
GENERATED_RESEARCH = load_showcase_dataset(
    "research_clinic",
    PACKAGE_ROOT / "showcase_data",
    RESEARCH_NOTIFICATIONS,
    RESEARCH_USERS,
    base_patients=PATIENTS,
    base_sessions=SESSIONS,
    base_evidence=EVIDENCE,
)
if GENERATED_RESEARCH:
    RESEARCH_CLINIC = GENERATED_RESEARCH
    DATASETS["research_clinic"] = RESEARCH_CLINIC

DEMO2_NORTHSTAR = load_showcase_dataset(
    "northstar",
    PACKAGE_ROOT / "showcase_data" / "demo2",
    NORTHSTAR_NOTIFICATIONS,
    NORTHSTAR_USERS,
    base_patients=NORTHSTAR_PATIENTS,
    base_sessions=NORTHSTAR_SESSIONS,
    base_evidence=NORTHSTAR_EVIDENCE,
)
if DEMO2_NORTHSTAR:
    NORTHSTAR = DEMO2_NORTHSTAR
    DATASETS["northstar"] = NORTHSTAR


def now() -> str:
    """Return stable-format UTC timestamp."""

    return datetime.now(UTC).isoformat()


# Stable ids for the reports the workspace can generate on a schedule; the
# frontend reports view and the /report-schedules endpoints share these ids.
REPORT_CATALOG: tuple[tuple[str, str], ...] = (
    ("daily-command", "Daily clinical command report"),
    ("extraction-quality", "Extraction quality report"),
    ("cohort-risk", "Patient cohort risk report"),
    ("storage-lineage", "Storage and lineage report"),
)


def default_report_schedules() -> dict[str, dict[str, Any]]:
    """Seed every report with generation disabled until a user schedules it."""

    return {
        report_id: {
            "id": report_id,
            "name": name,
            "frequency": "off",
            "nextRun": None,
            "updatedAt": None,
        }
        for report_id, name in REPORT_CATALOG
    }


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
            row = stats.setdefault(
                name,
                {
                    "agent": name,
                    "pipeline": run.get("workflow", ""),
                    "steps": 0,
                    "errors": 0,
                    "reviews": 0,
                    "confidences": [],
                    "lastRun": "",
                },
            )
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
        rows.append(
            {
                **row,
                "status": "degraded" if errors else "healthy",
                "avgConfidence": round(sum(confidences) / len(confidences), 3)
                if confidences
                else 0.0,
                "failureRate": round(errors / steps, 3),
                "reviewRate": round(reviews / steps, 3),
                "avgDurationMs": 0,
                "linkedPatients": 0,
            }
        )
    rows.sort(key=lambda item: item["lastRun"], reverse=True)
    return rows


class DemoRepository:
    """Mutable state belonging to exactly one browser demo session."""

    def __init__(
        self, dataset: DemoDataset = RESEARCH_CLINIC, db_path: Path | None = None
    ) -> None:
        self.session_id = ""
        self.is_demo = True
        self._dataset = dataset
        self.db_path = db_path
        self.reset()

    def reset(self) -> None:
        """Restore deterministic seed state for this repository's dataset."""

        self.patients = {
            item["patient_id"]: item for item in deepcopy(self._dataset.patients)
        }
        self.sessions = {
            item["session_id"]: item for item in deepcopy(self._dataset.sessions)
        }
        self.evidence = deepcopy(self._dataset.evidence)
        self.source_assets: dict[str, tuple[bytes, str]] = {}
        for patient_id, evidence_rows in self.evidence.items():
            for evidence in evidence_rows:
                if evidence["source_type"] == "image":
                    asset_id = evidence["source_id"]
                    self.source_assets[asset_id] = (
                        f"DEMO IMAGE {patient_id} {asset_id}".encode(),
                        "image/png",
                    )
                    evidence["asset_id"] = asset_id
        self.uploads: dict[str, dict[str, Any]] = (
            deepcopy(self._dataset.uploads) if self._dataset.uploads else {}
        )
        self.asset_contents: dict[str, bytes] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.query_history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        if self._dataset.dashboard_seed:
            ds = self._dataset.dashboard_seed
            seeded_activity = [
                (
                    "showcase_database_loaded",
                    "database_intelligence_pipeline",
                    "RUN-SEED-DB",
                    {
                        "patients": ds.get("patients", 0),
                        "sessions": ds.get("sessions", 0),
                        "databaseRows": ds.get("databaseRows", 0),
                    },
                ),
                (
                    "showcase_extraction_assets_loaded",
                    "image_extraction_pipeline",
                    "RUN-SEED-EXT",
                    {
                        "imageExtractionsToday": ds.get("imageExtractionsToday", 0),
                        "pendingReview": ds.get("pendingReviewEstimate", 0),
                    },
                ),
                (
                    "showcase_multimodal_corpus_loaded",
                    "patient_qa_pipeline",
                    "RUN-SEED-QA",
                    {
                        "knowledgeBaseDocuments": ds.get("knowledgeBaseDocuments", 0),
                        "citations": ds.get("citations", 0),
                        "qaPrompts": ds.get("qaPrompts", 0),
                    },
                ),
            ]
            self.audit = [
                {
                    "audit_id": f"AUD-SEED-{index:03d}",
                    "timestamp": now(),
                    "action": action,
                    "actor": actor,
                    "role": "system",
                    "details": {"run_id": run_id, "result": "recorded", **details},
                }
                for index, (action, actor, run_id, details) in enumerate(
                    seeded_activity, 1
                )
            ]
            # Materialize the bootstrap runs the seeded audit events reference so
            # /runs/{id} navigation from any log entry resolves instead of 404ing.
            # "seeded" excludes them from /runs listing (they are not conversation
            # turns) and "persisted": False keeps them out of the /storage scan.
            workflow_by_run = {
                "RUN-SEED-DB": "database",
                "RUN-SEED-EXT": "extraction",
                "RUN-SEED-QA": "qa",
            }
            for index, (action, actor, run_id, details) in enumerate(
                seeded_activity, 1
            ):
                self.runs[run_id] = {
                    "id": run_id,
                    "workflow": workflow_by_run[run_id],
                    "status": "completed",
                    "agentName": actor,
                    "confidence": 0.97,
                    "createdAt": now(),
                    "auditId": f"AUD-SEED-{index:03d}",
                    "traceId": f"TRACE-{run_id}",
                    "seeded": True,
                    "steps": [
                        {
                            "id": f"{run_id}-S1",
                            "name": "Showcase dataset generation",
                            "status": "completed",
                            "detail": "Deterministic generator produced governed synthetic assets",
                            "timestamp": now(),
                        },
                        {
                            "id": f"{run_id}-S2",
                            "name": "Tenant bootstrap load",
                            "status": "completed",
                            "detail": action.replace("_", " "),
                            "timestamp": now(),
                        },
                    ],
                    "evidence": [],
                    "result": {
                        "persisted": False,
                        "storageReceipts": [],
                        "summary": dict(details),
                    },
                    "review": None,
                }
        for conversation in deepcopy(self._dataset.conversation_runs or []):
            self.runs[conversation["id"]] = conversation
        self.agent_config: dict[str, Any] = {
            "version": 1,
            "autoApprovalThreshold": 90,
            "reviewThreshold": 75,
            "maxConcurrentRuns": 8,
            "databaseEnabled": True,
        }
        self.report_schedules: dict[str, dict[str, Any]] = default_report_schedules()
        self.notifications = [
            dict(item, createdAt=now())
            for item in deepcopy(self._dataset.notifications)
        ]
        self.users = deepcopy(self._dataset.users)
        self.permissions = {
            "roles": list(system_module.ROLES),
            "matrix": deepcopy(system_module.DEFAULT_PERMISSIONS),
            "version": 1,
        }
        self.sequence = 0
        self.dashboard_seed = self._dataset.dashboard_seed
        self.storage_seed = self._dataset.storage_seed
        self.database_queries = (
            deepcopy(self._dataset.database_queries)
            if self._dataset.database_queries
            else []
        )

    def record_run(self, item: dict[str, Any]) -> None:
        """Store one demo workflow turn for this isolated browser session."""

        self.runs[item["id"]] = item

    def identifier(self, prefix: str) -> str:
        """Create deterministic identifier within session state."""

        self.sequence += 1
        return f"{prefix}-{self.sequence:04d}"

    def log(self, action: str, actor: str, role: str, **details: Any) -> dict[str, Any]:
        """Append auditable product event."""

        event = {
            "audit_id": self.identifier("AUD"),
            "timestamp": now(),
            "action": action,
            "actor": actor,
            "role": role,
            "details": details,
        }
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

    def save_permissions(
        self, matrix: list[dict[str, Any]], actor: str
    ) -> dict[str, Any]:
        """Update the session-scoped permission matrix (demo tenants only)."""

        self.permissions["matrix"] = deepcopy(matrix)
        self.permissions["version"] = int(self.permissions["version"]) + 1
        return self.permissions

    def build_notifications(self) -> list[dict[str, Any]]:
        """Demo notifications are seeded; return them unchanged."""

        return self.notifications


class LiveRepository:
    """Mutable per-session view over the real clinical database plus agent runs."""

    def __init__(
        self, db_path: Path | None = None, uploads_root: Path | None = None
    ) -> None:
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
        self.report_schedules: dict[str, dict[str, Any]] = default_report_schedules()
        self.notifications: list[dict[str, Any]] = []
        self.sequence = 0
        self._hydrate_from_database()
        self._hydrate_workflow_runs()

    def _hydrate_workflow_runs(self) -> None:
        """Restore persisted workflow conversations for this real tenant."""

        db_path = self._governance_db()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path, timeout=30) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow TEXT NOT NULL,
                    patient_id TEXT,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            rows = conn.execute(
                "SELECT payload FROM workflow_runs ORDER BY created_at ASC LIMIT 500"
            ).fetchall()
        for row in rows:
            try:
                item = json.loads(row[0])
            except (TypeError, json.JSONDecodeError):
                continue
            self.runs[item["id"]] = item
            if item.get("workflow") == "database" and item.get("status") == "completed":
                self.query_history.append(item)

    def record_run(self, item: dict[str, Any]) -> None:
        """Persist one real-tenant workflow turn for cross-session history."""

        self.runs[item["id"]] = item
        patient_id = str(item.get("result", {}).get("patientId") or "")
        with sqlite3.connect(self._governance_db(), timeout=30) as conn:
            conn.execute(
                """
                INSERT INTO workflow_runs (run_id, workflow, patient_id, created_at, payload)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    workflow = excluded.workflow,
                    patient_id = excluded.patient_id,
                    created_at = excluded.created_at,
                    payload = excluded.payload
                """,
                (
                    item["id"],
                    item.get("workflow", ""),
                    patient_id or None,
                    item.get("createdAt", now()),
                    json.dumps(item, default=str),
                ),
            )
            conn.commit()

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

        return (
            Path(self.db_path)
            if self.db_path is not None
            else PACKAGE_ROOT / "clinical.db"
        )

    def _load_rows(self, database: Any) -> None:
        """Read patients, sessions, and notes from the active database file."""

        patients = database.execute_sql(
            "SELECT patient_id, name, age, sex, risk_level, primary_diagnosis, "
            "assigned_clinician, last_session_date, data_completeness_score, "
            "open_tasks, ai_review_status FROM patients_core"
        )
        for row in patients.get("rows", []):
            item = dict(row)
            item["data_completeness_score"] = float(
                item.get("data_completeness_score") or 0
            )
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
            item["extraction_confidence"] = float(
                item.get("extraction_confidence") or 0
            )
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
                session["extracted_fields"].append(
                    {
                        "field_name": row["field_name"],
                        "value": row["value"],
                        "confidence": float(row.get("confidence") or 0),
                    }
                )

        notes = database.execute_sql(
            "SELECT note_id, patient_id, note_date, note_text FROM clinical_notes"
        )
        for row in notes.get("rows", []):
            self.evidence.setdefault(row["patient_id"], []).append(
                {
                    "source_id": row["note_id"],
                    "source_type": "text",
                    "date": row["note_date"],
                    "text": row["note_text"],
                }
            )

    def reset(self) -> None:
        """Clear session data while keeping tenant storage paths."""

        self.__init__(db_path=self.db_path, uploads_root=self.uploads_root)  # type: ignore[misc]

    def identifier(self, prefix: str) -> str:
        """Create identifier within session state."""

        self.sequence += 1
        return f"{prefix}-{self.sequence:04d}"

    def log(self, action: str, actor: str, role: str, **details: Any) -> dict[str, Any]:
        """Append auditable event."""

        event = {
            "audit_id": self.identifier("AUD"),
            "timestamp": now(),
            "action": action,
            "actor": actor,
            "role": role,
            "details": details,
        }
        self.audit.append(event)
        return event

    def find_patient(self, patient_id: str) -> dict[str, Any] | None:
        """Return one patient, re-reading the tenant database on a memory miss.

        A live session hydrates its roster once at creation, so patients that
        reach the store afterwards (ETL ingestion, another session's approved
        extraction, agent writes) are invisible to that snapshot. Falling back
        to the database keeps every stored patient addressable from any open
        session — the Q&A and extraction workflows both resolve patients here.
        """

        item = self.patients.get(patient_id)
        if item is not None:
            return item
        try:
            from capstone_agent import database
        except Exception:
            return None
        if self.db_path is not None:
            with database.tenant_storage(self.db_path, self.uploads_root):
                return self._load_patient_row(database, patient_id)
        return self._load_patient_row(database, patient_id)

    def _load_patient_row(
        self, database: Any, patient_id: str
    ) -> dict[str, Any] | None:
        """Read a single patients_core row and cache it in the session roster."""

        with database.get_connection() as conn:
            row = conn.execute(
                "SELECT patient_id, name, age, sex, risk_level, primary_diagnosis, "
                "assigned_clinician, last_session_date, data_completeness_score, "
                "open_tasks, ai_review_status FROM patients_core WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["data_completeness_score"] = float(
            item.get("data_completeness_score") or 0
        )
        item["open_tasks"] = int(item.get("open_tasks") or 0)
        self.patients[patient_id] = item
        return item

    def add_patient(self, patient_id: str, name: str, **kwargs: Any) -> dict[str, Any]:
        """Register a patient from extraction results."""

        patient = {
            "patient_id": patient_id,
            "name": name,
            "age": kwargs.get("age"),
            "sex": kwargs.get("sex"),
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

    def save_permissions(
        self, matrix: list[dict[str, Any]], actor: str
    ) -> dict[str, Any]:
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
                route = (
                    "/app/inbox"
                    if run.get("workflow") == "extraction"
                    else "/app/database"
                )
                derived.append(
                    {
                        "id": f"NTF-{run['id']}",
                        "title": f"{run.get('workflow', 'run').title()} awaiting review",
                        "detail": f"Run {run['id']}{f' for {patient_id}' if patient_id else ''} needs an explicit clinician decision.",
                        "severity": "critical",
                        "agent": run.get("agentName", "pipeline"),
                        "read": any(
                            n["id"] == f"NTF-{run['id']}" and n.get("read")
                            for n in self.notifications
                        ),
                        "route": route,
                        "createdAt": run.get("createdAt", now()),
                    }
                )
            elif run.get("status") == "error":
                derived.append(
                    {
                        "id": f"NTF-{run['id']}",
                        "title": f"{run.get('workflow', 'run').title()} run failed",
                        "detail": f"Run {run['id']} ended in an error; inspect the run steps and retry.",
                        "severity": "warning",
                        "agent": run.get("agentName", "pipeline"),
                        "read": any(
                            n["id"] == f"NTF-{run['id']}" and n.get("read")
                            for n in self.notifications
                        ),
                        "route": "/app/inbox",
                        "createdAt": run.get("createdAt", now()),
                    }
                )
        self.notifications = derived
        return derived


class RepositoryRegistry:
    """Thread-safe registry of isolated repositories, tenant-aware."""

    def __init__(self, max_count: int = 100, ttl_seconds: int = 3600) -> None:
        self._items: OrderedDict[str, tuple[DemoRepository | LiveRepository, float]] = (
            OrderedDict()
        )
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
        db_path = PACKAGE_ROOT / tenant.db_filename if tenant.db_filename else None
        return DemoRepository(
            DATASETS[tenant.dataset or "research_clinic"], db_path=db_path
        )

    def get(
        self, session_id: str, tenant: TenantConfig | None = None
    ) -> DemoRepository | LiveRepository:
        """Return existing repository or create tenant-appropriate session state."""

        active = tenant or TENANTS["research-clinic"]
        key = f"{active.id}::{session_id}"
        with self._lock:
            current = monotonic()
            expired = [
                item
                for item, (_, touched) in self._items.items()
                if current - touched > self._ttl_seconds
            ]
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

    def find(
        self, session_id: str, asset_id: str | None = None
    ) -> DemoRepository | LiveRepository | None:
        """Find existing session without creating state for invalid capability URLs.

        When asset_id is given, prefer the repository that actually holds the
        asset: two tenants can share one browser session id, and header-less
        capability URLs (image tags) cannot say which tenant they meant.
        """

        suffix = f"::{session_id}"
        with self._lock:
            current = monotonic()
            fallback: DemoRepository | LiveRepository | None = None
            # Most-recently-used entries sit at the end of the OrderedDict, so
            # scan in reverse to prefer the tenant the caller last touched.
            for key in [
                item for item in reversed(self._items) if item.endswith(suffix)
            ]:
                repository, touched = self._items[key]
                if current - touched > self._ttl_seconds:
                    self._items.pop(key, None)
                    continue
                if asset_id is None:
                    return repository
                if (
                    asset_id in repository.asset_contents
                    or asset_id in repository.source_assets
                    or asset_id in repository.uploads
                ):
                    return repository
                fallback = fallback or repository
            return fallback
            return None
