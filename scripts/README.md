# scripts - Harness Management Utilities

Maintenance and showcase scripts for the project harness and clinical demo data.

## Scripts

| Script | Purpose |
|--------|---------|
| `check_harness.py` | Validates harness integrity: required directories, root indexes, rule files, and configuration consistency. |
| `sync_harness.py` | Mirrors `.claude/` to `.agents/` and `CLAUDE.md` to `AGENTS.md`. |
| `showcase_clinical_core.py` | Shared enterprise cohort engine used by the database, extraction, and multimodal generators for deterministic patient IDs, tenant rosters, reference codes, medications, care gaps, labs, privacy, and source-system metadata. |
| `generate_extraction_showcase.py` | Generates uploadable five-patient PDF extraction packets with per-patient PNG previews, OCR targets, structured fields, and embedded visualizations. |
| `generate_multimodal_patient_showcase.py` | Generates Q&A bundles with uploadable PDFs, mixed DOCX/PDF/MD/TXT/JSON knowledge-base files, citations, tables, charts, and prompts. |
| `generate_database_showcase.py` | Generates a 1,500-patient clinically coherent SQLite cohort across 4 years (archetype-driven diagnoses, condition-biased labs, longitudinal vitals, payer/SDoH context, narrative notes) with SQL examples, textual insights, Plotly specs, and Matplotlib charts. |
| `generate_extraction_showcase_demo2.py` | Generates a distinct second-platform synthetic extraction picker, five-patient PDF packets, and app manifest. |
| `generate_multimodal_patient_showcase_demo2.py` | Generates a distinct second-platform multimodal Q&A corpus with PDFs, knowledge-base files, citations, tables, and charts. |
| `generate_database_showcase_demo2.py` | Generates a distinct second-platform governed SQLite cohort and app-facing dashboard/storage seed contract. |

## Usage

```powershell
# Validate harness
python scripts/check_harness.py

# Sync harness files
python scripts/sync_harness.py

# IMPORTANT: stop any running backend first (uvicorn holds the SQLite file open,
# which blocks --replace). Then regenerate and restart the app.

# Research Clinic tenant (primary)
python scripts/generate_database_showcase.py --replace
python scripts/generate_extraction_showcase.py
python scripts/generate_multimodal_patient_showcase.py

# Northstar Health tenant (demo2)
python scripts/generate_database_showcase_demo2.py --replace
python scripts/generate_extraction_showcase_demo2.py
python scripts/generate_multimodal_patient_showcase_demo2.py

# Smaller smoke runs
python scripts/generate_multimodal_patient_showcase.py --bundle-count 1 --pdfs-per-bundle 12 --kb-docs-per-bundle 10
python scripts/generate_database_showcase.py --patient-count 1000 --replace
python scripts/generate_database_showcase_demo2.py --patient-count 1000 --replace
```

Full-scale defaults:

- Extraction: 48 patient-level extraction targets packaged into five-patient PDF source files, with PNG previews for the frontend picker.
- Multimodal Q&A: 12 enterprise patient bundles from the same tenant ID space, 432 PDFs, 300 mixed knowledge-base documents.
- Database intelligence: 1,500 patients per tenant across 4 years (about 220,000 relational rows), matching the enterprise seeder's per-patient depth, plus SQL, insight, Plotly, and Matplotlib artifacts.
- Database schema: normalized patient demographics, reference codes, providers, insurance, emergency contacts, conditions, medications, allergies, encounters, appointments, immunizations, vital signs, care gaps, procedures, medical/surgical/family/social history, notes, labs, imaging, documents, vectors, and audit rows.

The generators also write app-facing manifests. The deterministic product loader reads those manifests so generated records populate dashboard KPIs, storage totals, schema discovery, SQL examples, synthetic extraction choices, multimodal evidence, and knowledge-base file lists instead of sitting as disconnected artifacts.

## Cross-use-case coherence

All three generators derive patients deterministically from `(seed, prefix, index)`
via `showcase_clinical_core.build_patient`, so the SQL cohort, the extraction
packets, and the Q&A bundles for one tenant describe the same patients. Run all
three scripts for a tenant with their default seeds to keep that linkage intact.
The app loads whichever tenants have generated manifests; tenants without them
fall back to small built-in fixtures.
