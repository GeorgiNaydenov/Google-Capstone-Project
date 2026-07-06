# Custom Clinical Showcase Data Generation Guide

This guide describes how to use custom templates to seed the database, render clinical intake forms (OCR target images), and compile multimodal patient Q&A bundles.

With template-based generation, you can customize the synthetic cohort to represent specific disease courses, specific lab trends, or specific multimodal evidence packets (PDF, DOCX, Markdown, images, Plotly charts).

---

## Directory Layout

All templates and sample files are located under:
```
showcase_templates/
  ├── database_template.json       # Empty layout for seeding SQLite tables
  ├── database_sample.json         # Seeding sample (1 patient, session, audit trail)
  ├── extraction_template.json     # Empty layout for PIL intake form rendering
  ├── extraction_sample.json       # Intake form sample (Nora Evans, EF echocardiogram note)
  ├── multimodal_template.json     # Empty layout for PDF / KB / Matplotlib bundles
  └── multimodal_sample.json       # Multimodal sample (David Okafor, retinopathy)
```

---

## 1. Persisted SQLite Cohort Seeding

Uses `scripts/generate_database_showcase.py` to insert patients, notes, timeline encounters, labs, and session logs directly into the persisted SQLite schemas.

### Seeding Command
```bash
python scripts/generate_database_showcase.py --template showcase_templates/database_sample.json --replace
```

### JSON Schema Breakdown
- **`patients_core`**: The main demographic and risk driver table.
  - `extended_data`: A nested JSON block that populates the flexible demographics, care team list, medications list, allergies list, and ICD-10 diagnoses.
- **`sessions`**: Clinical session logs that track image uploads and ingestion verification statuses.
- **`extracted_fields`**: Key-value findings extracted from forms (e.g., `tumor_size_cm`, `ejection_fraction_pct`).
- **`clinical_notes`**: Textual patient notes (e.g., progress notes, consults).
- **`lab_results`**: Quantitative lab measurements with standard references and high/low alert flags.
- **`imaging_studies`**: Imaging scan metadata linked to Google Cloud Storage (GCS) URIs.
- **`audit_log`**: Security and tracking records auditing database index actions.
- **`documents` & `document_chunks`**: Document processor files and raw text chunks for vector indices.
- **`qa_memory`**: Historical Q&A logs linking questions to SQL query results.

---

## 2. Intake Form Image & OCR Ingestion

Uses `scripts/generate_extraction_showcase.py` to draw custom patient data, clinical notes, tabular values, and a patient metric trend line chart onto a clean PIL canvas, outputting a high-fidelity `.png` intake sheet alongside ground-truth `.json` metrics.

### Rendering Command
```bash
python scripts/generate_extraction_showcase.py --template showcase_templates/extraction_sample.json --output showcase_data/extraction_output
```

### JSON Schema Breakdown
- **`patient`**: Demographic dictionary drawn into the header block of the intake sheet.
- **`encounter_date`**: The date stamp drawn in the top-right corner of the sheet.
- **`note`**: Multi-line clinical summary drawn as the main OCR text block.
- **`fields`**: List of measurements populated into the tabular section of the intake form. Used by evaluations as the ground truth.
- **`trend_values`**: List of floats drawn as a trend line chart at the bottom-right corner of the form.

---

## 3. Multimodal Patient Q&A Bundles

Uses `scripts/generate_multimodal_patient_showcase.py` to build complete patient dossiers containing:
- Multi-format knowledge-base documents (PDF, DOCX, Markdown, TXT, JSON)
- Custom Matplotlib multi-page report packets
- Interactive Plotly chart panel configurations
- Dense timeline, image, and citation schemas

### Compilation Command
```bash
python scripts/generate_multimodal_patient_showcase.py --template showcase_templates/multimodal_sample.json --output showcase_data/multimodal_output
```

### JSON Schema Breakdown
- **`patient`**: Patient profile containing care team, active medications, and allergies.
- **`timeline`**: Encounter timeline drawn into the Matplotlib timeline page.
- **`labs`**: Lab trend data points drawn into both the tabular pages and trend charts.
- **`images`**: Imaging studies linked to GCS URIs.
- **`notes`**: Textual notes used to generate different knowledge base documents.
- **`comparator_cohort`**: Cohort of comparable patients populated in the Plotly panels.
- **`qa_prompts`**: Predefined Q&A prompts containing expected sources and ground-truth answers.

---

## Test Verification

To run formatting, schema verification, and assert that database and template integrations succeed:
```bash
pytest tests/test_template_generators.py -v
```
