"""Deterministic mock data for the Clinical AI Command Center.

Provides fixture data for all clinical tools so the agent demo works
without real GCS, Firestore, BigQuery, or Vertex AI backends. Every
tool in tools.py reads from these fixtures. Data matches the frontend
prototype patients (PT-8829, PT-1044, PT-5510, PT-9921).

Design decisions:
- All data is deterministic (no randomness) so adk eval can validate
  tool trajectories against known outputs.
- GCS URIs follow gs://clinical-data/{patient_id}/... convention.
- Vector chunks include pre-computed relevance scores for search tools.
- Timestamps use ISO 8601 strings for JSON serialization.

To replace with real backends, swap the lookup functions in this module
with actual GCS/Firestore/BigQuery/Vertex AI client calls.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Patient records (Firestore documents)
# ---------------------------------------------------------------------------

PATIENTS: dict[str, dict[str, Any]] = {
    "PT-8829": {
        "patient_id": "PT-8829",
        "name": "Jonathan Doe",
        "age": 62,
        "sex": "Male",
        "risk_level": "high",
        "primary_diagnosis": "Non-small cell lung cancer (NSCLC)",
        "diagnosis_codes": ["C34.1", "C78.7"],
        "assigned_clinician": "Dr. Sarah Chen",
        "last_session_date": "2026-06-15",
        "data_completeness_score": 0.92,
        "open_tasks": 2,
        "ai_review_status": "needs_review",
        "demographics": {
            "dob": "1964-03-12",
            "mrn": "MRN-882901",
            "insurance": "Medicare Part B",
            "primary_language": "English",
            "emergency_contact": "Jane Doe (spouse)",
        },
        "diagnoses": [
            {"code": "C34.1", "description": "NSCLC, right upper lobe", "date": "2025-11-10", "status": "active"},
            {"code": "C78.7", "description": "Hepatic metastases", "date": "2026-01-22", "status": "active"},
            {"code": "J44.1", "description": "COPD with acute exacerbation", "date": "2024-08-15", "status": "resolved"},
        ],
        "medications": [
            {"name": "Pembrolizumab", "dose": "200mg IV q3w", "status": "active"},
            {"name": "Carboplatin", "dose": "AUC 5 IV q3w", "status": "active"},
            {"name": "Ondansetron", "dose": "8mg PRN", "status": "active"},
            {"name": "Albuterol", "dose": "90mcg INH PRN", "status": "active"},
        ],
        "allergies": ["Sulfonamides", "Iodine contrast (mild)"],
        "care_team": ["Dr. Sarah Chen (Oncology)", "Dr. James Park (Pulmonology)", "RN Lisa Wong"],
    },
    "PT-1044": {
        "patient_id": "PT-1044",
        "name": "Sarah Smith",
        "age": 45,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Type 2 Diabetes Mellitus with complications",
        "diagnosis_codes": ["E11.65", "I10"],
        "assigned_clinician": "Dr. Michael Torres",
        "last_session_date": "2026-06-12",
        "data_completeness_score": 0.78,
        "open_tasks": 3,
        "ai_review_status": "needs_review",
        "demographics": {
            "dob": "1981-07-22",
            "mrn": "MRN-104401",
            "insurance": "Aetna PPO",
            "primary_language": "English",
            "emergency_contact": "Robert Smith (brother)",
        },
        "diagnoses": [
            {"code": "E11.65", "description": "T2DM with hyperglycemia", "date": "2022-03-10", "status": "active"},
            {"code": "I10", "description": "Essential hypertension", "date": "2023-01-15", "status": "active"},
            {"code": "E78.5", "description": "Hyperlipidemia", "date": "2023-06-20", "status": "active"},
        ],
        "medications": [
            {"name": "Metformin", "dose": "1000mg BID", "status": "active"},
            {"name": "Lisinopril", "dose": "20mg daily", "status": "active"},
            {"name": "Atorvastatin", "dose": "40mg daily", "status": "active"},
            {"name": "Glipizide", "dose": "5mg BID", "status": "active"},
        ],
        "allergies": ["Penicillin"],
        "care_team": ["Dr. Michael Torres (Endocrinology)", "RN David Kim"],
    },
    "PT-5510": {
        "patient_id": "PT-5510",
        "name": "Wei Chen",
        "age": 38,
        "sex": "Male",
        "risk_level": "stable",
        "primary_diagnosis": "Major depressive disorder, recurrent",
        "diagnosis_codes": ["F33.1"],
        "assigned_clinician": "Dr. Emily Nakamura",
        "last_session_date": "2026-06-18",
        "data_completeness_score": 0.95,
        "open_tasks": 0,
        "ai_review_status": "verified",
        "demographics": {
            "dob": "1988-11-05",
            "mrn": "MRN-551002",
            "insurance": "Blue Cross Blue Shield",
            "primary_language": "English",
            "emergency_contact": "Lin Chen (mother)",
        },
        "diagnoses": [
            {"code": "F33.1", "description": "MDD, recurrent, moderate", "date": "2024-02-10", "status": "active"},
            {"code": "F41.1", "description": "Generalized anxiety disorder", "date": "2024-02-10", "status": "active"},
        ],
        "medications": [
            {"name": "Sertraline", "dose": "100mg daily", "status": "active"},
            {"name": "Buspirone", "dose": "10mg BID", "status": "active"},
        ],
        "allergies": [],
        "care_team": ["Dr. Emily Nakamura (Psychiatry)", "LCSW Maria Rodriguez"],
    },
    "PT-9921": {
        "patient_id": "PT-9921",
        "name": "Maria Garcia",
        "age": 71,
        "sex": "Female",
        "risk_level": "needs_review",
        "primary_diagnosis": "Congestive heart failure",
        "diagnosis_codes": ["I50.9", "I48.0"],
        "assigned_clinician": "Dr. Sarah Chen",
        "last_session_date": "2026-06-10",
        "data_completeness_score": 0.65,
        "open_tasks": 4,
        "ai_review_status": "needs_review",
        "demographics": {
            "dob": "1955-04-18",
            "mrn": "MRN-992103",
            "insurance": "Medicare Advantage",
            "primary_language": "Spanish",
            "emergency_contact": "Carlos Garcia (son)",
        },
        "diagnoses": [
            {"code": "I50.9", "description": "Heart failure, unspecified", "date": "2025-08-20", "status": "active"},
            {"code": "I48.0", "description": "Atrial fibrillation, paroxysmal", "date": "2025-09-10", "status": "active"},
            {"code": "N18.3", "description": "CKD stage 3", "date": "2025-10-05", "status": "active"},
        ],
        "medications": [
            {"name": "Furosemide", "dose": "40mg daily", "status": "active"},
            {"name": "Carvedilol", "dose": "12.5mg BID", "status": "active"},
            {"name": "Apixaban", "dose": "5mg BID", "status": "active"},
            {"name": "Sacubitril/Valsartan", "dose": "49/51mg BID", "status": "active"},
        ],
        "allergies": ["ACE inhibitors (cough)", "Aspirin (GI bleed)"],
        "care_team": ["Dr. Sarah Chen (Cardiology)", "Dr. Raj Patel (Nephrology)", "RN Lisa Wong"],
    },
}


# ---------------------------------------------------------------------------
# Imaging sessions (extraction pipeline input/output)
# ---------------------------------------------------------------------------

SESSIONS: dict[str, list[dict[str, Any]]] = {
    "PT-8829": [
        {
            "session_id": "SES-8829-003",
            "patient_id": "PT-8829",
            "date": "2026-06-15",
            "uploaded_image_count": 2,
            "images": [
                {
                    "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-chest-axial.png",
                    "modality": "CT",
                    "body_region": "Chest",
                    "description": "CT chest axial, lung window",
                },
                {
                    "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-abdomen-portal.png",
                    "modality": "CT",
                    "body_region": "Abdomen",
                    "description": "CT abdomen portal venous phase",
                },
            ],
            "extraction_confidence": 0.87,
            "clinician_verification_status": "pending",
            "json_sync_status": "synced",
            "relational_sync_status": "synced",
            "vector_sync_status": "synced",
            "audit_status": "logged",
            "extracted_fields": [
                {"field_name": "primary_tumor_size", "value": "4.2cm", "confidence": 0.91, "ontology_code": "SNOMED:399417005"},
                {"field_name": "tumor_location", "value": "Right upper lobe", "confidence": 0.95, "ontology_code": "SNOMED:44029006"},
                {"field_name": "lymph_node_status", "value": "Mediastinal lymphadenopathy, 2.1cm", "confidence": 0.82, "ontology_code": "SNOMED:274744008"},
                {"field_name": "hepatic_lesion_count", "value": "3", "confidence": 0.88, "ontology_code": "SNOMED:126851005"},
                {"field_name": "largest_hepatic_lesion", "value": "3.5cm", "confidence": 0.85, "ontology_code": "SNOMED:126851005"},
                {"field_name": "pleural_effusion", "value": "Small, right-sided", "confidence": 0.93, "ontology_code": "SNOMED:60046008"},
            ],
        },
        {
            "session_id": "SES-8829-002",
            "patient_id": "PT-8829",
            "date": "2026-04-10",
            "uploaded_image_count": 2,
            "images": [
                {
                    "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-002/ct-chest-axial.png",
                    "modality": "CT",
                    "body_region": "Chest",
                    "description": "CT chest axial, lung window",
                },
                {
                    "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-002/ct-abdomen-portal.png",
                    "modality": "CT",
                    "body_region": "Abdomen",
                    "description": "CT abdomen portal venous phase",
                },
            ],
            "extraction_confidence": 0.90,
            "clinician_verification_status": "verified",
            "json_sync_status": "synced",
            "relational_sync_status": "synced",
            "vector_sync_status": "synced",
            "audit_status": "logged",
            "extracted_fields": [
                {"field_name": "primary_tumor_size", "value": "3.8cm", "confidence": 0.93, "ontology_code": "SNOMED:399417005"},
                {"field_name": "tumor_location", "value": "Right upper lobe", "confidence": 0.96, "ontology_code": "SNOMED:44029006"},
                {"field_name": "lymph_node_status", "value": "Mediastinal lymphadenopathy, 1.8cm", "confidence": 0.85, "ontology_code": "SNOMED:274744008"},
                {"field_name": "hepatic_lesion_count", "value": "2", "confidence": 0.90, "ontology_code": "SNOMED:126851005"},
                {"field_name": "largest_hepatic_lesion", "value": "2.3cm", "confidence": 0.88, "ontology_code": "SNOMED:126851005"},
                {"field_name": "pleural_effusion", "value": "Trace, right-sided", "confidence": 0.94, "ontology_code": "SNOMED:60046008"},
            ],
        },
        {
            "session_id": "SES-8829-001",
            "patient_id": "PT-8829",
            "date": "2026-01-22",
            "uploaded_image_count": 1,
            "images": [
                {
                    "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-001/ct-chest-axial.png",
                    "modality": "CT",
                    "body_region": "Chest",
                    "description": "CT chest axial, initial staging",
                },
            ],
            "extraction_confidence": 0.92,
            "clinician_verification_status": "verified",
            "json_sync_status": "synced",
            "relational_sync_status": "synced",
            "vector_sync_status": "synced",
            "audit_status": "logged",
            "extracted_fields": [
                {"field_name": "primary_tumor_size", "value": "3.2cm", "confidence": 0.94, "ontology_code": "SNOMED:399417005"},
                {"field_name": "tumor_location", "value": "Right upper lobe", "confidence": 0.97, "ontology_code": "SNOMED:44029006"},
                {"field_name": "lymph_node_status", "value": "No significant lymphadenopathy", "confidence": 0.91, "ontology_code": "SNOMED:274744008"},
                {"field_name": "hepatic_lesion_count", "value": "0", "confidence": 0.96, "ontology_code": "SNOMED:126851005"},
                {"field_name": "pleural_effusion", "value": "None", "confidence": 0.98, "ontology_code": "SNOMED:60046008"},
            ],
        },
    ],
    "PT-1044": [
        {
            "session_id": "SES-1044-001",
            "patient_id": "PT-1044",
            "date": "2026-06-12",
            "uploaded_image_count": 1,
            "images": [
                {
                    "gcs_uri": "gs://clinical-data/PT-1044/sessions/SES-1044-001/fundoscopy-right.png",
                    "modality": "Fundoscopy",
                    "body_region": "Eye",
                    "description": "Right eye fundoscopy, diabetic screening",
                },
            ],
            "extraction_confidence": 0.72,
            "clinician_verification_status": "pending",
            "json_sync_status": "synced",
            "relational_sync_status": "pending",
            "vector_sync_status": "pending",
            "audit_status": "logged",
            "extracted_fields": [
                {"field_name": "retinopathy_grade", "value": "Moderate NPDR", "confidence": 0.74, "ontology_code": "SNOMED:390834004"},
                {"field_name": "macular_edema", "value": "Possible", "confidence": 0.65, "ontology_code": "SNOMED:37231002"},
                {"field_name": "hemorrhage_count", "value": "Multiple dot-blot", "confidence": 0.78, "ontology_code": "SNOMED:78144005"},
                {"field_name": "hard_exudates", "value": "Present, perifoveal", "confidence": 0.70, "ontology_code": "SNOMED:247099008"},
            ],
        },
    ],
    "PT-5510": [
        {
            "session_id": "SES-5510-001",
            "patient_id": "PT-5510",
            "date": "2026-06-18",
            "uploaded_image_count": 1,
            "images": [
                {
                    "gcs_uri": "gs://clinical-data/PT-5510/sessions/SES-5510-001/phq9-screenshot.png",
                    "modality": "Document",
                    "body_region": "N/A",
                    "description": "PHQ-9 questionnaire screenshot",
                },
            ],
            "extraction_confidence": 0.94,
            "clinician_verification_status": "verified",
            "json_sync_status": "synced",
            "relational_sync_status": "synced",
            "vector_sync_status": "synced",
            "audit_status": "logged",
            "extracted_fields": [
                {"field_name": "phq9_total_score", "value": "8", "confidence": 0.96, "ontology_code": "LOINC:44261-6"},
                {"field_name": "severity_category", "value": "Mild depression", "confidence": 0.95, "ontology_code": "LOINC:44261-6"},
                {"field_name": "suicidal_ideation_item", "value": "0 - Not at all", "confidence": 0.98, "ontology_code": "LOINC:44260-8"},
                {"field_name": "functional_impairment", "value": "Somewhat difficult", "confidence": 0.93, "ontology_code": "LOINC:69722-7"},
            ],
        },
    ],
    "PT-9921": [
        {
            "session_id": "SES-9921-001",
            "patient_id": "PT-9921",
            "date": "2026-06-10",
            "uploaded_image_count": 1,
            "images": [
                {
                    "gcs_uri": "gs://clinical-data/PT-9921/sessions/SES-9921-001/chest-xr-pa.png",
                    "modality": "X-Ray",
                    "body_region": "Chest",
                    "description": "Chest X-ray PA view",
                },
            ],
            "extraction_confidence": 0.79,
            "clinician_verification_status": "pending",
            "json_sync_status": "synced",
            "relational_sync_status": "pending",
            "vector_sync_status": "pending",
            "audit_status": "logged",
            "extracted_fields": [
                {"field_name": "cardiac_silhouette", "value": "Enlarged, CTR 0.62", "confidence": 0.88, "ontology_code": "SNOMED:24484000"},
                {"field_name": "pulmonary_edema", "value": "Mild interstitial", "confidence": 0.76, "ontology_code": "SNOMED:19242006"},
                {"field_name": "pleural_effusion", "value": "Bilateral, small", "confidence": 0.82, "ontology_code": "SNOMED:60046008"},
                {"field_name": "lung_fields", "value": "Vascular cephalization", "confidence": 0.71, "ontology_code": "SNOMED:274744008"},
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# Clinical notes (Vertex AI Vector Search — text embeddings)
# ---------------------------------------------------------------------------

CLINICAL_NOTES: dict[str, list[dict[str, Any]]] = {
    "PT-8829": [
        {
            "note_id": "NOTE-8829-005",
            "date": "2026-06-15",
            "author": "Dr. Sarah Chen",
            "type": "Oncology Progress Note",
            "text": (
                "Patient presents for cycle 4 pembrolizumab/carboplatin. CT chest/abdomen shows "
                "interval increase in right upper lobe mass from 3.8cm to 4.2cm. New hepatic "
                "lesion identified (total now 3, largest 3.5cm vs prior 2.3cm). Small right "
                "pleural effusion stable. Assessment: disease progression on current regimen. "
                "Plan: complete current cycle, discuss switch to docetaxel + ramucirumab at "
                "next tumor board. Refer to interventional radiology for hepatic lesion biopsy."
            ),
            "vector_chunk_id": "VEC-8829-005-001",
        },
        {
            "note_id": "NOTE-8829-004",
            "date": "2026-04-10",
            "author": "Dr. Sarah Chen",
            "type": "Oncology Progress Note",
            "text": (
                "Cycle 2 restaging CT shows slight increase in primary tumor 3.8cm (prior 3.2cm). "
                "Two hepatic lesions identified, largest 2.3cm. Mediastinal lymphadenopathy "
                "1.8cm. Assessment: mixed response. Plan: continue pembrolizumab/carboplatin "
                "for 2 more cycles then reassess. Monitor hepatic lesions closely."
            ),
            "vector_chunk_id": "VEC-8829-004-001",
        },
        {
            "note_id": "NOTE-8829-003",
            "date": "2026-01-22",
            "author": "Dr. Sarah Chen",
            "type": "Oncology Initial Consult",
            "text": (
                "62yo male referred for newly diagnosed NSCLC, right upper lobe, 3.2cm. "
                "Biopsy confirmed adenocarcinoma, PD-L1 TPS 60%. No distant metastases on "
                "initial staging. ECOG PS 1. Plan: initiate pembrolizumab + carboplatin + "
                "pemetrexed per KEYNOTE-189. Baseline labs within normal limits except mild "
                "anemia (Hgb 11.2)."
            ),
            "vector_chunk_id": "VEC-8829-003-001",
        },
        {
            "note_id": "NOTE-8829-002",
            "date": "2025-12-15",
            "author": "Dr. James Park",
            "type": "Pulmonology Consult",
            "text": (
                "Patient referred for persistent cough and hemoptysis. Spirometry shows "
                "moderate obstruction (FEV1 62% predicted). CT chest reveals 3.2cm right "
                "upper lobe mass. Recommend tissue biopsy. COPD management optimized — "
                "continue albuterol PRN, add tiotropium."
            ),
            "vector_chunk_id": "VEC-8829-002-001",
        },
    ],
    "PT-1044": [
        {
            "note_id": "NOTE-1044-002",
            "date": "2026-06-12",
            "author": "Dr. Michael Torres",
            "type": "Endocrinology Progress Note",
            "text": (
                "HbA1c 8.2% (prior 7.8%). Fundoscopy shows moderate NPDR with possible "
                "macular edema — referral to ophthalmology. Medication history conflict: "
                "patient reports taking metformin 500mg BID but records show 1000mg BID "
                "prescribed. Possible non-adherence. Plan: clarify dosing, consider adding "
                "semaglutide if HbA1c not improved in 3 months."
            ),
            "vector_chunk_id": "VEC-1044-002-001",
        },
        {
            "note_id": "NOTE-1044-001",
            "date": "2026-03-15",
            "author": "Dr. Michael Torres",
            "type": "Endocrinology Progress Note",
            "text": (
                "HbA1c 7.8%, improved from 8.5%. Blood pressure well controlled on "
                "lisinopril. Lipid panel: LDL 98 on atorvastatin. Foot exam unremarkable. "
                "Continue current regimen. Annual diabetic screening due in June."
            ),
            "vector_chunk_id": "VEC-1044-001-001",
        },
    ],
    "PT-5510": [
        {
            "note_id": "NOTE-5510-002",
            "date": "2026-06-18",
            "author": "Dr. Emily Nakamura",
            "type": "Psychiatry Progress Note",
            "text": (
                "PHQ-9 score 8 (mild), improved from 14 (moderate) at last visit. "
                "Patient reports improved sleep, reduced anhedonia. Continuing sertraline "
                "100mg. GAD-7 score 6 (mild anxiety). No suicidal ideation. Therapy "
                "sessions with LCSW Rodriguez going well. Plan: maintain current medications, "
                "follow up in 8 weeks."
            ),
            "vector_chunk_id": "VEC-5510-002-001",
        },
    ],
    "PT-9921": [
        {
            "note_id": "NOTE-9921-002",
            "date": "2026-06-10",
            "author": "Dr. Sarah Chen",
            "type": "Cardiology Progress Note",
            "text": (
                "71yo female with CHF (EF 35%) and paroxysmal AFib. Chest X-ray shows "
                "enlarged cardiac silhouette, mild interstitial edema, bilateral small "
                "pleural effusions. Weight up 3kg from last visit. BNP elevated at 890. "
                "Assessment: CHF exacerbation, likely volume overload. Plan: increase "
                "furosemide to 80mg daily, restrict fluids to 1.5L/day, recheck in 1 week. "
                "If no improvement, consider IV diuretics."
            ),
            "vector_chunk_id": "VEC-9921-002-001",
        },
        {
            "note_id": "NOTE-9921-001",
            "date": "2026-05-01",
            "author": "Dr. Raj Patel",
            "type": "Nephrology Consult",
            "text": (
                "CKD stage 3 (eGFR 42). Likely cardiorenal etiology. Creatinine 1.6, "
                "stable. Urine albumin/creatinine ratio 180mg/g (A2 stage). Electrolytes "
                "stable. Recommend continuing sacubitril/valsartan at current dose. "
                "Avoid NSAIDs and nephrotoxins. Recheck renal panel in 3 months."
            ),
            "vector_chunk_id": "VEC-9921-001-001",
        },
    ],
}


# ---------------------------------------------------------------------------
# Lab results (Cloud SQL / BigQuery rows)
# ---------------------------------------------------------------------------

LAB_RESULTS: dict[str, list[dict[str, Any]]] = {
    "PT-8829": [
        {"date": "2026-06-14", "test": "CBC", "component": "Hemoglobin", "value": "10.8", "unit": "g/dL", "reference_range": "13.5-17.5", "flag": "low"},
        {"date": "2026-06-14", "test": "CBC", "component": "WBC", "value": "3.2", "unit": "K/uL", "reference_range": "4.5-11.0", "flag": "low"},
        {"date": "2026-06-14", "test": "CBC", "component": "Platelets", "value": "145", "unit": "K/uL", "reference_range": "150-400", "flag": "low"},
        {"date": "2026-06-14", "test": "CMP", "component": "ALT", "value": "52", "unit": "U/L", "reference_range": "7-56", "flag": "normal"},
        {"date": "2026-06-14", "test": "CMP", "component": "AST", "value": "68", "unit": "U/L", "reference_range": "10-40", "flag": "high"},
        {"date": "2026-06-14", "test": "Tumor Marker", "component": "CEA", "value": "12.4", "unit": "ng/mL", "reference_range": "<3.0", "flag": "high"},
    ],
    "PT-1044": [
        {"date": "2026-06-10", "test": "HbA1c", "component": "HbA1c", "value": "8.2", "unit": "%", "reference_range": "<7.0", "flag": "high"},
        {"date": "2026-06-10", "test": "Lipid Panel", "component": "LDL", "value": "102", "unit": "mg/dL", "reference_range": "<100", "flag": "high"},
        {"date": "2026-06-10", "test": "CMP", "component": "Creatinine", "value": "0.9", "unit": "mg/dL", "reference_range": "0.6-1.2", "flag": "normal"},
        {"date": "2026-06-10", "test": "CMP", "component": "eGFR", "value": "82", "unit": "mL/min", "reference_range": ">60", "flag": "normal"},
    ],
    "PT-5510": [
        {"date": "2026-06-15", "test": "TSH", "component": "TSH", "value": "2.1", "unit": "mIU/L", "reference_range": "0.4-4.0", "flag": "normal"},
        {"date": "2026-06-15", "test": "CBC", "component": "Hemoglobin", "value": "14.5", "unit": "g/dL", "reference_range": "13.5-17.5", "flag": "normal"},
    ],
    "PT-9921": [
        {"date": "2026-06-09", "test": "BNP", "component": "BNP", "value": "890", "unit": "pg/mL", "reference_range": "<100", "flag": "high"},
        {"date": "2026-06-09", "test": "CMP", "component": "Creatinine", "value": "1.6", "unit": "mg/dL", "reference_range": "0.6-1.2", "flag": "high"},
        {"date": "2026-06-09", "test": "CMP", "component": "eGFR", "value": "42", "unit": "mL/min", "reference_range": ">60", "flag": "low"},
        {"date": "2026-06-09", "test": "CMP", "component": "Potassium", "value": "5.1", "unit": "mEq/L", "reference_range": "3.5-5.0", "flag": "high"},
        {"date": "2026-06-09", "test": "CMP", "component": "Sodium", "value": "132", "unit": "mEq/L", "reference_range": "136-145", "flag": "low"},
    ],
}


# ---------------------------------------------------------------------------
# Vector search chunks (Vertex AI Vector Search — pre-scored for mock search)
# ---------------------------------------------------------------------------

VECTOR_CHUNKS: list[dict[str, Any]] = [
    # PT-8829 text chunks
    {"chunk_id": "VEC-8829-005-001", "patient_id": "PT-8829", "source_type": "text", "source_id": "NOTE-8829-005",
     "date": "2026-06-15", "text": "CT shows interval increase RUL mass 3.8cm to 4.2cm. New hepatic lesion, total 3, largest 3.5cm. Disease progression on pembrolizumab/carboplatin.",
     "keywords": ["tumor progression", "hepatic lesion", "CT findings", "NSCLC"]},
    {"chunk_id": "VEC-8829-004-001", "patient_id": "PT-8829", "source_type": "text", "source_id": "NOTE-8829-004",
     "date": "2026-04-10", "text": "Restaging CT slight increase primary tumor 3.8cm. Two hepatic lesions, largest 2.3cm. Mixed response. Continue treatment.",
     "keywords": ["restaging", "hepatic lesion", "mixed response"]},
    {"chunk_id": "VEC-8829-003-001", "patient_id": "PT-8829", "source_type": "text", "source_id": "NOTE-8829-003",
     "date": "2026-01-22", "text": "Newly diagnosed NSCLC RUL 3.2cm. Adenocarcinoma PD-L1 60%. No distant metastases. Initiated pembrolizumab/carboplatin.",
     "keywords": ["initial staging", "NSCLC diagnosis", "treatment initiation"]},
    # PT-8829 image chunks
    {"chunk_id": "VEC-8829-IMG-003", "patient_id": "PT-8829", "source_type": "image", "source_id": "SES-8829-003",
     "date": "2026-06-15", "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-abdomen-portal.png",
     "text": "CT abdomen portal venous phase showing 3 hepatic lesions, largest 3.5cm in right lobe segment VII.",
     "keywords": ["hepatic lesion", "CT abdomen", "liver metastasis"]},
    {"chunk_id": "VEC-8829-IMG-002", "patient_id": "PT-8829", "source_type": "image", "source_id": "SES-8829-002",
     "date": "2026-04-10", "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-002/ct-abdomen-portal.png",
     "text": "CT abdomen portal venous phase showing 2 hepatic lesions, largest 2.3cm in right lobe segment VII.",
     "keywords": ["hepatic lesion", "CT abdomen", "liver metastasis"]},
    {"chunk_id": "VEC-8829-IMG-001", "patient_id": "PT-8829", "source_type": "image", "source_id": "SES-8829-001",
     "date": "2026-01-22", "gcs_uri": "gs://clinical-data/PT-8829/sessions/SES-8829-001/ct-chest-axial.png",
     "text": "CT chest axial initial staging. 3.2cm RUL mass. No mediastinal lymphadenopathy. No hepatic lesions.",
     "keywords": ["initial staging", "CT chest", "baseline"]},
    # PT-1044 chunks
    {"chunk_id": "VEC-1044-002-001", "patient_id": "PT-1044", "source_type": "text", "source_id": "NOTE-1044-002",
     "date": "2026-06-12", "text": "HbA1c 8.2% worsened. Moderate NPDR on fundoscopy. Medication conflict identified: patient reports 500mg vs prescribed 1000mg metformin.",
     "keywords": ["diabetes", "retinopathy", "medication adherence", "HbA1c"]},
    {"chunk_id": "VEC-1044-IMG-001", "patient_id": "PT-1044", "source_type": "image", "source_id": "SES-1044-001",
     "date": "2026-06-12", "gcs_uri": "gs://clinical-data/PT-1044/sessions/SES-1044-001/fundoscopy-right.png",
     "text": "Right eye fundoscopy showing moderate NPDR: multiple dot-blot hemorrhages, hard exudates perifoveal, possible macular edema.",
     "keywords": ["diabetic retinopathy", "fundoscopy", "NPDR", "macular edema"]},
    # PT-9921 chunks
    {"chunk_id": "VEC-9921-002-001", "patient_id": "PT-9921", "source_type": "text", "source_id": "NOTE-9921-002",
     "date": "2026-06-10", "text": "CHF exacerbation, EF 35%. CXR enlarged heart, bilateral effusions. BNP 890. Weight up 3kg. Increase furosemide.",
     "keywords": ["heart failure", "CHF exacerbation", "volume overload", "BNP"]},
    {"chunk_id": "VEC-9921-IMG-001", "patient_id": "PT-9921", "source_type": "image", "source_id": "SES-9921-001",
     "date": "2026-06-10", "gcs_uri": "gs://clinical-data/PT-9921/sessions/SES-9921-001/chest-xr-pa.png",
     "text": "Chest X-ray PA: enlarged cardiac silhouette CTR 0.62, vascular cephalization, mild interstitial edema, bilateral small pleural effusions.",
     "keywords": ["heart failure", "cardiomegaly", "pulmonary edema", "pleural effusion"]},
]


# ---------------------------------------------------------------------------
# Audit events (Cloud Logging)
# ---------------------------------------------------------------------------

AUDIT_EVENTS: list[dict[str, Any]] = [
    {"timestamp": "2026-06-15T14:32:00Z", "agent_name": "image_extraction_pipeline", "action": "extraction_complete", "patient_id": "PT-8829", "session_id": "SES-8829-003", "details": {"fields_extracted": 6, "avg_confidence": 0.87, "needs_review": True}, "user_role": "clinician"},
    {"timestamp": "2026-06-15T14:30:00Z", "agent_name": "vision_analyzer_agent", "action": "image_analyzed", "patient_id": "PT-8829", "session_id": "SES-8829-003", "details": {"images_processed": 2, "modality": "CT"}, "user_role": "system"},
    {"timestamp": "2026-06-15T14:28:00Z", "agent_name": "quality_assessor_agent", "action": "quality_check_passed", "patient_id": "PT-8829", "session_id": "SES-8829-003", "details": {"resolution": "512x512", "quality_score": 0.91}, "user_role": "system"},
    {"timestamp": "2026-06-12T10:15:00Z", "agent_name": "image_extraction_pipeline", "action": "extraction_complete", "patient_id": "PT-1044", "session_id": "SES-1044-001", "details": {"fields_extracted": 4, "avg_confidence": 0.72, "needs_review": True}, "user_role": "clinician"},
    {"timestamp": "2026-06-18T09:45:00Z", "agent_name": "image_extraction_pipeline", "action": "extraction_verified", "patient_id": "PT-5510", "session_id": "SES-5510-001", "details": {"fields_extracted": 4, "avg_confidence": 0.94, "verified_by": "Dr. Emily Nakamura"}, "user_role": "clinician"},
    {"timestamp": "2026-06-10T16:20:00Z", "agent_name": "patient_qa_pipeline", "action": "question_answered", "patient_id": "PT-9921", "details": {"question_type": "clinical_status", "sources_used": 3, "confidence": 0.85}, "user_role": "clinician"},
    {"timestamp": "2026-06-10T11:30:00Z", "agent_name": "db_intelligence_pipeline", "action": "query_executed", "patient_id": None, "details": {"question": "How many high-risk patients this month?", "rows_returned": 12, "chart_generated": True}, "user_role": "admin"},
]


# ---------------------------------------------------------------------------
# Image quality metadata (GCS metadata)
# ---------------------------------------------------------------------------

IMAGE_QUALITY_DB: dict[str, dict[str, Any]] = {
    "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-chest-axial.png": {
        "resolution": "512x512",
        "bit_depth": 16,
        "modality": "CT",
        "contrast": "adequate",
        "artifacts": "none",
        "dicom_compliant": True,
        "quality_score": 0.93,
        "file_size_kb": 2048,
    },
    "gs://clinical-data/PT-8829/sessions/SES-8829-003/ct-abdomen-portal.png": {
        "resolution": "512x512",
        "bit_depth": 16,
        "modality": "CT",
        "contrast": "adequate",
        "artifacts": "none",
        "dicom_compliant": True,
        "quality_score": 0.91,
        "file_size_kb": 2150,
    },
    "gs://clinical-data/PT-8829/sessions/SES-8829-002/ct-chest-axial.png": {
        "resolution": "512x512",
        "bit_depth": 16,
        "modality": "CT",
        "contrast": "adequate",
        "artifacts": "none",
        "dicom_compliant": True,
        "quality_score": 0.92,
        "file_size_kb": 1980,
    },
    "gs://clinical-data/PT-8829/sessions/SES-8829-002/ct-abdomen-portal.png": {
        "resolution": "512x512",
        "bit_depth": 16,
        "modality": "CT",
        "contrast": "adequate",
        "artifacts": "none",
        "dicom_compliant": True,
        "quality_score": 0.90,
        "file_size_kb": 2100,
    },
    "gs://clinical-data/PT-1044/sessions/SES-1044-001/fundoscopy-right.png": {
        "resolution": "1024x1024",
        "bit_depth": 8,
        "modality": "Fundoscopy",
        "contrast": "adequate",
        "artifacts": "mild_reflection",
        "dicom_compliant": False,
        "quality_score": 0.78,
        "file_size_kb": 850,
    },
    "gs://clinical-data/PT-5510/sessions/SES-5510-001/phq9-screenshot.png": {
        "resolution": "1920x1080",
        "bit_depth": 8,
        "modality": "Document",
        "contrast": "high",
        "artifacts": "none",
        "dicom_compliant": False,
        "quality_score": 0.95,
        "file_size_kb": 320,
    },
    "gs://clinical-data/PT-9921/sessions/SES-9921-001/chest-xr-pa.png": {
        "resolution": "2048x2048",
        "bit_depth": 12,
        "modality": "X-Ray",
        "contrast": "adequate",
        "artifacts": "none",
        "dicom_compliant": True,
        "quality_score": 0.88,
        "file_size_kb": 1500,
    },
}


# ---------------------------------------------------------------------------
# Lookup helpers (replace these with real service clients)
# ---------------------------------------------------------------------------

def get_patient(patient_id: str) -> dict[str, Any] | None:
    """Retrieve a patient record by ID from SQLite."""
    from .database import execute_sql
    res = execute_sql(f"SELECT * FROM patients_core WHERE patient_id = '{patient_id}'")
    if res["rows"]:
        pt = dict(res["rows"][0])
        # Include full mock data dict to keep tool contracts satisfied (like demographics)
        full = PATIENTS.get(patient_id, pt).copy()
        full.update(pt)
        return full
    return None


def get_all_patients() -> list[dict[str, Any]]:
    """List all patients from SQLite."""
    from .database import execute_sql
    res = execute_sql("SELECT * FROM patients_core")
    pts = []
    for row in res["rows"]:
        pt = dict(row)
        full = PATIENTS.get(pt["patient_id"], pt).copy()
        full.update(pt)
        pts.append(full)
    return pts


def get_sessions(patient_id: str) -> list[dict[str, Any]]:
    """Get extraction sessions for a patient from SQLite."""
    from .database import execute_sql
    res = execute_sql(f"SELECT * FROM sessions WHERE patient_id = '{patient_id}'")
    return [dict(row) for row in res["rows"]]


def get_session(session_id: str) -> dict[str, Any] | None:
    """Get a specific session by ID from SQLite."""
    from .database import execute_sql
    res = execute_sql(f"SELECT * FROM sessions WHERE session_id = '{session_id}'")
    if res["rows"]:
        return dict(res["rows"][0])
    return None


def get_clinical_notes(patient_id: str) -> list[dict[str, Any]]:
    """Get clinical notes for a patient. (Mock: Firestore subcollection.)"""
    return CLINICAL_NOTES.get(patient_id, [])


def get_lab_results(patient_id: str) -> list[dict[str, Any]]:
    """Get lab results for a patient. (Mock: Cloud SQL query.)"""
    return LAB_RESULTS.get(patient_id, [])


def get_image_quality(gcs_uri: str) -> dict[str, Any] | None:
    """Get image quality metadata. (Mock: GCS object metadata.)"""
    return IMAGE_QUALITY_DB.get(gcs_uri)


def search_vectors(patient_id: str, query_keywords: list[str],
                   source_types: list[str] | None = None,
                   max_results: int = 10) -> list[dict[str, Any]]:
    """Search vector store for relevant chunks. (Mock: Vertex AI Vector Search.)

    Simulates semantic search by keyword overlap scoring.
    """
    results = []
    for chunk in VECTOR_CHUNKS:
        if chunk["patient_id"] != patient_id:
            continue
        if source_types and chunk["source_type"] not in source_types:
            continue
        overlap = len(set(query_keywords) & set(chunk.get("keywords", [])))
        if overlap > 0:
            score = min(0.98, 0.60 + overlap * 0.12)
            results.append({**chunk, "relevance_score": round(score, 2)})

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:max_results]


def get_audit_events(patient_id: str | None = None,
                     limit: int = 20) -> list[dict[str, Any]]:
    """Get audit events, optionally filtered by patient. (Mock: Cloud Logging.)"""
    if patient_id:
        events = [e for e in AUDIT_EVENTS if e.get("patient_id") == patient_id]
    else:
        events = list(AUDIT_EVENTS)
    return events[:limit]
