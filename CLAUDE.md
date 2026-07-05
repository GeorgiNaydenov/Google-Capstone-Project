# Google Capstone Project — Claude Code Harness

## Project Overview

Google ADK capstone project for Kaggle's 5-Day AI Agents: Intensive Vibe Coding Course. Must demonstrate at least 3 of: Agent/Multi-agent (ADK), MCP Server, Antigravity, Security, Deployability, Agent Skills.

## Tech Stack

- **Framework**: Google ADK (`google-adk`) — Python
- **LLM**: Google Gemini 3.1 via a 3-tier registry (`llm.build_model`): `flash-lite` (default), `pro`, `pro-customtools`
- **MCP**: Model Context Protocol for tool interoperability
- **A2A**: Agent2Agent protocol for cross-agent communication (`a2a_server.py`, `google-adk[a2a]`)
- **Observability**: OpenTelemetry (OTLP / Cloud Trace) + ADK plugins + structured JSON logging
- **Validation**: Pydantic for tool I/O contracts
- **Testing**: pytest + pytest-asyncio + ADK `AgentEvaluator` eval set
- **Deployment**: Cloud Run (Docker) · Vertex AI Agent Engine · GKE

This harness is **universal/domain-agnostic** and covers all 10 course notebooks (Days 1a–5b). To specialize it for a capstone domain, follow `docs/CAPSTONE_GUIDE.md` (edit points marked `# >>> CUSTOMIZE:`).

## Project Structure

<!-- AUTO:STRUCTURE:BEGIN -->
```
capstone_agent/
  a2a_server.py             # Expose this agent over the Agent2Agent (A2A) protocol (Day 5a).
  agent.py                  # Root agent definition — entry point for `adk run capstone_agent`.
  app.py                    # ADK `App` wrapper — the richer runtime around the root agent.
  callbacks.py              # Security callbacks — defense in depth for agent safety.
  clinical_schemas.py       # Clinical database schema definitions and query engine.
  config.py                 # Centralized configuration and secret management.
  context.py                # Context engineering — token budgeting, compaction, structured assembly.
  database.py               # SQLite database layer — real persistence for all clinical data.
  document_processor.py     # Document processing — real PDF and image extraction using PyMuPDF and Gemini.
  human_in_the_loop.py      # Human-in-the-loop / long-running operations (Day 2b).
  llm.py                    # Model registry and factory — the one place model selection happens.
  memory.py                 # Memory management — Layer 2 (Session State), Layer 3 (Long-Term), Layer 4 (A2A Context).
  mock_data.py              # Deterministic mock data for the Clinical AI Command Center.
  models.py                 # Pydantic models for tool input/output contracts.
  observability.py          # Observability — structured logging, tracing, and audit trail.
  orchestration.py          # Multi-agent orchestration building blocks (Day 1b, 2a, 5a).
  plugins.py                # Observability plugins (Day 4a).
  prompts.py                # Clinical AI Command Center — agent instruction templates.
  security.py               # Security module — PII detection, secret scanning, input sanitization.
  tools.py                  # Clinical AI Command Center — tool definitions (production).
clinical_app/
  agent_runtime.py          # Deterministic product adapters for the real clinical agent tool layer.
  app.py                    # FastAPI routes for clinician-facing deterministic application.
  document.py               # Document parsing and upload policy for clinical evidence files.
  live_bridge.py            # Lazy Google ADK execution bridge for live product mode.
  models.py                 # Pydantic contracts for the clinician product API.
  repository.py             # Session-isolated mutable repository for deterministic product demos.
  system.py                 # Real system introspection and tenant governance storage.
  tenancy.py                # Tenant registry for the clinician product — single source of truth.
mcp_server/
  server.py                 # Clinical MCP server — real database-backed tools via Model Context Protocol.
scripts/
  build_llm_wiki.py         # Script to compile the Obsidian Project Wiki into the Karpathy LLM Wiki structure.
  check_harness.py
  export_diagrams.py        # Export Project Wiki draw.io diagrams into frontend public assets.
  generate_database_showcase.py # Generate a large governed SQLite cohort for the database agent.
  generate_extraction_showcase.py # Generate synthetic extraction assets for the image extraction agent.
  generate_multimodal_patient_showcase.py # Generate multimodal patient bundles for the Q&A agent.
  sync_harness.py
  sync_wiki.py              # Deterministic Project Wiki and harness synchronization.
tests/
  conftest.py               # Pytest configuration and shared fixtures for agent evaluation.
  test_agent_eval.py        # Agent evaluation tests — validates agent behavior end-to-end.
  test_callbacks.py         # Unit tests for the 3-layer security callbacks.
  test_clinical_api.py      # Frontend contract tests for deterministic clinician product API.
  test_clinical_tools.py    # Clinical tool integration tests — mock data consistency and HITL.
  test_context.py           # Tests for context engineering utilities (Day 1 working memory).
  test_document_parsing.py  # Document upload policy and extraction contract tests.
  test_eval.py              # ADK evaluation harness test (Day 4b).
  test_live_bridge.py       # Unit tests for the live-mode ADK bridge parsing helpers.
  test_memory.py            # Tests for memory governance (Day 3b).
  test_orchestration.py     # Tests for the orchestration building blocks (Day 1b / 2a).
  test_product_integration.py # End-to-end contracts joining the clinical UI API to product state.
  test_product_orchestration.py # Contract tests for clinician-facing production workflow boundaries.
  test_security.py          # Security test suite — validates all detection and sanitization functions.
  test_showcase_generators.py # Smoke tests for showcase data generators.
  test_tools.py             # Clinical tool validation tests — ensures consistent I/O contracts.
  test_versioned_api.py     # Unit tests for the versioned API backend endpoints (V1 and V2).
  test_wiki_sync.py         # Unit tests for the deterministic wiki sync script (scripts/sync_wiki.py).
frontend/                   # React/Vite/TypeScript clinical UI (16 routes)
eval/                       # ADK evaluation suite (evalset + scoring config)
deployment/                 # Dockerfile, cloudbuild.yaml, Agent Engine config
docs/                       # Architecture and product documentation
Project Wiki/               # Obsidian knowledge base (auto-synced)
```
<!-- AUTO:STRUCTURE:END -->

