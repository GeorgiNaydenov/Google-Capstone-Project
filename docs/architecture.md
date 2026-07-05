# Clinical AI Command Center — Architecture

## System Overview

A **16-agent clinical AI platform** built on Google ADK that processes medical imaging, answers patient questions with cited evidence, and runs natural-language database intelligence — all gated by clinician-in-the-loop review and HIPAA-aligned security.

The system has four layers: a **React frontend** (Vite + TypeScript), a **FastAPI product server** (`clinical_app/`), the **ADK agent backend** (`capstone_agent/`), and an **MCP tool server** (`mcp_server/`). The frontend talks to the FastAPI server, which can operate in deterministic demo mode or bridge live to the ADK runner. On first workspace entry the frontend runs a full-takeover onboarding tour (`frontend/src/Onboarding.tsx`) that walks the clinician through every section and the three AI workflows over the live screens; it is skippable, replayable from the topbar, and fully deterministic (no API calls).

```
┌──────────────────────────────────────────────────────────┐
│  React Frontend (frontend/)                              │
│  16 routes · clinician + admin views · Vite + TS         │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP /api/*
┌────────────────────────▼─────────────────────────────────┐
│  FastAPI Product Server (clinical_app/app.py)            │
│  Demo mode (deterministic) or Live ADK bridge            │
│  Session isolation · role-based access · audit trail     │
└────────────────────────┬─────────────────────────────────┘
                         │ ADK Runner
┌────────────────────────▼─────────────────────────────────┐
│  ADK Agent Backend (capstone_agent/)                     │
│  22 sub-agents · 3 pipelines · 24+ tools                 │
│  3-layer security · 4-layer memory · HITL · observability│
├──────────────────────────────────────────────────────────┤
│  MCP Server (mcp_server/server.py)                       │
│  7 clinical tools via FastMCP (JSON-RPC 2.0)             │
└──────────────────────────────────────────────────────────┘
```

## Model Registry (Day 1a)

`llm.py` is the single place model selection happens. Every agent gets a `Gemini` built with `HttpRetryOptions` (exponential backoff) via `build_model(tier)` — never a bare string.

| Tier | Model | Used by |
|------|-------|---------|
| `flash-lite` (default) | gemini-3.1-flash-lite | Orchestrator routing, simple stages |
| `pro` | gemini-3.1-pro-preview | Reasoning-heavy agents (answer synthesis, SQL generation) |
| `pro-customtools` | gemini-3.1-pro-preview-customtools | Tool-heavy agents (evidence retrieval, execution) |

## 16-Agent Clinical Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  content_safety_callback (Layer 1: Input Security)          │
│  - 18 injection patterns (including 3 HIPAA-specific)       │
│  - Unicode sanitization                                     │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  clinical_orchestrator (flash-lite)                          │
│  Routes to 3 clinical pipelines based on intent             │
│  MCP tools · search_past_conversations · HITL approval      │
└──────┬────────────────────┬────────────────────┬────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ IMAGE        │  │ PATIENT Q&A      │  │ DB INTELLIGENCE  │
│ EXTRACTION   │  │ PIPELINE         │  │ PIPELINE         │
│ PIPELINE     │  │ (SequentialAgent)│  │ (SequentialAgent)│
│ (Sequential) │  │                  │  │                  │
└──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘
       │                   │                     │
  (9 agents)          (7 agents)            (6 agents)
```

### Image Extraction Pipeline (SequentialAgent)

Processes clinical images through quality assessment, AI vision analysis, structured field extraction, and clinician review before persistence.

```
quality_assessor_agent (flash-lite)
  └─ assess_image_quality
       │
       ▼
vision_analyzer_agent (pro)
  └─ analyze_clinical_image
       │
       ▼
clinical_structuring_agent (pro)
  └─ structure_clinical_findings, store_to_gcs
       │
       ▼
validation_gate (LoopAgent)          ◄── Day 1b loop pattern
  ├─ critic_agent → exit_loop        (confidence >= threshold)
  └─ refiner_agent → flag_for_review (fields below 0.80)
       │
       ▼
  [HITL: clinician review gate]      ◄── Day 2b
  └─ transition_extraction_review
  └─ persist_extraction_relational, persist_extraction_vector
