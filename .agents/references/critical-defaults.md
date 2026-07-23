# Critical Defaults

Always-on behaviors for the agent.

- **Apply brevity rules**: Always format conversations using Caveman-Micro style unless exceptions trigger.
- **Load durable memory**: Read root `MEMORY.md` plus `.agents/memory/project.md`
  at session start; lifecycle hooks inject shared harness context.
- **Use machine-readable handoffs**: Delegated agents write a sanitized handoff
  before returning control to parent.
- **Run the Pre-Commit Gate**: Ensure all format, check, and test scripts pass successfully.
- **Redact secrets**: Ensure any variables, tokens, or environment outputs are redacted.
- **Maintain CLAUDE.md and AGENTS.md sync**: Always execute the sync script when editing rules, commands, or index files.
- **Respect wiki auto-sync**: `scripts/sync_wiki.py` (Stop hook) owns `Project Wiki/_generated/` and all `AUTO:*` marker blocks. Hand-edit only the hand-written wiki notes; review `Project Wiki/_generated/Drift Report.md` for coverage gaps.
