# Nexus Clinical AI Command Center

A clinician-facing AI platform powered by **23 agents** (1 orchestrator + 22 pipeline sub-agents) built on [Google ADK](https://google.github.io/adk-docs/), demonstrating production-grade multi-agent orchestration, security, memory, observability, and deployment for clinical intelligence workflows.

> **Capstone submission** for [Kaggle's AI Agents: Intensive Vibe Coding Capstone Project](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project) (Google 5-Day AI Agents course).

## For Reviewers — Competition Concepts Demonstrated (5 of the required 3)

| Concept | Where to look |
|---------|---------------|
| **Agent/Multi-agent system (ADK)** | `capstone_agent/agent.py` (root orchestrator), `capstone_agent/orchestration.py` (3 SequentialAgent pipelines + LoopAgent validation, 22 sub-agents) |
| **MCP Server** | `mcp_server/server.py` — FastMCP clinical tools over JSON-RPC/stdio, consumed by the ADK agent and any MCP client |
| **Security** | `capstone_agent/callbacks.py` + `security.py` — 3-layer callback pipeline (injection blocking, tool validation/rate limits, PII/PHI/secret output scanning), tested in `tests/test_security.py` |
| **Deployability** | `deployment/` — multi-stage Dockerfile (frontend + API single origin), Cloud Build → Cloud Run pipeline, Vertex AI Agent Engine config |
| **Agent Skills** | `.agents/skills/` + `.claude/` harness — reusable agent skills (diagramming, testing workflow, deployment) governing this repo's own development |

**Fastest demo path (no API key needed):** follow [Local Setup](#local-setup), open `http://localhost:8000`, take the built-in product tour, then run the three guided workflows (`/app/extraction`, `/app/qa`, `/app/database`). The demo tenants are deterministic; switching the org selector to the **Capstone (Live)** tenant exercises the real ADK + Gemini path when credentials are configured.

---

## Problem

Clinical work spans disconnected notes, session images, structured records, historical evidence, and population databases. Clinicians need an auditable way to turn those inputs into structured findings without hiding uncertainty, evidence, or human review behind a generic chatbot.

## Solution

Nexus provides a dense, role-aware command center for synthetic clinical data. The product exposes three guided AI workflows:

1. **Session Image Extraction** — OCR, field confidence, clinician review, storage receipts, timeline updates, and audit events.
2. **Patient-Scoped Multimodal Q&A** — Evidence citations, source viewing, and multi-modal reasoning with text and images.
3. **Database Intelligence** — Natural-language SQL generation, safety approval, table/chart/CSV export, history, and audit.

The public demo is fully deterministic and requires no model key. The live agent engine in `capstone_agent/` implements the same workflows using Google ADK and Gemini when valid credentials are configured.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  React Frontend (frontend/)                                  │
│  16 routes · clinician + admin views · Vite + TypeScript     │
│  First-run guided onboarding tour (skippable, replayable)    │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP /api/*
┌─────────────────────────▼────────────────────────────────────┐
│  FastAPI Product Server (clinical_app/)                       │
│  Demo mode (deterministic) or Live ADK bridge                │
│  Session isolation · role-based access · audit trail         │
└─────────────────────────┬────────────────────────────────────┘
                          │ ADK Runner
┌─────────────────────────▼────────────────────────────────────┐
│  ADK Agent Backend (capstone_agent/)                          │
│  22 sub-agents · 3 pipelines · 24+ tools                    │
│  3-layer security · 4-layer memory · HITL · observability    │
├──────────────────────────────────────────────────────────────┤
│  MCP Server (mcp_server/)                                    │
│  Clinical tools via FastMCP (JSON-RPC 2.0 / stdio)           │
└──────────────────────────────────────────────────────────────┘
```

### 22-Agent Pipeline Overview

| Pipeline | Agents | Model Tiers | Purpose |
|----------|--------|-------------|---------|
| **Image Extraction** | 9 agents (SequentialAgent + LoopAgent) | flash-lite, pro, pro-customtools | Quality → OCR → AI vision → structuring → critic/refiner loop → review gate → persistence → audit |
| **Patient Q&A** | 7 agents (SequentialAgent) | flash-lite, pro, pro-customtools, flash-image | Validation → context → retrieval → image evidence → citations → answer synthesis (with generated visuals) → audit |
| **DB Intelligence** | 6 agents (SequentialAgent) | flash-lite, pro, flash-image | Schema discovery → NL-to-SQL → safety validation → approval gate → execution → insights/charts |
| **Orchestrator** | 1 root agent | flash-lite | Intent routing, MCP tools, memory recall, HITL approval |

---

## Course Concepts Demonstrated

This project covers **all 10 course notebooks** (Days 1a through 5b):

| Day | Notebook | Implementation |
|-----|----------|---------------|
| 1a | Foundational models | `llm.py` — 4-tier model registry (incl. image output) with retry/backoff |
| 1b | Multi-agent systems | `orchestration.py` — 22-agent pipelines, SequentialAgent |
| 2a | Agent tools & MCP | `tools.py`, `mcp_server/` — 22+ tools, FastMCP server |
| 2b | Agent-as-tool & HITL | `orchestration.py`, `human_in_the_loop.py` — LongRunningFunctionTool |
| 3a | Memory & state | `memory.py` — session/memory factories, state prefixes |
| 3b | Context engineering | `context.py` — token budgeting, compaction, boundary injection |
| 4a | Observability | `observability.py`, `plugins.py` — OpenTelemetry, Cloud Trace, structured logging |
| 4b | Evaluation | `eval/` — ADK EvalSet, tool trajectory + response match scoring |
| 5a | Agent2Agent (A2A) | `a2a_server.py` — ASGI A2A server with agent card |
| 5b | Deployment | `deployment/` — Cloud Run, Vertex AI Agent Engine, GKE |

---

## Project Structure

```
├── capstone_agent/          # ADK agent package (22 sub-agents, 3 pipelines)
│   ├── agent.py             # Root agent wiring — entry point
│   ├── app.py               # App wrapper (plugins, compaction, resumability)
│   ├── a2a_server.py        # Agent2Agent ASGI server
│   ├── llm.py               # Model registry with build_model(tier)
│   ├── orchestration.py     # Pipeline builders (extraction, Q&A, DB)
│   ├── tools.py             # Custom tools with Pydantic validation
│   ├── callbacks.py         # 3-layer security callbacks
│   ├── security.py          # PII/secret detection (pure functions)
│   ├── memory.py            # Session/memory service factories
│   ├── context.py           # Context engineering utilities
│   ├── observability.py     # Structured logging + OpenTelemetry
│   ├── plugins.py           # ADK observability plugins
│   ├── prompts.py           # Agent instruction templates
│   ├── models.py            # Pydantic models (ToolResponse, ToolError)
│   ├── config.py            # Centralized config + secret redaction
│   ├── clinical_schemas.py  # SQL validation and clinical field schemas
│   ├── database.py          # SQLite clinical database layer
│   ├── document_processor.py# PDF/image document processing
│   ├── mock_data.py         # Synthetic patient data generation
│   └── human_in_the_loop.py # Long-running approval tool
├── clinical_app/            # FastAPI product server
│   ├── app.py               # Routes, middleware, static serving
│   ├── agent_runtime.py     # ADK runner bridge
│   ├── repository.py        # Demo + Live repository pattern
│   ├── models.py            # API request/response models
│   ├── document.py          # Upload validation and parsing
│   └── live_bridge.py       # Live ADK execution bridge
├── frontend/                # React/Vite/TypeScript clinical UI
│   ├── src/                 # 16-route application
│   └── dist/                # Production build (served by FastAPI)
├── mcp_server/              # Model Context Protocol server
│   └── server.py            # FastMCP clinical tools (stdio)
├── eval/                    # ADK evaluation suite
│   ├── capstone.evalset.json# Evaluation cases
│   └── test_config.json     # Scoring criteria
├── tests/                   # pytest + async test suite
├── scripts/                 # Harness management utilities
├── deployment/              # Docker, Cloud Build, Agent Engine config
└── docs/                    # Architecture and product documentation
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Installation

```powershell
# Clone the repository
git clone https://github.com/GeorgiNaydenov/Google-Capstone-Project.git
cd Google-Capstone-Project

# Python environment
uv venv .venv --python 3.11
uv pip install --python .venv\Scripts\python.exe -r requirements.txt

# Frontend build
cd frontend
npm ci
npm run build
cd ..

# Environment configuration
Copy-Item .env.example .env
# Demo mode works with no credentials at all.
# For LIVE agent mode, pick ONE auth path in .env:
#   Option 1 — GOOGLE_API_KEY=<your key>
#   Option 2 — Vertex AI via your Google Cloud account (no key):
#       gcloud auth application-default login
#       GOOGLE_GENAI_USE_VERTEXAI=TRUE
#       GOOGLE_CLOUD_PROJECT=<your-project-id>
#       GOOGLE_CLOUD_LOCATION=global   # Gemini 3.1 requires the global endpoint
# Then enable live execution:
#       AGENT_EXECUTION_MODE=live
```

### Run the Product

```powershell
# Start the clinical application (demo mode by default; live mode if
# AGENT_EXECUTION_MODE=live is set in .env)
.venv\Scripts\python.exe -m uvicorn clinical_app.app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000). FastAPI serves the frontend build. During frontend development, run `npm run dev` in `frontend/` — Vite proxies `/api` to port 8000.

### ADK Developer Surfaces (requires GOOGLE_API_KEY)

```powershell
adk run capstone_agent          # CLI interaction
adk web .                       # ADK Web UI at localhost:8000
uvicorn capstone_agent.a2a_server:app --port 8001  # A2A server
```

---

## Testing

```powershell
# Full test suite (model-dependent tests skip without GOOGLE_API_KEY)
pytest tests/ -v

# Individual test modules
pytest tests/test_security.py -v     # Security detection (pure functions, no API key)
pytest tests/test_callbacks.py -v    # Security callback wiring
pytest tests/test_tools.py -v        # Tool validation
pytest tests/test_context.py -v      # Context engineering
pytest tests/test_memory.py -v       # Memory governance / PII redaction
pytest tests/test_orchestration.py -v # Workflow construction

# Frontend
cd frontend
npm run typecheck
npm test
npm run build
```

### ADK Evaluation (requires GOOGLE_API_KEY)

```powershell
adk eval capstone_agent eval/capstone.evalset.json \
  --config_file_path eval/test_config.json --print_detailed_results
```

---

## Security Architecture

Three-layer callback pipeline applied to every agent interaction:

| Layer | Callback | Protection |
|-------|----------|------------|
| **1. Input** | `before_model_callback` | Blocks 15+ injection patterns, sanitizes unicode |
| **2. Tool** | `before_tool_callback` | Validates arguments (Pydantic), rate limits, scans for secrets |
| **3. Output** | `after_model_callback` | Catches PII and secrets in LLM responses, redacts or blocks |

All security events are logged via `observability.log_security_event()` with full audit trail.

## Memory Architecture

Four-layer memory system with automatic PII redaction:

| Layer | Module | Scope | Persistence |
|-------|--------|-------|-------------|
| 1. Working Memory | `context.py` | Per LLM call | Never |
| 2. Session State | ADK `session.state` | Per conversation | With DB backend |
| 3. Long-Term Memory | `memory.py` → MemoryService | Cross-session | With Vertex AI |
| 4. A2A Context | `orchestration.py` → RemoteA2aAgent | Per delegation | Never |

---

## Deployment

Three supported deployment targets — all read secrets from Secret Manager at runtime, never baked into images.

| Target | Command | Use Case |
|--------|---------|----------|
| **Cloud Run** | `gcloud builds submit --config deployment/cloudbuild.yaml .` | Production clinical product |
| **Vertex AI Agent Engine** | `adk deploy agent_engine ...` | Fully managed with autoscaling |
| **GKE** | Custom K8s manifests | Self-managed Kubernetes |

See [`deployment/README.md`](deployment/README.md) for detailed instructions.

---

## Model Registry

All agents use `llm.build_model(tier)` — never bare model-id strings. This centralizes retry behavior, backoff, and model selection.

| Tier | Model | Used By |
|------|-------|---------|
| `flash-lite` (default) | `gemini-3.1-flash-lite` | Orchestrator routing, validation, audit |
| `pro` | `gemini-3.1-pro-preview` | Reasoning-heavy: SQL generation, answer synthesis |
| `pro-customtools` | `gemini-3.1-pro-preview-customtools` | Tool-heavy: evidence retrieval, image analysis |

---

## Safety and Demo Scope

- All patient data is synthetic — no real PHI
- Per-demo-session isolated state with full reset capability
- Role-aware API operations (clinician vs. admin)
- Read-only SQL preview with explicit execution boundary
- Human-in-the-loop review before extraction persistence
- Structured secret/PII controls and redacted observability
- **This capstone demo is not a medical device and is not authorized for real patient data**

---

## Evaluation Rubric Alignment

| Category | Points | Implementation |
|----------|--------|----------------|
| Technical Implementation | 50 | Multi-agent (23 agents), MCP, 3-layer security, 4-layer memory, Pydantic, observability |
| Documentation | 20 | README, inline docstrings, architecture docs, delivery map |
| Core Concept & Value | 10 | Clinical intelligence with visible agent reasoning |
| Video Demo | 10 | End-to-end workflow demonstration |
| Writeup | 10 | Problem-solution-architecture-journey articulation |

---

## License

Licensed under the [Apache License 2.0](LICENSE). This project is a capstone
submission; all clinical data is synthetic.
