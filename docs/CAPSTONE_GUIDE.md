# Capstone Specialization Guide

This harness is **domain-agnostic**: every principle from the 5-day course is
wired as reusable scaffolding with placeholder tools. For an agent-only domain
demo, specialization follows the short checklist below without changing the
core harness structure.

The Clinical AI Command Center has progressed beyond agent-only
specialization. Its full-stack product work requires additional application
boundaries while preserving this ADK foundation. Use
[`clinical-product/README.md`](clinical-product/README.md) for the current
requirements matrix, harness transformation, and swarm delivery plan.

Every place you edit is marked in code with a `# >>> CUSTOMIZE:` comment, so you
can `grep -rn "CUSTOMIZE" capstone_agent mcp_server` to find them all.

## The 6-step checklist

### 1. Name your project
`.env` → set `APP_NAME` (and pick a `MODEL_TIER`). Copy `.env.example` to `.env`
and add your `GOOGLE_API_KEY`.

### 2. Replace the tools
[`capstone_agent/tools.py`](../capstone_agent/tools.py) → swap `example_search` /
`example_action` for your real tools. Keep the pattern: Pydantic-validated input
(add models in [`models.py`](../capstone_agent/models.py)), `ToolResponse`/`ToolError`
return, `log_tool_call` for observability.

### 3. Write the instructions
[`capstone_agent/prompts.py`](../capstone_agent/prompts.py) → rewrite
`ROOT_AGENT_INSTRUCTION` and the specialist template for your domain. Keep the
safety constraints (no secrets/PII).

### 4. Compose your agents + pick model tiers
[`capstone_agent/agent.py`](../capstone_agent/agent.py) → rename
`research_agent`/`action_agent`, attach your tools, and choose a model tier per
agent with `build_model(tier=...)`:
- `flash-lite` — cheap routing / simple tasks (default)
- `pro` — hard reasoning sub-tasks
- `pro-customtools` — tool-heavy agents (most reliable function calling)

Need a pipeline/parallel/loop instead of a coordinator? Use the factories in
[`orchestration.py`](../capstone_agent/orchestration.py).

### 5. Swap the MCP tools
[`mcp_server/server.py`](../mcp_server/server.py) → replace `get_status` /
`list_items` / `create_item` with your domain tools, then update the
`tool_filter` allowlist in `agent.py`.

### 6. Write your eval set
[`eval/capstone.evalset.json`](../eval/capstone.evalset.json) → add cases with
expected responses and `tool_uses` for tool-trajectory scoring. Run:
`adk eval capstone_agent eval/capstone.evalset.json --config_file_path eval/test_config.json`.

## What you get for free (no edits required)

| Principle | Where | Notes |
|-----------|-------|-------|
| Retry-wrapped model factory (Day 1a) | `llm.py` | 3 selectable tiers |
| Workflow agents (Day 1b) | `orchestration.py` | sequential / parallel / loop |
| Agent-as-tool + code executor (Day 2a) | `orchestration.py`, `agent.py` | |
| MCP integration (Day 2a) | `agent.py` + `mcp_server/` | |
| Human-in-the-loop approval (Day 2b) | `human_in_the_loop.py` + `app.py` | resumable |
| Sessions + compaction (Day 3a) | `memory.py`, `app.py` | env-switchable backend |
| Long-term memory + PII redaction (Day 3b) | `memory.py` | `load_memory` + custom search |
| Observability plugins + tracing (Day 4a) | `plugins.py`, `observability.py` | Cloud Trace ready |
| ADK evaluation (Day 4b) | `eval/`, `tests/test_eval.py` | |
| A2A serving + consuming (Day 5a) | `a2a_server.py`, `orchestration.py` | |
| Cloud Run / Agent Engine / GKE (Day 5b) | `deployment/` | |
| 3-layer security (rubric) | `callbacks.py`, `security.py` | |

## Optional toggles (via `.env`)

- Persistent sessions: `SESSION_BACKEND=database`
- Cloud memory: `MEMORY_BACKEND=vertex` + `AGENT_ENGINE_ID=...`
- Cloud Trace: `ENABLE_TRACING=TRUE` + `TRACE_EXPORTER=gcp`
- Proactive memory: add `preload_memory` to an agent's `tools` instead of `load_memory`.
