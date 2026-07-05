# Deployment Pipeline

> Sources: Antigravity, 2026-07-05
> Raw: [Deployment Pipeline Source](../../raw/processes/2026-07-04-deployment-pipeline.md)

# Deployment Pipeline

Three targets fed by one hardened build. Lanes: Developer, Cloud Build, Runtime.

```mermaid
flowchart TD
    subgraph LANE_DEV["Lane: Developer"]
        SUBMIT["gcloud builds submit<br/>--config deployment/cloudbuild.yaml"]
        ADK_DEPLOY["adk deploy agent_engine<br/>(.agent_engine_config.json)"]
        K8S["kubectl apply (custom manifests)"]
    end

    subgraph LANE_BUILD["Lane: Cloud Build"]
        BUILD["Build hardened image<br/>(Dockerfile: non-root, healthcheck)"]
        SECRET["Pull GOOGLE_API_KEY<br/>from Secret Manager"]
    end

    subgraph LANE_RUN["Lane: Runtime"]
        CR["Cloud Run :8000<br/>production clinical product"]
        AE["Vertex AI Agent Engine<br/>autoscale + Memory Bank"]
        GKE["GKE<br/>self-managed Kubernetes"]
        A2A["A2A server :8001<br/>agent card for agent-to-agent calls"]
        GEM["Gemini 3.1 API<br/>(LLM inference)"]
    end

    SUBMIT --> BUILD --> SECRET --> CR
    ADK_DEPLOY --> AE
    K8S --> GKE
    CR --> GEM
    AE --> GEM
    GKE --> GEM
    CR -.-> A2A
```

Key facts:

- Secrets come from Secret Manager at build/runtime — never baked into images ([[Deployment]]).
- The Dockerfile runs as a non-root user with a healthcheck on port 8000.
- Agent Engine deployments use `deployment/.agent_engine_config.json` for hardware config and add managed Memory Bank ([[Memory Layers]] Layer 3).
- The A2A server is a separate serving surface for agent-to-agent calls ([[MCP and A2A]]).

Related: [[Deployment]] · [[System Overview]]
