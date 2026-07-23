# clinical_app — FastAPI Product Server

The clinician-facing application layer that bridges the React frontend with the ADK agent backend. Operates in two modes: **deterministic demo** (no API key needed) and **live ADK** (requires Gemini credentials).

---

## Architecture

```
Frontend (React)
     │ HTTP /api/*
     ▼
┌─────────────────────────────────────────┐
│  FastAPI Product Server (app.py)         │
│  ├── Demo mode: DemoRepository          │
│  │   (isolated, deterministic, reset)   │
│  └── Live mode: LiveRepository          │
│       └── ADK Runner (agent_runtime.py) │
└─────────────────────────────────────────┘
```

---

## Modules

| Module | Purpose |
|--------|---------|
| `app.py` | FastAPI application with all API routes, middleware, static file serving. Handles patient CRUD, session management, extraction workflows, Q&A, database intelligence, audit, admin operations, and demo reset |
| `agent_runtime.py` | ADK runner bridge — wraps the `capstone_agent` root agent for live execution. Provides tool sets for each pipeline (extraction, Q&A, database) |
| `repository.py` | Repository pattern with two implementations: `DemoRepository` (in-memory, deterministic, per-session isolation) and `LiveRepository` (backed by ADK + real database). `RepositoryRegistry` manages per-session instances |
| `models.py` | Pydantic request/response models: `RunRequest`, `ReviewRequest`, `QuestionRequest`, `DatabaseRequest`, `OrchestrateRequest`, `Role` enum |
| `document.py` | Upload validation (`validate_upload()`) and document parsing (`parse_upload()`). Enforces file type, size limits, and content safety |
| `live_bridge.py` | `execute_live()` — bridges FastAPI request/response to async ADK runner execution for live agent mode |

---

## API Endpoints

Interactive API documentation is served by the FastAPI app:

- `GET /docs` - branded Swagger UI for the versioned `/api/v1` and `/api/v2` schema.
- `GET /redoc` - branded ReDoc reference for the same OpenAPI schema.
- `GET /openapi.json` - raw OpenAPI schema used by the developer console.

The frontend diagram atlas is intentionally outside the OpenAPI schema. Its SVG and PNG assets are static product documentation under `frontend/public/diagrams/` and are cataloged in `Project Wiki/02 Architecture/Diagram Atlas.md`.

### Patient Operations
- `GET /api/patients` — List all patients (role-filtered)
- `GET /api/patients/{id}` — Patient detail with sessions
- `GET /api/patients/{id}/timeline` — Patient event timeline

### Extraction Workflow
- `POST /api/patients/{id}/sessions/{sid}/runs` — Start extraction run
- `POST /api/patients/{id}/sessions/{sid}/runs/{rid}/review` — Clinician review
- `GET /api/patients/{id}/sessions/{sid}/runs/{rid}` — Run status and results

### Patient Q&A
- `POST /api/patients/{id}/qa` — Ask a patient-scoped question

### Database Intelligence
- `POST /api/database/preview` — Generate and preview SQL
- `POST /api/database/execute` — Execute approved SQL query

### Admin & Audit
- `GET /api/audit` — Audit event trail
- `GET /api/dashboard` — Dashboard metrics
- `POST /api/demo/reset` — Reset demo state
- `GET /api/orchestrate/plan` — View orchestration plan

### System
- `GET /health` — Health check endpoint
- `GET /api/agent-catalog` — Agent pipeline catalog

---

## Demo vs. Live Mode

| Feature | Demo Mode | Live Mode |
|---------|-----------|-----------|
| API Key Required | No | Yes (`GOOGLE_API_KEY`) |
| Data Source | In-memory synthetic data | SQLite + ADK agents |
| Deterministic | Yes — same inputs produce same outputs | No — LLM responses vary |
| Session Isolation | Full — each session gets fresh state | Shared database |
| Reset | `POST /api/demo/reset` | N/A |
| Agent Execution | Simulated pipeline steps | Real ADK runner |

---

## Running

```powershell
# Start the product server
.venv\Scripts\python.exe -m uvicorn clinical_app.app:app --reload --port 8000

# The server serves frontend/dist as static files when available
# Open http://localhost:8000
```
