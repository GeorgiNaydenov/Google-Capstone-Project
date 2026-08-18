# Image Extraction Pipeline

> Source: Project Wiki/03 Processes/Image Extraction Pipeline.md
> Collected: 2026-07-05
> Published: 2026-07-04

# Image Extraction Pipeline

`SequentialAgent` containing 7 specialist LLM agents, with a nested `LoopAgent`, processes clinical images through quality assessment, OCR, AI vision analysis, structured field extraction, critic/refiner validation, and review-request preparation. Clinician review and persistence remain external deterministic boundaries. Lanes: Agents, Validation Loop, Clinician.

```mermaid
flowchart TD
    subgraph LANE_AG["Lane: Pipeline agents"]
        QA["quality_assessor_agent (flash-lite)<br/>assess_image_quality"]
        OCR["ocr_processor_agent (flash-lite)<br/>extract_clinical_text"]
        VA["vision_analyzer_agent (pro-customtools)<br/>analyze_clinical_image"]
        CS["clinical_structuring_agent (pro)<br/>structure_clinical_findings, store_to_gcs"]
        RR["clinical_review_request_agent (flash-lite)<br/>prepare pending review packet"]
    end

    subgraph LANE_LOOP["Lane: validation_gate (LoopAgent, Day 1b)"]
        CRIT{extraction_critic_agent<br/>confidence >= threshold?}
        REF["extraction_refiner_agent<br/>flag_for_review (fields < 0.80)"]
        EXIT["exit_loop"]
    end

    subgraph LANE_HITL["Lane: Clinician (HITL, Day 2b)"]
        GATE{Clinician review<br/>transition_extraction_review}
        PERSIST["persist_extraction_relational<br/>persist_extraction_vector"]
        DISCARD["Discard + reason logged"]
    end

    START([Clinical image uploaded]) --> QA --> OCR --> VA --> CS --> CRIT
    CRIT -->|below threshold| REF --> CRIT
    CRIT -->|passes| EXIT --> RR --> GATE
    GATE -->|approve| PERSIST --> DONE([Stored + timeline updated + audit event])
    GATE -->|reject| DISCARD --> DONE2([Rejected, audit logged])
```

Key facts:

- **output_key plumbing**: each agent writes its result to `session.state`; the next stage reads it — no direct coupling ([[Memory Layers]] Layer 2).
- The **LoopAgent** repeats critic → refiner until field confidence passes the threshold; fields below 0.80 are flagged for review.
- The seven LLM specialists end with `clinical_review_request_agent`; clinician approval, persistence, and audit are product/tool boundaries rather than extra agents.
- **State machine**: `transition_extraction_review` only allows `needs_review` → `approved` or `needs_review` → `rejected`. Persistence tools require an approved review receipt — see [[Human-in-the-Loop Approval]].

Related: [[Agent Architecture]] · [[End-to-End Request Flow]]
