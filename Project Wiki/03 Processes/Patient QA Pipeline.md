---
title: Patient QA Pipeline
type: process
status: active
updated: 2026-07-04
source: docs/architecture.md
tags:
  - process
  - bpmn
  - pipeline
---

# Patient QA Pipeline

SequentialAgent (7 agents) answering clinical questions with cited evidence from notes, images, and vector search — grounded in patient context.

```mermaid
flowchart TD
    START([Patient-scoped question]) --> CA
    CA["context_assembly_agent (flash-lite)<br/>lookup_patient_record, validate_qa_request"] --> ER
    ER["evidence_retrieval_agent (pro-customtools)<br/>search_clinical_notes, search_vector_store,<br/>retrieve_imaging_evidence"] --> IE
    IE["image_evidence_agent (pro)<br/>analyze_evidence_images, fetch_image_from_gcs"] --> CB
    CB["citation_builder_agent (flash-lite)<br/>build_citations"] --> AS
    AS["answer_synthesis_agent (pro)<br/>compose_clinical_answer"] --> AU
    AU["qa_audit_agent (flash-lite)<br/>log_audit_event, save_qa_to_memory"] --> DONE([Cited answer + audit trail])
```

Key facts:

- Validation happens first: `validate_qa_request` rejects out-of-scope requests before any retrieval.
- Evidence is multimodal — text notes, vector search hits, and imaging pulled from GCS and analyzed by Gemini Vision.
- Every answer carries citations built before synthesis, so sources are traceable in the UI ([[Clinical App]]).
- The audit stage persists the exchange to long-term memory (`save_qa_to_memory`) with PHI filtered first ([[Memory Layers]] Layer 3).

Related: [[Agent Architecture]] · [[End-to-End Request Flow]]
