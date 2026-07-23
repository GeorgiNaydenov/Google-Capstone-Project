# Generic-to-Clinical Harness Specialization

## Correction to the Existing Guide

`docs/CAPSTONE_GUIDE.md` says domain specialization needs no structural
changes. That was true for turning the generic agent demo into a domain agent.
It is not true for the requested full-stack clinical product.

The agent layer is already substantially specialized. The remaining work adds
new product boundaries while preserving the dependency graph inside
`capstone_agent`.

## Preserve

| Module | Preserve because |
|---|---|
| `llm.py` | Central tier registry and retry-wrapped `build_model()` are correct. |
| `orchestration.py` patterns | ADK sequential, loop, parallel, and agent-as-tool patterns remain useful. |
| `models.py` envelope | Pydantic validation plus `ToolResponse`/`ToolError` is the right tool boundary. |
| `app.py` | ADK App, compaction, plugins, and resumability remain the agent runtime. |
| `context.py` | Working Memory utilities remain separate from product records. |
| `a2a_server.py` | Keep as optional interoperability, not the product API. |
| `security.py` pure functions | Extend the testable detection base. |
| session/memory factories | Preserve workflow continuity, with stricter PHI governance. |
| OTel base | Extend with product run, actor, review, and storage correlation. |
| `mock_data.py` | Reuse only as seed input for an isolated mutable demo repository. |

## Add Product Boundaries

```text
clinical_app/
  api/             FastAPI routes and OpenAPI contracts
  auth/            demo principal, role activation, policy context
  contracts/       product entities, run events, reviews, receipts, audit
  events/          persisted events and SSE delivery
  repositories/    protocols, DemoRepository, Google Cloud adapters
  services/        workflow facade, ADK Runner adapter, idempotency, outbox
frontend/
  src/app/         router, shell, role-aware workspace
  src/components/  clinical design system
  src/features/    screens and three workflow slices
e2e/               browser tests for the guided workflows
```

One repository contract must feed the UI, HTTP API, ADK tools, MCP tools,
analytics, storage panels, and audit views.

## Minimum Shared Contracts

### Request Context

- request ID and idempotency key
- demo session ID
- actor ID and assigned roles
- active role and organization ID
- optional patient and session scope

### Agent Run

- run ID, workflow, detected intent, state, timestamps
- data sources and permissions required
- ordered agent/tool steps and safe rationale
- confidence, evidence references, errors
- review state, storage state, audit event ID, trace ID

### Evidence and Citation

- immutable evidence ID and version/checksum
- patient/session scope and source type
- source URI or asset ID, excerpt or image region
- relevance/confidence and authorized access URL

### Review Decision

- pending artifact version and proposed field-level diff
- approve, reject, edit, or re-run decision
- reviewer ID, active role, reason, timestamps
- optimistic-lock version and idempotency key

### Storage Receipt

- target, resource ID/version, checksum
- pending/synced/failed state
- attempt, error, and sync timestamp

### Audit Event

- append-only event ID
- actor, role, organization, action, and outcome
- patient/session/run/step/tool references
- before/after resource references, trace ID, timestamp

## Harden Existing Modules

### `orchestration.py`

- Extraction: intake/upload -> quality -> vision + OCR -> clinical structuring
  -> deterministic validation -> required clinician review -> JSON store ->
  relational write -> vector index -> audit/timeline.
- Q&A: scoped context -> retrieval -> image analysis -> citation assembly ->
  answer -> deterministic citation/coverage validation -> audit.
- Database: schema -> NL-to-SQL -> deterministic safety -> SQL preview ->
  explicit approval -> execution -> chart/insight -> audit/history.
- Remove generic writing/research factories from the production surface.

### `tools.py`

- Stop reading `mock_data` directly.
- Depend on repository/provider ports injected through the service layer.
- Add OCR, JSON write, relational write, embedding/index, review transition,
  run state, asset access, and export tools.
- Return real resource IDs, versions, receipts, and post-write state.
- Replace comma-separated JSON strings with structured Pydantic inputs.

### `mcp_server/server.py`

