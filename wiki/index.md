# Knowledge Base Index

## architecture

Nexus compiled knowledge on architecture.

| Article | Summary | Updated |
|---------|---------|---------|
| [Agent Architecture](architecture/agent-architecture.md) | A root orchestrator routes every request to one of three SequentialAgent pipelines. | 2026-07-04 |
| [Diagram Atlas](architecture/diagram-atlas.md) | The product now exposes the prepared architecture diagrams as an interactive atlas in the landing page, clinician dashboard, admin dashboard, and contextual workflow panels. | 2026-07-05 |
| [Model Registry](architecture/model-registry.md) | `capstone_agent/llm.py` is the single place model selection happens. | 2026-07-04 |
| [Module Dependency Graph](architecture/module-dependency-graph.md) | No circular dependencies. | 2026-07-04 |
| [Module Reference](architecture/module-reference.md) | Every Python module currently in the repository, with its purpose (taken from module docstrings). | 2026-07-04 |
| [System Overview](architecture/system-overview.md) | A multi-agent clinical AI platform built on Google ADK that processes medical imaging, answers patient questions with cited evidence, and runs natural-language database intelligence — all gated by clinician-in-the-loop review and HIPAA-aligned security. | 2026-07-05 |

## harness

Nexus compiled knowledge on harness.

| Article | Summary | Updated |
|---------|---------|---------|
| [Claude Harness](harness/claude-harness.md) | The `.claude/` harness controls and validates agent-assisted development on this repository. | 2026-07-04 |

## operations

Nexus compiled knowledge on operations.

| Article | Summary | Updated |
|---------|---------|---------|
| [Clinical App](operations/clinical-app.md) | The clinician-facing product: a React frontend served by a FastAPI server that runs in **deterministic demo mode** by default or bridges **live** to the ADK agent backend. | 2026-07-05 |
| [Deployment](operations/deployment.md) | Three supported targets — all read secrets from `.env` / Secret Manager at runtime, never baked into images. | 2026-07-04 |
| [MCP and A2A](operations/mcp-and-a2a.md) | Two interoperability surfaces let external clients and agents use Nexus capabilities. | 2026-07-04 |
| [Observability](operations/observability.md) | Three pillars — Logs (diary), Traces (narrative), Metrics (timing) — plus clinical audit events. | 2026-07-04 |
| [REST API and Developer Console](operations/rest-api-and-developer-console.md) | Nexus exposes a versioned, secure REST API backend built on FastAPI and a React-based interactive Developer/API Console to assist developers in testing, auditing, and executing agent pipelines and MCP tools. | 2026-07-05 |
| [Testing & Eval](operations/testing-eval.md) | pytest + pytest-asyncio for system contracts; ADK `AgentEvaluator` for content quality. | 2026-07-04 |

## overview

Nexus compiled knowledge on overview.

| Article | Summary | Updated |
|---------|---------|---------|
| [Course Concepts Map](overview/course-concepts-map.md) | The project covers **all 10 course notebooks** (Days 1a through 5b). | 2026-07-04 |
| [Problem & Solution](overview/problem-solution.md) | Clinical work spans disconnected notes, session images, structured records, historical evidence, and population databases. | 2026-07-04 |

## processes

Nexus compiled knowledge on processes.

| Article | Summary | Updated |
|---------|---------|---------|
| [DB Intelligence Pipeline](processes/db-intelligence-pipeline.md) | SequentialAgent (6 agents) translating natural language into safe SQL with validation before execution and chart-spec generation after. | 2026-07-04 |
| [Deployment Pipeline](processes/deployment-pipeline.md) | Three targets fed by one hardened build. | 2026-07-04 |
| [Development Workflow](processes/development-workflow.md) | How work happens on this repository, including the automated wiki/harness sync layer. | 2026-07-04 |
| [End-to-End Request Flow](processes/end-to-end-request-flow.md) | Every request crosses three security gates and one routing decision. | 2026-07-04 |
| [Human-in-the-Loop Approval](processes/human-in-the-loop-approval.md) | The clinical review gate (Day 2b) — a LongRunningFunctionTool pauses the pipeline until a clinician decides. | 2026-07-04 |
| [Image Extraction Pipeline](processes/image-extraction-pipeline.md) | SequentialAgent (9 agents) processing clinical images through quality assessment, AI vision analysis, structured field extraction, a critic/refiner validation loop, and clinician review before persistence. | 2026-07-04 |
| [Patient QA Pipeline](processes/patient-qa-pipeline.md) | SequentialAgent (7 agents) answering clinical questions with cited evidence from notes, images, and vector search — grounded in patient context. | 2026-07-04 |

## security-memory

Nexus compiled knowledge on security memory.

| Article | Summary | Updated |
|---------|---------|---------|
| [Memory Layers](security-memory/memory-layers.md) | Four-layer memory system with automatic PII/PHI redaction before anything persists. | 2026-07-04 |
| [Security Layers](security-memory/security-layers.md) | Defense in depth — three fixed callback layers plus clinical extensions. | 2026-07-04 |

