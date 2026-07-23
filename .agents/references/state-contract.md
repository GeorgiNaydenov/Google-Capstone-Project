# Harness State Contract

`scripts/harness_runtime.py` owns local state under `.agents/state/`.

## Session schema

- `schema_version`: state contract version.
- `session_id`: Claude Code session identifier.
- `status`: `active`, `compacting`, `waiting`, or `ended`.
- `started_at`, `updated_at`, `ended_at`: UTC timestamps.
- `turn_count`: completed root turns.
- `active_agents`: current subagents keyed by runtime id.
- `completed_agents`: bounded recent completion metadata.

## Lifecycle

`SessionStart` initializes or resumes state and injects project memory.
`PreCompact` snapshots metadata. `SubagentStart` registers ownership and injects
pending handoffs. `SubagentStop` creates a sanitized fallback handoff. `Stop`
increments turn state and runs deterministic wiki/harness sync. `SessionEnd`
marks state ended without deleting recovery data.

State is gitignored and may be deleted safely between sessions. Durable facts
belong in `.agents/memory/` or project-scoped subagent memory.
