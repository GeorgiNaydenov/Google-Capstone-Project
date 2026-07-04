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
    a2a_server[a2a_server.py]
    agent[agent.py]
    app[app.py]
    callbacks[callbacks.py]
    clinical_schemas[clinical_schemas.py]
    config[config.py]
    context[context.py]
    database[database.py]
    document_processor[document_processor.py]
    human_in_the_loop[human_in_the_loop.py]
    llm[llm.py]
    memory[memory.py]
    mock_data[mock_data.py]
    models[models.py]
    observability[observability.py]
    orchestration[orchestration.py]
    plugins[plugins.py]
    prompts[prompts.py]
    security[security.py]
    tools[tools.py]

    agent --> a2a_server
    agent --> app
    callbacks --> agent
    callbacks --> plugins
    clinical_schemas --> tools
    config --> a2a_server
    config --> agent
    config --> app
    config --> context
    config --> document_processor
    config --> llm
    config --> memory
    config --> observability
    config --> plugins
    config --> security
    config --> tools
    context --> agent
    context --> plugins
    database --> mock_data
    document_processor --> tools
    human_in_the_loop --> agent
    llm --> agent
    llm --> orchestration
    llm --> tools
    memory --> agent
    memory --> orchestration
    models --> tools
    observability --> agent
    observability --> callbacks
    observability --> human_in_the_loop
    observability --> memory
    observability --> plugins
    observability --> tools
    orchestration --> agent
    plugins --> app
    prompts --> agent
    prompts --> orchestration
    security --> callbacks
    security --> memory
    security --> plugins
    tools --> agent
    tools --> orchestration
```
<!-- AUTO:DEPGRAPH:END -->

## Design property

No circular dependencies. `config.py` and `prompts.py` are standalone; everything converges on `agent.py`, which wires the root agent, then `app.py` (runtime) and `a2a_server.py` (A2A serving) consume it.

Related: [[Module Reference]] · [[Agent Architecture]]
