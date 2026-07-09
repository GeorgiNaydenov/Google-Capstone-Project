---
title: Development Workflow
type: process
status: active
updated: 2026-07-04
source: CLAUDE.md, .claude/settings.json, scripts/
tags:
  - process
  - bpmn
  - harness
---

# Development Workflow

How work happens on this repository, including the automated wiki/harness sync layer. Lanes: Developer/Claude, Hooks, Sync.

```mermaid
flowchart TD
    subgraph LANE_DEV["Lane: Developer / Claude"]
        EDIT["Edit code / docs / wiki"]
        TEST["uv run pytest tests/ -v"]
        GATE["Pre-commit gate:<br/>format + harness audit + pytest"]
        COMMIT["git commit (files staged by name)"]
    end

    subgraph LANE_HOOK["Lane: Hooks (.claude/settings.json)"]
        PRE{"PreToolUse:<br/>check_harness.py passes?"}
        STOP["Stop hook: sync_wiki.py<br/>(end of each work turn)"]
    end

    subgraph LANE_SYNC["Lane: Deterministic sync (scripts/sync_wiki.py)"]
        GEN["Regenerate _generated/ pages:<br/>Module Inventory, Test Inventory,<br/>Harness Index, Changelog, Drift Report"]
        DEP["Rewrite AUTO:DEPGRAPH block<br/>in Module Dependency Graph"]
        CMD["Rewrite AUTO:STRUCTURE block<br/>in CLAUDE.md + root MEMORY.md"]
        MIRROR["sync_harness.py:<br/>.claude -> .agents, CLAUDE.md -> AGENTS.md"]
    end

    PRE -->|fail: fix harness first| EDIT
    PRE -->|pass| EDIT
    EDIT --> TEST --> GATE --> COMMIT
    COMMIT --> STOP
    EDIT -.->|every turn end| STOP
    STOP --> GEN --> DEP --> CMD --> MIRROR --> DONE([Wiki + harness up to date])
```

Key facts:

- `check_harness.py` runs before **every** tool call (PreToolUse, matcher `.*`) and fails fast on harness drift — see [[Claude Harness]].
- `sync_wiki.py` runs at the end of every Claude work turn (Stop hook). It is deterministic (stdlib only, no LLM), idempotent, and always exits 0 — sync problems land in [[Drift Report]] instead of blocking.
- Machine-owned pages live in `_generated/`; AUTO-marked blocks in [[Module Dependency Graph]], `CLAUDE.md`, and root `MEMORY.md` are rewritten in place. Hand-written prose is never touched.
- After any CLAUDE.md change, `sync_harness.py` must mirror it to AGENTS.md — the sync script does this automatically as its last step.

Related: [[Claude Harness]] · [[Testing and Eval]]
