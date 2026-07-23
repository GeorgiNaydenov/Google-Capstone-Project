# Agent Handoff

Create a machine-readable handoff before delegated work returns to parent.

```powershell
uv run --no-project --python 3.11 python scripts/harness_runtime.py handoff `
  --from AGENT_NAME `
  --to root `
  --summary "Outcome, blockers, verification." `
  --file path/to/relevant-file
```

Do not include secrets, PHI, raw prompts, or hidden reasoning.
