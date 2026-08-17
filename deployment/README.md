# Deployment (Day 5b)

Three supported targets. All read configuration from `.env` / Secret Manager —
no secrets are baked into images.

## 1. Cloud Run (clinical product)

The `Dockerfile` builds `frontend/`, installs the FastAPI and ADK runtime, runs
as a non-root user, and serves the clinical product on Cloud Run's `PORT`.
ADK Web remains a local developer surface. Deploy via Cloud Build:

```bash
# One-time: let the default Cloud Run runtime service account call Vertex AI.
PROJECT_ID="your-project-id"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Optional when ENABLE_TRACING=TRUE is kept in cloudbuild.yaml.
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/cloudtrace.agent"

# Build + push + deploy
gcloud builds submit --config deployment/cloudbuild.yaml .
```

Live-mode environment set by `cloudbuild.yaml`:

| Variable | Value | Why |
|---|---|---|
| `AGENT_EXECUTION_MODE` | `live` | Product API routes through real ADK agents |
| `GOOGLE_GENAI_USE_VERTEXAI` | `TRUE` | Gemini via Vertex AI with the runtime SA's ADC — no API key |
| `GOOGLE_CLOUD_LOCATION` | `global` | Gemini 3.1 models are only served from the global endpoint |
| `HIPAA_MODE` | `TRUE` | Forces PHI redaction on all output paths |
| `CLINICAL_DATA_DIR` | `/data` | Writable path owned by the non-root container user |
| `MODEL_REQUESTS_PER_MINUTE` | `10` | Per-session sliding-window model request budget |
| `MAX_CONCURRENT_MODEL_RUNS` | `2` | Per-session active model execution cap |
| `MAX_TOOL_COUNT` | `15` | Per-tool invocation cap enforced by ADK callbacks |

Constraints to respect until the storage layer moves off-instance:

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

`cloudbuild.yaml` mounts `CLINICAL_DATA_DIR=/data` onto a GCS bucket
(`_DATA_BUCKET`, GCS FUSE volume) via `--execution-environment=gen2` so the
real `capstone.db` and `uploads_capstone/` persist across restarts, scale-to-
zero, and redeploys. One-time setup before the first deploy:

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

The default Cloud Run path uses Vertex AI ADC. If you must deploy with a Gemini
API key instead, create a Secret Manager secret and edit the Cloud Run deploy
step in `deployment/cloudbuild.yaml`:

```bash
gcloud secrets create GOOGLE_API_KEY --replication-policy=automatic
printf "KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-
```

Then set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` and add:

```bash
--update-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest
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