```

**output_key plumbing**: Each agent writes to `session.state` via its `output_key`. The next agent reads its predecessor's output from state, creating a typed data flow through the pipeline without direct agent-to-agent coupling.

### Patient Q&A Pipeline (SequentialAgent)

Answers clinical questions with cited evidence from notes, images, and vector search — grounded in patient context.

```
context_assembly_agent (flash-lite)
  └─ lookup_patient_record, validate_qa_request
       │
       ▼
evidence_retrieval_agent (pro-customtools)
  └─ search_clinical_notes, search_vector_store, retrieve_imaging_evidence
       │
       ▼
image_evidence_agent (pro)
  └─ analyze_evidence_images, fetch_image_from_gcs
       │
       ▼
citation_builder_agent (flash-lite)
  └─ build_citations
       │
       ▼
answer_synthesis_agent (pro)
  └─ compose_clinical_answer
       │
       ▼
qa_audit_agent (flash-lite)
  └─ log_audit_event, save_qa_to_memory
```

### DB Intelligence Pipeline (SequentialAgent)

Translates natural language questions into safe SQL, validates before execution, and generates visual chart specs.

```
schema_discovery_agent (flash-lite)
  └─ get_database_schema
       │
       ▼
nl_to_sql_agent (pro)
  └─ generate_sql
       │
       ▼
sql_validator_agent (flash-lite)
  └─ validate_sql_safety
       │
       ▼
query_executor_agent (pro-customtools)
  └─ execute_clinical_query (or approve_sql_preview → execute_approved_clinical_query)
       │
       ▼
insight_chart_agent (flash-lite)
  └─ generate_chart_spec, save_query_to_memory
```

## Security Architecture (3 Layers + Clinical)

Defense in depth — no single point of failure. All blocks are logged via `observability.log_security_event()`.

```
┌───────────────────────────────────────────────────────────┐
│  LAYER 1: Input Security (before_model_callback)          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 15 generic injection patterns                       │  │
│  │ + 3 HIPAA-specific: hipaa_bypass, phi_extraction,   │  │
│  │   safety_disable                                    │  │
│  │ Unicode NFKC normalization (anti-homoglyph)         │  │
│  └─────────────────────────────────────────────────────┘  │
├───────────────────────────────────────────────────────────┤
│  LAYER 2: Tool Security (before_tool_callback)            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Pydantic validation on all 22 tool inputs           │  │
│  │ Per-tool rate limiting via temp: state               │  │
│  │ Secret scanning on tool arguments                   │  │
│  └─────────────────────────────────────────────────────┘  │
├───────────────────────────────────────────────────────────┤
│  LAYER 3: Output Security (after_model_callback)          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ PII detection (email, phone, SSN, credit card)      │  │
│  │ PHI detection (MRN, ICD-10, NPI, DEA, drug dosage)  │  │
│  │ Secret leak detection (API keys, tokens, passwords) │  │
│  └─────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

**Clinical audit plugin** (`ClinicalAuditPlugin` in `plugins.py`): Tracks patient-data tool access, counts PHI detections, and flushes per-turn HIPAA audit summaries via `log_clinical_event()`.

## Memory Architecture (4 Layers)

