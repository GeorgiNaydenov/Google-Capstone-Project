# scripts - Harness Management Utilities

Maintenance and showcase scripts for the project harness and clinical demo data.

## Scripts

| Script | Purpose |
|--------|---------|
| `check_harness.py` | Validates harness integrity: required directories, root indexes, rule files, and configuration consistency. |
| `sync_harness.py` | Mirrors `.claude/` to `.agents/` and `CLAUDE.md` to `AGENTS.md`. |
| `generate_extraction_showcase.py` | Generates uploadable PNG clinical sheets with patient data, OCR targets, structured fields, and embedded visualizations. |
| `generate_multimodal_patient_showcase.py` | Generates Q&A bundles with uploadable PDFs, mixed DOCX/PDF/MD/TXT/JSON knowledge-base files, citations, tables, charts, and prompts. |
| `generate_database_showcase.py` | Generates a 10,000-patient default SQLite cohort across 4 years with SQL examples, textual insights, Plotly specs, and Matplotlib charts. |

## Usage

```powershell
# Validate harness
python scripts/check_harness.py

# Sync harness files
python scripts/sync_harness.py

# Generate full showcase data
python scripts/generate_extraction_showcase.py
python scripts/generate_multimodal_patient_showcase.py
python scripts/generate_database_showcase.py --replace

# Smaller smoke runs
python scripts/generate_multimodal_patient_showcase.py --bundle-count 1 --pdfs-per-bundle 12 --kb-docs-per-bundle 10
python scripts/generate_database_showcase.py --patient-count 1000 --replace
```

Full-scale defaults:

- Extraction: 48 uploadable PNG clinical sheets.
- Multimodal Q&A: 12 patient bundles, 432 PDFs, 300 mixed knowledge-base documents.
- Database intelligence: 10,000 patients across 4 years plus SQL, insight, Plotly, and Matplotlib artifacts.
