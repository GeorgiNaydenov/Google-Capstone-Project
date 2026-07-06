# Nexus Clinical AI Command Center

Nexus Clinical AI Command Center is a clinician-facing AI workspace built with Google ADK for Kaggle's AI Agents: Intensive Vibe Coding Capstone Project. It demonstrates a production-shaped multi-agent clinical workflow with visible evidence, human review, security callbacks, MCP tooling, observability, and deployable packaging.

This is a capstone demo, not a medical device. All bundled clinical data is synthetic.

## Reviewer Quick Path

1. Run the app locally with no API key.
2. Open `http://localhost:8000`.
3. Take the guided tour.
4. Run the three workflows: `/app/extraction`, `/app/qa`, and `/app/database`.
5. Open `/documentation` for the architecture hub and diagram atlas.

The demo tenants are deterministic. The **Capstone (Live)** tenant is the real ADK/Gemini path when credentials are configured.

## Competition Concepts Demonstrated

| Required concept | Evidence |
| --- | --- |
| Agent / multi-agent system with ADK | `capstone_agent/agent.py` root orchestrator and `capstone_agent/orchestration.py` with 22 pipeline sub-agents |
| MCP Server | `mcp_server/server.py` exposes clinical tools through FastMCP over JSON-RPC/stdio |
| Security | `capstone_agent/callbacks.py` and `capstone_agent/security.py` implement input, tool, and output safety layers |
| Deployability | `deployment/Dockerfile`, `deployment/cloudbuild.yaml`, `/healthz`, `/readyz`, and Vertex AI Agent Engine config |
| Agent Skills | `.agents/skills/` and `.claude/` provide reusable testing, deployment, documentation, and diagram workflows |

## Problem

Clinical work is fragmented across notes, scanned intake forms, images, patient timelines, and population databases. Clinicians need help turning that evidence into structured findings, but they also need to see evidence, uncertainty, review gates, and audit trails. A black-box chatbot is not enough.

## Solution

Nexus Clinical AI Command Center exposes three guided workflows:

1. **Session Image Extraction**: upload clinical images or PDFs, extract structured fields, inspect confidence and source evidence, and approve before persistence.
2. **Patient-Scoped Multimodal Q&A**: ask a patient-specific question and receive a cited answer grounded in notes, documents, images, and timeline evidence.
3. **Database Intelligence**: ask a cohort question, inspect generated read-only SQL, approve execution, then review rows, charts, and exports.

## Architecture

```text
React / Vite / TypeScript frontend
        |
        | HTTP /api/*
        v
FastAPI clinical product server
        |
        | demo adapters or live ADK bridge
        v
Google ADK agent backend
        |
        +-- 1 root orchestrator
        +-- 22 pipeline sub-agents
        +-- Pydantic tool contracts
        +-- 3-layer security callbacks
        +-- 4-layer memory/context architecture
        +-- OpenTelemetry and structured logs
        +-- A2A server
        +-- MCP server
```

### Agent Pipelines

| Pipeline | Agents | Purpose |
| --- | ---: | --- |
| Image Extraction | 9 | Quality, OCR, vision analysis, structuring, validation loop, review, persistence, audit |
| Patient Q&A | 7 | Scope validation, context assembly, retrieval, image evidence, citations, answer synthesis, audit |
| Database Intelligence | 6 | Schema discovery, NL-to-SQL, safety validation, approval, execution, insights/charts |
| Root Orchestrator | 1 | Intent routing, tool access, memory recall, workflow selection |

## Course Coverage

| Course topic | Implementation |
| --- | --- |
| Foundational models | `capstone_agent/llm.py` model registry with `flash-lite`, `pro`, `pro-customtools`, and `flash-image` tiers |
| Multi-agent systems | `capstone_agent/orchestration.py` ADK SequentialAgent and LoopAgent pipelines |
| Tools and MCP | `capstone_agent/tools.py` and `mcp_server/server.py` |
| Human-in-the-loop | `capstone_agent/human_in_the_loop.py` and review gates in the product API |
| Memory and state | `capstone_agent/memory.py` and session-scoped product repositories |
| Context engineering | `capstone_agent/context.py` token budgeting, compaction, and boundary injection |
| Observability | `capstone_agent/observability.py` and `capstone_agent/plugins.py` |
| Evaluation | `eval/` and `tests/test_eval.py` |
| Agent2Agent | `capstone_agent/a2a_server.py` |
| Deployment | `deployment/` Cloud Run, Agent Engine, and container configuration |