```
┌────────────────────────────────────────────────────────────┐
│  Layer 1: Working Memory (context.py)                      │
│  Token-budgeted context per LLM call                       │
│  Compacted when exceeding threshold                        │
│  "Lost in middle" mitigation (inject at boundaries)        │
│  Used by: all agents on every call                         │
├────────────────────────────────────────────────────────────┤
│  Layer 2: Session State (ADK session.state)                │
│  output_key plumbing between pipeline stages               │
│  state["key"] — session scope                              │
│  state["user:pref"] — user scope (cross-session)           │
│  state["app:setting"] — app scope (global)                 │
│  state["temp:scratch"] — invocation-only (never persisted) │
│  Used by: SequentialAgent pipelines for inter-stage data    │
├────────────────────────────────────────────────────────────┤
│  Layer 3: Long-Term Memory (memory.py)                     │
│  InMemoryMemoryService (dev) / VertexAiMemoryBankService   │
│  Auto-saved via after_agent_callback                       │
│  PHI filtered before storage (detect_phi + redact_phi)     │
│  Used by: save_qa_to_memory, save_query_to_memory          │
├────────────────────────────────────────────────────────────┤
│  Layer 4: A2A Context (prepare_a2a_context)                │
│  Task-only data crosses agent boundaries                   │
│  No PII/PHI, no secrets, no temp:/user: keys               │
│  Used by: RemoteA2aAgent delegations                       │
└────────────────────────────────────────────────────────────┘
```

## Human-in-the-Loop (Day 2b)

Clinical review gate for extraction persistence:

```
Extraction pipeline completes
         │
         ▼
  confidence >= threshold? ──yes──▶ Auto-approve path
         │no
         ▼
  [Pause: needs_review]
  Clinician sees results in Clinical Inbox
         │
    ┌────┴────┐
    ▼         ▼
 Approve   Reject
    │         │
    ▼         ▼
 persist   discard + reason logged
 to stores
```

The `transition_extraction_review` tool enforces the state machine: only `needs_review` → `approved` or `needs_review` → `rejected` transitions are valid. Persistence tools (`persist_extraction_relational`, `persist_extraction_vector`) require an approved review receipt.

## MCP + A2A Interoperability

**MCP Server** (`mcp_server/server.py`): 7 clinical tools exposed via FastMCP (JSON-RPC 2.0). Any MCP-compatible client (ADK, Claude Desktop, other frameworks) can discover and call these tools.

**A2A Server** (`a2a_server.py`): Agent2Agent protocol endpoint. Serves an agent card at `/.well-known/agent-card.json` describing the agent's capabilities, input/output schemas, and supported skills. Remote agents delegate tasks via the A2A protocol with isolated memory context.

```
┌─────────────────┐     MCP (JSON-RPC 2.0)     ┌─────────────────┐
│ External Client  │ ◀───────────────────────▶  │ mcp_server/     │
│ (Claude Desktop, │                            │ 7 clinical tools│
│  other agents)   │                            └─────────────────┘
└─────────────────┘
                        A2A Protocol
┌─────────────────┐ ◀───────────────────────▶  ┌─────────────────┐
│ Remote Agent     │     agent card + tasks     │ a2a_server.py   │
│ (any A2A client) │                            │ :8001           │
└─────────────────┘                            └─────────────────┘
```

## Google Cloud Ecosystem Mapping

| Tool / Module | Cloud Service | Purpose |
|---------------|---------------|---------|
| `store_to_gcs`, `fetch_image_from_gcs` | Cloud Storage (GCS) | Clinical image and document storage |
| `lookup_patient_record` | Firestore | Structured patient records |
| `search_clinical_notes`, `search_vector_store` | Vertex AI Vector Search | Semantic search over embeddings |
| `execute_clinical_query` | Cloud SQL / BigQuery | Relational clinical data queries |
| `analyze_clinical_image`, `analyze_evidence_images` | Vertex AI (Gemini Vision) | Multimodal image analysis |
| `observability.py` | Cloud Trace (OTLP) | Distributed tracing |
| `observability.py` | Cloud Logging | Structured JSON logs + audit trail |
| `memory.py` | Vertex AI Memory Bank | Long-term cross-session memory |
| `app.py` (deploy) | Cloud Run / Agent Engine / GKE | Production hosting |

## Observability (Day 4a)

Three pillars, all output redacted via `config.redact_secrets()`:

| Pillar | Implementation | Purpose |
|--------|---------------|---------|
| **Logs** | `setup_logging()` — structured JSON | Machine-parseable, searchable audit trail |
| **Traces** | `setup_tracing()` — OpenTelemetry OTLP/GCP | Distributed request tracing |
| **Clinical Events** | `log_clinical_event()` | HIPAA-style audit (patient access, PHI redaction, review decisions) |

