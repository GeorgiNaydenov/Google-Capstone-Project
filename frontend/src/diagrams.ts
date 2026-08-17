export type DiagramCategoryId = "system" | "agents" | "security" | "processes" | "data" | "deployment";

export interface DiagramView {
  id: string;
  title: string;
  category: DiagramCategoryId;
  summary: string;
  svg: string;
  png?: string;
  points: string[];
}

export interface DiagramCategory {
  id: DiagramCategoryId;
  title: string;
  summary: string;
}

export const diagramCategories: DiagramCategory[] = [
  { id: "system", title: "System", summary: "Product surface, C4 levels, module map, routes, and API boundary." },
  { id: "agents", title: "Agents & Pipelines", summary: "Orchestration, protocol, MCP, execution modes, context, and model tiers." },
  { id: "security", title: "Security & Memory", summary: "Memory, security callbacks, blocking paths, and harness governance." },
  { id: "processes", title: "Processes", summary: "Clinical, review, ingestion, sync, chat, approval, and A2A sequences." },
  { id: "data", title: "Data & API", summary: "Clinical database model and Pydantic contract surface." },
  { id: "deployment", title: "Deployment & Quality", summary: "Cloud topology, observability, evaluation, and rubric coverage." },
];

export const diagramCatalog: DiagramView[] = [
  {
    id: "01-system-architecture",
    title: "System architecture",
    category: "system",
    summary: "The complete command-center path from UI through FastAPI, ADK, tools, storage, retrieval, and audit.",
    svg: "/diagrams/svg/01-system-architecture.svg",
    png: "/diagrams/01-system-architecture.png",
    points: ["Best first view for a new reviewer", "Shows where product actions enter the agent runtime", "Makes storage and audit boundaries visible"],
  },
  {
    id: "02-c4-p1",
    title: "C4 system context",
    category: "system",
    summary: "Places the clinical workspace in its human, data, Google service, and governance environment.",
    svg: "/diagrams/svg/02-c4-p1.svg",
    png: "/diagrams/02-c4-p1.png",
    points: ["Clinician and admin entry points", "External service relationships", "Trust boundary at the system edge"],
  },
  {
    id: "02-c4-p2",
    title: "C4 containers",
    category: "system",
    summary: "Breaks the product into the React UI, FastAPI layer, ADK runtime, MCP server, A2A server, database, and model services.",
    svg: "/diagrams/svg/02-c4-p2.svg",
    png: "/diagrams/02-c4-p2.png",
    points: ["Frontend and backend responsibilities", "Agent runtime separation", "Persistence and protocol containers"],
  },
  {
    id: "02-c4-p3",
    title: "C4 components",
    category: "system",
    summary: "Shows the main Python components that support routing, tools, callbacks, memory, document parsing, and persistence.",
    svg: "/diagrams/svg/02-c4-p3.svg",
    png: "/diagrams/02-c4-p3.png",
    points: ["Root agent and clinical pipelines", "Tool and callback modules", "Persistence and observability components"],
  },
  {
    id: "03-module-dependency-graph",
    title: "Module dependency graph",
    category: "system",
    summary: "Maps the project modules so reviewers can see the real code boundaries behind the product.",
    svg: "/diagrams/svg/03-module-dependency-graph.svg",
    png: "/diagrams/03-module-dependency-graph.png",
    points: ["Useful for code review", "Highlights dependency direction", "Keeps the ADK scaffold visible"],
  },
  {
    id: "05-frontend-route-map",
    title: "Frontend route map",
    category: "system",
    summary: "Shows every clinical and admin route available in the command center.",
    svg: "/diagrams/svg/05-frontend-route-map.svg",
    png: "/diagrams/05-frontend-route-map.png",
    points: ["Role-aware navigation", "Clinical workflow destinations", "Admin data-platform surfaces"],
  },
  {
    id: "25-rest-api-map",
    title: "REST API map",
    category: "system",
    summary: "Connects the frontend workflows to the V1/V2 API endpoints that serve agents, data, and diagnostics.",
    svg: "/diagrams/svg/25-rest-api-map.svg",
    png: "/diagrams/25-rest-api-map.png",
    points: ["Endpoint family overview", "V1 product and V2 integration split", "Good bridge from UI to backend"],
  },
  {
    id: "06-agent-hierarchy",
    title: "Agent hierarchy",
    category: "agents",
    summary: "Shows the orchestrator and specialist agents across extraction, Q&A, database intelligence, storage, and audit.",
    svg: "/diagrams/svg/06-agent-hierarchy.svg",
    png: "/diagrams/06-agent-hierarchy.png",
    points: ["Most direct ADK story", "Specialists grouped by workflow", "Human review and audit agents included"],
  },
  {
    id: "07-a2a-communication",
    title: "A2A communication",
    category: "agents",
    summary: "Shows how the local root agent, A2A server, agent card, and remote participants exchange context safely.",
    svg: "/diagrams/svg/07-a2a-communication.svg",
    png: "/diagrams/07-a2a-communication.png",
    points: ["Agent card discovery", "Remote delegation path", "Context isolation boundary"],
  },
  {
    id: "08-mcp-server-topology",
    title: "MCP server topology",
    category: "agents",
    summary: "Explains how MCP exposes database-backed clinical tools to the agent runtime.",
    svg: "/diagrams/svg/08-mcp-server-topology.svg",
    png: "/diagrams/08-mcp-server-topology.png",
    points: ["Tool interoperability", "Database-backed server surface", "Auditable tool execution"],
  },
  {
    id: "09-execution-mode-switch",
    title: "Execution mode switch",
    category: "agents",
    summary: "Clarifies deterministic demo execution versus live tenant execution.",
    svg: "/diagrams/svg/09-execution-mode-switch.svg",
    png: "/diagrams/09-execution-mode-switch.png",
    points: ["Demo and live mode split", "Tenant-aware runtime routing", "Keeps local testing honest"],
  },
  {
    id: "12-context-engineering-pipeline",
    title: "Context engineering pipeline",
    category: "agents",
    summary: "Shows how context is collected, ranked, compressed, budgeted, and assembled for agent calls.",
    svg: "/diagrams/svg/12-context-engineering-pipeline.svg",
    png: "/diagrams/12-context-engineering-pipeline.png",
    points: ["Layer 1 working memory", "Token budget controls", "Structured prompt assembly"],
  },
  {
    id: "28-gemini-model-tier-registry",
    title: "Gemini model tier registry",
    category: "agents",
    summary: "Shows the model registry that keeps agent model selection centralized and tiered.",
    svg: "/diagrams/svg/28-gemini-model-tier-registry.svg",
    png: "/diagrams/28-gemini-model-tier-registry.png",
    points: ["Flash-lite default path", "Pro and custom-tool tiers", "Single model selection boundary"],
  },
  {
    id: "10-memory-architecture",
    title: "Memory architecture",
    category: "security",
    summary: "Explains the four memory layers from per-call working memory through A2A context.",
    svg: "/diagrams/svg/10-memory-architecture.svg",
    png: "/diagrams/10-memory-architecture.png",
    points: ["Working, session, long-term, and A2A layers", "State prefix rules", "PII-conscious persistence"],
  },
  {
    id: "11-security-pipeline",
    title: "Security pipeline",
    category: "security",
    summary: "Shows the input, tool, and output callback gates that guard every agent execution.",
    svg: "/diagrams/svg/11-security-pipeline.svg",
    png: "/diagrams/11-security-pipeline.png",
    points: ["Prompt injection blocking", "Tool argument validation", "Output PII and secret scanning"],
  },
  {
    id: "22-security-block-sequence",
    title: "Security block sequence",
    category: "security",
    summary: "Shows how a suspicious request is blocked, logged, and kept out of downstream tools.",
    svg: "/diagrams/svg/22-security-block-sequence.svg",
    png: "/diagrams/22-security-block-sequence.png",
    points: ["Block path is explicit", "Audit event retained", "No unsafe tool call proceeds"],
  },
  {
    id: "26-harness-governance-map",
    title: "Harness governance map",
    category: "security",
    summary: "Connects the harness, generated wiki, skills, rules, and validation checks that keep the project aligned.",
    svg: "/diagrams/svg/26-harness-governance-map.svg",
    png: "/diagrams/26-harness-governance-map.png",
    points: ["Rules and skills are visible", "Wiki sync boundary", "Validation and drift controls"],
  },
  {
    id: "14-clinical-request-lifecycle-bpmn",
    title: "Clinical request lifecycle",
    category: "processes",
    summary: "A BPMN view of request intake, routing, specialist execution, review, persistence, and audit.",
    svg: "/diagrams/svg/14-clinical-request-lifecycle-bpmn.svg",
    png: "/diagrams/14-clinical-request-lifecycle-bpmn.png",
    points: ["End-to-end workflow", "Review gate placement", "Storage and audit handoff"],
  },
  {
    id: "15-human-in-the-loop-bpmn",
    title: "Human-in-the-loop BPMN",
    category: "processes",
    summary: "Shows the approval boundary that keeps consequential clinical output under named clinician control.",
    svg: "/diagrams/svg/15-human-in-the-loop-bpmn.svg",
    png: "/diagrams/15-human-in-the-loop-bpmn.png",
    points: ["Review queue entry", "Approve or reject path", "Synchronized only after approval"],
  },
  {
    id: "16-document-ingestion-flow",
    title: "Document ingestion flow",
    category: "processes",
    summary: "Shows PDF and image ingestion through validation, parsing, extraction, review, and storage.",
    svg: "/diagrams/svg/16-document-ingestion-flow.svg",
    png: "/diagrams/16-document-ingestion-flow.png",
    points: ["Upload policy", "Multimodal parsing", "Structured output and receipts"],
  },
  {
    id: "17-wiki-auto-sync-bpmn",
    title: "Wiki auto-sync BPMN",
    category: "processes",
    summary: "Explains the deterministic sync path that keeps generated wiki and harness indexes current.",
    svg: "/diagrams/svg/17-wiki-auto-sync-bpmn.svg",
    png: "/diagrams/17-wiki-auto-sync-bpmn.png",
    points: ["Machine-owned wiki blocks", "Harness mirroring", "Drift reporting"],
  },
  {
    id: "19-chat-turn-sequence",
    title: "Chat turn sequence",
    category: "processes",
    summary: "Shows a clinical Q&A turn from user question through retrieval, answer synthesis, citations, and audit.",
    svg: "/diagrams/svg/19-chat-turn-sequence.svg",
    png: "/diagrams/19-chat-turn-sequence.png",
    points: ["Patient scope validation", "Multimodal retrieval", "Cited answer return path"],
  },
  {
    id: "20-hitl-approval-sequence",
    title: "HITL approval sequence",
    category: "processes",
    summary: "Sequence view of the review handoff between agent output, clinician decision, persistence, and audit.",
    svg: "/diagrams/svg/20-hitl-approval-sequence.svg",
    png: "/diagrams/20-hitl-approval-sequence.png",
    points: ["Approval is explicit", "Rejected output does not persist", "Receipt and audit are captured"],
  },
  {
    id: "21-a2a-delegation-sequence",
    title: "A2A delegation sequence",
    category: "processes",
    summary: "Shows cross-agent delegation using A2A without leaking unrelated context.",
    svg: "/diagrams/svg/21-a2a-delegation-sequence.svg",
    png: "/diagrams/21-a2a-delegation-sequence.png",
    points: ["Remote agent task handoff", "Minimal context exchange", "Result returns through root agent"],
  },
  {
    id: "29-animated-chat-flow",
    title: "Animated chat flow",
    category: "processes",
    summary: "Animated view of the patient Q&A path for demos and video capture.",
    svg: "/diagrams/svg/29-animated-chat-flow.svg",
    points: ["Movement helps explain retrieval flow", "Good video segment", "Pairs with the Q&A workflow screen"],
  },
  {
    id: "23-clinical-database-erd",
    title: "Clinical database ERD",
    category: "data",
    summary: "Shows the governed clinical schema used by database intelligence and population analytics.",
    svg: "/diagrams/svg/23-clinical-database-erd.svg",
    png: "/diagrams/23-clinical-database-erd.png",
    points: ["Patient, session, extraction, and audit relationships", "SQL pipeline grounding", "Schema review before queries"],
  },
  {
    id: "24-pydantic-contract-class",
    title: "Pydantic contract classes",
    category: "data",
    summary: "Maps the typed API and tool contracts that keep clinical data exchange validated.",
    svg: "/diagrams/svg/24-pydantic-contract-class.svg",
    png: "/diagrams/24-pydantic-contract-class.png",
    points: ["Request and response models", "Validation at boundaries", "Shared frontend-backend contract"],
  },
  {
    id: "04-deployment-topology",
    title: "Deployment topology",
    category: "deployment",
    summary: "Shows the local and cloud deployment targets including Cloud Run, Agent Engine, storage, tracing, and logs.",
    svg: "/diagrams/svg/04-deployment-topology.svg",
    png: "/diagrams/04-deployment-topology.png",
    points: ["Local demo path", "Cloud Run and Vertex AI targets", "Observability routing"],
  },
  {
    id: "13-observability-pillars",
    title: "Observability pillars",
    category: "deployment",
    summary: "Explains logs, traces, and metrics across agent execution and product actions.",
    svg: "/diagrams/svg/13-observability-pillars.svg",
    png: "/diagrams/13-observability-pillars.png",
    points: ["Structured logs", "Trace narrative", "Timing and health metrics"],
  },
  {
    id: "18-eval-quality-flywheel",
    title: "Evaluation quality flywheel",
    category: "deployment",
    summary: "Shows how evaluation data, failures, fixes, and reruns create an improvement loop.",
    svg: "/diagrams/svg/18-eval-quality-flywheel.svg",
    png: "/diagrams/18-eval-quality-flywheel.png",
    points: ["ADK eval loop", "Failure analysis", "Regression control"],
  },
  {
    id: "27-capstone-rubric-coverage",
    title: "Capstone rubric coverage",
    category: "deployment",
    summary: "Maps the implemented product and architecture evidence to the capstone rubric.",
    svg: "/diagrams/svg/27-capstone-rubric-coverage.svg",
    png: "/diagrams/27-capstone-rubric-coverage.png",
    points: ["Multi-agent evidence", "Security, deployment, and documentation", "Demo-video checklist support"],
  },
];

export const diagramsByCategory = diagramCategories.map(category => ({
  ...category,
  diagrams: diagramCatalog.filter(diagram => diagram.category === category.id),
}));

export function getDiagram(id: string): DiagramView {
  const diagram = diagramCatalog.find(item => item.id === id);
  if (!diagram) throw new Error(`Unknown diagram: ${id}`);
  return diagram;
}
