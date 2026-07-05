# Clinical Product Delivery Map

## Purpose

This directory is the execution source of truth for turning the existing
Google ADK capstone harness and static Clinical AI Command Center prototype
into the end-to-end clinician-facing application described in the product
brief.

The current repository contains two valuable foundations:

1. A specialized ADK backend with three clinical pipelines, security,
   memory, observability, MCP, evaluation, and deployment scaffolding.
2. A dense 16-screen visual prototype that demonstrates the intended user
   experience and clinical design language.

They are not yet one application. The product work is the application and
integration layer between them.

## Documents

- [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md): current-state audit for
  cross-cutting requirements, all 16 screens, and the three guided workflows.
- [HARNESS_SPECIALIZATION.md](HARNESS_SPECIALIZATION.md): preserve, replace,
  add, and harden decisions for moving from the generic harness to this
  clinical product.
- [SWARM_DELIVERY_PLAN.md](SWARM_DELIVERY_PLAN.md): multi-agent ownership,
  waves, integration protocol, gates, milestones, and definition of done.
- [AI_FIRST_REMEDIATION_PLAN.md](AI_FIRST_REMEDIATION_PLAN.md): audit and
  delivery plan for AI-first UX, document ingestion, upload limits, agent
  traces, optimization, and stale harness documentation.
- [../../Project Wiki/02 Architecture/Diagram Atlas.md](../../Project%20Wiki/02%20Architecture/Diagram%20Atlas.md): Obsidian catalog for
  the exported architecture, process, security, data, deployment, and agent
  diagrams rendered in the frontend atlas.

## Product Boundary

The target architecture is:

```text
Clinical React UI
  -> visible diagram atlas and contextual architecture embeds
  -> FastAPI product API
  -> application services and policy enforcement
  -> ADK Runner and clinical pipelines
  -> repository/provider ports
  -> demo repository or Google Cloud adapters
```

ADK Web remains a developer surface. It is not the clinician product.

## Delivery Principles

1. Preserve `capstone_agent` as the agent-engine foundation.
2. Treat the `.dc.html` prototype as the visual and feature reference, not
   production source code.
3. Use one mutable, deterministic demo repository for UI, API, tools, MCP,
   analytics, audit, and reset behavior.
4. Put deterministic policy, validation, authorization, and state transitions
   in Python. Use LLMs for interpretation, extraction, synthesis, and routing.
5. Require review before clinical record commits.
6. Persist run and step events before showing them in the UI.
7. Make every mutation visible through the API response, repository state,
   audit event, refreshed UI, and browser assertion.
8. Expose safe workflow rationale and evidence, never hidden chain-of-thought.
9. Keep architecture diagrams visible in the product and wiki when routes,
   agents, data flows, or API boundaries change.
10. Use synthetic data only in the public demo.
11. Deploy only after explicit human approval.

## Priority Order

1. Repair the environment and freeze product/API/event contracts.
2. Build the product spine over one shared data source.
3. Complete extraction as the first end-to-end vertical slice.
4. Complete multimodal Q&A and database intelligence.
5. Connect admin, storage, configuration, and monitoring workflows.
6. Harden, document, package, and verify the submission.

## Product Completion Test

The product is complete only when all 16 screens are routed and connected,
the three guided workflows pass end to end, role changes preserve relevant
context, the demo resets deterministically, all security and quality gates
pass, and the deployed public application matches the documented behavior.
