# Production Readiness Plan — Clinical AI Kit

## Context

The capstone must ship as an end-to-end clinician-facing product powered by a visible multi-agent system (3 workflows: Session Image Extraction, Multimodal Patient Q&A, Database Intelligence). The product contains 16 brief-defined core screens plus 3 documentation/utility routes (19 public routes total). The ADK backend has 1 root orchestrator and 21 specialist LLM agents (22 total) across 3 `SequentialAgent` pipelines, with a nested `LoopAgent` in extraction, 22+ tools, SQLite `clinical.db`, an MCP server, 3-layer security, and HITL gates. `clinical_app/` bridges the UI to deterministic and live execution modes.

**Planning history:** The original implementation pass verified live mode locally with user-supplied credentials and stopped at deploy readiness. The current public release is deployed separately in deterministic mode with paid ADK/Gemini execution disabled; live mode remains available only for self-controlled deployments.

## Confirmed bugs (verified against source + installed ADK)

1. **Live toolCalls always empty** — `clinical_app/live_bridge.py:60`,68 uses `event.function_calls` attribute; installed ADK `Event` only has `get_function_calls()` / `get_function_responses()` methods → `hasattr` is always False. AgentStepper never shows tool calls in live mode.
2. **`patient_context` silently dropped** — `create_session()` returns a copy; mutating `session.state` post-hoc (`clinical_app/live_bridge.py:40-42`) never reaches the stored session. Must pass `state=` into `create_session`.
3. **Wrong text parsed for results** — pipelines are SequentialAgents; final response comes from the *audit* agent, so regex on final text reads narration, not fields/SQL. Real outputs live in `session.state` via `output_key`: extraction `structured_output`/`refined_output`, Q&A `qa_answer`/`cited_sources`, DB `generated_sql`/`validated_sql`/`query_results`. Also `_extract_fields` regex `\{[^{}]*\}` can't match nested JSON.
4. **Ungated server-side SQL execution** — `database_execute` route → `clinical_schemas.execute_query` → `capstone_agent/database.py:203` runs raw `cursor.execute(sql)` on a read-write connection with **no `validate_sql` call**; `validate_sql` exists (`capstone_agent/clinical_schemas.py:180`) but is only enforced inside the agent pipeline. Agent-generated SQL reaches raw execution.
5. **Double execution + masked errors in `database_execute`** (`clinical_app/app.py:536-585`) — live mode calls `execute_live("Execute this SQL…")` AND executes locally; result discarded. Empty result sets raise `ValueError("No rows returned")` → 500 on legitimate 0-row queries; `execute_sql` errors return `{"error": ...}` dict the route never checks.
6. **`.env` never loaded by product API** — `load_dotenv()` only runs in `capstone_agent/config.py`, imported lazily; `execution_mode()` reads `os.environ` at request time, so `AGENT_EXECUTION_MODE` in `.env` does nothing today.
7. **No cross-request session continuity in live mode** — fresh `InMemorySessionService` per request; Q&A follow-ups (a spec demo scenario) can't reference prior turns.
8. Hygiene: `frontend/dist` never built (SPA-serving branch unexercised); `test_db.py` stray debug script at repo root (print + hardcoded path); `.env.example` missing `AGENT_EXECUTION_MODE`; public documentation had stale topology counts. The canonical topology is extraction 7, Q&A 8, database 6, plus the root orchestrator (22 LLM agents total).

## Implementation steps (dependency order, minimal diffs — no UI changes, no refactors)

### Step 0 — Write test plan into the project (user request)
Create `PRODUCTION_TEST_PLAN.md` in the repo root containing the confirmed-bug list, implementation steps, and the full verification matrix below, so the plan is tracked with the app itself. Then proceed with implementation immediately.

### Step 1 — Fix `clinical_app/live_bridge.py`
- Module-level lazy `_session_service` singleton (created inside `execute_live`, preserving lazy-import contract).
- New kwarg `session_key: str | None = None` → session id `f"live-{session_key}"` if provided else uuid; `get_session` first, create if missing. (Default keeps existing behavior; monkeypatched tests unaffected.)
- Pass `state=dict(patient_context or {})` into `create_session`; delete post-hoc state mutation loop.
- Replace `hasattr`/attribute access with `event.get_function_calls()` / `event.get_function_responses()`.
- After event loop, re-fetch session and collect `state_outputs` from the known `output_key`s (redact strings via `redact_pii(redact_secrets(...))`); return as new `"stateOutputs"` key.
- `_extract_fields`: prefer `structured_output` state; parse with `json.loads` whole-text then `json.JSONDecoder().raw_decode` from first `{` (handles nesting); keep line-based fallback.
- `_extract_sql`: prefer `validated_sql` → `generated_sql` state → final-text regex.

