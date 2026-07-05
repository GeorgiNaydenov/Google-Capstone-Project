# Writeup facts — verified numbers for the Kaggle submission

Source-of-truth figures for the ≤2,500-word writeup and the 5-minute video.
Everything here is verified against the code, not estimated.

## One-line pitch

Nexus Clinical AI Command Center — a clinician-facing platform where a visible
multi-agent system turns fragmented clinical evidence (images, notes, records,
population data) into decisions clinicians can verify, with every consequential
write held behind human review.

## Competition concepts demonstrated (5 of the required 3)

| Concept | Evidence |
|---------|----------|
| Agent / multi-agent (ADK) | 1 root orchestrator + 22 pipeline sub-agents across 3 SequentialAgent pipelines (`capstone_agent/agent.py`, `orchestration.py`) |
| MCP server | `mcp_server/server.py` — FastMCP clinical tools over JSON-RPC/stdio, consumed by the agent and any MCP client |
| Security | 3-layer callback pipeline: input injection blocking, tool validation + rate limiting, output PII/PHI/secret scanning (`capstone_agent/callbacks.py`, `security.py`) |
| Deployability | Multi-stage Dockerfile (frontend + API single origin), Cloud Build → Cloud Run, Vertex AI Agent Engine config (`deployment/`) |
| Agent Skills | `.claude/` + `.agents/` harness skills (diagramming, testing workflow, deployment) that govern this repo's own development |

## Architecture counts (verified)

- **Agents**: 23 total = 1 orchestrator + 22 sub-agents. Pipelines: Image
  Extraction **9**, Patient Q&A **7**, Database Intelligence **6**.
- **Model tiers** (`capstone_agent/llm.py`): flash-lite (default), pro,
  pro-customtools, flash-image.
- **Security**: 15 generic + 3 HIPAA-specific injection patterns; PII (email,
  phone, SSN, credit card) + PHI (MRN, ICD-10, NPI, DEA, dosage) detection.
- **Memory**: 4 layers — working (context.py), session state, long-term
  (MemoryService), A2A context.
- **Frontend**: 18 primary routes; React + Vite + TypeScript; fully responsive.
- **Tests**: 274 pytest passing (model tests skip without a key) + 13 frontend
  vitest passing.

## Tenancy — demo vs live (say this clearly in the video)

- **Research Clinic** and **Northstar Health**: seeded demo tenants that
  demonstrate the product with realistic data and the ability to switch
  between organizations.
- **Capstone**: the live tenant. It starts empty and fills only with what is
  actually uploaded and approved, executing the real ADK + Gemini agents.
- No authentication anywhere (a capstone requirement) — role is chosen client
  side; the switcher lives in the top bar.

## What is real vs emulated (be honest in the writeup)

- Real: SQLite persistence, document parsing (PyMuPDF + Gemini Vision), the
  full ADK agent graph, MCP server, 3-layer security, audit trail, live-mode
  seam (tool calls, session continuity, server-gated SQL).
- Emulated locally under Google-service names: GCS object storage, Vertex
  Vector Search, Firestore — SQLite-backed and labelled as such.

## Links to include

- Public repo (Apache-2.0): https://github.com/GeorgiNaydenov/Google-Capstone-Project
- Documentation hub (when deployed): `/documentation` — Karpathy LLM Wiki,
  Obsidian Project Wiki, and interactive API docs.
