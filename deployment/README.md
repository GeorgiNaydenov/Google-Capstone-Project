# Deployment (Day 5b)

Three supported targets. No secrets are baked into images. Public hosted build
uses deterministic workflows and needs no model credentials; self-controlled
live deployments read model configuration from environment variables or Secret
Manager.

## 1. Cloud Run (clinical product)

The `Dockerfile` builds `frontend/`, installs FastAPI plus ADK dependencies,
runs as a non-root user, and serves Clinical AI Kit on Cloud Run's `PORT`.
ADK Web remains a local developer surface.

### Public deterministic deployment

The checked-in `cloudbuild.yaml` intentionally deploys a cost-controlled public
showcase. It keeps deterministic clinical workflows, synthetic data, API docs,
diagram atlas, Project Wiki, and LLM Wiki available while disabling paid model,
Vertex retrieval/reranking, MCP/A2A runtime, tracing, and cloud storage calls.
Deploy it with:

```bash
# Build + push + deploy
gcloud builds submit --config deployment/cloudbuild.yaml .
```

Public environment set by `cloudbuild.yaml`:

| Variable | Value | Why |
|---|---|---|
| `AGENT_EXECUTION_MODE` | `disabled` | Prevents paid live-agent execution on public routes |
| `ENABLE_VECTOR_SEARCH` | `FALSE` | Disables Vertex embedding calls |
| `ENABLE_RERANKER` | `FALSE` | Disables Vertex Ranking API calls |
| `ENABLE_TRACING` | `FALSE` | Disables external trace export |
| `HIPAA_MODE` / `PHI_REDACTION` | `TRUE` | Keeps privacy-aware redaction controls enabled; this is not a compliance certification |
| `CLINICAL_DATA_DIR` | `/data` | Writable ephemeral path owned by non-root container user |

`--max-instances=1` keeps in-memory demo sessions coherent. Cloud Run storage is
ephemeral and the public demo is designed to reset safely between revisions.

### Self-controlled live deployment

To enable real ADK/Gemini execution, clone `cloudbuild.yaml` into a private
deployment configuration and set `AGENT_EXECUTION_MODE=live`. Configure either
Vertex AI ADC (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`, project, and location) or a
Secret Manager-backed `GOOGLE_API_KEY`. Enable retrieval, reranking, tracing,
MCP, or A2A only when their required IAM roles and service budgets exist.

Live-mode constraints until storage moves off-instance:

- **`--max-instances=1` is mandatory.** Browser demo/live session state lives in
  process memory (`RepositoryRegistry`) and clinical data in a local SQLite
  file; a second instance would serve divergent data.
- The live bridge intentionally uses in-memory ADK sessions per instance;
  `SESSION_BACKEND=database` applies to the `adk run` / Agent Engine path only.
- Q&A follow-up continuity therefore survives requests but not restarts or
  redeploys.

### Data persistence (real tenant)

The real (`capstone`) tenant writes `capstone.db` and `uploads_capstone/` to
disk. Set `CLINICAL_DATA_DIR` to a writable, persistent path and both the
tenant database and uploads relocate there:

```bash
# Local container with a named volume that survives restarts
docker build -f deployment/Dockerfile -t clinical-ai-kit .
docker run --rm -p 8080:8080 \
    -e CLINICAL_DATA_DIR=/data -v clinical-ai-kit-data:/data \
    clinical-ai-kit
```

On Cloud Run the container filesystem is ephemeral, so real-tenant data does
not survive a new revision unless `CLINICAL_DATA_DIR` points at a mounted
volume (Cloud Run volume mounts or a GCS FUSE mount). The demo tenants keep no
files, so they need no volume. The default `clinical.db` self-seeds on first
touch and is safe to leave ephemeral.

For a private live Cloud Run deployment, a GCS FUSE volume can persist the
real `capstone.db` and `uploads_capstone/` across restarts. The checked-in public
`cloudbuild.yaml` explicitly clears volume mounts. Example one-time setup:

```bash
gcloud storage buckets create gs://capstone-project-500212-clinical-data --location=us-central1
gsutil iam ch serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com:roles/storage.objectAdmin \
    gs://capstone-project-500212-clinical-data
```

For real production beyond the Kaggle demo, move the clinical database and
uploads to Cloud SQL plus object storage instead of GCS FUSE.

### Health and readiness

- `GET /health` — liveness (used by the Docker `HEALTHCHECK`).
- `GET /ready` — runs real component checks (database reachable, uploads
  writable, agent + MCP importable) and returns `503` until the database and
  upload storage are usable. Check this URL after deploy before submitting the
  public project link.

Do not rename these routes to paths ending in `z`. Cloud Run reserves some such
paths at its edge, so a route such as `/healthz` can return a Google-generated
404 before the request reaches FastAPI. See the
[Cloud Run known issues](https://cloud.google.com/run/docs/known-issues#reserved-url-paths).

### Optional API-key deployment

A private live Cloud Run path can use Vertex AI ADC. To use a Gemini API key
instead, create a Secret Manager secret and add it to your private deploy step:

```bash
gcloud secrets create GOOGLE_API_KEY --replication-policy=automatic
printf "KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-
```

Then set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` and add:

```bash
--update-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest
```

The generic ADK CLI deployment below exposes ADK developer UI rather than the
Clinical AI Kit product and is retained only for agent-runtime troubleshooting:

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
