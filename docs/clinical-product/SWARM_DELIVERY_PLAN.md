# Multi-Agent Swarm Delivery Plan

## Operating Model

Use one Integration Lead plus up to three concurrent implementation swarms per
wave. Swarm completion means a bounded, verified handoff. Only the Integration
Lead claims product milestones complete.

## Ownership

### Integration Lead

- product specification and traceability
- shared contracts and architectural decisions
- baseline branch, worktrees, and integration queue
- root dependencies, lockfiles, OpenAPI, README, and composition files
- cross-swarm verification and release candidate

### Swarm A: Contracts, API, and Demo Data

Owns `clinical_app/api/`, product contracts, mutable demo repository, reset,
patients, sessions, runs, reviews, receipts, audit, RBAC, and patient scope.

Does not edit `capstone_agent/`, frontend, or deployment without approval.

### Swarm B: Clinical Frontend

Owns `frontend/`, design tokens, components, router, shell, 16 screens, API
client, role-aware navigation, evidence, confidence, review, sync, and audit UI.

Must not embed a second product dataset. Fixtures are allowed only in tests.

### Swarm C: Agent Engine and Tools

Owns `capstone_agent/`, `mcp_server/`, ADK runner adapter, run events, the three
clinical workflows, HITL resume, tools, and agent evals.

Exposes structured workflow rationale only, never hidden chain-of-thought.

### Swarm D: Quality, Security, and Observability

Owns API/integration/security tests, frontend tests, accessibility, Playwright,
eval regression, trace/audit correlation, performance, and failure paths.

Avoids implementation edits except narrowly approved testability changes.

### Swarm E: Deployment and Submission

Activated after local workflows pass. Owns product container, Cloud Build,
health/readiness, architecture diagram, setup/deployment docs, guided demo,
screenshots, limitations, and capstone evidence matrix.

## Wave 0: Stabilize and Freeze

Integration Lead:

1. Preserve the current dirty worktree deliberately; do not discard user work.
2. Repair Python and `uv` cache execution.
3. Run `agents-cli info`, harness audit, Ruff, pytest, and record the baseline.
4. Convert the supplied brief into an approved `.agents-cli-spec.md` and ADRs.
5. Approve React/Vite + FastAPI + existing ADK + provider-port architecture.
6. Freeze product, API, event, permission, and demo-reset contracts.

Exit: executable baseline, approved contracts, ownership map, integration branch.

## Wave 1: Product Spine

Run A, B, and C concurrently.

- A: seed graph and read APIs for patients, sessions, dashboards, and search.
- B: app shell, public demo, role switcher, search, overview, and profile.
- C: FastAPI-to-ADK runner adapter and persisted run-event contract.

Integration proof:

```text
Enter demo -> switch role -> search exact patient -> open profile
-> refresh -> inspect the same shared record
```

Exit: no timer-driven runs and no embedded product fixture store.

## Wave 2: Extraction Vertical Slice

- A: upload, run, review, storage, audit, and timeline persistence.
- B: real upload/preview, stepper, editable fields, decisions, receipts.
- C: quality -> vision/OCR -> structure -> validate -> review -> stores/audit.
- D: contracts, upload security, idempotency, integration, browser workflow.

Exit proof:

```text
Upload -> visible agents -> structured fields -> edit/approve
-> JSON/relational/vector receipts -> timeline and audit mutation
```

This is the first capstone-grade milestone.

## Wave 3: Intelligence Workflows

Parallelize by workflow after shared contracts are stable:

- Q&A: filters, scoped retrieval, citations, image viewer, validation, audit.
- Database: schema, SQL generation, safety, preview, execution, table/chart/CSV.
- Platform: shared history, evidence, chart, export, and audit endpoints.
- Quality: groundedness, citation integrity, SQL refusal, browser workflows.

Exit: guided workflows 2 and 3 pass end to end.

## Wave 4: Operations and Screen Completion

- global command bar with auto and manual orchestration
- users, multi-role assignment, permissions, and access scope
- storage lineage, sync jobs, failures, and idempotent retry
- versioned agent settings, thresholds, disable/re-run, logs, metrics
- role switch preserving patient/session context
- remaining navigation, reports, system health, and settings subsections

Exit: all 16 screens use shared state; admin mutations persist and authorize.

