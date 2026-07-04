---
title: Clinical App
type: operations
status: active
updated: 2026-07-04
source: README.md, clinical_app module docstrings
tags:
  - operations
  - product
---

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

## Demo vs live mode

- **Demo (default)** — fully deterministic, no model key required. `repository.py` provides session-isolated state with full reset; `agent_runtime.py` adapts the same tool layer deterministically.
- **Live** — set `AGENT_EXECUTION_MODE=live` in `.env` plus one auth path (API key or Vertex ADC — see [[Model Registry]]). `live_bridge.py` lazily wires the ADK runner so demo mode never imports ADK.

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

Related: [[System Overview]] · [[End-to-End Request Flow]] · [[Testing & Eval]] (test_clinical_api.py, test_product_integration.py, test_live_bridge.py)
