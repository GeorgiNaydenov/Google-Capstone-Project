---
title: End-to-End Request Flow
type: process
status: active
updated: 2026-07-04
source: docs/architecture.md, capstone_agent/callbacks.py
tags:
  - process
  - bpmn
---

# End-to-End Request Flow

Every request crosses three security gates and one routing decision. BPMN-style lanes: User, Security, Orchestrator, Pipelines.

```mermaid
flowchart TD
    subgraph LANE_USER["Lane: User"]
        START([User request]) --> IN[Message enters agent]
        RESP([Response delivered])
    end

    subgraph LANE_SEC["Lane: Security (callbacks.py)"]
        L1{Layer 1<br/>content_safety_callback<br/>injection? unicode attack?}
        L2{Layer 2<br/>tool_authorization_callback<br/>args valid? rate ok? secrets?}
        L3{Layer 3<br/>output_safety_callback<br/>PII/PHI/secret leak?}
        BLOCK1[Block + log_security_event]
        BLOCK2[Block + log_security_event]
        REDACT[Redact or block + log]
    end

    subgraph LANE_ORCH["Lane: Orchestrator (flash-lite)"]
        ROUTE{Intent routing}
        MCPT[MCP tools / memory recall / HITL approval]
    end

    subgraph LANE_PIPE["Lane: Pipelines (SequentialAgent)"]
        P1[Image Extraction<br/>9 agents]
        P2[Patient Q&A<br/>7 agents]
        P3[DB Intelligence<br/>6 agents]
        TOOLS[Tool execution<br/>Pydantic-validated]
    end

    IN --> L1
    L1 -->|blocked| BLOCK1 --> RESP
    L1 -->|clean| ROUTE
    ROUTE -->|image workflow| P1
    ROUTE -->|patient question| P2
    ROUTE -->|database question| P3
    ROUTE -->|direct| MCPT
    P1 --> L2
    P2 --> L2
    P3 --> L2
    MCPT --> L2
    L2 -->|blocked| BLOCK2 --> RESP
    L2 -->|valid| TOOLS
    TOOLS --> L3
    L3 -->|found| REDACT --> RESP
    L3 -->|clean| RESP
```

Key facts:

- Layer 1 blocks 18 injection/extraction patterns (15 generic + 3 HIPAA-specific) after unicode NFKC normalization.
- Layer 2 runs per tool call: Pydantic validation, `temp:` state rate limiting, secret scan on arguments.
- Layer 3 inspects every model response for PII, PHI, and secrets before it reaches the user.
- Every block/detection is logged via `observability.log_security_event()`.

Related: [[Security Layers]] · [[Agent Architecture]] · [[Image Extraction Pipeline]] · [[Patient QA Pipeline]] · [[DB Intelligence Pipeline]]
