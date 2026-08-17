# Course Concepts Map

> Source: Project Wiki/01 Overview/Course Concepts Map.md
> Collected: 2026-07-05
> Published: 2026-07-04

# Course Concepts Map

The project covers **all 10 course notebooks** (Days 1a through 5b).

| Day | Notebook | Implementation | Wiki page |
|-----|----------|----------------|-----------|
| 1a | Foundational models | `llm.py` — tiered model registry with retry/backoff | [[Model Registry]] |
| 1b | Multi-agent systems | `orchestration.py` — SequentialAgent pipelines, LoopAgent | [[Agent Architecture]] |
| 2a | Agent tools & MCP | `tools.py`, `mcp_server/` — clinical tools, FastMCP server | [[MCP and A2A]] |
| 2b | Agent-as-tool & HITL | `orchestration.py`, `human_in_the_loop.py` — LongRunningFunctionTool | [[Human-in-the-Loop Approval]] |
| 3a | Memory & state | `memory.py` — session/memory factories, state prefixes | [[Memory Layers]] |
| 3b | Context engineering | `context.py` — token budgeting, compaction, boundary injection | [[Memory Layers]] |
| 4a | Observability | `observability.py`, `plugins.py` — OpenTelemetry, Cloud Trace, structured logging | [[Observability]] |
| 4b | Evaluation | `eval/` — ADK EvalSet, tool trajectory + response match scoring | [[Testing and Eval]] |
| 5a | Agent2Agent (A2A) | `a2a_server.py` — ASGI A2A server with agent card | [[MCP and A2A]] |
| 5b | Deployment | `deployment/` — Cloud Run, Vertex AI Agent Engine, GKE | [[Deployment]] |

## Evaluation rubric alignment

| Category | Points | Implementation |
|----------|--------|----------------|
| Technical Implementation | 50 | Multi-agent pipelines, MCP, 3-layer security, 4-layer memory, Pydantic, observability |
| Documentation | 20 | README, inline docstrings, architecture docs, this wiki |
| Core Concept & Value | 10 | Clinical intelligence with visible agent reasoning |
| Video Demo | 10 | End-to-end workflow demonstration |
| Writeup | 10 | Problem-solution-architecture-journey articulation |

> [!note] Capstone requirement
> Must demonstrate at least 3 of: ADK multi-agent, MCP server, Antigravity, security, deployability, Agents CLI. Nexus demonstrates multi-agent ([[Agent Architecture]]), MCP ([[MCP and A2A]]), security ([[Security Layers]]), and deployability ([[Deployment]]).
