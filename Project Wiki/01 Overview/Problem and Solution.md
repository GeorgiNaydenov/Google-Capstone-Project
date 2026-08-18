---
title: Problem and Solution
type: overview
status: active
updated: 2026-07-04
source: README.md
tags:
  - overview
---

# Problem and Solution

## Problem

Clinical work spans disconnected notes, session images, structured records, historical evidence, and population databases. Clinicians need an auditable way to turn those inputs into structured findings without hiding uncertainty, evidence, or human review behind a generic chatbot.

## Solution

Clinical AI Kit provides a dense, role-aware command center for synthetic clinical data. The product exposes three guided AI workflows:

1. **Session Image Extraction** — OCR, field confidence, clinician review, storage receipts, timeline updates, and audit events. See [[Image Extraction Pipeline]].
2. **Patient-Scoped Multimodal Q&A** — evidence citations, source viewing, and multi-modal reasoning with text and images. See [[Patient QA Pipeline]].
3. **Database Intelligence** — natural-language SQL generation, safety approval, table/chart/CSV export, history, and audit. See [[DB Intelligence Pipeline]].

The public Cloud Run build is fully deterministic and requires no model key; paid ADK/Gemini execution is disabled there. A self-controlled deployment can enable the live agent engine in `capstone_agent/` with valid Google credentials — see [[Clinical App]] for deterministic versus live execution.

> [!warning] Demo scope
> All patient data is synthetic — no real PHI. This capstone demo is not a medical device and is not authorized for real patient data.

## Safety posture

- Per-demo-session isolated state with full reset capability
- Role-aware API operations (clinician vs admin)
- Read-only SQL preview with explicit execution boundary ([[DB Intelligence Pipeline]])
- Human-in-the-loop review before extraction persistence ([[Human-in-the-Loop Approval]])
- Structured secret/PII controls and redacted observability ([[Security Layers]], [[Observability]])
