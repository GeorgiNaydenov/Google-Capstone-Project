"""Shared clinically coherent synthetic cohort engine for all showcase generators.

Adapted from the enterprise healthcare seeder (BP-02 v1.1): patient risk
archetypes, mixed synthetic-PII / de-identified records, condition-biased lab
values, coherent longitudinal vitals, payer and SDoH context, and narrative
clinical notes.

Every patient is derived deterministically from ``(seed, prefix, index)`` so
the database, extraction, and multimodal generators can rebuild the exact same
patient independently. That is what links one tenant's SQL cohort, intake-form
images, and Q&A evidence bundles to the same human being.
"""

from __future__ import annotations

import hashlib
import random
import string
from datetime import date, datetime, timedelta
from typing import Any

# =============================================================================
# REFERENCE CATALOGS (ICD-10, CPT, medications, labs, vaccines, allergies)
# =============================================================================

SPECIALTIES = [
    ("Internal Medicine", "General Medicine"), ("Cardiology", "Cardiovascular"),
    ("Endocrinology", "Endocrinology"), ("Pulmonology", "Respiratory"),
    ("Nephrology", "Nephrology"), ("Gastroenterology", "GI"),
    ("Neurology", "Neurology"), ("Orthopedics", "Orthopedics"),
    ("Oncology", "Oncology"), ("Psychiatry", "Behavioral Health"),
    ("Rheumatology", "Rheumatology"), ("Hematology", "Hematology"),
    ("Family Medicine", "Primary Care"), ("Emergency Medicine", "Emergency"),
    ("Geriatrics", "Geriatrics"), ("Ophthalmology", "Ophthalmology"),
]

PROVIDER_TITLES = ["MD", "DO", "MD, PhD", "DO, FACP", "MD, FACC", "MD, FACG"]

