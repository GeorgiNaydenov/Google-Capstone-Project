# Problem & Solution

> Source: Project Wiki/01 Overview/Problem & Solution.md
> Collected: 2026-07-05
> Published: 2026-07-04

# Problem & Solution

## Problem

Clinical work spans disconnected notes, session images, structured records, historical evidence, and population databases. Clinicians need an auditable way to turn those inputs into structured findings without hiding uncertainty, evidence, or human review behind a generic chatbot.

## Solution

Nexus provides a dense, role-aware command center for synthetic clinical data. The product exposes three guided AI workflows:

1. **Session Image Extraction** — OCR, field confidence, clinician review, storage receipts, timeline updates, and audit events. See [[Image Extraction Pipeline]].
2. **Patient-Scoped Multimodal Q&A** — evidence citations, source viewing, and multi-modal reasoning with text and images. See [[Patient QA Pipeline]].
3. **Database Intelligence** — natural-language SQL generation, safety approval, table/chart/CSV export, history, and audit. See [[DB Intelligence Pipeline]].

The public demo is fully deterministic and requires no model key. The live agent engine in `capstone_agent/` implements the same workflows using Google ADK and Gemini when valid credentials are configured — see [[Clinical App]] for demo vs live mode.

> [!warning] Demo scope
> All patient data is synthetic — no real PHI. This capstone demo is not a medical device and is not authorized for real patient data.

## Safety posture

- Per-demo-session isolated state with full reset capability
- Role-aware API operations (clinician vs admin)
- Read-only SQL preview with explicit execution boundary ([[DB Intelligence Pipeline]])
- Human-in-the-loop review before extraction persistence ([[Human-in-the-Loop Approval]])
- Structured secret/PII controls and redacted observability ([[Security Layers]], [[Observability]])
