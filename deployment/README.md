# Deployment (Day 5b)

Three supported targets. All read configuration from `.env` / Secret Manager —
no secrets are baked into images.

## 1. Cloud Run (clinical product)

The `Dockerfile` builds `frontend/`, installs the FastAPI and ADK runtime, runs
as a non-root user, and serves the clinical product on Cloud Run's `PORT`.
ADK Web remains a local developer surface. Deploy via Cloud Build:

```bash
# One-time: store the API key in Secret Manager
echo -n "YOUR_GEMINI_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# Build + push + deploy
gcloud builds submit --config deployment/cloudbuild.yaml .
```

The generic ADK CLI deployment below exposes the ADK developer UI rather than
the Nexus product and is retained only for agent-runtime troubleshooting:

```bash
adk deploy cloud_run --project=PROJECT_ID --region=us-central1 \
    --service_name=capstone-agent --with_ui .
```

## 2. Vertex AI Agent Engine (fully managed)

Managed runtime with autoscaling and the Vertex AI Memory Bank. Hardware is
described by `.agent_engine_config.json` (min/max instances, CPU, memory).

Set these in `.env` first: `GOOGLE_GENAI_USE_VERTEXAI=TRUE`,
`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`.

```bash
adk deploy agent_engine --project=PROJECT_ID --region=us-central1 \
    --agent_engine_config_file=deployment/.agent_engine_config.json .
```

To use persistent cloud memory after deploy, set `MEMORY_BACKEND=vertex` and
`AGENT_ENGINE_ID=<resource-name>` (see `memory.create_memory_service`).

Clean up to avoid charges:

```bash
python -c "from vertexai import agent_engines; agent_engines.delete(resource_name='RESOURCE', force=True)"
```

## 3. GKE (self-managed Kubernetes)

For full control, deploy the same container image to GKE. Build/push with the
Dockerfile above, then apply a Deployment + Service that injects `GOOGLE_API_KEY`
from a Kubernetes Secret and exposes port 8000. (Manifests are domain-specific;
add them under `deployment/k8s/` when you pick your capstone.)

## Agent2Agent serving (Day 5a)

To expose the agent to *other agents* (not end users), serve the A2A app instead
of the web UI:

```bash
uvicorn capstone_agent.a2a_server:app --host 0.0.0.0 --port 8001
# Agent card: http://<host>:8001/.well-known/agent-card.json
```
