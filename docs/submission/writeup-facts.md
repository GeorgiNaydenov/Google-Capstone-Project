# Writeup Facts

Source-of-truth figures for the Kaggle writeup and 5-minute video. These are grounded in the current code and submission docs.

## One-Line Pitch

Clinical AI Kit is a clinician-facing platform where a visible multi-agent system turns fragmented clinical evidence - images, notes, records, and population data - into decisions clinicians can verify, with every consequential write held behind human review.

## Competition Concepts Demonstrated

| Concept | Evidence |
| --- | --- |
| Agent / multi-agent system with ADK | 1 root orchestrator plus 22 pipeline sub-agents across 3 SequentialAgent pipelines in `capstone_agent/agent.py` and `capstone_agent/orchestration.py` |
| MCP server | `mcp_server/server.py` exposes FastMCP clinical tools over JSON-RPC/stdio |
| Security | 3-layer callback pipeline: input injection blocking, tool validation/rate limiting, and output PII/PHI/secret scanning |
| Deployability | Multi-stage Dockerfile, Cloud Build to Cloud Run, health/readiness endpoints, and Vertex AI Agent Engine config |
| Agent Skills | `.claude/` and `.agents/` harness skills for testing, deployment, documentation, diagramming, and repo governance |

## Architecture Counts

- Agents: 23 total = 1 orchestrator plus 22 sub-agents.
- Image Extraction pipeline: 9 agents.
- Patient Q&A pipeline: 7 agents.
- Database Intelligence pipeline: 6 agents.
- Model tiers in `capstone_agent/llm.py`: `flash-lite`, `pro`, `pro-customtools`, `flash-image`.
- Memory: 4 layers - working context, session state, long-term memory, and A2A context.
- Frontend: React, Vite, TypeScript, clinician and admin routes.

## Demo vs Live

- Research Clinic and Northstar Health are deterministic seeded demo tenants.
- Capstone is the live tenant. It starts empty and uses the real ADK/Gemini path when credentials are configured.
- There is no production authentication in this capstone demo. Role and tenant selection are exposed in the UI for judging.

## Real vs Emulated

Real:

- ADK agent graph.
- MCP server.
- Pydantic tool contracts.
- SQLite persistence.
- Document parsing and upload policy.
- Human-in-the-loop approval gates.
- Tool-call traces.
- Security callbacks.
- Audit trail.
- Live-mode bridge to Gemini.
- Cloud Run/Agent Engine deployment assets.

Local demo equivalents:

- Object storage.
- Vector search.
- Firestore-like state.

## Links

- Public repo: https://github.com/GeorgiNaydenov/Google-Capstone-Project
- Local app: http://localhost:8000
- Local documentation hub: http://localhost:8000/documentation
