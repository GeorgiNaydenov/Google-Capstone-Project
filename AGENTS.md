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

```
capstone_agent/           # Main ADK agent package
  __init__.py             # Package init — imports agent module
  config.py               # Centralized config, secret redaction, serialization
  llm.py                  # Model registry + build_model(tier) with retry (Day 1a)
  models.py               # Pydantic models for tool I/O (ToolResponse, ToolError)
  security.py             # PII detection, secret scanning, input sanitization
  context.py              # Context engineering: token budgeting, compaction
  observability.py        # Structured logging, OpenTelemetry (OTLP/GCP) tracing
  memory.py               # Session/memory factories, PII filter, A2A context prep
  callbacks.py            # 3-layer security callbacks (input/tool/output)
  plugins.py              # Observability plugin (BasePlugin) + LoggingPlugin (Day 4a)
  orchestration.py        # Workflow agents, agent-as-tool, code exec, remote A2A (Day 1b/2a/5a)
  human_in_the_loop.py    # Long-running approval tool (Day 2b)
  prompts.py              # Agent instruction templates
  tools.py                # Custom tools with Pydantic validation
  agent.py                # Root agent wiring — imports all modules (entry point)
  app.py                  # App(root_agent, plugins, compaction, resumability)
  a2a_server.py           # to_a2a(root_agent) ASGI app (Day 5a; guarded import)
mcp_server/               # Custom MCP server
  server.py               # FastMCP tools with validation
eval/                     # ADK evaluation (Day 4b)
  capstone.evalset.json   # Eval cases (user_content, final_response, tool_uses)
  test_config.json        # Criteria: tool_trajectory_avg_score, response_match_score
tests/                    # Test + evaluation harness
  conftest.py             # Pytest fixtures (runner, session, memory)
  test_agent_eval.py      # Agent behavior tests (model tests skip w/o key)
  test_security.py        # Security detection tests
  test_callbacks.py       # Security callback wiring (no API key)
  test_tools.py           # Tool validation tests
  test_orchestration.py   # Workflow primitives construction
  test_memory.py          # Memory governance / PII redaction
  test_context.py         # Context engineering utilities
  test_eval.py            # ADK AgentEvaluator (skips w/o key)
deployment/               # Production deployment
  Dockerfile              # Hardened container (non-root, healthcheck)
  cloudbuild.yaml         # Cloud Build pipeline (Secret Manager for the key)
  .agent_engine_config.json  # Vertex AI Agent Engine hardware config (Day 5b)
  README.md               # Cloud Run / Agent Engine / GKE / A2A deploy guide
docs/                     # Documentation and diagrams
  architecture.md         # Architecture description
  CAPSTONE_GUIDE.md       # 6-step domain specialization checklist
```

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

`.agents/rules/brevity.md` is **always active**. Every response uses the caveman-micro rule (unless auto-clarity exceptions fire).

## Harness Rules & Customizations

This harness controls and validates agent executions.

### Rules

| File | Use for |
|---|---|
| `.agents/rules/brevity.md` | Terse caveman communication layout |
| `.agents/rules/engineering.md` | Python, ADK coding, and Pydantic rules |
| `.agents/rules/security.md` | 3-layer security callback rules |
| `.agents/rules/testing.md` | Pytest structure and non-determinism rules |

### Skills

| Skill | Use for |
|---|---|
| `.agents/skills/grill-me/SKILL.md` | Question-based plan pressure testing |
| `.agents/skills/grill-with-docs/SKILL.md` | Doc/architecture plan validation |
| `.agents/skills/testing-workflow/SKILL.md` | pytest and ADK evaluation guidelines |
| `.agents/skills/defuddle/SKILL.md` | Fetching and parsing web URLs |
| `.agents/skills/deployment/SKILL.md` | Deploying to Cloud Run / Agent Engine |
| `.agents/skills/obsidian-markdown/SKILL.md` | Create and edit Obsidian Flavored Markdown |
| `.agents/skills/json-canvas/SKILL.md` | Create and edit JSON Canvas files |
| `.agents/skills/obsidian-bases/SKILL.md` | Create and edit Obsidian Bases |
| `.agents/skills/obsidian-cli/SKILL.md` | Interact with vaults via Obsidian CLI |

### Commands

| Command | Purpose |
|---|---|
| `.agents/commands/pre-commit-gate.md` | Runs formatting, harness audit, and pytest |
| `.agents/commands/harness-audit.md` | Audits the files indexing and sync status |
| `.agents/commands/sync-agents-md.md` | Mirrors .claude to .agents and CLAUDE.md to AGENTS.md |

### References

| File | Contains |
|---|---|
| `.agents/references/critical-defaults.md` | Always-on agent behaviors |
| `.agents/references/known-baselines.md` | Baseline stats and linting status |
| `.agents/references/source-policy.md` | Local check priorities and link citations |

### Memory

| File | Contains |
|---|---|
| `MEMORY.md` | Workspace variables and active model registers (Developer Agent Memory) |
