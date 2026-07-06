# Kaggle Writeup Paste-In

Use this content in the Kaggle writeup editor. It is written for the 2,500-word limit shown in the form.

## Basic Details

Title:

Nexus Clinical AI Command Center

Subtitle:

A Google ADK multi-agent clinical workspace that turns fragmented evidence into auditable, clinician-approved decisions.

Suggested submission tracks:

- Technical Implementation
- Deployability
- Security
- Agent / Multi-agent Systems

Pick the closest available tracks in Kaggle's selector. If Kaggle only allows one, choose Technical Implementation.

## Project Description

Nexus Clinical AI Command Center is a clinician-facing capstone project for Kaggle's AI Agents: Intensive Vibe Coding challenge. It is built around a practical clinical problem: care teams often have too much evidence and too little structure. A single patient question may involve scanned intake forms, clinical images, historical notes, medication changes, structured database rows, prior visits, and risk signals from a larger population. A normal chatbot can summarize part of that context, but it usually hides the process that matters most: what evidence was used, which tools ran, what was uncertain, and where a human approved the result.

Nexus Clinical AI Command Center turns that process into a visible command center. The application is not meant to be a medical device, and all demo data is synthetic. The project is a production-shaped demonstration of how agentic clinical workflows can be made inspectable, governable, and safe enough to reason about.

The product has three guided workflows.

The first workflow is session image extraction. A clinician uploads a clinical image or PDF, and the system runs a pipeline that checks source quality, extracts text, reasons over visual evidence, structures clinical fields, validates the extraction, and stops at a human review gate. Nothing consequential is persisted until the reviewer approves it. After approval, the app shows storage receipts, audit events, extracted fields, and the updated patient timeline.

The second workflow is patient-scoped multimodal Q&A. The clinician asks a question inside a selected patient context. The system validates scope, assembles patient context, retrieves evidence, includes image and document evidence where available, builds citations, and returns an answer that can be inspected. The important part is not only the answer; it is the evidence package around the answer. Judges can open the cited sources and see why the response was produced.

The third workflow is database intelligence. A user asks a cohort or operational question in natural language. The system discovers the schema, generates read-only SQL, validates the query, shows it before execution, and requires an approval step before returning rows, chart specifications, and exports. This keeps the agent useful without letting it silently run database actions.

The application is designed around the reviewer journey. A judge can start in demo mode, choose a clinician role, and immediately see a realistic workspace without needing a model key. The dashboard shows queue pressure, notifications, recent activity, system diagrams, and quick actions. From there, the judge can run extraction, Q&A, and database workflows in sequence and see the same design pattern repeated: the agent plans or performs work, the product exposes intermediate evidence, and the user gets a reviewable artifact instead of an opaque answer.

Nexus Clinical AI Command Center demonstrates five of the required competition concepts.

First, it is a Google ADK multi-agent system. The backend contains one root orchestrator and 22 pipeline sub-agents. The image extraction pipeline has nine agent stages, including quality assessment, OCR processing, vision analysis, clinical structuring, a critic/refiner validation loop, review, persistence, and audit. The patient Q&A pipeline has seven stages for validation, context assembly, evidence retrieval, image evidence, citation building, answer synthesis, and audit. The database intelligence pipeline has six stages for schema discovery, natural-language-to-SQL generation, SQL validation, approval, execution, and insight/chart generation. The root agent routes intent across these workflows and exposes a coherent clinical interaction surface.

Second, the project includes an MCP server. `mcp_server/server.py` exposes clinical tools through FastMCP over JSON-RPC/stdio. The same clinical tool layer can be used by the ADK agent or by any MCP-compatible client, which makes the tool surface portable instead of locked inside one UI.

Third, the project implements a three-layer security architecture. `before_model_callback` runs before model calls and blocks prompt-injection patterns while sanitizing suspicious input. `before_tool_callback` runs before tool execution and validates arguments, rate-limits, and scans tool inputs for secrets. `after_model_callback` runs before model output reaches the user and scans for PII, PHI, and leaked secrets. Security events are logged through structured observability so blocks and redactions leave an audit trail.

Fourth, the project is deployable. The repository includes a production Dockerfile, a Cloud Build pipeline for Cloud Run, health and readiness endpoints, and a Vertex AI Agent Engine configuration. The Cloud Run target serves the React frontend and FastAPI backend as a single-origin product service. The deployment notes also document an important honesty boundary: until state is moved to external managed storage, Cloud Run should run with one instance and persistent real-tenant data should be placed under `CLINICAL_DATA_DIR`.

Fifth, the project uses agent skills as part of the development harness. The `.agents/` and `.claude/` folders contain reusable skills and rules for testing, deployment, diagram generation, Obsidian/JSON Canvas documentation, and project governance. Those skills were used to keep the code, documentation, diagrams, and submission materials synchronized.

