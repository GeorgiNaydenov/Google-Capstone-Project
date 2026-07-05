# Security Layers

> Sources: Antigravity, 2026-07-05
> Raw: [Security Layers Source](../../raw/security-memory/2026-07-04-security-layers.md)

# Security Layers

Defense in depth — three fixed callback layers plus clinical extensions. No single point of failure. All blocks are logged via `observability.log_security_event()` ([[Observability]]).

```mermaid
flowchart TD
    U[User input] --> L1
    subgraph L1["Layer 1 — Input Security (before_model_callback)"]
        P["15 generic injection patterns<br/>+ 3 HIPAA-specific: hipaa_bypass, phi_extraction, safety_disable<br/>Unicode NFKC normalization (anti-homoglyph)"]
    end
    L1 -->|clean| AG[Agent + LLM]
    L1 -->|blocked| B1[Blocked + logged]
    AG --> L2
    subgraph L2["Layer 2 — Tool Security (before_tool_callback)"]
        T["Pydantic validation on all tool inputs<br/>Per-tool rate limiting via temp: state<br/>Secret scanning on tool arguments"]
    end
    L2 -->|valid| TOOLS[Tool execution]
    L2 -->|blocked| B2[Blocked + logged]
    TOOLS --> L3
    subgraph L3["Layer 3 — Output Security (after_model_callback)"]
        O["PII detection: email, phone, SSN, credit card<br/>PHI detection: MRN, ICD-10, NPI, DEA, drug dosage<br/>Secret leak detection: API keys, tokens, passwords"]
    end
    L3 -->|clean| R[Response to user]
    L3 -->|found| RED[Redact or block + logged]
```

## The three callbacks (order is fixed)

| Layer | Callback | What it does |
|-------|----------|--------------|
| 1. Input | `content_safety_callback` (`before_model_callback`) | Sanitizes unicode (NFKC), blocks 18 injection/extraction patterns — 15 generic + 3 HIPAA-specific |
| 2. Tool | `tool_authorization_callback` (`before_tool_callback`) | Rate limits tool usage, Pydantic-validates arguments, scans arguments for secrets |
| 3. Output | `output_safety_callback` (`after_model_callback`) | Detects leaked secrets and PII/PHI in model responses; redacts or blocks |

Security logic lives in `security.py` as pure, testable functions (`scan_for_secrets`, `detect_pii`, `detect_phi`, `redact_phi`); `callbacks.py` wires it to ADK.

## Clinical extensions

- **PHI detection** adds clinical identifiers on top of PII: MRN, ICD-10 codes, NPI, DEA numbers, drug dosages.
- **`ClinicalAuditPlugin`** (`plugins.py`) tracks patient-data tool access, counts PHI detections, and flushes per-turn HIPAA audit summaries via `log_clinical_event()`.
- PHI is filtered before anything reaches long-term memory — see [[Memory Layers]].

## Rules

> [!warning] Invariants
> - The 3-layer callback order in `callbacks.py` is fixed and must be preserved.
> - All loggers route strings through `config.redact_secrets()` before emission.
> - Never write API keys or GCP credentials to long-term memory or session storage; run `redact_pii` before persisting memory layers.
> - Store sensitive config in `.env`, never commit API keys.

Related: [[End-to-End Request Flow]] · [[Testing & Eval]] (test_security.py, test_callbacks.py)