# (code, description, category)
ICD10_CATALOG = [
    ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia", "Endocrine"),
    ("E11.40", "Type 2 diabetes mellitus with diabetic neuropathy", "Endocrine"),
    ("E10.9", "Type 1 diabetes mellitus without complications", "Endocrine"),
    ("E78.5", "Hyperlipidemia, unspecified", "Endocrine"),
    ("E03.9", "Hypothyroidism, unspecified", "Endocrine"),
    ("E66.9", "Obesity, unspecified", "Endocrine"),
    ("E55.9", "Vitamin D deficiency, unspecified", "Nutritional"),
    ("I10", "Essential (primary) hypertension", "Cardiovascular"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery", "Cardiovascular"),
    ("I50.9", "Heart failure, unspecified", "Cardiovascular"),
    ("I50.20", "Systolic (congestive) heart failure", "Cardiovascular"),
    ("I48.0", "Paroxysmal atrial fibrillation", "Cardiovascular"),
    ("I48.11", "Longstanding persistent atrial fibrillation", "Cardiovascular"),
    ("I21.9", "Acute myocardial infarction, unspecified", "Cardiovascular"),
    ("I63.9", "Cerebral infarction, unspecified", "Cardiovascular"),
    ("I73.9", "Peripheral vascular disease, unspecified", "Cardiovascular"),
    ("I11.9", "Hypertensive heart disease without heart failure", "Cardiovascular"),
    ("I13.10", "Hypertensive heart and chronic kidney disease", "Cardiovascular"),
    ("J44.1", "COPD with acute exacerbation", "Respiratory"),
    ("J44.9", "Chronic obstructive pulmonary disease, unspecified", "Respiratory"),
    ("J45.50", "Severe persistent asthma, uncomplicated", "Respiratory"),
    ("J45.20", "Mild intermittent asthma, uncomplicated", "Respiratory"),
    ("J18.9", "Pneumonia, unspecified organism", "Respiratory"),
    ("J30.9", "Allergic rhinitis, unspecified", "Respiratory"),
    ("G47.33", "Obstructive sleep apnea", "Respiratory"),
    ("J96.00", "Acute respiratory failure, unspecified", "Respiratory"),
    ("N18.3", "Chronic kidney disease, stage 3", "Renal"),
    ("N18.4", "Chronic kidney disease, stage 4", "Renal"),
    ("N18.5", "Chronic kidney disease, stage 5", "Renal"),
    ("N17.9", "Acute kidney failure, unspecified", "Renal"),
    ("N39.0", "Urinary tract infection, site not specified", "Urology"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis", "Gastrointestinal"),
    ("K57.30", "Diverticulosis of large intestine without perforation", "Gastrointestinal"),
    ("K76.0", "Fatty (change of) liver, not elsewhere classified", "Gastrointestinal"),
    ("K50.90", "Crohn's disease of small intestine without complications", "Gastrointestinal"),
    ("K51.90", "Ulcerative colitis, unspecified, without complications", "Gastrointestinal"),
    ("K70.30", "Alcoholic cirrhosis of liver", "Gastrointestinal"),
    ("M54.5", "Low back pain", "Musculoskeletal"),
    ("M17.11", "Primary osteoarthritis, right knee", "Musculoskeletal"),
    ("M81.0", "Age-related osteoporosis without current pathological fracture", "Musculoskeletal"),
    ("M06.9", "Rheumatoid arthritis, unspecified", "Musculoskeletal"),
    ("M10.9", "Gout, unspecified", "Musculoskeletal"),
    ("M48.06", "Spinal stenosis, lumbar region", "Musculoskeletal"),
    ("M25.511", "Pain in right shoulder", "Musculoskeletal"),
    ("G43.909", "Migraine, unspecified, not intractable", "Neurological"),
    ("G20", "Parkinson's disease", "Neurological"),
    ("G30.9", "Alzheimer's disease, unspecified", "Neurological"),
    ("G40.909", "Epilepsy, unspecified, not intractable", "Neurological"),
    ("G62.9", "Polyneuropathy, unspecified", "Neurological"),
    ("G89.29", "Other chronic pain", "Neurological"),
    ("F32.9", "Major depressive disorder, single episode, unspecified", "Mental Health"),
    ("F33.9", "Major depressive disorder, recurrent, unspecified", "Mental Health"),
    ("F41.1", "Generalized anxiety disorder", "Mental Health"),
    ("F31.9", "Bipolar disorder, unspecified", "Mental Health"),
    ("F43.10", "Post-traumatic stress disorder, unspecified", "Mental Health"),
    ("F10.20", "Alcohol use disorder, moderate", "Mental Health"),
    ("F17.210", "Nicotine dependence, cigarettes, uncomplicated", "Mental Health"),
    ("B18.2", "Chronic viral hepatitis C", "Infectious Disease"),
    ("U07.1", "COVID-19", "Infectious Disease"),
    ("C34.10", "Malignant neoplasm of upper lobe bronchus or lung", "Oncology"),
    ("C50.911", "Malignant neoplasm of right female breast", "Oncology"),
    ("C61", "Malignant neoplasm of prostate", "Oncology"),
    ("C18.9", "Malignant neoplasm of colon, unspecified", "Oncology"),
    ("C85.90", "Non-Hodgkin lymphoma, unspecified", "Oncology"),
    ("L40.0", "Psoriasis vulgaris", "Dermatology"),
    ("L20.9", "Atopic dermatitis, unspecified", "Dermatology"),
    ("N40.0", "Benign prostatic hyperplasia without LUTS", "Urology"),
    ("D64.9", "Anaemia, unspecified", "Hematology"),
    ("D50.9", "Iron deficiency anaemia, unspecified", "Hematology"),
    ("H25.10", "Age-related nuclear cataract, unspecified eye", "Ophthalmology"),
    ("H35.30", "Unspecified macular degeneration", "Ophthalmology"),
    ("H40.10X0", "Open-angle glaucoma, unspecified", "Ophthalmology"),
    ("Z87.891", "Personal history of nicotine dependence", "History"),
    ("Z82.49", "Family history of ischaemic heart disease", "History"),
    ("Z85.038", "Personal history of malignant neoplasm of large intestine", "History"),
    ("Z96.641", "Presence of right artificial knee joint", "Status Post"),
    ("Z95.0", "Presence of cardiac pacemaker", "Status Post"),
    ("Z95.1", "Presence of aortocoronary bypass graft", "Status Post"),
    ("Z79.01", "Long-term (current) use of anticoagulants", "Medication Use"),
    ("Z79.4", "Long-term (current) use of insulin", "Medication Use"),
    ("Z79.899", "Other long-term (current) drug therapy", "Medication Use"),
    ("R73.09", "Other abnormal glucose", "Symptoms"),
    ("R06.00", "Dyspnoea, unspecified", "Symptoms"),
    ("R53.83", "Other fatigue", "Symptoms"),
    ("R60.9", "Oedema, unspecified", "Symptoms"),
    ("R63.4", "Abnormal weight loss", "Symptoms"),
    ("R51", "Headache", "Symptoms"),
    ("R55", "Syncope and collapse", "Symptoms"),
    ("Z00.00", "Encounter for general adult medical examination", "Preventive"),
    ("Z12.11", "Encounter for screening for malignant neoplasm of colon", "Preventive"),
    ("Z12.31", "Encounter for screening mammogram", "Preventive"),
    ("Z13.6", "Encounter for screening for cardiovascular disorders", "Preventive"),
    ("Z23", "Encounter for immunization", "Preventive"),
    ("E87.5", "Hyperkalaemia", "Metabolic"),
    ("E86.0", "Dehydration", "Metabolic"),
    ("W19.XXXA", "Unspecified fall", "Injury"),
    ("S72.001A", "Fracture of unspecified part of neck of femur", "Injury"),
]

ICD10_BY_CODE = {code: (description, category) for code, description, category in ICD10_CATALOG}

# (code, description, category)
CPT_CATALOG = [
    ("99213", "Office visit, established, low complexity", "Office Visit"),
    ("99214", "Office visit, established, moderate complexity", "Office Visit"),
    ("99215", "Office visit, established, high complexity", "Office Visit"),
    ("99204", "Office visit, new, moderate complexity", "Office Visit"),
    ("99232", "Subsequent hospital care, low complexity", "Hospital"),
    ("99238", "Hospital discharge day management", "Hospital"),
    ("99285", "Emergency department visit, high complexity", "Emergency"),
    ("99284", "Emergency department visit, moderate complexity", "Emergency"),
    ("93000", "Electrocardiogram, routine ECG with 12 leads", "Diagnostic"),
    ("93306", "Echocardiography, complete", "Diagnostic"),
    ("71046", "Radiologic examination, chest, 2 views", "Diagnostic"),
    ("74177", "CT abdomen and pelvis with contrast", "Diagnostic"),
    ("70553", "MRI brain with and without contrast", "Diagnostic"),
    ("72148", "MRI lumbar spine without contrast", "Diagnostic"),
    ("93880", "Duplex scan carotid arteries, bilateral", "Diagnostic"),
    ("85027", "Blood count; complete (CBC)", "Laboratory"),
    ("80053", "Comprehensive metabolic panel", "Laboratory"),
    ("80061", "Lipid panel", "Laboratory"),
    ("83036", "Hemoglobin A1C", "Laboratory"),
    ("84484", "Troponin, quantitative", "Laboratory"),
    ("43239", "Upper GI endoscopy with biopsy", "Endoscopy"),
    ("45378", "Colonoscopy, diagnostic", "Endoscopy"),
    ("45380", "Colonoscopy with biopsy", "Endoscopy"),
    ("27447", "Total knee arthroplasty", "Surgery"),
    ("27130", "Total hip arthroplasty", "Surgery"),
    ("33533", "Coronary artery bypass, arterial graft", "Surgery"),
    ("47562", "Laparoscopic cholecystectomy", "Surgery"),
    ("49505", "Repair inguinal hernia, initial", "Surgery"),
    ("66984", "Extracapsular cataract removal", "Ophthalmology"),
    ("31622", "Bronchoscopy, diagnostic", "Pulmonology"),
    ("93452", "Left heart catheterization", "Cardiology"),
    ("92928", "Percutaneous coronary intervention", "Cardiology"),
    ("96365", "Intravenous infusion, initial", "Infusion"),
    ("90471", "Immunization administration", "Preventive"),
    ("90658", "Influenza virus vaccine, trivalent", "Preventive"),
    ("G0438", "Annual wellness visit, initial", "Preventive"),
    ("97110", "Therapeutic exercises", "Therapy"),
    ("90834", "Psychotherapy, 45 minutes", "Mental Health"),
    ("90837", "Psychotherapy, 60 minutes", "Mental Health"),
    ("64483", "Injection, anesthetic agent, lumbar epidural", "Pain Management"),
    ("90935", "Hemodialysis procedure", "Dialysis"),
    ("96413", "Chemotherapy, intravenous infusion, initial", "Oncology"),
    ("19083", "Biopsy, breast, ultrasound guidance", "Biopsy"),
    ("11042", "Debridement, subcutaneous tissue", "Wound Care"),
    ("97802", "Medical nutrition therapy, initial assessment", "Nutrition"),
    ("94010", "Spirometry", "Pulmonary"),
    ("95810", "Polysomnography, 7 or more parameters", "Sleep"),
    ("93224", "Electrocardiographic monitoring, up to 48 hours", "Cardiac Monitoring"),
    ("17000", "Destruction of premalignant lesion", "Dermatology"),
    ("52000", "Cystourethroscopy", "Urology"),
]

# Medication catalog with drug class so adherence and interaction insights are queryable.
MEDICATION_CATALOG = [
    {"name": "Metformin", "generic": "metformin hydrochloride", "brand": "Glucophage", "class": "Biguanide", "dose": "1000 mg", "freq": "Twice daily", "route": "Oral", "indication": "Type 2 Diabetes Mellitus"},
    {"name": "Glipizide", "generic": "glipizide", "brand": "Glucotrol", "class": "Sulfonylurea", "dose": "5 mg", "freq": "Once daily", "route": "Oral", "indication": "Type 2 Diabetes Mellitus"},
    {"name": "Sitagliptin", "generic": "sitagliptin phosphate", "brand": "Januvia", "class": "DPP-4 inhibitor", "dose": "100 mg", "freq": "Once daily", "route": "Oral", "indication": "Type 2 Diabetes Mellitus"},
    {"name": "Empagliflozin", "generic": "empagliflozin", "brand": "Jardiance", "class": "SGLT2 inhibitor", "dose": "10 mg", "freq": "Once daily", "route": "Oral", "indication": "Type 2 Diabetes Mellitus"},
    {"name": "Insulin Glargine", "generic": "insulin glargine", "brand": "Lantus", "class": "Basal insulin", "dose": "20 units", "freq": "Once daily at bedtime", "route": "SC", "indication": "Type 2 Diabetes Mellitus"},
    {"name": "Lisinopril", "generic": "lisinopril", "brand": "Prinivil", "class": "ACE inhibitor", "dose": "20 mg", "freq": "Once daily", "route": "Oral", "indication": "Essential Hypertension"},
    {"name": "Amlodipine", "generic": "amlodipine besylate", "brand": "Norvasc", "class": "Calcium channel blocker", "dose": "5 mg", "freq": "Once daily", "route": "Oral", "indication": "Essential Hypertension"},
    {"name": "Losartan", "generic": "losartan potassium", "brand": "Cozaar", "class": "ARB", "dose": "50 mg", "freq": "Once daily", "route": "Oral", "indication": "Essential Hypertension"},
    {"name": "Metoprolol Succinate", "generic": "metoprolol succinate", "brand": "Toprol-XL", "class": "Beta blocker", "dose": "50 mg", "freq": "Once daily", "route": "Oral", "indication": "Essential Hypertension"},
    {"name": "Hydrochlorothiazide", "generic": "hydrochlorothiazide", "brand": "Microzide", "class": "Thiazide diuretic", "dose": "25 mg", "freq": "Once daily", "route": "Oral", "indication": "Essential Hypertension"},
    {"name": "Furosemide", "generic": "furosemide", "brand": "Lasix", "class": "Loop diuretic", "dose": "40 mg", "freq": "Once daily", "route": "Oral", "indication": "Heart Failure"},
    {"name": "Sacubitril/Valsartan", "generic": "sacubitril-valsartan", "brand": "Entresto", "class": "ARNI", "dose": "97/103 mg", "freq": "Twice daily", "route": "Oral", "indication": "Heart Failure"},
    {"name": "Atorvastatin", "generic": "atorvastatin calcium", "brand": "Lipitor", "class": "Statin", "dose": "40 mg", "freq": "Once daily at bedtime", "route": "Oral", "indication": "Hyperlipidemia"},
    {"name": "Rosuvastatin", "generic": "rosuvastatin calcium", "brand": "Crestor", "class": "Statin", "dose": "20 mg", "freq": "Once daily", "route": "Oral", "indication": "Hyperlipidemia"},
    {"name": "Ezetimibe", "generic": "ezetimibe", "brand": "Zetia", "class": "Cholesterol absorption inhibitor", "dose": "10 mg", "freq": "Once daily", "route": "Oral", "indication": "Hyperlipidemia"},
    {"name": "Albuterol", "generic": "albuterol sulfate", "brand": "ProAir HFA", "class": "SABA inhaler", "dose": "90 mcg", "freq": "Every 4-6 hours as needed", "route": "Inhaled", "indication": "Asthma / COPD"},
    {"name": "Fluticasone/Salmeterol", "generic": "fluticasone-salmeterol", "brand": "Advair Diskus", "class": "ICS/LABA inhaler", "dose": "250 mcg", "freq": "Twice daily", "route": "Inhaled", "indication": "COPD / Asthma"},
    {"name": "Tiotropium", "generic": "tiotropium bromide", "brand": "Spiriva", "class": "LAMA inhaler", "dose": "18 mcg", "freq": "Once daily", "route": "Inhaled", "indication": "COPD"},
    {"name": "Montelukast", "generic": "montelukast sodium", "brand": "Singulair", "class": "Leukotriene antagonist", "dose": "10 mg", "freq": "Once daily at bedtime", "route": "Oral", "indication": "Asthma / Allergic Rhinitis"},
    {"name": "Sertraline", "generic": "sertraline hydrochloride", "brand": "Zoloft", "class": "SSRI", "dose": "100 mg", "freq": "Once daily", "route": "Oral", "indication": "Major Depressive Disorder"},
    {"name": "Escitalopram", "generic": "escitalopram oxalate", "brand": "Lexapro", "class": "SSRI", "dose": "10 mg", "freq": "Once daily", "route": "Oral", "indication": "Generalized Anxiety Disorder"},
    {"name": "Duloxetine", "generic": "duloxetine hydrochloride", "brand": "Cymbalta", "class": "SNRI", "dose": "60 mg", "freq": "Once daily", "route": "Oral", "indication": "Major Depressive Disorder"},
    {"name": "Bupropion", "generic": "bupropion hydrochloride", "brand": "Wellbutrin", "class": "NDRI", "dose": "150 mg", "freq": "Twice daily", "route": "Oral", "indication": "Major Depressive Disorder"},
    {"name": "Quetiapine", "generic": "quetiapine fumarate", "brand": "Seroquel", "class": "Atypical antipsychotic", "dose": "50 mg", "freq": "Once daily at bedtime", "route": "Oral", "indication": "Bipolar Disorder"},
    {"name": "Omeprazole", "generic": "omeprazole", "brand": "Prilosec", "class": "Proton pump inhibitor", "dose": "20 mg", "freq": "Once daily before meal", "route": "Oral", "indication": "GERD"},
    {"name": "Pantoprazole", "generic": "pantoprazole sodium", "brand": "Protonix", "class": "Proton pump inhibitor", "dose": "40 mg", "freq": "Once daily", "route": "Oral", "indication": "GERD"},
    {"name": "Warfarin", "generic": "warfarin sodium", "brand": "Coumadin", "class": "Vitamin K antagonist", "dose": "5 mg", "freq": "Once daily", "route": "Oral", "indication": "Atrial Fibrillation / DVT Prevention"},
    {"name": "Apixaban", "generic": "apixaban", "brand": "Eliquis", "class": "DOAC anticoagulant", "dose": "5 mg", "freq": "Twice daily", "route": "Oral", "indication": "Atrial Fibrillation / DVT Prevention"},
    {"name": "Aspirin", "generic": "aspirin", "brand": "Bayer", "class": "Antiplatelet", "dose": "81 mg", "freq": "Once daily", "route": "Oral", "indication": "Cardiovascular Risk Reduction"},
    {"name": "Clopidogrel", "generic": "clopidogrel bisulfate", "brand": "Plavix", "class": "Antiplatelet", "dose": "75 mg", "freq": "Once daily", "route": "Oral", "indication": "Antiplatelet Therapy"},
    {"name": "Levothyroxine", "generic": "levothyroxine sodium", "brand": "Synthroid", "class": "Thyroid hormone", "dose": "100 mcg", "freq": "Once daily on empty stomach", "route": "Oral", "indication": "Hypothyroidism"},
    {"name": "Ibuprofen", "generic": "ibuprofen", "brand": "Advil", "class": "NSAID", "dose": "400 mg", "freq": "Three times daily", "route": "Oral", "indication": "Pain / Inflammation"},
    {"name": "Celecoxib", "generic": "celecoxib", "brand": "Celebrex", "class": "COX-2 inhibitor", "dose": "200 mg", "freq": "Once daily", "route": "Oral", "indication": "Osteoarthritis"},
    {"name": "Tramadol", "generic": "tramadol hydrochloride", "brand": "Ultram", "class": "Opioid analgesic", "dose": "50 mg", "freq": "Every 6 hours as needed", "route": "Oral", "indication": "Moderate to Severe Pain"},
    {"name": "Prednisone", "generic": "prednisone", "brand": "Deltasone", "class": "Corticosteroid", "dose": "10 mg", "freq": "Once daily", "route": "Oral", "indication": "Inflammatory Condition"},
    {"name": "Gabapentin", "generic": "gabapentin", "brand": "Neurontin", "class": "Anticonvulsant", "dose": "300 mg", "freq": "Three times daily", "route": "Oral", "indication": "Neuropathic Pain"},
    {"name": "Allopurinol", "generic": "allopurinol", "brand": "Zyloprim", "class": "Xanthine oxidase inhibitor", "dose": "300 mg", "freq": "Once daily", "route": "Oral", "indication": "Gout"},
    {"name": "Methotrexate", "generic": "methotrexate", "brand": "Trexall", "class": "DMARD", "dose": "15 mg", "freq": "Once weekly", "route": "Oral", "indication": "Rheumatoid Arthritis"},
    {"name": "Pembrolizumab", "generic": "pembrolizumab", "brand": "Keytruda", "class": "PD-1 immunotherapy", "dose": "200 mg", "freq": "Every 3 weeks", "route": "IV", "indication": "Oncology Treatment"},
    {"name": "Erythropoetin Alfa", "generic": "epoetin alfa", "brand": "Epogen", "class": "ESA", "dose": "10000 units", "freq": "Three times weekly", "route": "SC", "indication": "Anemia of CKD"},
    {"name": "Sevelamer", "generic": "sevelamer carbonate", "brand": "Renvela", "class": "Phosphate binder", "dose": "800 mg", "freq": "Three times daily with meals", "route": "Oral", "indication": "CKD Mineral Management"},
    {"name": "Vitamin D3", "generic": "cholecalciferol", "brand": "Nature Made", "class": "Vitamin supplement", "dose": "1000 IU", "freq": "Once daily", "route": "Oral", "indication": "Vitamin D Deficiency"},
    {"name": "Ferrous Sulfate", "generic": "ferrous sulfate", "brand": "Slow Fe", "class": "Iron supplement", "dose": "325 mg", "freq": "Once daily", "route": "Oral", "indication": "Iron Deficiency Anemia"},
    {"name": "Ondansetron", "generic": "ondansetron hydrochloride", "brand": "Zofran", "class": "5-HT3 antagonist", "dose": "4 mg", "freq": "Every 8 hours as needed", "route": "Oral", "indication": "Nausea"},
    {"name": "Lorazepam", "generic": "lorazepam", "brand": "Ativan", "class": "Benzodiazepine", "dose": "1 mg", "freq": "Twice daily as needed", "route": "Oral", "indication": "Anxiety"},
]

VACCINE_CATALOG = [
    ("Influenza", "IIV", "141", "Sanofi Pasteur", "Left deltoid", "IM"),
    ("Tetanus/Diphtheria/Pertussis", "Tdap", "115", "GSK", "Right deltoid", "IM"),
    ("Pneumococcal (PPSV23)", "PPSV23", "33", "Merck", "Left deltoid", "IM"),
    ("Pneumococcal (PCV13)", "PCV13", "133", "Pfizer", "Right deltoid", "IM"),
    ("Hepatitis B", "HepB", "8", "Merck", "Right deltoid", "IM"),
    ("Hepatitis A", "HepA", "85", "Merck", "Left deltoid", "IM"),
    ("COVID-19 mRNA", "COVID", "228", "Moderna", "Left deltoid", "IM"),
    ("COVID-19 mRNA Booster", "COVIDb", "228", "Pfizer-BioNTech", "Right deltoid", "IM"),
    ("Zoster (RZV)", "RZV", "187", "GSK", "Left deltoid", "IM"),
    ("MMR", "MMR", "3", "Merck", "Left arm", "SC"),
    ("Varicella", "Var", "21", "Merck", "Right arm", "SC"),
]

# Analyte definitions: name, LOINC, unit, low, high, category.
LAB_CATALOG = [
    {"name": "White Blood Cell Count", "loinc": "6690-2", "unit": "10^3/uL", "low": 4.5, "high": 11.0, "category": "CBC"},
    {"name": "Red Blood Cell Count", "loinc": "789-8", "unit": "10^6/uL", "low": 4.2, "high": 5.9, "category": "CBC"},
    {"name": "Hemoglobin", "loinc": "718-7", "unit": "g/dL", "low": 12.0, "high": 17.5, "category": "CBC"},
    {"name": "Hematocrit", "loinc": "4544-3", "unit": "%", "low": 36.0, "high": 52.0, "category": "CBC"},
    {"name": "Platelet Count", "loinc": "777-3", "unit": "10^3/uL", "low": 150.0, "high": 400.0, "category": "CBC"},
    {"name": "MCV", "loinc": "787-2", "unit": "fL", "low": 80.0, "high": 100.0, "category": "CBC"},
    {"name": "Sodium", "loinc": "2951-2", "unit": "mEq/L", "low": 136.0, "high": 145.0, "category": "CMP"},
    {"name": "Potassium", "loinc": "2823-3", "unit": "mEq/L", "low": 3.5, "high": 5.1, "category": "CMP"},
    {"name": "Chloride", "loinc": "2075-0", "unit": "mEq/L", "low": 98.0, "high": 106.0, "category": "CMP"},
    {"name": "CO2 (Bicarbonate)", "loinc": "2028-9", "unit": "mEq/L", "low": 22.0, "high": 29.0, "category": "CMP"},
    {"name": "BUN", "loinc": "3094-0", "unit": "mg/dL", "low": 7.0, "high": 25.0, "category": "CMP"},
    {"name": "Creatinine", "loinc": "2160-0", "unit": "mg/dL", "low": 0.6, "high": 1.2, "category": "CMP"},
    {"name": "Glucose", "loinc": "2345-7", "unit": "mg/dL", "low": 70.0, "high": 100.0, "category": "CMP"},
    {"name": "Calcium", "loinc": "17861-6", "unit": "mg/dL", "low": 8.5, "high": 10.5, "category": "CMP"},
    {"name": "ALT", "loinc": "1742-6", "unit": "IU/L", "low": 7.0, "high": 56.0, "category": "CMP"},
    {"name": "AST", "loinc": "1920-8", "unit": "IU/L", "low": 10.0, "high": 40.0, "category": "CMP"},
    {"name": "Albumin", "loinc": "1751-7", "unit": "g/dL", "low": 3.4, "high": 5.4, "category": "CMP"},
    {"name": "Total Cholesterol", "loinc": "2093-3", "unit": "mg/dL", "low": 0.0, "high": 200.0, "category": "Lipid"},
    {"name": "LDL Cholesterol", "loinc": "13457-7", "unit": "mg/dL", "low": 0.0, "high": 100.0, "category": "Lipid"},
    {"name": "HDL Cholesterol", "loinc": "2085-9", "unit": "mg/dL", "low": 40.0, "high": 999.0, "category": "Lipid"},
    {"name": "Triglycerides", "loinc": "2571-8", "unit": "mg/dL", "low": 0.0, "high": 150.0, "category": "Lipid"},
    {"name": "HbA1c", "loinc": "4548-4", "unit": "%", "low": 4.0, "high": 5.6, "category": "Diabetes"},
    {"name": "Fasting Glucose", "loinc": "1558-6", "unit": "mg/dL", "low": 70.0, "high": 99.0, "category": "Diabetes"},
    {"name": "TSH", "loinc": "3016-3", "unit": "mIU/L", "low": 0.4, "high": 4.0, "category": "Thyroid"},
    {"name": "Free T4", "loinc": "3024-7", "unit": "ng/dL", "low": 0.8, "high": 1.8, "category": "Thyroid"},
    {"name": "eGFR", "loinc": "69405-9", "unit": "mL/min/1.73m2", "low": 60.0, "high": 999.0, "category": "Renal"},
    {"name": "Uric Acid", "loinc": "3084-1", "unit": "mg/dL", "low": 2.6, "high": 7.2, "category": "Renal"},
    {"name": "Troponin I", "loinc": "10839-9", "unit": "ng/mL", "low": 0.0, "high": 0.04, "category": "Cardiac"},
    {"name": "BNP", "loinc": "42637-9", "unit": "pg/mL", "low": 0.0, "high": 100.0, "category": "Cardiac"},
    {"name": "Serum Iron", "loinc": "2498-4", "unit": "ug/dL", "low": 60.0, "high": 170.0, "category": "Iron"},
    {"name": "Ferritin", "loinc": "2276-4", "unit": "ng/mL", "low": 12.0, "high": 300.0, "category": "Iron"},
    {"name": "Vitamin D, 25-OH", "loinc": "1989-3", "unit": "ng/mL", "low": 30.0, "high": 100.0, "category": "Vitamins"},
    {"name": "Vitamin B12", "loinc": "2132-9", "unit": "pg/mL", "low": 200.0, "high": 900.0, "category": "Vitamins"},
    {"name": "INR", "loinc": "34714-6", "unit": "ratio", "low": 0.8, "high": 1.2, "category": "Coagulation"},
    {"name": "PT", "loinc": "5902-2", "unit": "seconds", "low": 11.0, "high": 13.5, "category": "Coagulation"},
    {"name": "CRP", "loinc": "1988-5", "unit": "mg/L", "low": 0.0, "high": 10.0, "category": "Inflammation"},
    {"name": "ESR", "loinc": "4537-7", "unit": "mm/hr", "low": 0.0, "high": 20.0, "category": "Inflammation"},
    {"name": "Urine Microalbumin", "loinc": "14585-4", "unit": "mg/g", "low": 0.0, "high": 30.0, "category": "Urine"},
]

LABS_BY_CATEGORY: dict[str, list[dict[str, Any]]] = {}
for _lab in LAB_CATALOG:
    LABS_BY_CATEGORY.setdefault(_lab["category"], []).append(_lab)

PANEL_DEFINITIONS = {
    "Comprehensive Metabolic Panel": ["CMP"],
    "Complete Blood Count": ["CBC"],
    "Lipid Panel": ["Lipid"],
    "Thyroid Function Panel": ["Thyroid"],
    "HbA1c and Fasting Glucose": ["Diabetes"],
    "Renal Function Panel": ["Renal", "CMP"],
    "Iron Studies Panel": ["Iron"],
    "Cardiac Biomarker Panel": ["Cardiac"],
    "Coagulation Panel": ["Coagulation"],
    "Inflammation Markers Panel": ["Inflammation"],
    "Vitamin Panel": ["Vitamins"],
    "Urinalysis with Microscopy": ["Urine"],
}

ALLERGY_CATALOG = [
    ("Penicillin", "Drug", "Urticaria and anaphylaxis", "Severe"),
    ("Sulfonamides", "Drug", "Rash and pruritus", "Moderate"),
    ("Aspirin", "Drug", "Angioedema and bronchoconstriction", "Severe"),
    ("Codeine", "Drug", "Nausea and respiratory depression", "Moderate"),
    ("Contrast Dye", "Contrast", "Anaphylactoid reaction", "Life-Threatening"),
    ("Latex", "Latex", "Contact dermatitis", "Moderate"),
    ("Peanuts", "Food", "Anaphylaxis", "Life-Threatening"),
    ("Shellfish", "Food", "Urticaria and angioedema", "Severe"),
    ("Eggs", "Food", "Urticaria", "Mild"),
    ("Bee Venom", "Environmental", "Anaphylaxis", "Life-Threatening"),
    ("Pollen", "Environmental", "Allergic rhinitis", "Mild"),
    ("Dust Mites", "Environmental", "Allergic rhinitis and asthma", "Moderate"),
    ("Amoxicillin", "Drug", "Maculopapular rash", "Moderate"),
    ("Statins", "Drug", "Myopathy", "Moderate"),
    ("ACE Inhibitors", "Drug", "Dry cough and angioedema", "Moderate"),
    ("NSAIDs", "Drug", "Renal function decline", "Moderate"),
]

APPOINTMENT_TYPES = ["Routine Follow-Up", "New Patient", "Urgent Care", "Annual Physical",
                     "Specialist Consultation", "Post-Procedure Follow-Up", "Telehealth Visit",
                     "Pre-Operative Evaluation", "Disease Management"]

VISIT_REASONS = [
    "Routine follow-up for chronic condition management",
    "Annual wellness examination",
    "Evaluation of worsening symptoms",
    "Medication review and adjustment",
    "Post-hospitalization follow-up",
    "Specialist referral evaluation",
    "Pre-operative medical clearance",
    "Screening examination",
    "Diabetes management visit",
    "Hypertension management",
    "Cardiology follow-up",
    "Mental health follow-up",
]

SURGICAL_PROCEDURES = [
    ("Appendectomy", "44950", "General anesthesia"),
    ("Laparoscopic Cholecystectomy", "47562", "General anesthesia"),
    ("Inguinal Hernia Repair", "49505", "General anesthesia"),
    ("Total Hip Arthroplasty", "27130", "Spinal anesthesia"),
    ("Total Knee Arthroplasty", "27447", "Spinal anesthesia"),
    ("Coronary Artery Bypass Grafting", "33533", "General anesthesia"),
    ("Percutaneous Coronary Intervention", "92928", "Local anesthesia with sedation"),
    ("Cataract Extraction", "66984", "Local anesthesia"),
    ("Lumbar Discectomy", "63030", "General anesthesia"),
    ("Thyroidectomy", "60240", "General anesthesia"),
]

PAST_MEDICAL_CONDITIONS = [
    "Childhood asthma", "Recurrent otitis media", "Mononucleosis", "Chicken pox",
    "Anemia of childhood", "Recurrent urinary tract infections", "Pneumonia (resolved)",
    "Migraine without aura", "Irritable bowel syndrome", "Seasonal allergic rhinitis",
    "Peptic ulcer disease (resolved)", "Deep vein thrombosis (resolved)",
    "Atrial fibrillation (converted)", "Community-acquired pneumonia (resolved)",
    "Cellulitis (resolved)", "Acute kidney injury (resolved)",
]

FAMILY_CONDITIONS = [
    "Coronary artery disease", "Type 2 diabetes mellitus", "Hypertension",
    "Breast cancer", "Colon cancer", "Prostate cancer", "Stroke",
    "Alzheimer's disease", "Osteoporosis", "Rheumatoid arthritis",
    "Hypothyroidism", "Asthma", "COPD", "Hyperlipidemia", "Depression",
]

RELATIONS = ["Father", "Mother", "Brother", "Sister", "Maternal Grandmother",
             "Maternal Grandfather", "Paternal Grandmother", "Paternal Grandfather"]

OCCUPATIONS = ["Software Engineer", "Registered Nurse", "Teacher", "Accountant",
               "Retail Manager", "Construction Worker", "Truck Driver", "Chef",
               "Administrative Assistant", "Sales Representative", "Electrician",
               "Social Worker", "Firefighter", "Pharmacist", "Physical Therapist",
               "Financial Analyst", "Marketing Manager", "Paralegal"]

EMPLOYMENT_STATUS = ["Employed full-time", "Employed part-time", "Self-employed",
                     "Unemployed", "Retired", "Disabled", "Student"]

EDUCATION_LEVELS = ["Less than high school", "High school diploma/GED", "Some college",
                    "Associate degree", "Bachelor's degree", "Master's degree",
                    "Doctoral degree", "Professional degree"]

FIRST_NAMES_MALE = ["James", "Robert", "Michael", "William", "David", "Richard", "Joseph",
                    "Thomas", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Andrew",
                    "Noah", "Lucas", "Mateo", "Omar", "Wei", "Rajesh", "Diego", "Kofi",
                    "Henry", "Samuel", "Adam", "Owen", "Jack", "Luis", "Ivan", "Amir"]

FIRST_NAMES_FEMALE = ["Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth",
                      "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Margaret",
                      "Sofia", "Amelia", "Priya", "Mei", "Fatima", "Aisha", "Grace",
                      "Nora", "Isabella", "Elena", "Rosa", "Yuki", "Amara", "Ingrid", "Leila"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
              "Davis", "Rodriguez", "Martinez", "Chen", "Okafor", "Rossi", "Nair",
              "Brooks", "Kim", "Patel", "Lewis", "Martin", "Silva", "Hassan", "Tan",
              "Kowalski", "Costa", "Evans", "Thompson", "Rahman", "Alvarez", "Li", "Reed"]

CITY_STATE = [("Columbus", "OH"), ("Austin", "TX"), ("Denver", "CO"), ("Portland", "OR"),
              ("Charlotte", "NC"), ("Phoenix", "AZ"), ("Madison", "WI"), ("Rochester", "NY"),
              ("Sacramento", "CA"), ("Pittsburgh", "PA"), ("Nashville", "TN"), ("Tampa", "FL")]

RACE_CHOICES = ["White", "Black or African American", "Asian", "Hispanic",
                "Middle Eastern", "Two or More Races", "Unknown"]
RACE_WEIGHTS = [52, 15, 9, 14, 3, 4, 3]

LANGUAGES = ["English", "Spanish", "Mandarin", "Arabic", "Hindi", "Portuguese", "Vietnamese", "Korean"]
LANGUAGE_WEIGHTS = [72, 12, 4, 3, 3, 2, 2, 2]

INSURANCE_PROVIDERS = ["Anthem Blue Cross", "UnitedHealthcare", "Aetna", "Cigna", "Humana",
                       "Kaiser Permanente", "Centene", "Medicare", "Medicaid", "Tricare"]

PHARMACIES = ["CVS Pharmacy", "Walgreens", "Rite Aid", "Walmart Pharmacy",
              "Kroger Pharmacy", "Costco Pharmacy", "Hospital Outpatient Pharmacy"]

CLINICAL_NOTE_TYPES = ["Progress Note", "History and Physical", "Consultation",
                       "Discharge Summary", "Nursing Note"]

CARE_GAP_LIBRARY = [
    ("overdue_lab", "Overdue follow-up laboratory monitoring"),
    ("imaging_followup", "Imaging follow-up not yet scheduled"),
    ("medication_reconciliation", "Medication refill gap requires reconciliation"),
    ("vaccination", "Recommended immunization not on record"),
    ("specialist_referral", "Specialist referral pending completion"),
    ("annual_wellness", "Overdue annual wellness visit"),
]

# Tenant themes keep the two demo organizations visually and textually distinct.
TENANT_THEMES = {
    "primary": {
        "org": "Research Clinic",
        "facilities": ["Research Clinic Main Campus", "Riverside Community Hospital",
                       "University Health System", "Lakeside Medical Center"],
        "lab_facilities": ["Research Clinic Core Laboratory", "LabCorp — National Processing Center",
                           "Quest Diagnostics — Regional Lab", "University Reference Laboratory"],
        "provider_seed": "research-clinic-providers",
        "gcs_bucket": "research-clinic-data",
    },
    "demo2": {
        "org": "Northstar Health",
        "facilities": ["Northstar Medical Center", "Summit Healthcare Regional Medical Center",
                       "Northside Hospital", "Valley View Hospital"],
        "lab_facilities": ["Northstar Central Laboratory", "ARUP Laboratories",
                           "Mayo Clinic Laboratories", "Regional Diagnostics Alliance"],
        "provider_seed": "northstar-health-providers",
        "gcs_bucket": "northstar-health-data",
    },
}

# Archetype-driven diagnosis blueprints keyed by care archetype.
ARCHETYPE_BLUEPRINTS = {
    "cardiometabolic": ["I10", "E11.9", "E78.5", "E66.9", "Z79.899"],
    "cardiac": ["I50.20", "I48.0", "I10", "Z79.01", "R60.9"],
    "respiratory": ["J44.1", "G47.33", "J30.9", "Z87.891", "R06.00"],
    "renal": ["N18.3", "I13.10", "E87.5", "D64.9", "Z79.899"],
    "musculoskeletal": ["M54.5", "M17.11", "G89.29", "M81.0", "M25.511"],
    "behavioral_health": ["F41.1", "F33.9", "F43.10", "G47.33", "Z79.899"],
    "preventive_primary_care": ["Z00.00", "Z13.6", "E78.5", "I10", "Z23"],
    "oncology_surveillance": ["Z85.038", "Z12.11", "D64.9", "R63.4", "C34.10"],
    "complex_multimorbidity": ["E11.65", "I50.9", "N18.3", "J44.1", "F41.1"],
}

# Archetype display labels used in primary_diagnosis and report copy.
ARCHETYPE_PRIMARY_LABEL = {
    "cardiometabolic": "Type 2 diabetes with hypertension",
    "cardiac": "Heart failure with reduced EF",
    "respiratory": "COPD with acute exacerbation",
    "renal": "Chronic kidney disease stage 3-4",
    "musculoskeletal": "Chronic low back pain with osteoarthritis",
    "behavioral_health": "Generalized anxiety with recurrent depression",
    "preventive_primary_care": "Preventive care and screening",
    "oncology_surveillance": "Oncology surveillance post-treatment",
    "complex_multimorbidity": "Complex multimorbidity (DM, HF, CKD)",
}

PII_RECORD_RATE = 0.65
HIGH_RISK_RATE = 0.22
CARE_GAP_RATE = 0.36
SDOH_COMPLEXITY_RATE = 0.28


# =============================================================================
# DETERMINISTIC HELPERS
# =============================================================================

def patient_rng(seed: int, prefix: str, index: int) -> random.Random:
    """Return the deterministic RNG for one patient, stable across generators."""

    return random.Random(f"{seed}:{prefix}:{index}")


def deid_token(seed_value: str) -> str:
    """Build a stable de-identification token from any seed string."""

    digest = hashlib.sha256(seed_value.encode("utf-8")).hexdigest().upper()
    return f"DEID-{digest[:8]}"


def rand_npi(rng: random.Random) -> str:
    """Generate a synthetic 10-digit NPI number."""

    return "".join(str(rng.randint(0, 9)) for _ in range(10))


def rand_ndc(rng: random.Random) -> str:
    """Generate a synthetic NDC drug code."""

    return f"{rng.randint(10000, 99999)}-{rng.randint(100, 999)}-{rng.randint(10, 99)}"


def rand_accession(rng: random.Random) -> str:
    """Generate a synthetic lab accession number."""

    return "ACC" + "".join(str(rng.randint(0, 9)) for _ in range(8))


def rand_lot(rng: random.Random) -> str:
    """Generate a synthetic vaccine lot number."""

    return "LOT" + "".join(rng.choices(string.ascii_uppercase + string.digits, k=7))


def rand_date(rng: random.Random, start: date, end: date) -> date:
    """Return a random date within [start, end]."""

    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=rng.randint(0, delta))


# =============================================================================
# PROVIDERS
# =============================================================================

def build_providers(seed: int, theme_key: str, count: int = 24) -> list[dict[str, Any]]:
    """Build the deterministic provider directory for one tenant."""

    theme = TENANT_THEMES.get(theme_key, TENANT_THEMES["primary"])
    rng = random.Random(f"{seed}:{theme['provider_seed']}")
    providers = []
    used_npis: set[str] = set()
    for index in range(1, count + 1):
        specialty, department = SPECIALTIES[(index - 1) % len(SPECIALTIES)]
        sex = rng.choice(("Male", "Female"))
        first = rng.choice(FIRST_NAMES_MALE if sex == "Male" else FIRST_NAMES_FEMALE)
        last = rng.choice(LAST_NAMES)
        npi = rand_npi(rng)
        while npi in used_npis:
            npi = rand_npi(rng)
        used_npis.add(npi)
        providers.append({
            "provider_id": index,
            "first_name": first,
            "last_name": last,
            "full_name": f"Dr. {first} {last}",
            "title": rng.choice(PROVIDER_TITLES),
            "specialty": specialty,
            "department": department,
            "npi": npi,
            "email": f"{first.lower()}.{last.lower()}@{theme['org'].lower().replace(' ', '')}.example",
            "phone": f"(555) {rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
        })
    return providers


# =============================================================================
# PATIENT PROFILE ENGINE
# =============================================================================

def _choose_archetype(rng: random.Random, age: int, bmi: float, smoking: str) -> str:
    """Pick a care archetype weighted by demographics and risk factors."""

    weighted = [
        ("cardiometabolic", 26),
        ("cardiac", 10 if age >= 60 else 5),
        ("respiratory", 12 if smoking in ("Current", "Former") else 6),
        ("renal", 10 if age >= 55 else 4),
        ("musculoskeletal", 12 if age >= 45 else 7),
        ("behavioral_health", 10),
        ("preventive_primary_care", 12),
        ("oncology_surveillance", 8 if age >= 50 else 3),
        ("complex_multimorbidity", 12 if (age >= 60 or bmi >= 32) else 5),
    ]
    choices, weights = zip(*weighted)
    return rng.choices(choices, weights=weights)[0]


def _lab_value(rng: random.Random, test: dict[str, Any], conditions_text: str,
               anticoagulated: bool) -> tuple[float, bool, str, str]:
    """Generate one lab value biased by the patient's documented conditions.

    Returns (value, is_abnormal, flag, status) where flag follows the app's
    lowercase vocabulary and status the report vocabulary.
    """

    low, high, name = float(test["low"]), float(test["high"]), test["name"]
    lowered = conditions_text.lower()
    value: float | None = None
    if "diabet" in lowered and name == "HbA1c":
        value = round(rng.uniform(6.5, 11.0), 1)
    elif "diabet" in lowered and name in ("Glucose", "Fasting Glucose"):
        value = round(rng.uniform(126.0, 290.0), 1)
    elif ("hyperlipid" in lowered or "cholesterol" in lowered) and name == "LDL Cholesterol":
        value = round(rng.uniform(100.0, 200.0), 1)
    elif "kidney" in lowered and name == "Creatinine":
        value = round(rng.uniform(1.5, 4.2), 2)
    elif "kidney" in lowered and name == "eGFR":
        value = round(rng.uniform(18.0, 55.0), 0)
    elif "heart failure" in lowered and name == "BNP":
        value = round(rng.uniform(180.0, 1400.0), 0)
    elif "hypothyroid" in lowered and name == "TSH":
        value = round(rng.uniform(5.0, 15.0), 2)
    elif "anaemia" in lowered and name == "Hemoglobin":
        value = round(rng.uniform(8.4, 11.8), 1)
    if name == "INR" and anticoagulated:
        # Therapeutic INR only occurs for anticoagulated patients.
        value = round(rng.uniform(2.0, 3.5), 2)
    if value is None:
        if rng.random() < 0.85:
            value = round(rng.uniform(low, min(high, low + (high - low))), 2)
        elif rng.random() < 0.5:
            value = round(rng.uniform(low * 0.6, low), 2)
        else:
            value = round(rng.uniform(high, high * 1.4), 2)

    is_abnormal = not (low <= value <= high)
    if not is_abnormal:
        return value, False, "normal", "Normal"
    if value < low:
        if value < low * 0.8:
            return value, True, "critical_low", "Critical Low"
        return value, True, "low", "Low"
    if value > high * 1.2:
        return value, True, "critical_high", "Critical High"
    return value, True, "high", "High"


def generate_clinical_note(rng: random.Random, patient: dict[str, Any], diagnosis: str,
                           medication: str, lab_sentence: str) -> str:
    """Compose a realistic multi-paragraph clinician progress note."""

    pronoun = "He" if patient["sex"] == "Male" else "She"
    display = f"{patient['last_name']}, {patient['first_name']}"
    symptom = rng.choice(["mild fatigue", "occasional dyspnea on exertion",
                          "intermittent headaches", "mild lower extremity edema",
                          "stable appetite with no weight change"])
    monitor = rng.choice(["blood pressure", "blood glucose", "weight", "oxygen saturation"])
    control = rng.choice(["well-controlled", "adequately managed", "stable on current regimen",
                          "suboptimally controlled and requiring titration"])
    weeks = rng.choice(["4", "6", "8", "12"])
    return (
        f"The patient, {display}, is a {patient['age']}-year-old "
        f"{patient['sex'].lower()} who presents for a scheduled follow-up visit. "
        f"{pronoun} was last seen approximately 3 months ago and reports "
        f"{rng.choice(['stable', 'generally stable', 'slightly improved'])} symptoms overall. "
        f"The primary concern during today's encounter is ongoing management of {diagnosis}. "
        f"{pronoun} has been adherent to the prescribed regimen of {medication} and notes {symptom}.\n\n"
        f"Review of recent laboratory data: {lab_sentence} "
        f"The results were discussed with the patient in detail. Vital signs obtained today "
        f"were within acceptable parameters for this patient's baseline. {pronoun} continues "
        f"to monitor {monitor} at home and maintains a log for review at each visit.\n\n"
        f"Social history is notable for {patient['smoking'].lower()} smoking status and "
        f"{patient['alcohol'].lower()} alcohol use. No new allergies have been identified "
        f"since the last visit.\n\n"
        f"Assessment and Plan: The patient's {diagnosis} is {control} at this time. "
        f"Continue current pharmacotherapy and schedule follow-up in {weeks} weeks. "
        f"Additional laboratory testing will be ordered to monitor disease progression and "
        f"medication efficacy. The patient was counseled on medication adherence and "
        f"lifestyle modification, verbalized understanding, and agreed to the outlined plan."
    )


# =============================================================================
# PATIENT BUILDER
# =============================================================================

def build_patient(index: int, seed: int, prefix: str, anchor: date, years: int,
                  providers: list[dict[str, Any]], theme_key: str = "primary",
                  include_longitudinal: bool = True) -> dict[str, Any]:
    """Build one clinically coherent synthetic patient record.

    The record carries demographics, an archetype-driven longitudinal profile,
    and every downstream table's rows (conditions, medications, allergies,
    vitals, panels, procedures, immunizations, appointments, histories, social
    context, insurance, contacts, and narrative notes). ``include_longitudinal``
    can be disabled for cheap comparator summaries.
    """

    rng = patient_rng(seed, prefix, index)
    theme = TENANT_THEMES.get(theme_key, TENANT_THEMES["primary"])
    lookback_days = max(365, years * 365)
    history_start = anchor - timedelta(days=lookback_days)

    # --- Demographics ---
    age = int(min(89, max(21, rng.gauss(56, 16))))
    sex = rng.choices(["Male", "Female"], weights=[49, 51])[0]
    first = rng.choice(FIRST_NAMES_MALE if sex == "Male" else FIRST_NAMES_FEMALE)
    last = rng.choice(LAST_NAMES)
    birth_date = anchor - timedelta(days=age * 365 + rng.randint(0, 364))
    height_cm = round(max(145.0, min(200.0, rng.gauss(175 if sex == "Male" else 162, 8))), 1)
    weight_kg = round(max(45.0, min(180.0, rng.gauss(88 if sex == "Male" else 74, 18))), 1)
    bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 1)
    smoking = rng.choices(["Never", "Former", "Current"], weights=[62, 24, 14])[0]
    alcohol = rng.choices(["None", "Social", "Moderate", "Heavy"], weights=[30, 38, 22, 10])[0]
    drug_use = rng.choices(["None", "Former", "Current"], weights=[81, 12, 7])[0]
    city, state = rng.choice(CITY_STATE)
    zip3 = str(rng.randint(100, 999))

    # --- Longitudinal profile ---
    archetype = _choose_archetype(rng, age, bmi, smoking)
    base_risk = 1
    base_risk += 1 if age >= 65 else 0
    base_risk += 1 if bmi >= 30 else 0
    base_risk += 1 if smoking == "Current" else 0
    base_risk += 1 if alcohol == "Heavy" or drug_use == "Current" else 0
    base_risk += 1 if archetype in ("complex_multimorbidity", "renal", "cardiac") else 0
    if rng.random() < HIGH_RISK_RATE:
        base_risk += 1
    risk_tier = "Low" if base_risk <= 1 else ("Moderate" if base_risk <= 3 else "High")
    risk_level = {"Low": "stable", "Moderate": "needs_review", "High": "high"}[risk_tier]
    sdoh_complexity = rng.random() < SDOH_COMPLEXITY_RATE or risk_tier == "High"
    privacy_class = "PII" if rng.random() < PII_RECORD_RATE else "DEIDENTIFIED"
    token = deid_token(f"{seed}:{prefix}:{index}")

    care_gaps: list[tuple[str, str]] = []
    if rng.random() < CARE_GAP_RATE or risk_tier == "High":
        care_gaps.append(rng.choice(CARE_GAP_LIBRARY))
    if risk_tier == "High" and rng.random() < 0.5:
        extra = rng.choice(CARE_GAP_LIBRARY)
        if extra not in care_gaps:
            care_gaps.append(extra)

    provider = providers[(index + rng.randint(0, 3)) % len(providers)]
    care_team = [provider["full_name"],
                 providers[(index + 7) % len(providers)]["full_name"],
                 f"RN {rng.choice(FIRST_NAMES_FEMALE)} {rng.choice(LAST_NAMES)}"]

    if privacy_class == "DEIDENTIFIED":
        display_name = f"Patient {token}"
        occupation = None
        employer = None
    else:
        display_name = f"{first} {last}"
        occupation = rng.choice(OCCUPATIONS) if rng.random() < 0.65 else None
        employer = f"{rng.choice(LAST_NAMES)} {rng.choice(['Group', 'Industries', 'Health', 'Logistics', 'Partners'])}" if occupation and rng.random() < 0.7 else None

    record: dict[str, Any] = {
        "index": index,
        "patient_id": f"{prefix}{index:05d}",
        "mrn": f"MRN-{prefix.strip('PT-')}{index:06d}",
        "first_name": first if privacy_class == "PII" else "Patient",
        "last_name": last if privacy_class == "PII" else token,
        "name": display_name,
        "age": age,
        "sex": sex,
        "birth_date": birth_date.isoformat() if privacy_class == "PII" else birth_date.replace(month=1, day=1).isoformat(),
        "gender_identity": rng.choices(["Woman", "Man", "Nonbinary", "Not documented"], weights=[49, 48, 1, 2])[0],
        "race": rng.choices(RACE_CHOICES, weights=RACE_WEIGHTS)[0],
        "language": rng.choices(LANGUAGES, weights=LANGUAGE_WEIGHTS)[0],
        "zip3": zip3,
        "city": city if privacy_class == "PII" else "Generalized locality",
        "state": state,
        "marital_status": rng.choices(["Married", "Single", "Divorced", "Widowed", "Domestic Partner"], weights=[46, 28, 14, 9, 3])[0],
        "blood_type": rng.choices(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], weights=[35, 6, 9, 2, 3, 1, 38, 6])[0],
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "occupation": occupation,
        "employer": employer,
        "smoking": smoking,
        "alcohol": alcohol,
        "drug_use": drug_use,
        "archetype": archetype,
        "risk_tier": risk_tier,
        "risk_level": risk_level,
        "privacy_class": privacy_class,
        "deid_token": token,
        "consent_status": rng.choices(["full", "limited_research", "treatment_only"], weights=[72, 18, 10])[0],
        "record_quality": rng.choices(["high", "mixed", "requires_reconciliation"], weights=[68, 24, 8])[0],
        "sdoh_complexity": sdoh_complexity,
        "care_gaps": care_gaps,
        "source_systems": rng.sample(["EHR", "Claims", "Lab", "Pharmacy", "Patient Portal", "RPM"], rng.randint(3, 5)),
        "provider": provider,
        "care_team": care_team,
        "primary_diagnosis": ARCHETYPE_PRIMARY_LABEL[archetype],
    }

    # --- Conditions (archetype blueprint first, then thematic extras) ---
    condition_count = rng.randint(4, 7) if risk_tier == "High" else rng.randint(3, 5)
    codes = [code for code in ARCHETYPE_BLUEPRINTS[archetype] if code in ICD10_BY_CODE]
    extra_pool = [code for code, _, _ in ICD10_CATALOG if code not in codes]
    rng.shuffle(extra_pool)
    codes.extend(extra_pool[: max(0, condition_count - len(codes))])
    conditions = []
    for position, code in enumerate(codes[:condition_count]):
        description, category = ICD10_BY_CODE[code]
        if position == 0:
            status = rng.choices(["Active", "Chronic"], weights=[45, 55])[0]
            severity = {"High": ["Moderate", "Severe", "Critical"], "Moderate": ["Mild", "Moderate", "Severe"], "Low": ["Mild", "Moderate"]}[risk_tier]
            severity = rng.choices(severity, weights=[45, 45, 10][: len(severity)])[0]
        else:
            status = rng.choices(["Active", "Chronic", "Resolved", "In Remission"], weights=[40, 32, 18, 10])[0]
            severity = rng.choices(["Mild", "Moderate", "Severe"], weights=[38, 42, 20])[0]
        onset = rand_date(rng, date(2012, 1, 1), anchor - timedelta(days=60))
        gap_note = f" Care gap: {care_gaps[0][1]}." if care_gaps and position == 0 else ""
        conditions.append({
            "code": code,
            "name": description,
            "category": category,
            "onset_date": onset.isoformat(),
            "status": status,
            "severity": severity,
            "is_primary": position == 0,
            "notes": (f"Archetype={archetype}; risk={risk_tier}; quality={record['record_quality']}.{gap_note}" if position == 0 else None),
            "resolved_date": rand_date(rng, onset, anchor).isoformat() if status == "Resolved" else None,
            "provider": provider["full_name"],
        })
    record["conditions"] = conditions
    conditions_text = " | ".join(item["name"] for item in conditions)
    anticoagulated = any("fibrillation" in item["name"].lower() or "thromb" in item["name"].lower() for item in conditions)

    # --- Medications (forced coherence with documented conditions) ---
    med_count = rng.randint(6, 9) if risk_tier == "High" else rng.randint(4, 6)
    lowered = conditions_text.lower()
    forced: list[dict[str, Any]] = []

    def _force(match: str, pool_filter) -> None:
        if match in lowered:
            candidates = [med for med in MEDICATION_CATALOG if pool_filter(med) and med not in forced]
            if candidates:
                forced.append(rng.choice(candidates))

    _force("diabet", lambda med: "Diabetes" in med["indication"])
    _force("hypertens", lambda med: "Hypertension" in med["indication"])
    _force("hyperlipid", lambda med: "Hyperlipidemia" in med["indication"])
    _force("heart failure", lambda med: "Heart Failure" in med["indication"])
    _force("copd", lambda med: "COPD" in med["indication"])
    _force("asthma", lambda med: "Asthma" in med["indication"])
    _force("depress", lambda med: "Depressive" in med["indication"])
    _force("anxiety", lambda med: "Anxiety" in med["indication"])
    _force("kidney", lambda med: "CKD" in med["indication"])
    if anticoagulated:
        _force("", lambda med: "Anticoagulant" in med["class"] or "antagonist" in med["class"].lower())
    remaining = [med for med in MEDICATION_CATALOG if med not in forced]
    rng.shuffle(remaining)
    selected = (forced + remaining)[:med_count]
    medications = []
    for med in selected:
        start = rand_date(rng, date(2018, 1, 1), anchor - timedelta(days=30))
        is_active = rng.random() < 0.78
        adherence = round(rng.uniform(0.55, 0.99), 2)
        if any(gap[0] == "medication_reconciliation" for gap in care_gaps):
            adherence = round(min(adherence, rng.uniform(0.42, 0.72)), 2)
        medications.append({
            "name": med["name"],
            "generic": med["generic"],
            "brand": med["brand"],
            "class": med["class"],
            "dose": med["dose"],
            "frequency": med["freq"],
            "route": med["route"],
            "indication": med["indication"],
            "start_date": start.isoformat(),
            "end_date": rand_date(rng, start, anchor).isoformat() if not is_active else None,
            "status": "active" if is_active else rng.choice(["held", "stopped"]),
            "adherence": adherence,
            "refills": rng.randint(0, 5),
            "pharmacy": rng.choice(PHARMACIES),
            "ndc": rand_ndc(rng),
            "prescriber": provider["full_name"],
        })
    record["medications"] = medications

    # --- Allergies ---
    allergies = []
    pool = list(ALLERGY_CATALOG)
    rng.shuffle(pool)
    for allergen, category, reaction, severity in pool[: rng.randint(0, 3)]:
        allergies.append({
            "allergen": allergen,
            "category": category,
            "reaction": reaction,
            "severity": severity,
            "onset_date": rand_date(rng, date(1995, 1, 1), anchor).isoformat() if rng.random() < 0.7 else None,
            "verified_by": provider["full_name"] if rng.random() < 0.5 else None,
            "active": True,
        })
    record["allergies"] = allergies

    if not include_longitudinal:
        record.update({"vitals": [], "panels": [], "procedures": [], "immunizations": [],
                       "appointments": [], "medical_history": [], "surgical_history": [],
                       "family_history": [], "notes": [], "insurance": [], "contacts": [],
                       "social": {}, "completeness": round(rng.uniform(0.62, 0.98), 2),
                       "open_tasks": len(care_gaps), "key_metrics": {},
                       "last_session_date": (anchor - timedelta(days=rng.randint(0, lookback_days))).isoformat(),
                       "ai_review_status": "needs_review" if risk_level != "stable" else "verified"})
        return record

    # --- Vital signs (archetype-biased longitudinal series) ---
    cardio = archetype in ("cardiometabolic", "cardiac", "renal", "complex_multimorbidity")
    n_vitals = rng.randint(24, 36) if risk_tier == "High" else rng.randint(15, 25)
    base_sbp = rng.randint(132, 168) if cardio else rng.randint(110, 142)
    base_dbp = rng.randint(78, 100) if cardio else rng.randint(65, 88)
    base_hr = rng.randint(72, 102) if archetype in ("respiratory", "complex_multimorbidity") else rng.randint(60, 88)
    base_spo2 = rng.uniform(90.0, 96.0) if archetype == "respiratory" else rng.uniform(94.5, 99.0)
    base_temp = rng.uniform(36.3, 37.1)
    # Gentle improvement or worsening trend over the record window.
    trend = rng.choice((-1, -1, 0, 1)) * rng.uniform(0.0, 8.0)
    vitals = []
    used_days: set[int] = set()
    while len(vitals) < n_vitals:
        day_offset = rng.randint(0, lookback_days - 1)
        if day_offset in used_days:
            continue
        used_days.add(day_offset)
        progress = 1.0 - day_offset / lookback_days
        measured = datetime.combine(anchor - timedelta(days=day_offset), datetime.min.time()).replace(hour=rng.randint(7, 18), minute=rng.choice([0, 15, 30, 45]))
        glucose_base = rng.uniform(125.0, 250.0) if "diabet" in lowered else rng.uniform(72.0, 150.0)
        vitals.append({
            "measured_at": measured.isoformat(),
            "sbp": int(max(88, min(200, base_sbp + trend * progress + rng.randint(-13, 13)))),
            "dbp": int(max(52, min(118, base_dbp + trend * progress * 0.5 + rng.randint(-9, 9)))),
            "hr": int(max(46, min(138, base_hr + rng.randint(-9, 13)))),
            "rr": rng.randint(12, 22),
            "spo2": round(max(87.0, min(100.0, base_spo2 + rng.uniform(-1.8, 1.0))), 1),
            "temp": round(max(35.6, min(39.4, base_temp + rng.uniform(-0.4, 0.5))), 1),
            "weight": round(max(42.0, weight_kg + rng.uniform(-2.5, 2.5)), 1),
            "bmi": bmi,
            "pain": rng.choices(range(11), weights=[22, 11, 11, 15, 13, 9, 8, 5, 3, 2, 1])[0],
            "glucose": round(glucose_base + rng.uniform(-18.0, 24.0), 1),
        })
    vitals.sort(key=lambda item: item["measured_at"])
    record["vitals"] = vitals

    # --- Lab panels + results (condition-biased composition) ---
    preferred = []
    if "diabet" in lowered:
        preferred.append("HbA1c and Fasting Glucose")
    if "hyperlipid" in lowered or "cholesterol" in lowered:
        preferred.append("Lipid Panel")
    if "kidney" in lowered:
        preferred.append("Renal Function Panel")
    if "heart failure" in lowered:
        preferred.append("Cardiac Biomarker Panel")
    if anticoagulated:
        preferred.append("Coagulation Panel")
    preferred.append("Comprehensive Metabolic Panel")
    filler = [name for name in PANEL_DEFINITIONS if name not in preferred]
    rng.shuffle(filler)
    chosen = (preferred + filler)[: rng.randint(3, 5)]
    panels = []
    key_metrics: dict[str, Any] = {}
    for panel_name in chosen:
        ordered = rand_date(rng, history_start, anchor - timedelta(days=7))
        collected = ordered + timedelta(days=rng.randint(0, 2))
        eligible = [test for category in PANEL_DEFINITIONS[panel_name] for test in LABS_BY_CATEGORY.get(category, [])]
        take = min(len(eligible), rng.randint(5, 8)) if len(eligible) > 5 else len(eligible)
        results = []
        for test in rng.sample(eligible, take):
            value, is_abnormal, flag, status = _lab_value(rng, test, conditions_text, anticoagulated)
            results.append({
                "test": test["name"], "loinc": test["loinc"], "value": value,
                "unit": test["unit"], "low": test["low"], "high": test["high"],
                "is_abnormal": is_abnormal, "flag": flag, "status": status,
            })
            metric_key = test["name"].lower().replace(" ", "_").replace(",", "")
            key_metrics[metric_key] = {"value": value, "unit": test["unit"], "flag": flag,
                                       "low": test["low"], "high": test["high"]}
        panels.append({
            "panel_name": panel_name,
            "ordered_date": ordered.isoformat(),
            "collected_date": collected.isoformat(),
            "resulted_date": (collected + timedelta(days=rng.randint(0, 3))).isoformat(),
            "facility": rng.choice(theme["lab_facilities"]),
            "accession": rand_accession(rng),
            "status": "Final",
            "ordered_by": provider["full_name"],
            "results": results,
        })
    record["panels"] = panels
    record["key_metrics"] = key_metrics

    # --- Procedures ---
    procedures = []
    for _ in range(rng.randint(2, 4)):
        code, description, category = rng.choice(CPT_CATALOG)
        status = rng.choices(["Completed", "Scheduled", "Cancelled"], weights=[76, 14, 10])[0]
        when = rand_date(rng, history_start, anchor) if status != "Scheduled" else rand_date(rng, anchor, anchor + timedelta(days=90))
        procedures.append({
            "name": description,
            "code": code,
            "category": category,
            "date": when.isoformat(),
            "facility": rng.choice(theme["facilities"]),
            "indication": f"Management of {conditions[0]['name']}",
            "outcome": rng.choice(["Successful, no complications", "Technically successful",
                                   "Completed without adverse events", "Tolerated well"]) if status == "Completed" else None,
            "duration_minutes": rng.randint(15, 180) if status == "Completed" else None,
            "anesthesia": rng.choice(["None", "Local anesthesia", "General anesthesia", "Sedation", None]),
            "status": status,
            "performer": provider["full_name"],
        })
    record["procedures"] = procedures

    # --- Immunizations (age-gated; vaccination care gap leaves pneumococcal off) ---
    immunizations = []
    vaccine_pool = [vaccine for vaccine in VACCINE_CATALOG
                    if not (vaccine[1] in ("PPSV23", "PCV13") and age < 60)
                    and not (vaccine[1] == "RZV" and age < 50)]
    has_vaccine_gap = any(gap[0] == "vaccination" for gap in care_gaps)
    if has_vaccine_gap:
        vaccine_pool = [vaccine for vaccine in vaccine_pool if vaccine[1] not in ("PPSV23", "PCV13")]
    rng.shuffle(vaccine_pool)
    for vaccine_name, abbreviation, cvx, manufacturer, site, route in vaccine_pool[: rng.randint(4, 7)]:
        administered = rand_date(rng, date(2015, 1, 1), anchor)
        immunizations.append({
            "name": vaccine_name, "abbreviation": abbreviation, "cvx": cvx,
            "date": administered.isoformat(), "administered_by": provider["full_name"],
            "lot": rand_lot(rng), "manufacturer": manufacturer, "site": site, "route": route,
            "dose_number": rng.randint(1, 2), "series_complete": rng.random() < 0.7,
            "expiration": (administered + timedelta(days=rng.randint(180, 730))).isoformat(),
        })
    record["immunizations"] = immunizations

    # --- Appointments (past + future; no-shows skew with SDoH complexity) ---
    appointments = []
    n_appointments = rng.randint(8, 12)
    noshow_weights = [62, 10, 22, 6] if sdoh_complexity else [78, 9, 8, 5]
    for position in range(n_appointments):
        if position < n_appointments - 2:
            when = rand_date(rng, history_start, anchor)
            status = rng.choices(["Completed", "Cancelled", "No-Show", "Rescheduled"], weights=noshow_weights)[0]
        else:
            when = rand_date(rng, anchor + timedelta(days=1), anchor + timedelta(days=180))
            status = "Scheduled"
        hour = rng.randint(8, 16)
        minute = rng.choice([0, 15, 30, 45])
        duration = rng.choice([15, 30, 45, 60])
        appointments.append({
            "date": when.isoformat(),
            "start": f"{hour:02d}:{minute:02d}",
            "end": f"{min(hour + (minute + duration) // 60, 17):02d}:{(minute + duration) % 60:02d}",
            "type": rng.choice(APPOINTMENT_TYPES),
            "department": provider["department"],
            "facility": rng.choice(theme["facilities"]),
            "status": status,
            "reason": rng.choice(VISIT_REASONS),
            "follow_up": rng.random() < 0.4,
            "provider": provider["full_name"],
        })
    record["appointments"] = appointments

    # --- Histories ---
    history_pool = list(PAST_MEDICAL_CONDITIONS)
    rng.shuffle(history_pool)
    record["medical_history"] = [
        {"condition": condition, "onset_year": rng.randint(1985, 2018),
         "resolution_year": rng.randint(2019, 2024) if rng.random() < 0.6 else None,
         "is_chronic": rng.random() < 0.35}
        for condition in history_pool[: rng.randint(3, 5)]
    ]
    surgical_pool = list(SURGICAL_PROCEDURES)
    rng.shuffle(surgical_pool)
    record["surgical_history"] = [
        {"procedure": name, "cpt": code, "date": rand_date(rng, date(1995, 1, 1), anchor - timedelta(days=90)).isoformat(),
         "facility": rng.choice(theme["facilities"]), "surgeon": providers[(index + offset) % len(providers)]["full_name"],
         "anesthesia": anesthesia, "outcome": "Successful, patient tolerated procedure well",
         "indication": "Elective surgical intervention for indicated condition"}
        for offset, (name, code, anesthesia) in enumerate(surgical_pool[: rng.randint(0, 3)])
    ]
    relation_pool = list(RELATIONS)
    condition_pool = list(FAMILY_CONDITIONS)
    rng.shuffle(relation_pool)
    rng.shuffle(condition_pool)
    family = []
    for relation, condition in zip(relation_pool, condition_pool[: rng.randint(3, 6)]):
        deceased = rng.random() < 0.3
        family.append({"relation": relation, "condition": condition,
                       "age_of_onset": rng.randint(35, 75) if (deceased or rng.random() < 0.6) else None,
                       "is_deceased": deceased, "cause_of_death": condition if deceased else None})
    record["family_history"] = family

    # --- Social determinants ---
    record["social"] = {
        "housing": rng.choices(["stable housing", "temporary housing", "housing insecurity"], weights=[45, 33, 22] if sdoh_complexity else [88, 9, 3])[0],
        "transportation": rng.choices(["reliable", "limited", "requires assistance"], weights=[38, 40, 22] if sdoh_complexity else [80, 15, 5])[0],
        "food_security": rng.choices(["secure", "intermittent insecurity", "high insecurity"], weights=[42, 38, 20] if sdoh_complexity else [86, 11, 3])[0],
        "financial_strain": rng.choices(["low", "moderate", "high"], weights=[18, 40, 42] if sdoh_complexity else [58, 32, 10])[0],
        "living_situation": rng.choice(["alone", "with spouse", "with family", "assisted living"]),
        "packs_per_day": round(rng.uniform(0.5, 2.0), 1) if smoking in ("Current", "Former") else None,
        "smoking_years": rng.randint(3, 40) if smoking in ("Current", "Former") else None,
        "drinks_per_week": rng.randint(1, 21) if alcohol not in ("None",) else None,
        "exercise": rng.choice(["Sedentary", "Light (1-2 days/week)", "Moderate (3-4 days/week)", "Active (5+ days/week)"]),
        "diet": rng.choice(["Regular", "Low-sodium", "Diabetic diet", "Mediterranean", "Low-carb", None]),
        "education": rng.choice(EDUCATION_LEVELS),
        "employment": rng.choice(["Unemployed", "Disabled", "Employed part-time", "Retired"] if sdoh_complexity else EMPLOYMENT_STATUS),
    }

    # --- Insurance ---
    insurance = []
    n_policies = 2 if (risk_tier == "High" and rng.random() < 0.5) else 1
    for position in range(n_policies):
        coverage = rng.choices(["HMO", "PPO", "EPO", "HDHP", "Medicare", "Medicaid", "Self-Pay"], weights=[24, 32, 7, 7, 16, 10, 4])[0]
        if age >= 65 and rng.random() < 0.6:
            coverage = "Medicare"
        if sdoh_complexity and rng.random() < 0.3:
            coverage = "Medicaid"
        start = rand_date(rng, date(2017, 1, 1), anchor - timedelta(days=30))
        insurance.append({
            "provider": rng.choice(INSURANCE_PROVIDERS),
            "plan_name": f"{coverage} {rng.choice(['Gold', 'Silver', 'Bronze', 'Platinum'])} {'Care Management' if risk_tier == 'High' else rng.choice(['Standard', 'Value', 'Preferred'])} Plan",
            "policy_number": f"POL{rng.randint(1000000, 9999999)}",
            "group_number": f"GRP{rng.randint(10000, 99999)}",
            "member_id": f"MBR{rng.randint(100000, 999999)}",
            "coverage_type": coverage,
            "subscriber": display_name if privacy_class == "PII" else token,
            "relation": "Self",
            "start_date": start.isoformat(),
            "end_date": None if rng.random() < 0.85 else (start + timedelta(days=rng.randint(365, 730))).isoformat(),
            "deductible": float(rng.choice([250, 500, 1000, 1500, 2000, 3000, 5000])),
            "copay": float(rng.choice([0, 10, 20, 25, 30, 40, 50])),
            "oop_max": float(rng.choice([2500, 3000, 5000, 6850, 8000, 10000])),
            "is_primary": position == 0,
        })
    record["insurance"] = insurance

    # --- Emergency contacts ---
    contacts = []
    for order in range(1, rng.randint(1, 3) + 1):
        if privacy_class == "DEIDENTIFIED":
            contact_name = f"Deidentified Contact {order}"
        else:
            contact_name = f"{rng.choice(FIRST_NAMES_FEMALE + FIRST_NAMES_MALE)} {last if rng.random() < 0.6 else rng.choice(LAST_NAMES)}"
        contacts.append({
            "order": order, "name": contact_name,
            "relationship": rng.choice(["Spouse", "Parent", "Sibling", "Child", "Friend"]),
            "phone": f"(555) {rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
            "is_primary": order == 1,
        })
    record["contacts"] = contacts

    # --- Narrative clinical notes grounded in this patient's actual data ---
    notes = []
    primary = conditions[0]["name"]
    for _ in range(rng.randint(3, 5)):
        note_date = rand_date(rng, history_start, anchor)
        med = rng.choice(medications)
        abnormal = [result for panel in panels for result in panel["results"] if result["is_abnormal"]]
        if abnormal:
            lab_ref = rng.choice(abnormal)
            lab_sentence = (f"{lab_ref['test']} returned {lab_ref['value']} {lab_ref['unit']} "
                            f"({lab_ref['status']}; reference {lab_ref['low']}-{lab_ref['high']}).")
        else:
            lab_sentence = "All recent laboratory values fell within their reference ranges."
        notes.append({
            "date": note_date.isoformat(),
            "type": rng.choice(CLINICAL_NOTE_TYPES),
            "author": provider["full_name"],
            "text": generate_clinical_note(rng, record, primary, med["name"], lab_sentence),
            "signed_at": datetime.combine(note_date, datetime.min.time()).replace(hour=rng.randint(8, 20), minute=rng.choice([0, 15, 30])).isoformat(),
        })
    notes.sort(key=lambda item: item["date"])
    record["notes"] = notes

    # --- App-facing summary fields ---
    quality_completeness = {"high": (0.86, 0.99), "mixed": (0.72, 0.9), "requires_reconciliation": (0.58, 0.78)}[record["record_quality"]]
    record["completeness"] = round(rng.uniform(*quality_completeness), 2)
    record["open_tasks"] = len(care_gaps) + (rng.randint(1, 3) if risk_tier == "High" else rng.randint(0, 1))
    record["ai_review_status"] = "needs_review" if (risk_level != "stable" and rng.random() < 0.75) else "verified"
    record["last_session_date"] = (anchor - timedelta(days=rng.randint(0, min(120, lookback_days)))).isoformat()
    return record
