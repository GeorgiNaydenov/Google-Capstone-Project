---
title: Claude Harness
type: harness
status: active
updated: 2026-07-23
source: CLAUDE.md, .claude/, scripts/
tags:
  - harness
---

# Claude Harness

The `.claude/` harness controls and validates agent-assisted development. The
live machine-generated inventory is [[Harness Index]].

## Executable components

| Area | Contents |
|------|----------|
| Rules | Engineering, security, testing, and response constraints |
| Skills | On-demand project workflows |
| Agents | Named specialists with bounded ownership and tools |
| Memory | Shared project facts, handoff contract, and per-agent learned memory |
| State | Gitignored session, compaction, active-agent, and handoff records |
| Commands | Harness audit, status, handoff, sync, and pre-commit gates |

## Named agents

| Agent | Responsibility |
|-------|----------------|
| `harness-governor` | Hooks, sync, state contracts, and harness integrity |
| `memory-state-reviewer` | ADK session, memory, compaction, and A2A boundaries |
| `security-reviewer` | Read-only data-leak and callback boundary review |
| `verification-runner` | Deterministic gates and reproducible failure reports |

Each profile uses project-scoped persistent memory and writes a sanitized
handoff before returning control.

## Lifecycle hooks

| Hook | Script | Purpose |
|------|--------|---------|
| `SessionStart` | `scripts/harness_runtime.py` | Initializes/resumes state and injects durable project memory |
| `PreToolUse` (matcher `*`) | `scripts/check_harness.py` | Verifies profiles, memory, hook wiring, indexes, and mirror integrity |
| `PreCompact` | `scripts/harness_runtime.py` | Snapshots local state before context compaction |
| `SubagentStart` | `scripts/harness_runtime.py` | Registers ownership and injects pending handoffs |
| `SubagentStop` | `scripts/harness_runtime.py` | Records completion and a sanitized fallback handoff |
| `Stop` | `scripts/harness_runtime.py` | Checkpoints turn state, then runs wiki/harness sync |
| `SessionEnd` | `scripts/harness_runtime.py` | Marks session ended without deleting recovery state |

## Scripts

- `harness_runtime.py` — standard-library lifecycle state, context injection,
  compaction snapshots, and handoff queue.
- `check_harness.py` — fails fast on missing executable contracts, invalid hook
  wiring/frontmatter, unindexed files, or mirror drift.
- `sync_harness.py` — incrementally mirrors managed `.claude/` files and
  preserves destination-only `.agents/` skills/assets.
- `sync_wiki.py` — regenerates machine-owned wiki content and calls safe mirror
  synchronization.

## Memory ownership

| File | Contains |
|------|----------|
| `MEMORY.md` | Generated workspace inventory |
| `.claude/memory/project.md` | Shared durable facts injected at lifecycle boundaries |
| `.claude/memory/handoff-protocol.md` | Cross-agent completion contract |
| `.claude/agent-memory/<agent>/MEMORY.md` | Project-scoped learned memory |
| `.claude/state/` | Gitignored ephemeral lifecycle and handoff state |

Related: [[Development Workflow]] · [[Testing and Eval]]
