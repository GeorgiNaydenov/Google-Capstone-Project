---
title: Deployment
type: operations
status: active
updated: 2026-07-04
source: README.md, docs/architecture.md, deployment/README.md
tags:
  - operations
  - deployment
---

# Deployment

Three supported targets are documented. The public Cloud Run target is intentionally deterministic and does not receive paid ADK/Gemini credentials. Self-controlled live targets read secrets from `.env`, Application Default Credentials, or Secret Manager at runtime; secrets are never baked into images. Full instructions are in `deployment/README.md`; the process diagram is in [[Deployment Pipeline]].

| Target | Command | Use case |
|--------|---------|----------|
| **Cloud Run** | `gcloud builds submit --config deployment/cloudbuild.yaml .` | Public deterministic product build; paid ADK/Gemini execution disabled |
| **Vertex AI Agent Engine** | `adk deploy agent_engine --agent_engine_config_file=deployment/.agent_engine_config.json .` | Fully managed with autoscaling + Memory Bank |
| **GKE** | Custom K8s manifests | Self-managed Kubernetes |

## Artifacts (deployment/)

| File | Purpose |
|------|---------|
| `Dockerfile` | Hardened container — non-root user, healthcheck, port 8000 |
| `cloudbuild.yaml` | Public Cloud Build pipeline — deploys deterministic mode and clears paid-service credentials |
| `.agent_engine_config.json` | Vertex AI Agent Engine hardware config (Day 5b) |
| `README.md` | Cloud Run / Agent Engine / GKE / A2A deploy guide |

## Additional serving surface

The A2A server (`uvicorn capstone_agent.a2a_server:app --port 8001`) serves the agent card for agent-to-agent calls — see [[MCP and A2A]].

> [!warning] Secrets
> Secrets live in `.env` locally and Secret Manager in production. Never commit API keys; never bake them into images.

Related: [[System Overview]] · [[Course Concepts Map]] (Day 5b)