## Module Dependency Graph

No circular dependencies. Leaf nodes have no project imports.

```
config.py (standalone) → llm.py, models.py, security.py, context.py
security.py → observability.py, memory.py
observability.py → callbacks.py, plugins.py
llm.py → orchestration.py, agent.py
memory.py → callbacks.py
models.py → tools.py
prompts.py (standalone)
callbacks.py + context.py → plugins.py
ALL → agent.py (wires root_agent) → app.py / a2a_server.py
```

## Memory Architecture (4 Layers)

| Layer | Module | Scope | Persistence |
|-------|--------|-------|-------------|
| 1. Working Memory | context.py | Per LLM call | Never |
| 2. Session State | ADK session.state | Per conversation | With DB-backed service |
| 3. Long-Term Memory | memory.py → MemoryService | Cross-session | With VertexAI |
| 4. A2A Context | agent.py → RemoteA2aAgent | Per delegation | Never |

- **State prefixes**: no prefix (session), `user:` (cross-session), `app:` (global), `temp:` (invocation-only)
- **Memory auto-save**: `after_agent_callback` persists completed sessions
- **A2A isolation**: only task-relevant, non-sensitive data crosses agent boundaries

## Security Architecture (3 Layers)

| Layer | Callback | What it does |
|-------|----------|-------------|
| 1. Input | `before_model_callback` | Blocks 15+ injection patterns, sanitizes unicode |
| 2. Tool | `before_tool_callback` | Validates args, rate limits, scans for secrets |
| 3. Output | `after_model_callback` | Catches PII and secrets in LLM responses |

