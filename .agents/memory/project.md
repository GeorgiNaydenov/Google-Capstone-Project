# Project Harness Memory

## Sources of truth

- `.agents/` is executable Claude Code harness source.
- `.agents/` is portable generated mirror plus destination-specific assets.
- `CLAUDE.md` is canonical project instruction index; `AGENTS.md` is generated.
- `scripts/sync_harness.py` mirrors incrementally and must never delete
  destination-only `.agents` content.
- `scripts/check_harness.py` validates structure, indexes, hook wiring, agent
  profiles, memory contracts, and logical mirror equality.

## State and memory boundaries

- `.agents/state/` is gitignored ephemeral lifecycle state. Never store durable
  architecture facts or credentials there.
- `.agents/memory/` is curated shared project memory.
- `.agents/agent-memory/<name>/MEMORY.md` is project-scoped learned memory for a
  named subagent.
- Root `MEMORY.md` is generated workspace inventory, not conversational memory.
- ADK `temp:` state must be deleted before long-term memory persistence.
- PHI, PII, and secrets must be recursively removed at memory and A2A boundaries.

## Working rules

- Preserve unrelated dirty-worktree changes.
- Use named files for git staging; never stage all files.
- Run targeted tests first, then harness and full gates.
- Model-dependent behavior belongs in ADK eval; deterministic contracts belong
  in pytest.
