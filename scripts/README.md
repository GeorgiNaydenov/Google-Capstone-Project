# scripts — Harness Management Utilities

Maintenance and showcase scripts for the project harness and clinical demo data.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `check_harness.py` | Validates harness integrity — checks required directories, root indexes (`CLAUDE.md`, `AGENTS.md`), rule files, and configuration consistency. Used as a pre-tool-use hook in `.claude/settings.json` |
| `sync_harness.py` | Mirrors `.claude/` directory to `.agents/` and `CLAUDE.md` to `AGENTS.md` — keeps the Antigravity-compatible harness in sync with the Claude Code harness |
| `generate_database_showcase.py` | Generates synthetic database intelligence showcase data — SQL queries, results, charts, and insights for demo mode |
| `generate_extraction_showcase.py` | Generates synthetic image extraction showcase data — clinical images, OCR results, structured fields, and confidence scores |
| `generate_multimodal_patient_showcase.py` | Generates synthetic multimodal patient Q&A showcase data — questions, evidence, citations, and answers |

---

## Usage

```powershell
# Validate harness (also runs automatically as a Claude Code hook)
python scripts/check_harness.py

# Sync harness files
python scripts/sync_harness.py

# Generate showcase data
python scripts/generate_database_showcase.py
python scripts/generate_extraction_showcase.py
python scripts/generate_multimodal_patient_showcase.py
```

---

## Harness Hook

`check_harness.py` is configured as a `PreToolUse` hook in `.claude/settings.json`. It runs automatically before every tool call to verify the project structure hasn't drifted. This ensures consistency between the harness configuration and the actual file layout.
