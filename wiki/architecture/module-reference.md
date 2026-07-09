# Module Reference

> Sources: Antigravity, 2026-07-05
> Raw: [Module Reference Source](../../raw/architecture/2026-07-04-module-reference.md)

# Module Reference

Every Python module currently in the repository, with its purpose (taken from module docstrings). The live, machine-generated version is [[Module Inventory]]; the import graph is [[Module Dependency Graph]].

## capstone_agent/ — ADK agent backend

| Module | Purpose |
|--------|---------|
| `agent.py` | Root agent definition — entry point for `adk run capstone_agent`; imports all modules and wires the root agent + sub-agents |
| `app.py` | ADK `App` wrapper — plugins, compaction, resumability around the root agent |
| `a2a_server.py` | Expose the agent over the Agent2Agent (A2A) protocol (Day 5a) |
| `llm.py` | Model registry and factory — the one place model selection happens ([[Model Registry]]) |
| `orchestration.py` | Multi-agent orchestration building blocks — the 3 pipeline factories, agent-as-tool, code exec, remote A2A |
| `tools.py` | Clinical tool definitions (production) — Pydantic-validated, clinical event logging |
| `callbacks.py` | Security callbacks — defense in depth ([[Security Layers]]) |
| `security.py` | PII detection, secret scanning, input sanitization (pure functions) |
| `memory.py` | Memory management — Layers 2, 3, 4 ([[Memory Layers]]) |
| `context.py` | Context engineering — token budgeting, compaction, structured assembly (Layer 1) |
| `observability.py` | Structured logging, tracing, and audit trail ([[Observability]]) |
| `plugins.py` | Observability plugins (Day 4a) — ObservabilityPlugin, ClinicalAuditPlugin, LoggingPlugin |
| `prompts.py` | Agent instruction templates (under 60 lines each) |
| `models.py` | Pydantic models for tool input/output contracts (ToolResponse, ToolError) |
| `config.py` | Centralized configuration and secret management (redaction, clinical governance) |
| `clinical_schemas.py` | Clinical database schema definitions and query engine (SQL DDL + validation) |
| `database.py` | SQLite database layer — real persistence for all clinical data |
| `document_processor.py` | Document processing — real PDF and image extraction using PyMuPDF and Gemini |
| `mock_data.py` | Deterministic mock data for the Clinical AI Command Center |
| `human_in_the_loop.py` | Human-in-the-loop / long-running operations (Day 2b) |

## clinical_app/ — FastAPI product server

| Module | Purpose |
|--------|---------|
| `app.py` | FastAPI routes for the clinician-facing application; serves the frontend build |
| `agent_runtime.py` | Deterministic product adapters for the real clinical agent tool layer |
| `live_bridge.py` | Lazy Google ADK execution bridge for live product mode |
| `repository.py` | Session-isolated mutable repository for deterministic product demos |
| `models.py` | Pydantic contracts for the clinician product API |
| `document.py` | Document parsing and upload policy for clinical evidence files |
| `system.py` | Real system health checks, latency monitoring, and database seeding for the real tenant |

## mcp_server/

| Module | Purpose |
|--------|---------|
| `server.py` | Clinical MCP server — real database-backed tools via Model Context Protocol (FastMCP) |

## scripts/ — harness and showcase utilities

| Module | Purpose |
|--------|---------|
| `check_harness.py` | PreToolUse hook — verifies harness integrity ([[Claude Harness]]) |
| `sync_harness.py` | Mirrors `.claude/` → `.agents/` and CLAUDE.md → AGENTS.md |
| `sync_wiki.py` | Stop hook — deterministic wiki/harness auto-update ([[Development Workflow]]) |
| `export_diagrams.py` | Export Project Wiki draw.io diagrams into frontend public assets |
| `generate_database_showcase.py` | Generate a large governed SQLite cohort for the database agent |
| `generate_extraction_showcase.py` | Generate synthetic extraction assets for the image extraction agent |
| `generate_multimodal_patient_showcase.py` | Generate multimodal patient bundles for the Q&A agent |

## Other top-level areas

| Area | Purpose |
|------|---------|
| `frontend/` | React/Vite/TypeScript clinical UI — 16 routes; `dist/` served by FastAPI |
| `eval/` | ADK evaluation suite — `capstone.evalset.json` + `test_config.json` ([[Testing and Eval]]) |
| `tests/` | pytest + async test suite ([[Testing and Eval]]) |
| `deployment/` | Dockerfile, cloudbuild.yaml, Agent Engine config ([[Deployment]]) |
| `docs/` | Architecture and product documentation |
