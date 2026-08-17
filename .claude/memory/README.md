# Shared Harness Memory

Files here are team-authored durable context. They are not Claude Code auto
memory and are not runtime state.

- `project.md`: stable repository facts loaded by lifecycle hooks.
- `handoff-protocol.md`: required cross-agent completion contract.

Per-agent learned memory lives in `.claude/agent-memory/<agent>/MEMORY.md`.
Ephemeral session and handoff records live in gitignored `.claude/state/`.
