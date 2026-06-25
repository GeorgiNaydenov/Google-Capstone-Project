---
name: deployment
description: Hardening, packaging, and deploying the Google ADK Capstone Project agent to Cloud Run or Vertex AI Agent Engine. Use when managing Dockerfiles, pipeline configurations, or deploying active code.
---

# Deployment

Deploying the ADK agent to Google Cloud Run or Vertex AI Agent Engine.

## Tech Stack & Files

- `deployment/Dockerfile`: Hardened python deployment image (non-root, uses uv).
- `deployment/cloudbuild.yaml`: Google Cloud Build pipeline using Secret Manager for keys.
- `deployment/.agent_engine_config.json`: Hardware, runtime, and model configuration for Agent Engine.

## Deploying

Always check test status and execute the pre-commit gate before deploying.

### Option 1: Cloud Run (via ADK CLI)
```bash
adk deploy cloud_run --project=PROJECT_ID --region=us-central1 --service_name=capstone-agent --with_ui .
```

### Option 2: Vertex AI Agent Engine (via ADK CLI)
```bash
adk deploy agent_engine --project=PROJECT_ID --region=us-central1 --agent_engine_config_file=deployment/.agent_engine_config.json .
```

## Production Verification

- Verify the service endpoints are up and trace signals route properly to Cloud Trace.
- Ensure secrets are stored securely in GCP Secret Manager, not hardcoded in `.env`.
