# capstone_agent — ADK Agent Backend

The core Google ADK agent package implementing a **16-agent clinical AI orchestrator** with three specialist pipelines, 22+ tools, 3-layer security, 4-layer memory, and full observability.

This package is discovered by ADK via `__init__.py` and can be run with `adk run capstone_agent` or served as an A2A endpoint.

---

## Module Map

### Entry Points

| Module | Purpose |
|--------|---------|
| `__init__.py` | Package init — imports `agent` so ADK discovers `root_agent` |
| `agent.py` | Root agent wiring — imports all modules, builds the `clinical_orchestrator` LlmAgent |
| `app.py` | `App(root_agent, plugins, compaction, resumability)` — production wrapper with plugins and history compaction |
| `a2a_server.py` | Agent2Agent ASGI server (`to_a2a(root_agent)`) — exposes agent card at `/.well-known/agent-card.json` |

### Core Infrastructure

| Module | Purpose |
|--------|---------|
| `config.py` | Centralized configuration from `.env`, secret redaction (`redact_secrets()`), deterministic JSON serialization |
| `llm.py` | 3-tier model registry (`flash-lite`, `pro`, `pro-customtools`) with `build_model(tier)` — exponential backoff + HTTP retry |
| `models.py` | Pydantic models for tool contracts: `ToolResponse`, `ToolError` — all tools return one of these |
| `prompts.py` | Agent instruction templates (root orchestrator, pipeline-specific). Each under 60 lines |

### Security (3 Layers)

| Module | Purpose |
|--------|---------|
| `security.py` | Pure-function security detection: `scan_for_secrets()` (15+ patterns), `detect_pii()` (email, phone, SSN, credit card), `sanitize_input()` (unicode normalization), `detect_injection()` (prompt injection patterns) |
| `callbacks.py` | ADK callback wiring — `content_safety_callback` (input), `tool_authorization_callback` (tool), `output_safety_callback` (output) |

### Memory (4 Layers)

| Module | Purpose |
|--------|---------|
| `context.py` | Layer 1 Working Memory — `estimate_tokens()`, `build_structured_context()`, `compact_history()`, `inject_at_boundaries()` |
| `memory.py` | Layers 2-3 — `create_session_service()` (in-memory or DatabaseSessionService), `create_memory_service()` (in-memory or VertexAiMemoryBankService), `auto_save_memory_callback`, `search_past_conversations` |

### Observability

| Module | Purpose |
|--------|---------|
| `observability.py` | Structured JSON logging (`setup_logging()`), OpenTelemetry tracing (`setup_tracing()`), `log_tool_call()`, `log_security_event()`, `timed_operation()` context manager |
| `plugins.py` | ADK `BasePlugin` implementation — `ObservabilityPlugin` (lifecycle-wide event logging with redaction) + ADK `LoggingPlugin` |

### Agent Orchestration

| Module | Purpose |
|--------|---------|
| `orchestration.py` | Pipeline builders: `build_image_extraction_pipeline()` (5 agents), `build_patient_qa_pipeline()` (6 agents), `build_db_intelligence_pipeline()` (5 agents). Also: `as_tool()` (agent-as-tool wrapper), `build_code_executor_agent()`, `build_remote_a2a_agent()` |
| `human_in_the_loop.py` | `request_sensitive_action()` — `LongRunningFunctionTool` that pauses execution for clinician review/approval |

### Clinical Domain

| Module | Purpose |
|--------|---------|
| `tools.py` | Custom ADK tools with Pydantic validation — audit logging, document upload/search, patient data, image analysis, clinical queries |
| `clinical_schemas.py` | SQL validation (`validate_sql()`), clinical field schemas, extraction confidence thresholds |
| `database.py` | SQLite clinical database layer — schema creation, `execute_sql()`, patient/session/extraction CRUD |
| `document_processor.py` | PDF and image document processing — text extraction (PyMuPDF), image analysis preparation |
| `mock_data.py` | Synthetic patient data generation for demo mode — realistic clinical scenarios without real PHI |

---

## Pipeline Architecture

### Image Extraction Pipeline (5 Agents)

```
quality_assessor_agent (flash-lite)  →  Assess image quality
vision_analyzer_agent (pro)          →  AI vision analysis
structuring_agent (pro)              →  Map to clinical fields (SNOMED)
validation_agent (flash-lite)        →  Flag low-confidence fields
persistence_agent (flash-lite)       →  Store to JSON/relational/vector + audit
```

### Patient Q&A Pipeline (6 Agents)

```
request_validator_agent (flash-lite)     →  Validate and classify question
patient_context_agent (pro-customtools)  →  Retrieve patient context
evidence_retriever_agent (pro-customtools) →  Find text + image evidence
citation_assembler_agent (flash-lite)    →  Build evidence citations
answer_synthesizer_agent (pro)           →  Compose cited answer
audit_agent (flash-lite)                 →  Log Q&A interaction
```

### DB Intelligence Pipeline (5 Agents)

```
schema_discovery_agent (flash-lite)      →  Discover available tables/columns
sql_generator_agent (pro)                →  NL-to-SQL translation
safety_validator_agent (flash-lite)      →  Deterministic SQL safety check
execution_agent (pro-customtools)        →  Execute with preview approval
insight_agent (pro)                      →  Charts, insights, CSV export
```

---

## Model Tiers

All agents use `llm.build_model(tier)` — never bare model strings.

| Tier | Model | Retry | Use Case |
|------|-------|-------|----------|
| `flash-lite` | `gemini-3.1-flash-lite` | 3 retries, exponential backoff | Routing, validation, audit (cheap/fast) |
| `pro` | `gemini-3.1-pro-preview` | 3 retries, exponential backoff | Reasoning (SQL gen, answer synthesis) |
| `pro-customtools` | `gemini-3.1-pro-preview-customtools` | 3 retries, exponential backoff | Tool-heavy (evidence retrieval, vision) |

---

## Usage

```powershell
# CLI interaction
adk run capstone_agent

# Web UI
adk web .

# A2A serving
uvicorn capstone_agent.a2a_server:app --port 8001

# As part of the clinical product
# (imported by clinical_app/agent_runtime.py)
```

---

## Module Dependency Graph

Leaf modules have no project imports. No circular dependencies.

```
config.py (standalone) → llm.py, models.py, security.py, context.py
security.py → observability.py, memory.py
observability.py → callbacks.py, plugins.py
llm.py → orchestration.py, agent.py
memory.py → callbacks.py
models.py → tools.py
prompts.py (standalone)
callbacks.py + context.py → plugins.py
ALL → agent.py → app.py / a2a_server.py
```
