---
title: System Overview
type: architecture
status: active
updated: 2026-07-05
source: docs/architecture.md
tags:
  - architecture
---

# System Overview

A multi-agent clinical AI platform built on Google ADK that processes medical imaging, answers patient questions with cited evidence, and runs natural-language database intelligence — all gated by clinician-in-the-loop review and HIPAA-aligned security.

## The four-layer stack

```mermaid
flowchart TD
    FE["React Frontend (frontend/)<br/>16 routes - clinician + admin views - Vite + TypeScript"]
    API["FastAPI Product Server (clinical_app/app.py)<br/>Demo mode (deterministic) or Live ADK bridge<br/>Session isolation - role-based access - audit trail"]
    ADK["ADK Agent Backend (capstone_agent/)<br/>22 sub-agents - 3 pipelines - 24+ tools<br/>3-layer security - 4-layer memory - HITL - observability"]
    MCP["MCP Server (mcp_server/server.py)<br/>7 clinical tools via FastMCP (JSON-RPC 2.0)"]

    FE -- "HTTP /api/*" --> API
    API -- "ADK Runner" --> ADK
    ADK --- MCP
```

- **React frontend** — 16-route clinical UI (Vite + TypeScript), served as a production build by FastAPI. See [[Clinical App]].
- **FastAPI product server** (`clinical_app/`) — operates in deterministic demo mode or bridges live to the ADK runner; session isolation, role-based access, audit trail. See [[Clinical App]].
- **ADK agent backend** (`capstone_agent/`) — the agent pipelines, tools, security callbacks, memory, and observability. See [[Agent Architecture]] and [[Module Reference]].
- **MCP tool server** (`mcp_server/`) — real database-backed clinical tools exposed over the Model Context Protocol. See [[MCP and A2A]].

## Visible Architecture

The frontend now exposes [[Diagram Atlas]] as a first-class product surface. It renders six categories with sub-tabs, pan and zoom controls, SVG-first assets, PNG fallbacks, fullscreen viewing, and contextual inline diagrams beside the workflows they explain.

| Category | Product coverage |
|---|---|
| System | Full stack, C4 pages, module graph, route map, REST API map |
| Agents & Pipelines | Agent hierarchy, A2A, MCP, execution mode, context pipeline, Gemini tiers |
| Security & Memory | Memory layers, security callbacks, security block sequence, harness governance |
| Processes | Request lifecycle, HITL, ingestion, wiki sync, chat, approval, A2A delegation, animated Q&A flow |
| Data & API | Clinical ERD and Pydantic contracts |
| Deployment & Quality | Deployment, observability, eval flywheel, rubric coverage |

## Google Cloud ecosystem mapping

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

Related: [[Model Registry]] · [[Security Layers]] · [[Memory Layers]] · [[Deployment]]
