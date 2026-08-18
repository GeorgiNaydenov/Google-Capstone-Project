# Agent Architecture

> Sources: Antigravity, 2026-07-05
> Raw: [Agent Architecture Source](../../raw/architecture/2026-07-04-agent-architecture.md)

# Agent Architecture

A root orchestrator routes every request to one of three `SequentialAgent` pipelines. The topology contains 22 LLM agents total: the root plus 21 specialists. Extraction also nests a `LoopAgent` container. All LLM agents get their model via `llm.build_model(tier)` — see [[Model Registry]] — and every interaction passes through the [[Security Layers]] callbacks.

## Pipeline overview

| Pipeline | Agents | Model tiers | Purpose |
|----------|--------|-------------|---------|
| **Image Extraction** | 7 specialist LLM agents (`SequentialAgent` + nested `LoopAgent`) | flash-lite, pro, pro-customtools | Quality → OCR → AI vision → structuring → critic/refiner loop → review-request preparation |
| **Patient Q&A** | 8 specialist LLM agents (`SequentialAgent`) | flash-lite, pro, pro-customtools | Validation → context → retrieval → image evidence → citations → answer synthesis → audit → response |
| **DB Intelligence** | 6 specialist LLM agents (`SequentialAgent`) | flash-lite, pro | Schema discovery → NL-to-SQL → safety validation → approval preparation → execution → insights/charts |
| **Orchestrator** | 1 root agent | flash-lite | Intent routing, MCP tools, memory recall, HITL approval |

## Root orchestrator

`clinical_orchestrator` (flash-lite) routes to the three pipelines based on intent. It carries MCP tools, `search_past_conversations` (memory recall), and the HITL approval tool. Every user turn first passes `content_safety_callback` (Layer 1 input security).

## Agent roster by pipeline

### Image Extraction (see [[Image Extraction Pipeline]] for the process diagram)

| Agent | Tier | Tools |
|-------|------|-------|
| `quality_assessor_agent` | flash-lite | `assess_image_quality` |
| `ocr_processor_agent` | flash-lite | `extract_clinical_text` |
| `vision_analyzer_agent` | pro-customtools | `analyze_clinical_image` |
| `clinical_structuring_agent` | pro | `structure_clinical_findings`, `store_to_gcs` |
| `extraction_critic_agent` | flash-lite | `exit_loop` (confidence check) |
| `extraction_refiner_agent` | flash-lite | `flag_for_review` (low-confidence fields) |
| `clinical_review_request_agent` | flash-lite | prepares a pending packet for external clinician review |

`validation_gate` is the non-LLM `LoopAgent` container around the critic and refiner. Clinician approval, persistence, and audit are external deterministic product/tool boundaries, not additional LLM agents.

### Patient Q&A (see [[Patient QA Pipeline]])

| Agent | Tier | Tools |
|-------|------|-------|
| `qa_request_validation_agent` | flash-lite | `validate_qa_request` |
| `context_assembly_agent` | flash-lite | `lookup_patient_record`, `load_memory`, `search_past_conversations` |
| `evidence_retrieval_agent` | pro-customtools | `search_clinical_notes`, `search_vector_store`, `search_documents`, `retrieve_imaging_evidence` |
| `image_evidence_agent` | pro-customtools | `analyze_evidence_images`, `fetch_image_from_gcs` |
| `citation_builder_agent` | flash-lite | `build_citations` |
| `answer_synthesis_agent` | pro | `compose_clinical_answer`, `generate_clinical_visual` |
| `qa_audit_agent` | flash-lite | `log_audit_event`, `save_qa_to_memory` |
| `qa_response_agent` | flash-lite | returns the cited response after audit and memory writes |

### DB Intelligence (see [[DB Intelligence Pipeline]])

| Agent | Tier | Tools |
|-------|------|-------|
| `schema_discovery_agent` | flash-lite | `get_database_schema` |
| `nl_to_sql_agent` | pro | `generate_sql` |
| `sql_validator_agent` | flash-lite | `validate_sql_safety` |
| `sql_preview_approval_agent` | pro | `approve_sql_preview` |
| `query_executor_agent` | pro | `execute_approved_clinical_query` |
| `insight_chart_agent` | pro | `generate_chart_spec`, `generate_clinical_visual`, `log_audit_event`, `save_query_to_memory` |

## output_key plumbing

Each agent writes to `session.state` via its `output_key`; the next agent reads its predecessor's output from state. This creates a typed data flow through the pipeline without direct agent-to-agent coupling — Layer 2 of the [[Memory Layers]].

> [!note] Where agents are wired
> Pipeline factories live in `capstone_agent/orchestration.py`; `capstone_agent/agent.py` imports all modules and wires the root agent. Instructions live in `prompts.py` (under 60 lines each).