All blocks are logged via `observability.log_security_event()`.

## Context Engineering (Layer 1: Working Memory)

`context.py` assembles the per-call context window. It never calls the LLM —
compaction is rule-based (truncation + metadata preservation).

| Function | Purpose |
|----------|---------|
| `estimate_tokens(text)` | chars/4 heuristic for budget decisions (no tokenizer) |
| `build_structured_context(role, environment, task, constraints)` | XML-delimited sections so the model can separate instructions from data |
| `compact_history(turns, keep_recent=10, max_total_tokens=8000)` | Summarizes old turns to metadata, preserves recent verbatim |
| `inject_at_boundaries(context, critical_info)` | Places critical info at start AND end ("lost in the middle" mitigation) |

- **Token pipeline**: Collect → Rank → Compress → Budget → Assemble
- **Append-only**: `compact_history` returns a new list, never mutates input
- **Cache-friendly**: `config.deterministic_json()` (sorted keys, compact separators) improves KV-cache hits for repeated context

## Observability

`observability.py` implements the three observability pillars: Logs (diary),
Traces (narrative), Metrics (timing). All output passes through
`config.redact_secrets()` before emission.

| Function | Purpose |
|----------|---------|
| `setup_logging(level)` | Structured JSON logger (machine-parseable, searchable) |
| `setup_tracing()` | OpenTelemetry OTLP exporter — opt-in via `ENABLE_TRACING` |
| `log_tool_call(name, args, result, duration_ms)` | Redacted tool audit with timing |
| `log_security_event(event_type, details)` | Audit trail for every block/detection |
| `timed_operation(name)` | Context manager for measuring operation duration |

- Logging and tracing initialize at import time in `agent.py`.
- Tracing degrades gracefully: if OTel packages are missing or `ENABLE_TRACING=FALSE`, the agent runs normally without traces. `TRACE_EXPORTER=gcp` routes spans to Cloud Trace.
- **Plugins (Day 4a)**: `plugins.py` adds `ObservabilityPlugin` (lifecycle-wide, redacted) + ADK's `LoggingPlugin`, attached via `app.py`'s `App(..., plugins=build_plugins())`.

## Key Commands

```bash
# Setup
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # Add your GOOGLE_API_KEY

# Development
adk run capstone_agent       # CLI interaction
adk web .                    # Web UI at localhost:8000

# Agent2Agent serving (Day 5a)
uvicorn capstone_agent.a2a_server:app --port 8001   # agent card at /.well-known/agent-card.json

# Testing
pytest tests/ -v                     # Full suite (model tests skip without GOOGLE_API_KEY)
pytest tests/test_security.py -v     # Security detection (pure functions)
pytest tests/test_callbacks.py -v    # Security callback wiring (no API key)
pytest tests/test_tools.py -v        # Tool validation only

# Evaluation (Day 4b) — needs GOOGLE_API_KEY
adk eval capstone_agent eval/capstone.evalset.json --config_file_path eval/test_config.json --print_detailed_results

# Deployment (see deployment/README.md)
adk deploy cloud_run --project=PROJECT_ID --region=us-central1 --service_name=capstone-agent --with_ui .
adk deploy agent_engine --project=PROJECT_ID --region=us-central1 --agent_engine_config_file=deployment/.agent_engine_config.json .
```

## Coding Conventions

- All tools return `ToolResponse` or `ToolError` from models.py (consistent contract)
- Validate tool inputs with Pydantic at the function boundary
- Use `config.redact_secrets()` on any text that might contain secrets before logging
- Security logic lives in security.py (pure functions, testable), callbacks.py wires it to ADK
- Never pass a bare model-id string — use `llm.build_model(tier)` (adds retry/backoff; tier-selectable). Add new tiers in `llm.MODEL_TIERS`.
- Agent instructions go in prompts.py — under 60 lines each
- Add comments explaining design decisions and agent behaviors (required by rubric)
- Store sensitive config in `.env`, never commit API keys