The architecture is intentionally full-stack. React, Vite, and TypeScript provide the clinical user interface. FastAPI hosts the product API, serves the built frontend, handles tenant switching, upload policy, document parsing, audit history, and system readiness checks. The ADK package contains the root agent, orchestration pipelines, tools, callbacks, memory, context engineering, observability plugins, model registry, and Agent2Agent server. SQLite provides local persistence for the capstone demo and live tenant prototype. The frontend includes an interactive diagram atlas, and the app also serves a documentation hub at `/documentation` generated from the project wiki and LLM-oriented architecture notes.

The model registry is deliberately centralized. Agents do not pass bare model strings around the codebase. They call `llm.build_model(tier)`, which maps workflow roles to model tiers such as `flash-lite`, `pro`, `pro-customtools`, and `flash-image`. That makes the system easier to audit because routing, retry behavior, and model selection live in one place instead of being scattered through prompts and tools.

The memory and context layers are also explicit. Working context is assembled with structured sections, compaction is deterministic, and critical information is injected at boundaries to reduce the "lost in the middle" problem. Session state, long-term memory, and A2A context are treated as separate layers with different persistence expectations. In a clinical setting, this distinction matters because not every fact that helps one turn should be saved forever or passed to another agent.

The frontend was built to show the agent system rather than decorate it. Workflow pages include stepper-style execution traces, confidence indicators, evidence panels, citation lists, review controls, and audit-driven status. Admin pages expose component health, monitoring, permissions, storage state, and documentation links. The diagram atlas is available inside the application so the architecture is not hidden in a README only; it becomes part of the product experience.

There are two execution modes. Demo mode is deterministic and requires no API key, so judges can run the project quickly and see the workflows without depending on external credentials. Live mode switches the Capstone tenant to the real Google ADK and Gemini execution path when credentials are configured. The live tenant starts empty and fills only with what is actually uploaded, approved, and run. That separation is deliberate: the demo tenants show the product story, while the live tenant proves the system boundary is real.

The project is also explicit about what is real and what is emulated. Real components include the ADK agent graph, MCP server, Pydantic tool contracts, SQLite persistence, document parsing, human-in-the-loop approval gates, tool-call traces, audit logs, security callbacks, model-tier registry, Cloud Run containerization, `/healthz`, `/readyz`, and live-mode bridging to Gemini. Local demo equivalents stand in for some cloud services such as object storage, vector search, and Firestore-like state. Those parts are labelled as local demo implementations rather than being oversold as managed production infrastructure.

Testing and verification are part of the submission story. The repo includes pytest coverage for security, callbacks, tools, context, memory, orchestration, document parsing, live bridge helpers, product API contracts, product orchestration boundaries, versioned APIs, showcase generators, and wiki sync. The frontend includes Vitest coverage for application behavior and UI contracts. The ADK eval assets live under `eval/` for model-dependent quality checks. The deterministic demo mode means most validation can run without a Gemini key, while live/eval paths are available when credentials are present.

The deployment path is intentionally honest rather than magical. The Cloud Run container builds the frontend, installs the Python agent/product runtime, and serves everything from FastAPI. `/healthz` is the liveness probe, while `/readyz` checks real dependencies such as database access, upload writability, frontend assets, and agent/MCP imports. The deployment documentation calls out the current persistence boundary: Cloud Run file systems are ephemeral, so real tenant data should use `CLINICAL_DATA_DIR` on persistent storage if it must survive revisions. That caveat is visible because production-readiness includes knowing what is not production-grade yet.

The project also includes synthetic showcase data and documentation assets. The generated datasets cover extraction packets, multimodal patient bundles, database cohorts, knowledge-base-ready files, charts, citations, and dashboard/storage/monitoring seed values. Those assets are not just offline samples; the app can consume generated manifest data so the UI demonstrates realistic volume and evidence rather than isolated toy rows.

My biggest implementation challenge was balancing demo reliability with real agent architecture. For a capstone judge, the app must work quickly and repeatably. For the technical rubric, the project must still prove real ADK, MCP, security, memory, observability, and deployment structure. The solution was a dual-mode product: deterministic demo adapters for review and a live Capstone tenant for real ADK/Gemini execution. That allowed the app to be judge-friendly without pretending the deterministic path was the live cloud path.

The most important design decision was to make agent behavior visible. Nexus Clinical AI Command Center does not ask reviewers to trust a black-box answer. It shows pipeline stages, tool calls, confidence, evidence, citations, generated SQL, approval gates, storage receipts, audit events, tenant mode, and deployment readiness. That visibility is what turns the project from a chatbot demo into a governed agentic workflow.

For the capstone, the value is not only that the system uses many agents. The value is that every agent has a boundary the user can inspect. The clinician can see where extraction happened, where validation happened, where the SQL was checked, where the answer got its evidence, and where human approval was required. That is the core lesson I would carry forward into any real clinical agent product: powerful agents need visible control surfaces, not just impressive output.

## Project Links

Add these under Attachments -> Project Links:

- GitHub repository: https://github.com/GeorgiNaydenov/nexus-clinical-ai-capstone
- Local app after setup: http://localhost:8000
- Local documentation hub after setup: http://localhost:8000/documentation
- Optional deployed app URL: add the Cloud Run URL after deployment, if available.
