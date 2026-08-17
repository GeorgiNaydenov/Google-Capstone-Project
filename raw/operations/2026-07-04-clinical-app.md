# Clinical App

> Source: Project Wiki/06 Operations/Clinical App.md
> Collected: 2026-07-05
> Published: 2026-07-04

# Clinical App

The clinician-facing product: a React frontend served by a FastAPI server that runs in **deterministic demo mode** by default or bridges **live** to the ADK agent backend.

## Components

| Module | Purpose |
|--------|---------|
| `clinical_app/app.py` | FastAPI routes for the clinician-facing application; middleware; serves `frontend/dist/` |
| `clinical_app/agent_runtime.py` | Deterministic product adapters for the real clinical agent tool layer |
| `clinical_app/live_bridge.py` | Lazy Google ADK execution bridge for live product mode |
| `clinical_app/repository.py` | Session-isolated mutable repository for deterministic product demos |
| `clinical_app/models.py` | Pydantic contracts for the clinician product API |
| `clinical_app/document.py` | Document parsing and upload policy for clinical evidence files |
| `frontend/` | React/Vite/TypeScript UI — 16 routes, clinician + admin views |

## Onboarding tour

`frontend/src/Onboarding.tsx` runs a full-takeover guided tour the first time a user enters the workspace (`/app/*`). The modal is the focal point while the real screens render dimmed behind it; each of the 9 steps navigates the actual route it describes (dashboard → queue → extraction → Q&A → database → inbox → orchestrator → finish) and the AI workflow steps play deterministic in-modal simulations (agent pipeline, cited answer, SQL-to-chart) with zero API calls.

- Persistence flag: `localStorage["clinicalOnboardingV1"] = "done"` (set by both Skip and Finish)
- Replay: "Replay product tour" utility button in the Shell topbar
- Keyboard: Escape skips, arrow keys navigate
- Frontend tests that render `/app` routes must seed the flag first (see `frontend/src/App.test.tsx`); the tour's own suite is `frontend/src/Onboarding.test.tsx`

## Tenancy

Three tenants are selectable from the organization dropdown in the Shell topbar (visible to both roles); the frontend sends the choice in the `X-Tenant` header and `clinical_app/tenancy.py` is the single registry:

| Tenant | Kind | Data |
|--------|------|------|
| Research Clinic (default) | demo | Original deterministic 24-patient dataset |
| Northstar Health | demo | Distinct deterministic 12-patient dataset (`NORTHSTAR_*` fixtures in `repository.py`) |
| Capstone | real | Live ADK execution over its own `capstone.db` + `uploads_capstone/`, created schema-only and empty |

- Repositories are keyed by `tenant::session` in `RepositoryRegistry`, so the same browser session sees isolated state per tenant.
- The Capstone tenant scopes every database and upload access per request through `capstone_agent.database.tenant_storage()` (contextvar-based), so live agent tools write to `capstone.db`, never `clinical.db`.
- Legacy header values (`local`, `demo`) map to Research Clinic; `live` maps to Capstone; unknown values fall back to the default demo tenant.
- Capstone has no canned fallbacks: transient model errors (429/503/RESOURCE_EXHAUSTED/…) are retried once in `live_bridge.execute_live`, then surfaced as honest 502 errors — never fake SQL or fields.

## Demo vs live mode

- **Demo (default)** — fully deterministic, no model key required. `repository.py` provides session-isolated state with full reset; `agent_runtime.py` adapts the same tool layer deterministically.
- **Live** — the Capstone tenant is always live; for demo tenants, set `AGENT_EXECUTION_MODE=live` in `.env` plus one auth path (API key or Vertex ADC — see [[Model Registry]]) to force live execution over `clinical.db`. `live_bridge.py` lazily wires the ADK runner so demo mode never imports ADK.

## Product guarantees

- Session isolation and full reset per demo session
- Role-based access (clinician vs admin)
- Audit trail on product actions
- Upload validation for evidence files (`document.py`)

## Running

```powershell
.venv\Scripts\python.exe -m uvicorn clinical_app.app:app --reload --port 8000
```

FastAPI serves the frontend build at `http://localhost:8000`. During frontend development, `npm run dev` in `frontend/` proxies `/api` to port 8000.

Related: [[System Overview]] · [[End-to-End Request Flow]] · [[Testing and Eval]] · [[REST API and Developer Console]]