## Evaluation Rubric Alignment

- **Technical Implementation (50 pts)**: Multi-agent, MCP, 3-layer security, 4-layer memory, Pydantic validation, observability
- **Documentation (20 pts)**: README with problem/solution/architecture/setup, inline code comments
- **Core Concept & Value (10 pts)**: Clear problem-solution fit with agents
- **Video (10 pts)**: Demo the agent working end-to-end
- **Writeup (10 pts)**: Articulate problem, solution, architecture, journey

---

## Default Style

`.claude/rules/brevity.md` is **always active**. Every response uses the caveman-micro rule (unless auto-clarity exceptions fire).

## Harness Rules & Customizations

This harness controls and validates agent executions.

### Rules

| File | Use for |
|---|---|
| `.claude/rules/brevity.md` | Terse caveman communication layout |
| `.claude/rules/engineering.md` | Python, ADK coding, and Pydantic rules |
| `.claude/rules/security.md` | 3-layer security callback rules |
| `.claude/rules/testing.md` | Pytest structure and non-determinism rules |

### Skills

| Skill | Use for |
|---|---|
| `.claude/skills/grill-me/SKILL.md` | Question-based plan pressure testing |
| `.claude/skills/grill-with-docs/SKILL.md` | Doc/architecture plan validation |
| `.claude/skills/testing-workflow/SKILL.md` | pytest and ADK evaluation guidelines |
| `.claude/skills/defuddle/SKILL.md` | Fetching and parsing web URLs |
| `.claude/skills/deployment/SKILL.md` | Deploying to Cloud Run / Agent Engine |
| `.claude/skills/obsidian-markdown/SKILL.md` | Create and edit Obsidian Flavored Markdown |
| `.claude/skills/json-canvas/SKILL.md` | Create and edit JSON Canvas files |
| `.claude/skills/obsidian-bases/SKILL.md` | Create and edit Obsidian Bases |
| `.claude/skills/obsidian-cli/SKILL.md` | Interact with vaults via Obsidian CLI |
| `.claude/skills/drawio/SKILL.md` | Generate .drawio diagrams (architecture, ERD, UML, flowcharts, network) and export PNG/SVG/PDF via draw.io CLI |

### Commands

| Command | Purpose |
|---|---|
| `.claude/commands/pre-commit-gate.md` | Runs formatting, harness audit, and pytest |
| `.claude/commands/harness-audit.md` | Audits the files indexing and sync status |
| `.claude/commands/sync-agents-md.md` | Mirrors .claude to .agents and CLAUDE.md to AGENTS.md |

### References

| File | Contains |
|---|---|
| `.claude/references/critical-defaults.md` | Always-on agent behaviors |
| `.claude/references/known-baselines.md` | Baseline stats and linting status |
| `.claude/references/source-policy.md` | Local check priorities and link citations |

### Memory

| File | Contains |
|---|---|
| `MEMORY.md` | Workspace variables and active model registers (Developer Agent Memory) |

### Project Wiki (auto-synced)

`Project Wiki/` is an Obsidian vault documenting the whole system; `Home.md` is the entry point.

- A `Stop` hook runs `scripts/sync_wiki.py` after every work turn. It is deterministic (stdlib only, no LLM), idempotent, and always exits 0.
- It regenerates the machine-owned pages in `Project Wiki/_generated/` (Module Inventory, Test Inventory, Harness Index, Changelog, Drift Report), the `AUTO:DEPGRAPH` block in `Project Wiki/02 Architecture/Module Dependency Graph.md`, the `AUTO:STRUCTURE` block in this file, and the root `MEMORY.md` registers, then runs `scripts/sync_harness.py` to mirror `CLAUDE.md` to `AGENTS.md`.
- Never hand-edit `_generated/` pages or content inside `AUTO:*` markers; edit the hand-written wiki notes instead. Check `_generated/Drift Report.md` for modules the wiki does not cover yet.
