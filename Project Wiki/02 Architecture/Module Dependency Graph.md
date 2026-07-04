---
title: Module Dependency Graph
type: architecture
status: auto-partial
updated: 2026-07-04
source: docs/architecture.md, scripts/sync_wiki.py
tags:
  - architecture
  - generated
---

# Module Dependency Graph

> [!info] Auto-regenerated section
> The Mermaid graph between the AUTO markers is rewritten by `scripts/sync_wiki.py` from the actual intra-project imports on every sync. Do not hand-edit inside the markers.

<!-- AUTO:DEPGRAPH:BEGIN -->
```mermaid
flowchart LR
    config[config.py]
    models[models.py]
    security[security.py]
    observability[observability.py]
    memory[memory.py]
    context[context.py]
    llm[llm.py]
    prompts[prompts.py]
    callbacks[callbacks.py]
    plugins[plugins.py]
    orchestration[orchestration.py]
    hitl[human_in_the_loop.py]
    tools[tools.py]
    schemas[clinical_schemas.py]
    mock[mock_data.py]
    agent[agent.py]
    app[app.py]
    a2a[a2a_server.py]

    config --> models
    config --> security
    config --> context
    config --> llm
    config --> prompts
    security --> observability
    security --> memory
    models --> tools
    schemas --> tools
    mock --> tools
    observability --> callbacks
    memory --> callbacks
    callbacks --> plugins
    context --> plugins
    llm --> orchestration
    tools --> orchestration
    hitl --> agent
    orchestration --> agent
    llm --> agent
    agent --> app
    agent --> a2a
```
<!-- AUTO:DEPGRAPH:END -->

## Design property

No circular dependencies. `config.py` and `prompts.py` are standalone; everything converges on `agent.py`, which wires the root agent, then `app.py` (runtime) and `a2a_server.py` (A2A serving) consume it.

Related: [[Module Reference]] · [[Agent Architecture]]
