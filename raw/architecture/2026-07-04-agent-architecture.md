# Agent Architecture

> Source: Project Wiki/02 Architecture/Agent Architecture.md
> Collected: 2026-07-05
> Published: 2026-07-04

# Agent Architecture

A root orchestrator routes every request to one of three SequentialAgent pipelines. All agents get their model via `llm.build_model(tier)` — see [[Model Registry]] — and every interaction passes through the [[Security Layers]] callbacks.

## Pipeline overview

| Pipeline | Agents | Model tiers | Purpose |
|----------|--------|-------------|---------|
| **Image Extraction** | 9 agents (SequentialAgent + LoopAgent) | flash-lite, pro, pro-customtools | Quality → OCR → AI vision → structuring → critic/refiner loop → review gate → persistence → audit |
| **Patient Q&A** | 7 agents (SequentialAgent) | flash-lite, pro, pro-customtools, flash-image | Validation → context → retrieval → image evidence → citations → answer synthesis (with generated visuals) → audit |
| **DB Intelligence** | 6 agents (SequentialAgent) | flash-lite, pro, flash-image | Schema discovery → NL-to-SQL → safety validation → approval gate → execution → insights/charts |
| **Orchestrator** | 1 root agent | flash-lite | Intent routing, MCP tools, memory recall, HITL approval |

## Root orchestrator

`clinical_orchestrator` (flash-lite) routes to the three pipelines based on intent. It carries MCP tools, `search_past_conversations` (memory recall), and the HITL approval tool. Every user turn first passes `content_safety_callback` (Layer 1 input security).

## Agent roster by pipeline

### Image Extraction (see [[Image Extraction Pipeline]] for the process diagram)

| Agent | Tier | Tools |
|-------|------|-------|
| `quality_assessor_agent` | flash-lite | `assess_image_quality` |
| `vision_analyzer_agent` | pro | `analyze_clinical_image` |
| `clinical_structuring_agent` | pro | `structure_clinical_findings`, `store_to_gcs` |
| `validation_gate` (LoopAgent) | — | wraps critic + refiner (Day 1b loop pattern) |
| `critic_agent` | — | `exit_loop` (confidence >= threshold) |
| `refiner_agent` | — | `flag_for_review` (fields below 0.80) |
| HITL review gate | — | `transition_extraction_review`, `persist_extraction_relational`, `persist_extraction_vector` |

### Patient Q&A (see [[Patient QA Pipeline]])

| Agent | Tier | Tools |
|-------|------|-------|
| `context_assembly_agent` | flash-lite | `lookup_patient_record`, `validate_qa_request` |
| `evidence_retrieval_agent` | pro-customtools | `search_clinical_notes`, `search_vector_store`, `retrieve_imaging_evidence` |
| `image_evidence_agent` | pro | `analyze_evidence_images`, `fetch_image_from_gcs` |
| `citation_builder_agent` | flash-lite | `build_citations` |
| `answer_synthesis_agent` | pro | `compose_clinical_answer` |
| `qa_audit_agent` | flash-lite | `log_audit_event`, `save_qa_to_memory` |

### DB Intelligence (see [[DB Intelligence Pipeline]])

| Agent | Tier | Tools |
|-------|------|-------|
| `schema_discovery_agent` | flash-lite | `get_database_schema` |
| `nl_to_sql_agent` | pro | `generate_sql` |
| `sql_validator_agent` | flash-lite | `validate_sql_safety` |
| `query_executor_agent` | pro-customtools | `execute_clinical_query` (or `approve_sql_preview` → `execute_approved_clinical_query`) |
| `insight_chart_agent` | flash-lite | `generate_chart_spec`, `save_query_to_memory` |

## output_key plumbing

Each agent writes to `session.state` via its `output_key`; the next agent reads its predecessor's output from state. This creates a typed data flow through the pipeline without direct agent-to-agent coupling — Layer 2 of the [[Memory Layers]].

> [!note] Where agents are wired
> Pipeline factories live in `capstone_agent/orchestration.py`; `capstone_agent/agent.py` imports all modules and wires the root agent. Instructions live in `prompts.py` (under 60 lines each).
