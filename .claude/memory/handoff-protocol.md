# Cross-Agent Handoff Protocol

Every delegated agent returns control with a machine-readable handoff.

Required fields:

- `from`: exact subagent name.
- `to`: recipient agent name or `root`.
- `summary`: outcome, blockers, and verification results; maximum 2,000 chars.
- `files`: only files inspected or changed for this task.

Create an explicit handoff:

```powershell
uv run --no-project --python 3.11 python scripts/harness_runtime.py handoff `
  --from memory-state-reviewer `
  --to root `
  --summary "Recursive memory filtering implemented; targeted tests pass." `
  --file capstone_agent/memory.py `
  --file tests/test_memory.py
```

`SubagentStop` also records a sanitized fallback handoff automatically.
Lifecycle records are local under `.claude/state/handoffs/` and must not be
committed. Durable reusable findings belong in agent `MEMORY.md`.