## Wave 5: Hardening and Submission

- complete threat and privacy review
- run the full automated gate
- perform the 1440px browser walkthrough and accessibility audit
- build and smoke-test the container
- prove demo reset and isolation
- finish architecture, README, setup, screenshots, walkthrough, limitations
- request explicit approval before public deployment

## Collision Avoidance

Implementation swarms use separate worktrees and branches:

- `codex/contracts-api`
- `codex/frontend`
- `codex/agent-engine`
- `codex/quality`
- `codex/deployment`

Rules:

1. The Integration Lead alone edits shared root files and frozen contracts.
2. Contract changes land as a versioned contract change before consumers.
3. Every handoff includes changed files, contract impact, commands run, known
   gaps, and screenshots/traces when relevant.
4. Rebase onto the integration branch before handoff.
5. Merge in order: contracts -> backend/agent -> frontend -> tests -> deploy/docs.
6. Never run parallel implementation agents in the same worktree.

## Integration Protocol

Every agent run uses a shared event envelope:

- run ID, workflow, status, agent name, step, timestamp
- confidence and evidence references
- review and storage state
- audit event ID and trace ID
- safe user-facing rationale

Start with SSE plus polling fallback. Persist every event before publishing it.

Every mutation must be proved in five places:

1. API response
2. repository state
3. audit event
4. refreshed UI
5. browser assertion

## Quality Gates

### Per Swarm

- focused tests and static analysis
- contract compatibility
- no secrets or real patient information
- changes restricted to owned files

### Existing Harness

```text
python scripts/check_harness.py
ruff check .
ruff format --check .
pytest tests/ -v
```

Use the repository-standard `uv run` form after the environment is repaired.

### Product Gate

- backend import/type and API contract checks
- OpenAPI snapshot compatibility
- API integration tests with demo reset
- frontend lint, format, typecheck, unit, and accessibility tests
- production frontend build
- Playwright guided workflows
- full pytest suite and ADK eval regression
- Docker build and local health/readiness smoke

### ADK Eval Gate

Evaluate intent routing, required tool trajectories, grounded citations,
extraction completeness, SQL refusal/safety, review escalation, security, and
multi-turn patient context. Deterministic contracts remain pytest territory.

### Browser Gate

- exactly 16 routable screens
- all primary controls work
- role switch preserves relevant context
- upload uses a real file input
- citations open the correct authorized evidence
- CSV matches displayed rows
- failed/retry states work
- demo reset restores the seed
- dense 1440px layout passes visual review
- keyboard navigation and accessible names pass

### Deployment Gate

- product server replaces ADK Web
- Cloud Run `$PORT`, `/health`, and `/ready`
- non-root container and runtime secrets only
- compiled UI and API in one initial artifact
- deterministic demo initialization
- structured logs and trace IDs
- deployed smoke test for all three workflows
- explicit approval before deployment

## Milestones

| Milestone | Proof |
|---|---|
| M0 Foundation | Repaired environment, baseline gates, approved specification and contracts |
| M1 Product Spine | Public demo through patient profile uses one shared repository |
| M2 Extraction | Upload-review-storage-audit browser workflow passes |
| M3 Intelligence | Cited Q&A and SQL/table/chart/export workflows pass |
| M4 Operations | Admin, RBAC, storage lineage, settings, and monitoring work |
| M5 Release Candidate | 16 screens and all local/container gates pass |
| M6 Submission | Public link, reproducible repo, diagram, screenshots, and demo script |

## Definition of Done

Done requires evidence that:

- all 16 screens are routed and connected
- all three guided workflows use shared repository state
- automatic and manual orchestration use the same persisted run model
- agent steps, confidence, evidence, review, sync, audit, and timestamps show
- Clinician/Admin switching preserves relevant context without login
- extraction supports upload, edit, approve, reject, re-run, storage, and audit
- Q&A citations reopen the correct text or image evidence
- database intelligence provides preview, safety, table, chart, CSV, history
- admin permissions and versioned settings are enforced and audited
- demo data is synthetic, isolated, mutable, and resettable
- secrets, unauthorized PHI, and hidden reasoning do not leak
- harness, unit, integration, browser, accessibility, eval, and container pass
- documentation and deployed behavior agree
- public deployment works after explicit approval