### Step 2 — Fix `clinical_app/app.py`
- Add `load_dotenv()` at module top (python-dotenv already in venv).
- `database_execute`: remove the `execute_live` call (agent's live role is preview; execution is deterministic + server-gated). Gate with `clinical_schemas.validate_sql(sql)` → on unsafe: status back to `review`, error step, `HTTPException(400)`. Check `res.get("error")` → HTTPException instead of masking. Empty `rows` = valid completed result (guard chart spec on `len(rows) > 0`). Always extend `toolCalls` with `database_execution_tools(...)`.
- `database_preview` live branch: drop inline `import re` fallback; use `live_result["sql"]` (now state-sourced); keep the literal fallback SQL for the error path.
- Q&A route: pass `session_key=repo.session_id`; prefer `stateOutputs.qa_answer` for the answer, fall back to `finalResponse`.
- Extraction route: additive — surface `stateOutputs` under `item["result"]["stateOutputs"]` for the Structured JSON tab.

### Step 3 — Tests (additive)
- `tests/test_product_integration.py`: (a) unsafe SQL (`DELETE FROM patients_core`) via fake `execute_live` → execute returns 400, run back in `review`; (b) empty-result query completes with `rows: []` (monkeypatch `execute_query`).
- New `tests/test_live_bridge.py`: pure unit tests for `_extract_fields` (nested/fenced JSON, line fallback) and `_extract_sql` preference order — no model key needed.

### Step 4 — Hygiene
- `git rm test_db.py` (nothing imports it; pytest `testpaths=tests` never collects it).

### Step 5 — Frontend build (no source edits)
- `cd frontend; npm run typecheck; npm test; npm run build` → `frontend/dist/` for single-origin serving.

### Step 6 — Docs + deploy config
- `.env.example`: add `AGENT_EXECUTION_MODE` block (unset/local = demo, live = real ADK agents).
- Align `README.md`, `docs/architecture.md`, and the agent module documentation with 22 total LLM agents: 1 root orchestrator plus 21 specialists split 7/8/6 across extraction, Q&A, and database intelligence.
- Describe the frontend as 16 core product screens plus 3 documentation/utility routes (19 public routes total).
- `README.md`: add "Demo walkthrough" section — demo vs live start commands + the 3 guided workflows with routes (`/app/extraction`, `/app/qa`, `/app/database`, `/app/audit`). Name GCS/vector/Firestore as "local emulations of the GCP services shown".
- `deployment/cloudbuild.yaml`: keep the public service deterministic (`AGENT_EXECUTION_MODE=disabled`) with paid model, vector, reranker, and tracing integrations disabled; keep `--max-instances=1` while state remains in-process/SQLite. Document live ADK/Gemini as a separate self-controlled deployment path.
- `deployment/README.md`: document live-mode env vars, single-instance constraint, and that live bridge intentionally uses in-memory ADK sessions (SESSION_BACKEND=database applies to the `adk run`/Agent Engine path only).

## Verification matrix (Windows, `.venv`)

| # | Proves | Command / action | Pass |
|---|---|---|---|
| 1 | Python suite green | `.venv\Scripts\python -m pytest` | 0 failures; model tests skip w/o key |
| 2 | FE types/tests/bundle | `cd frontend; npm run typecheck; npm test; npm run build` | `dist/index.html` exists |
| 3 | Single-origin prod serving | `uvicorn clinical_app.app:app --port 8000` → open `http://localhost:8000` | SPA served by FastAPI; `/health` and `/ready` report healthy |
| 4 | Demo workflow 1 | `/app/extraction`: PT-8829 → upload → run → review → approve | review→completed; receipts `synced`; audit shows `extraction_approved` |
| 5 | Demo workflow 2 | `/app/qa`: PT-8829 question | Answer + evidence cards; image source opens |
| 6 | Demo workflow 3 | `/app/database`: cohort question → approve → execute | SQL gated at review; rows + chart; history + CSV; audit event |
| 7 | Live mode boots | `.env` with `GOOGLE_API_KEY` + `AGENT_EXECUTION_MODE=live`; restart | `/api/health` `mode:"live"` |
| 8 | Live workflow 1 | Repeat #4 | Real ADK author steps; **toolCalls non-empty**; fields from `structured_output` |
| 9 | Live workflow 2 + continuity | Repeat #5, then a follow-up question | Answer from `qa_answer`; follow-up references prior turn |
| 10 | Live workflow 3 + gate | Repeat #6; plus new pytest | SQL from validated/generated state; unsafe SQL → 400 |
| 11 | Container parity (if Docker available) | `docker build -f deployment/Dockerfile .` | Image builds |

User must supply `GOOGLE_API_KEY` in `.env` (copy from `.env.example`) before steps 7-10. Never commit `.env`.

## Out of scope (explicitly)

- UI redesign/restyle (user: UI almost perfect).
- Real GCS / Vertex Vector Search / Firestore integration — stays as SQLite-backed local emulation, visibly labeled in UI + README.
- The public Cloud Run build uses deterministic execution with paid ADK/Gemini services disabled. Live mode is a separate self-controlled deployment path with credentials and explicit runtime configuration.
- Wiring DatabaseSessionService into live_bridge.

## Critical files

- `clinical_app/live_bridge.py`, `clinical_app/app.py` — seam fixes
- `capstone_agent/clinical_schemas.py` (`validate_sql` reuse — no changes needed there)
- `tests/test_product_integration.py`, new `tests/test_live_bridge.py`
- `.env.example`, `README.md`, `docs/architecture.md`, `capstone_agent/agent.py` (docstring), `deployment/cloudbuild.yaml`, `deployment/README.md`
- Delete: `test_db.py`