- Use the same services and repositories as the HTTP API.
- Default to read-only tool allowlists.
- Require actor context and idempotency for mutations.
- Use authenticated remote transport for non-demo production.

### `callbacks.py` and `security.py`

- Add actor, active-role, organization, patient-scope, purpose, permission,
  and resource-ownership policy checks before tool execution.
- Treat uploads, OCR, notes, and retrieved chunks as untrusted prompt data.
- Make output protection aware of authorized clinical context.
- Redact nested structures, not only flat strings.

### `human_in_the_loop.py`

- Replace constants with versioned agent configuration.
- Persist review requests and reviewer identity/role/reason/diff.
- Require optimistic locking and idempotent resume.
- Never auto-commit a clinical record solely from model confidence.

### `memory.py`

- Use ADK memory for workflow continuity and preferences.
- Keep patients, sessions, evidence, and clinical findings in repositories.
- Persist completed workflow runs in tenant storage and rehydrate them before
  merging browser-cached turns; seed curated prior conversations per demo tenant.
- Store minimum redacted summaries only.
- Do not treat cross-session conversation memory as clinical truth.

### `observability.py` and `plugins.py`

- Add run/step/trace IDs, actor/role/org, patient/session references, model
  tier, latency, cost, confidence, review state, and storage status.
- Separate operational logs from the immutable audit ledger.
- Disable verbose clinical payload logging outside isolated synthetic demo.

### `config.py` and `.env.example`

Add validated configuration for demo mode, repository backend, authentication,
allowed origins, bucket/database/vector resources, upload limits, retention,
review thresholds, payload logging, and feature flags.

### Deployment and Documentation

- Run the product FastAPI server rather than ADK Web.
- Serve the compiled frontend and API from one Cloud Run artifact initially.
- Bind `$PORT`; add `/healthz` and `/readyz`; retain non-root execution.
- Use runtime service identity and Secret Manager.
- Allow unauthenticated access only for the isolated synthetic demo.
- Rewrite architecture, README, setup, deployment, agent-role, limitations,
  and guided-demo documentation to describe the current product.

## Architectural Decisions to Record

1. ADK is behind an application service; the UI never invokes arbitrary tools.
2. One repository protocol supports demo and Google Cloud adapters.
3. Demo behavior is mutable and real, not timer-driven theater.
4. Policy and state machines are deterministic; models do not authorize work.
5. Review precedes persistence, using idempotency and a transactional outbox.
6. SSE carries visible progress; persisted events support reconnect and reload.
7. The audit ledger is append-only and separate from debug logs.
8. Cloud Run is the primary full-stack target; Agent Runtime and A2A are optional.

## Specialization Gates

| Stage | Gate |
|---|---|
| S0 Specification | Versioned product, route, data, event, and permission contracts; repaired environment; baseline tests recorded. |
| S1 Product spine | UI and API use one repository; role and patient/session views survive reload; no embedded product fixture store. |
| S2 Extraction | Approve/edit/reject/re-run persist; retries cannot double-write; packet/patient lineage remains visible; storage receipts reconcile. |
| S3 Q&A | Every material claim links to authorized reopenable evidence; patient images render in the answer when available; unsupported claims are identified; prior turns rehydrate. |
| S4 Database | Unsafe/cross-scope SQL is blocked; chart and CSV derive from the executed result; rate/threshold questions expose numerator, authorized denominator, and prevalence. |
| S5 Admin | Permissions apply at API and tool boundaries; configuration and retries are versioned and audited. |
| S6 Release | Deterministic tests, ADK eval, browser workflows, accessibility, container smoke, docs, and public demo all pass. |

## Principal Risks

- Cross-patient or cross-organization leakage from missing scope checks
- Prompt injection in OCR, uploaded files, notes, or retrieved evidence
- Duplicate commits after HITL resume or retry
- SQL validator bypass or over-broad database credentials
- Clinical payload leakage through verbose logs or traces
- Ephemeral Cloud Run state breaking demo continuity
- Contract drift between frontend, API, MCP, and tools
- Public synthetic demo being mistaken for a PHI-ready clinical system
