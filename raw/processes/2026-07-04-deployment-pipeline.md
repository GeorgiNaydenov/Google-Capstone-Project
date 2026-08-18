# Deployment Pipeline

> Source: Project Wiki/03 Processes/Deployment Pipeline.md
> Collected: 2026-07-05
> Published: 2026-07-04

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
        PUBLIC_CFG["Configure public deterministic mode<br/>clear paid-service credentials"]
    end

    subgraph LANE_RUN["Lane: Runtime"]
        CR["Cloud Run :8000<br/>public deterministic product"]
        AE["Vertex AI Agent Engine<br/>autoscale + Memory Bank"]
        GKE["GKE<br/>self-managed Kubernetes"]
        A2A["A2A server :8001<br/>agent card for agent-to-agent calls"]
        GEM["Gemini 3.1 API<br/>(LLM inference)"]
    end

    SUBMIT --> BUILD --> PUBLIC_CFG --> CR
    ADK_DEPLOY --> AE
    K8S --> GKE
    AE --> GEM
    GKE --> GEM
    CR -.-> A2A
```

Key facts:

- The public Cloud Run build disables paid ADK/Gemini execution and does not receive model credentials.
- Self-controlled Agent Engine or GKE live deployments load credentials at runtime; secrets are never baked into images ([[Deployment]]).
- The Dockerfile runs as a non-root user with a healthcheck on port 8000.
- Agent Engine deployments use `deployment/.agent_engine_config.json` for hardware config and add managed Memory Bank ([[Memory Layers]] Layer 3).
- The A2A server is a separate serving surface for agent-to-agent calls ([[MCP and A2A]]).

Related: [[Deployment]] · [[System Overview]]