**Plugins** (attached via `app.py`):
- `LoggingPlugin` — ADK built-in verbose request/response tracing
- `ObservabilityPlugin` — redacted lifecycle logging + token-budget estimates
- `ClinicalAuditPlugin` — patient-data access tracking + per-turn PHI metrics

## Module Dependency Graph

```
config.py ──────── standalone (env vars, redaction, clinical governance)
    │
    ├──▶ models.py ──── Pydantic I/O contracts (22 tool schemas)
    ├──▶ security.py ── PII + PHI detection, injection patterns, redaction
    │        │
    │        ├──▶ observability.py ── logging, tracing, clinical events
    │        └──▶ memory.py ────── session/memory factories, PHI filter, A2A prep
    │
    ├──▶ context.py ──── token budgeting, compaction, boundary injection
    ├──▶ llm.py ──────── 3-tier model registry + build_model (retry, backoff)
    └──▶ prompts.py ──── agent instruction templates

    callbacks.py ─────── 3-layer security (input → tool → output)
    plugins.py ───────── ObservabilityPlugin + ClinicalAuditPlugin + LoggingPlugin
    orchestration.py ── 3 pipeline factories, agent-as-tool, code exec, remote A2A
    human_in_the_loop.py ─ long-running approval tool (Day 2b)
    tools.py ─────────── 22 clinical tools + clinical event logging
    clinical_schemas.py ─ SQL DDL + validation + mock query engine
    mock_data.py ─────── deterministic clinical fixture data
    agent.py ─────────── imports ALL, wires root_agent + 22 sub-agents
    app.py ───────────── App(root_agent, plugins, compaction, resumability)
    a2a_server.py ────── to_a2a(root_agent) ASGI app (Day 5a)
```

## Course Day Coverage

| Day | Notebook | Module(s) | What it demonstrates |
|-----|----------|-----------|---------------------|
| 1a | Foundational LLM + Tools | `llm.py`, `tools.py`, `models.py` | 3-tier model registry, 22 Pydantic-validated tools |
| 1b | Multi-Agent Orchestration | `orchestration.py`, `agent.py` | SequentialAgent pipelines, LoopAgent validation, agent-as-tool |
| 2a | Agent Tools Deep Dive | `tools.py`, `clinical_schemas.py` | Code execution agent, MCP integration, tool diversity |
| 2b | Human-in-the-Loop | `human_in_the_loop.py`, `callbacks.py` | Long-running approval, confidence-gated review |
| 3a | Session State | `memory.py`, `orchestration.py` | output_key plumbing, state prefix scoping |
| 3b | Long-Term Memory | `memory.py` | MemoryService factories, PII/PHI governance |
| 4a | Observability | `observability.py`, `plugins.py` | Structured logging, OpenTelemetry tracing, clinical audit plugin |
| 4b | Evaluation | `eval/`, `tests/` | AgentEvaluator eval set, tool trajectory + response match |
| 5a | Agent2Agent | `a2a_server.py`, `orchestration.py` | A2A serving, agent card, RemoteA2aAgent |
| 5b | Deployment | `deployment/`, `app.py` | Cloud Run, Agent Engine, GKE, Dockerfile |

## Deployment (Day 5b)

Three targets, all reading secrets from `.env` / Secret Manager:

```
                 ┌──────────────────────────────────┐
   adk web ─────▶│  Cloud Run (Dockerfile)          │
                 │  non-root, healthcheck, :8000    │
                 └──────────────┬───────────────────┘
adk deploy       ┌──────────────▼───────────────────┐     ┌──────────────────┐
agent_engine ───▶│  Vertex AI Agent Engine          │────▶│  Gemini 3.1 API  │
                 │  autoscale, Memory Bank           │     │  (LLM inference) │
                 └──────────────┬───────────────────┘     └──────────────────┘
   container ────▶ GKE (self-managed Kubernetes)
   uvicorn   ────▶ A2A server (:8001, agent card) ── for agent-to-agent calls
```
