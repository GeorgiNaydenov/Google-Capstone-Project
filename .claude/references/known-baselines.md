# Known Baselines

Do not hardcode test counts here; `MEMORY.md` and generated Test Inventory own
current counts.

- Harness structure: `python scripts/check_harness.py`.
- Source safety: `python scripts/check_source_safety.py`.
- Python correctness: `pytest tests/ -v` with model tests skipped when
  credentials are absent.
- Frontend correctness: commands defined by `frontend/package.json`.
- Agent behavior: ADK eval, separate from deterministic pytest.
- Global `agents-cli` launcher may be environment-specific; repository scripts
  and `uv.lock` remain canonical.
