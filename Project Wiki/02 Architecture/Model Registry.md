---
title: Model Registry
type: architecture
status: active
updated: 2026-07-04
source: docs/architecture.md, README.md, capstone_agent/llm.py
tags:
  - architecture
  - models
---

# Model Registry

`capstone_agent/llm.py` is the single place model selection happens. Every agent gets a `Gemini` built with `HttpRetryOptions` (exponential backoff) via `build_model(tier)` — **never a bare model-id string**.

## Tiers

| Tier | Model | Used by |
|------|-------|---------|
| `flash-lite` (default) | `gemini-3.1-flash-lite` | Orchestrator routing, validation, audit, simple stages |
| `pro` | `gemini-3.1-pro-preview` | Reasoning-heavy: SQL generation, answer synthesis, vision analysis |
| `pro-customtools` | `gemini-3.1-pro-preview-customtools` | Tool-heavy: evidence retrieval, query execution |

The README also references a `flash-image` tier used by the Q&A and DB pipelines for generated visuals (image output).

## Rules

> [!warning] Never bypass the registry
> - Never pass a bare model-id string to an ADK `LlmAgent`. Always `llm.build_model(tier)` — it adds retry/backoff and centralizes selection.
> - Add new tiers in `llm.MODEL_TIERS`; never invent model identifiers.
> - Gemini 3.1 on Vertex AI requires `GOOGLE_CLOUD_LOCATION=global`.

## Auth paths (live mode)

Demo mode needs no credentials. For live agent mode, one of:

1. `GOOGLE_API_KEY=<key>` in `.env`
2. Vertex AI via ADC: `gcloud auth application-default login` + `GOOGLE_GENAI_USE_VERTEXAI=TRUE` + `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION=global`

Then `AGENT_EXECUTION_MODE=live`. See [[Clinical App]] for how the product server switches modes.

Related: [[Agent Architecture]] · [[Module Reference]]