## Local Setup

Prerequisites:

- Python 3.11+
- Node.js 20+
- `uv`

```powershell
git clone https://github.com/GeorgiNaydenov/nexus-clinical-ai-capstone.git
cd nexus-clinical-ai-capstone

uv venv .venv --python 3.11
uv pip install --python .venv\Scripts\python.exe -r requirements.txt

cd frontend
npm ci
npm run build
cd ..

Copy-Item .env.example .env
```

Demo mode works without credentials.

For live Google ADK/Gemini mode, configure one credential path in `.env`:

```powershell
# API key mode
GOOGLE_API_KEY=<your-key>

# Or Vertex AI mode
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=<your-project-id>
GOOGLE_CLOUD_LOCATION=global

# Then enable live execution
AGENT_EXECUTION_MODE=live
```

Run the product:

```powershell
.venv\Scripts\python.exe -m uvicorn clinical_app.app:app --reload --port 8000
```

Open `http://localhost:8000`.

## Useful URLs

| URL | Purpose |
| --- | --- |
| `http://localhost:8000/` | Nexus Clinical AI Command Center product |
| `http://localhost:8000/documentation` | Standalone documentation hub |
| `http://localhost:8000/healthz` | Liveness |
| `http://localhost:8000/readyz` | Readiness with real component checks |
| `http://localhost:8000/docs` | FastAPI Swagger docs |
| `http://localhost:8000/redoc` | FastAPI ReDoc |

## ADK Developer Surfaces

These require credentials:

```powershell
adk run capstone_agent
adk web .
uvicorn capstone_agent.a2a_server:app --port 8001
```

The A2A agent card is available at `http://localhost:8001/.well-known/agent-card.json`.

## Testing

```powershell
pytest tests/ -v

cd frontend
npm run typecheck
npm test
npm run build
```

ADK evaluation requires model credentials:

```powershell
adk eval capstone_agent eval/capstone.evalset.json --config_file_path eval/test_config.json --print_detailed_results
```

## Deployment

Cloud Run is the primary product deployment target:

```bash
gcloud builds submit --config deployment/cloudbuild.yaml .
```

The container builds the frontend, installs the FastAPI and ADK runtime, and serves the product through one origin. See `deployment/README.md` for runtime service-account permissions, Cloud Run persistence constraints, `CLINICAL_DATA_DIR`, and Vertex AI Agent Engine deployment.

Important Cloud Run note: until state is externalized, keep max instances at 1 and mount persistent storage for real tenant data if it must survive revisions.

## Safety Scope

- All bundled patient data is synthetic.
- The app is a capstone demo, not a medical device.
- Demo mode is deterministic and safe to run without credentials.
- Live mode uses the Capstone tenant and requires explicit credentials.
- The system includes prompt-injection filtering, tool validation, PII/PHI detection, secret scanning, audit logging, and human approval gates.

## Repository Map

```text
capstone_agent/     Google ADK agent, orchestration, tools, security, memory, observability
clinical_app/       FastAPI product API, tenancy, repositories, document parsing, live bridge
frontend/           React/Vite/TypeScript clinical workspace
mcp_server/         FastMCP clinical tools
deployment/         Dockerfile, Cloud Build, Agent Engine config
eval/               ADK eval set and scoring config
tests/              pytest suite
docs/               Architecture, product, and submission documentation
Project Wiki/       Obsidian project wiki source
```

## Submission Materials

Kaggle submission helper files live in `docs/submission/`:

- `kaggle-writeup.md`: paste-ready writeup.
- `media-gallery.md`: required media order and where to put the YouTube video.
- `demo-script.md`: 5-minute video shot list.
- `final-production-push-checklist.md`: final gate before submission.

## License

Apache License 2.0. See `LICENSE`.
