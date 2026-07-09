# Claude Harness

> Sources: Antigravity, 2026-07-05
> Raw: [Claude Harness Source](../../raw/harness/2026-07-04-claude-harness.md)

# Claude Harness

The `.claude/` harness controls and validates agent-assisted development on this repository. The live, machine-generated index is [[Harness Index]].

## Rules (`.claude/rules/`)

| File | Enforces |
|------|----------|
| `brevity.md` | Caveman-micro response style with auto-clarity exceptions |
| `engineering.md` | Python 3.11+, typing, scope discipline, `build_model(tier)` only, uv commands, named git staging |
| `security.md` | Fixed 3-layer callback order, secret/PII scan rules, redaction before logging |
| `testing.md` | pytest layout, LLM non-determinism constraint, `@requires_model` marker |

## Skills (`.claude/skills/`)

grill-me, grill-with-docs, testing-workflow, defuddle, deployment, obsidian-markdown, json-canvas, obsidian-bases, obsidian-cli.

## Commands (`.claude/commands/`)

| Command | Purpose |
|---------|---------|
| `pre-commit-gate.md` | Formatting, harness audit, and pytest before commits |
| `harness-audit.md` | Audits file indexing and sync status |
| `sync-agents-md.md` | Mirrors `.claude` → `.agents` and CLAUDE.md → AGENTS.md |

## References (`.claude/references/`)

`critical-defaults.md` (always-on behaviors), `known-baselines.md` (baseline stats), `source-policy.md` (local check priorities).

## Hooks (`.claude/settings.json`)

| Hook | Script | Purpose |
|------|--------|---------|
| `PreToolUse` (matcher `.*`) | `scripts/check_harness.py` | Verifies harness integrity before every tool call: required directories, CLAUDE.md/AGENTS.md sync, skill frontmatter, index completeness |
| `Stop` | `scripts/sync_wiki.py` | Deterministic wiki + harness auto-update after each work session — see [[Development Workflow]] |

## Sync scripts (`scripts/`)

- `check_harness.py` — fails fast when the harness drifts: missing dirs, unsynced CLAUDE.md/AGENTS.md (byte-compare after `## Default Style` with `.agents/`→`.claude/` translation), bad skill frontmatter, unindexed files.
- `sync_harness.py` — wipes and regenerates `.agents/` from `.claude/` (path-translated) and AGENTS.md from CLAUDE.md. Run after any CLAUDE.md edit.
- `sync_wiki.py` — regenerates the machine-owned wiki pages (`_generated/`), the [[Module Dependency Graph]] AUTO block, the `## Project Structure` AUTO block in CLAUDE.md, and root `MEMORY.md`; then calls `sync_harness` so everything stays consistent.

## Memory files

| File | Contains |
|------|----------|
| `MEMORY.md` (repo root) | Workspace variables and active model registers — AUTO block maintained by `sync_wiki.py` |
| `.claude/memory/` | Harness memory directory (currently placeholder) |
| User auto-memory (`~/.claude/projects/...`) | Cross-session facts maintained by Claude Code |

Related: [[Development Workflow]] · [[Testing and Eval]]
