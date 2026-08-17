---
title: Development Workflow
type: process
status: active
updated: 2026-07-23
source: CLAUDE.md, .claude/settings.json, scripts/
tags:
  - process
  - bpmn
  - harness
---

# Development Workflow

```mermaid
flowchart TD
    START["SessionStart: recover state + inject memory"]
    AUDIT{"PreToolUse: harness valid?"}
    WORK["Inspect / edit / test"]
    SUB["SubagentStart / SubagentStop: ownership + handoff"]
    GATE["Pre-commit gate"]
    STOP["Stop: checkpoint turn"]
    SYNC["sync_wiki + incremental sync_harness"]
    END["SessionEnd: mark state ended"]

    START --> AUDIT
    AUDIT -->|pass| WORK
    AUDIT -->|fail| WORK
    WORK -. delegate .-> SUB -. return .-> WORK
    WORK --> GATE --> STOP --> SYNC
    SYNC --> END
```

Key facts:

- `harness_runtime.py` manages SessionStart, PreCompact, subagent handoff, Stop,
  and SessionEnd transitions under gitignored `.claude/state/`.
- `check_harness.py` runs before every tool call and validates executable agent,
  memory, state, hook, index, and mirror contracts.
- `sync_wiki.py` is deterministic and idempotent; sync warnings land in
  [[Drift Report]].
- `sync_harness.py` only removes files named by its previous generated manifest,
  so destination-only `.agents/` assets survive.
- Machine-owned pages and `AUTO:*` blocks are never hand-edited.

Related: [[Claude Harness]] · [[Testing and Eval]]
