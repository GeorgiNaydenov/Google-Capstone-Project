---
title: Observability
type: operations
status: active
updated: 2026-07-04
source: docs/architecture.md, capstone_agent/observability.py, capstone_agent/plugins.py
tags:
  - operations
  - observability
---

# Observability

Three pillars — Logs (diary), Traces (narrative), Metrics (timing) — plus clinical audit events. All output passes through `config.redact_secrets()` before emission.

| Pillar | Implementation | Purpose |
|--------|----------------|---------|
| **Logs** | `setup_logging()` — structured JSON | Machine-parseable, searchable audit trail |
| **Traces** | `setup_tracing()` — OpenTelemetry OTLP/GCP | Distributed request tracing |
| **Clinical events** | `log_clinical_event()` | HIPAA-style audit: patient access, PHI redaction, review decisions |

## Key functions (`observability.py`)

| Function | Purpose |
|----------|---------|
| `setup_logging(level)` | Structured JSON logger |
| `setup_tracing()` | OTLP exporter — opt-in via `ENABLE_TRACING`; `TRACE_EXPORTER=gcp` routes to Cloud Trace |
| `log_tool_call(name, args, result, duration_ms)` | Redacted tool audit with timing |
| `log_security_event(event_type, details)` | Audit trail for every block/detection ([[Security Layers]]) |
| `log_clinical_event(...)` | Clinical audit events |
| `timed_operation(name)` | Context manager measuring operation duration |

Logging and tracing initialize at import time in `agent.py`. Tracing degrades gracefully: missing OTel packages or `ENABLE_TRACING=FALSE` means the agent runs normally without traces.

## Plugins (attached via `app.py` → `App(..., plugins=build_plugins())`)

| Plugin | Purpose |
|--------|---------|
| `LoggingPlugin` (ADK built-in) | Verbose request/response tracing |
| `ObservabilityPlugin` | Redacted lifecycle logging + token-budget estimates |
| `ClinicalAuditPlugin` | Patient-data access tracking + per-turn PHI metrics |

> [!note] Rule
> No `print()` statements in agent code — structured JSON logging via `observability.py` only. Harness scripts under `scripts/` are exempt.

Related: [[Security Layers]] · [[System Overview]] (Cloud Trace / Cloud Logging mapping)
