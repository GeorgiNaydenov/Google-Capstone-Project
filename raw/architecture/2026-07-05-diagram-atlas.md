# Diagram Atlas

> Source: Project Wiki/02 Architecture/Diagram Atlas.md
> Collected: 2026-07-05
> Published: 2026-07-05

# Diagram Atlas

The product now exposes the prepared architecture diagrams as an interactive atlas in the landing page, clinician dashboard, admin dashboard, and contextual workflow panels. The frontend renders SVG first and falls back to PNG when an image fails to load.

> [!info] Runtime locations
> The catalog lives in `frontend/src/diagrams.ts`. The viewer components are `DiagramAtlas`, `DiagramViewer`, and `InlineDiagram`. The export command is `scripts/export_diagrams.py`, which copies draw.io sources and PNG fallbacks into `frontend/public/diagrams/` and exports SVG files into `frontend/public/diagrams/svg/`.

## Product Routes

| Product surface | Component | Default diagram or category |
|---|---|---|
| `/` landing page | `DiagramAtlas` | System category |
| `/app/dashboard` | `DiagramAtlas compact` | System category |
| `/app/admin` | `DiagramAtlas compact` | System category |
| `/app/configuration` | `InlineDiagram` | [[#06 Agent Hierarchy]] |
| `/app/configuration?view=settings` | `InlineDiagram` | [[#11 Security Pipeline]] |
| `/app/storage` | `InlineDiagram` | [[#10 Memory Architecture]] |
| `/app/inbox` | `InlineDiagram` | [[#15 Human In The Loop BPMN]] |
| `/app/extraction` | `InlineDiagram` | [[#16 Document Ingestion Flow]] |
| `/app/qa` | `InlineDiagram` | [[#19 Chat Turn Sequence]] |
| `/app/database` | `InlineDiagram` | [[#23 Clinical Database ERD]] |

## System

### 01 System Architecture

![[02 Architecture/diagrams/01-system-architecture.png]]

### 02 C4 System Context

![[02 Architecture/diagrams/02-c4-p1.png]]

### 02 C4 Containers

![[02 Architecture/diagrams/02-c4-p2.png]]

### 02 C4 Components

![[02 Architecture/diagrams/02-c4-p3.png]]

### 03 Module Dependency Graph

![[02 Architecture/diagrams/03-module-dependency-graph.png]]

### 05 Frontend Route Map

![[02 Architecture/diagrams/05-frontend-route-map.png]]

### 25 REST API Map

![[02 Architecture/diagrams/25-rest-api-map.png]]

## Agents And Pipelines

### 06 Agent Hierarchy

![[02 Architecture/diagrams/06-agent-hierarchy.png]]

### 07 A2A Communication

![[02 Architecture/diagrams/07-a2a-communication.png]]

### 08 MCP Server Topology

![[02 Architecture/diagrams/08-mcp-server-topology.png]]

### 09 Execution Mode Switch

![[02 Architecture/diagrams/09-execution-mode-switch.png]]

### 12 Context Engineering Pipeline

![[02 Architecture/diagrams/12-context-engineering-pipeline.png]]

### 28 Gemini Model Tier Registry

![[02 Architecture/diagrams/28-gemini-model-tier-registry.png]]

## Security And Memory

### 10 Memory Architecture

![[02 Architecture/diagrams/10-memory-architecture.png]]

### 11 Security Pipeline

![[02 Architecture/diagrams/11-security-pipeline.png]]

### 22 Security Block Sequence

![[02 Architecture/diagrams/22-security-block-sequence.png]]

### 26 Harness Governance Map

![[02 Architecture/diagrams/26-harness-governance-map.png]]

## Processes

### 14 Clinical Request Lifecycle BPMN

![[02 Architecture/diagrams/14-clinical-request-lifecycle-bpmn.png]]

### 15 Human In The Loop BPMN

![[02 Architecture/diagrams/15-human-in-the-loop-bpmn.png]]

### 16 Document Ingestion Flow

![[02 Architecture/diagrams/16-document-ingestion-flow.png]]

### 17 Wiki Auto Sync BPMN

![[02 Architecture/diagrams/17-wiki-auto-sync-bpmn.png]]

### 19 Chat Turn Sequence

![[02 Architecture/diagrams/19-chat-turn-sequence.png]]

### 20 HITL Approval Sequence

![[02 Architecture/diagrams/20-hitl-approval-sequence.png]]

### 21 A2A Delegation Sequence

![[02 Architecture/diagrams/21-a2a-delegation-sequence.png]]

### 29 Animated Chat Flow

![[02 Architecture/diagrams/29-animated-chat-flow.svg]]

## Data And API

### 23 Clinical Database ERD

![[02 Architecture/diagrams/23-clinical-database-erd.png]]

### 24 Pydantic Contract Class

![[02 Architecture/diagrams/24-pydantic-contract-class.png]]

## Deployment And Quality

### 04 Deployment Topology

![[02 Architecture/diagrams/04-deployment-topology.png]]

### 13 Observability Pillars

![[02 Architecture/diagrams/13-observability-pillars.png]]

### 18 Eval Quality Flywheel

![[02 Architecture/diagrams/18-eval-quality-flywheel.png]]

### 27 Capstone Rubric Coverage

![[02 Architecture/diagrams/27-capstone-rubric-coverage.png]]

## Export Contract

| Asset kind | Location | Count |
|---|---|---:|
| Draw.io sources | `frontend/public/diagrams/*.drawio` | 28 |
| PNG fallbacks | `frontend/public/diagrams/*.png` | 31 |
| SVG viewer assets | `frontend/public/diagrams/svg/*.svg` | 31 |

Related: [[System Overview]] - [[Clinical App]] - [[REST API and Developer Console]] - [[MCP and A2A]] - [[Testing & Eval]]
