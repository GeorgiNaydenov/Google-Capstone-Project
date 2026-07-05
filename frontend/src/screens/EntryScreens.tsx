import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Icon, StatusBadge } from "../components";
import { useClinical } from "../context";
import type { Role } from "../types";

type ArchitectureDiagram = {
  id: string;
  label: string;
  title: string;
  image?: string;
  source: string;
  summary: string;
  points: string[];
};

const architectureDiagrams: ArchitectureDiagram[] = [
  {
    id: "system",
    label: "System",
    title: "System architecture",
    image: "/diagrams/01-system-architecture.png",
    source: "/diagrams/01-system-architecture.drawio",
    summary: "Shows how the clinician UI, FastAPI product layer, ADK orchestration, MCP tools, storage, vector search, SQL, and audit trail fit together.",
    points: ["Best first view for guests", "Explains where agent work becomes product behavior", "Makes the governance boundary visible"],
  },
  {
    id: "c4-context",
    label: "C4",
    title: "C4 context",
    image: "/diagrams/02-c4-p1.png",
    source: "/diagrams/02-c4-model.drawio",
    summary: "Places the command center in its clinical environment so reviewers can see users, external systems, and trust boundaries.",
    points: ["Clinician and admin entry points", "Clinical evidence and data stores", "External Google and deployment surfaces"],
  },
  {
    id: "c4-container",
    label: "C4",
    title: "C4 containers",
    image: "/diagrams/02-c4-p2.png",
    source: "/diagrams/02-c4-model.drawio",
    summary: "Breaks the product into the frontend, deterministic API, ADK agent runtime, MCP server, and persistence layers.",
    points: ["Frontend and backend responsibilities", "Agent runtime separation", "Storage and retrieval contracts"],
  },
  {
    id: "modules",
    label: "Code",
    title: "Module dependency graph",
    image: "/diagrams/03-module-dependency-graph.png",
    source: "/diagrams/03-module-dependency-graph.drawio",
    summary: "Maps the Python modules that power security, memory, orchestration, document processing, and product APIs.",
    points: ["No hidden parallel architecture", "Clear callback and tool boundaries", "Useful for code review"],
  },
  {
    id: "deployment",
    label: "Deploy",
    title: "Deployment topology",
    image: "/diagrams/04-deployment-topology.png",
    source: "/diagrams/04-deployment-topology.drawio",
    summary: "Explains how the capstone can run locally and move toward Cloud Run, Vertex AI Agent Engine, and governed Google services.",
    points: ["Local demo path", "Cloud Run and Agent Engine targets", "Observability and audit routing"],
  },
  {
    id: "routes",
    label: "UI",
    title: "Frontend route map",
    image: "/diagrams/05-frontend-route-map.png",
    source: "/diagrams/05-frontend-route-map.drawio",
    summary: "Shows the product surface a new user can navigate, including clinical workflows, admin control, storage, and governance.",
    points: ["Sixteen primary routes", "Role-aware navigation", "Where each agent workflow appears"],
  },
  {
    id: "agents",
    label: "Agents",
    title: "Agent hierarchy",
    image: "/diagrams/06-agent-hierarchy.png",
    source: "/diagrams/06-agent-hierarchy.drawio",
    summary: "Makes the orchestrator and specialist agents visible, including extraction, Q&A, database intelligence, storage, and audit roles.",
    points: ["Specialist agents by workflow", "Human review and audit agents", "Shows the ADK story directly"],
  },
  {
    id: "a2a",
    label: "A2A",
    title: "A2A communication source",
    source: "/diagrams/07-a2a-communication.drawio",
    summary: "The editable A2A diagram source is bundled for deeper inspection of cross-agent communication and agent-card exposure.",
    points: ["Editable draw.io source included", "Covers Agent2Agent serving", "Useful for protocol review"],
  },
];

export function Landing() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [openDiagrams, setOpenDiagrams] = useState<string[]>(["system", "agents"]);
  const enter = async () => {
    setBusy(true);
    try {
      if (!sessionStorage.getItem("tenant")) sessionStorage.setItem("tenant", "research-clinic");
      const session = await api.startDemo();
      sessionStorage.setItem("demoSession", session.sessionId);
      navigate("/roles");
    } finally {
      setBusy(false);
    }
  };
  const workflowCards = [
    {
      number: "01",
      title: "Session image extraction",
      copy: "A governed intake flow for PDFs and images. Agents check quality, read text and visuals, structure clinical fields, and stop for review before storage.",
      count: "9 agents",
    },
    {
      number: "02",
      title: "Multimodal patient Q&A",
      copy: "A cited answer flow for notes, labs, and images. The system validates patient scope, retrieves evidence, and returns an answer with sources you can reopen.",
      count: "7 agents",
    },
    {
      number: "03",
      title: "Database intelligence",
      copy: "A population insight flow for cohort questions. Natural language becomes inspectable read-only SQL, then approved tables, charts, and written findings.",
      count: "6 agents",
    },
  ];
  const toggleDiagram = (id: string) => {
    setOpenDiagrams(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]);
  };
  const setAllDiagrams = (open: boolean) => {
    setOpenDiagrams(open ? architectureDiagrams.map(item => item.id) : []);
  };

  return <main className="landing-page">
    <header className="landing-nav">
      <div className="product-lockup"><span className="product-symbol"><Icon name="brain" size={22}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div>
      <nav><a href="#workflows">Agent workflows</a><a href="#architecture">Architecture diagrams</a><a href="#governance">Governance</a></nav>
      <StatusBadge tone="info">Synthetic clinical data</StatusBadge>
    </header>
    <section className="landing-hero">
      <div className="hero-copy">
        <span className="eyebrow accent">GOOGLE ADK MULTI-AGENT CLINICAL COMMAND CENTER</span>
        <h1>Turn fragmented clinical evidence into decisions clinicians can verify.</h1>
        <p>Clinician AI KIT gives care teams one workspace for document extraction, cited patient Q&A, cohort analytics, review, storage, and audit. The agents do the heavy reading while every consequential action stays visible and clinician-approved.</p>
        <div className="button-row"><button className="button primary large" disabled={busy} onClick={() => void enter()}>{busy ? "Preparing workspace" : "Start clinical workspace"}</button><button className="button subtle large" onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })}>Inspect architecture</button></div>
        <div className="trust-row"><span>No login needed</span><span>Visible ADK agent traces</span><span>Clinician-gated writes</span><span>Synthetic demo data</span></div>
      </div>
      <div className="product-preview" aria-label="Application preview">
        <header><span>Clinician dashboard</span><StatusBadge tone="success">Agents operational</StatusBadge></header>
        <div className="preview-kpis">{[["Assigned", "24"], ["Verifications", "7"], ["Extractions", "12"], ["Alerts", "5"]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div>
        <div className="preview-body"><section><strong>Priority patient queue</strong>{["Eleanor Kim needs high-risk review", "David Okafor needs high-risk review", "Jonathan Doe has pending evidence", "Maria Garcia has pending evidence"].map(item => <p key={item}><i/>{item}<span>Review</span></p>)}</section><aside><strong>Agent recommendations</strong><p>Review fields below 80% confidence</p><p>High-risk cohort is increasing</p><p>Vector evidence sync is complete</p></aside></div>
      </div>
    </section>
    <section className="landing-section" id="workflows"><header><span className="eyebrow accent">THREE GUIDED WORKFLOWS</span><h2>The agents work in the open.</h2><p>Each workflow shows the plan, specialist agents, tools, evidence, confidence, approval point, storage receipt, and audit event. The product is built for clinical review, not blind automation.</p></header><div className="workflow-showcase">{workflowCards.map(({ number, title, copy, count }) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{copy}</p><StatusBadge tone="info">{count}</StatusBadge></article>)}</div></section>
    <section className="architecture-section" id="architecture">
      <header><span className="eyebrow accent">VISIBLE ARCHITECTURE</span><h2>From clinician intent to governed output.</h2><p>Open the prepared draw.io views to understand the system from the product surface down to agents, modules, deployment, and protocol boundaries.</p></header>
      <div className="architecture-flow">{[["Clinician UI", "Role-aware workflow"], ["ADK orchestrator", "Intent and routing"], ["Specialist agents", "Reasoning and tools"], ["Google services", "Object, JSON, SQL, Vector"], ["Verified outputs", "Evidence and audit"]].map(([title, detail], index) => <div key={title}><span>{index + 1}</span><strong>{title}</strong><small>{detail}</small>{index < 4 && <b>feeds</b>}</div>)}</div>
      <div className="diagram-controls"><div><strong>Architecture diagram atlas</strong><small>{openDiagrams.length} of {architectureDiagrams.length} views expanded</small></div><div><button onClick={() => setAllDiagrams(true)}>Expand all</button><button onClick={() => setAllDiagrams(false)}>Collapse all</button></div></div>
      <div className="diagram-grid">{architectureDiagrams.map(diagram => {
        const open = openDiagrams.includes(diagram.id);
        return <article className={open ? "diagram-card open" : "diagram-card"} key={diagram.id}>
          <button className="diagram-toggle" aria-expanded={open} onClick={() => toggleDiagram(diagram.id)}>
            <span>{diagram.label}</span><strong>{diagram.title}</strong><small>{diagram.summary}</small><b>{open ? "Collapse" : "Expand"}</b>
          </button>
          {open && <div className="diagram-body">
            {diagram.image ? <a className="diagram-frame" href={diagram.image} target="_blank" rel="noreferrer" aria-label={`Open ${diagram.title} image`}><img src={diagram.image} alt={`${diagram.title} diagram`}/></a> : <div className="diagram-empty"><strong>Editable draw.io source ready</strong><p>Open the source file to inspect this protocol view in draw.io.</p></div>}
            <div className="diagram-notes"><ul>{diagram.points.map(point => <li key={point}>{point}</li>)}</ul><div className="diagram-actions">{diagram.image && <a href={diagram.image} target="_blank" rel="noreferrer">Open image</a>}<a href={diagram.source} target="_blank" rel="noreferrer">Open draw.io source</a></div></div>
          </div>}
        </article>;
      })}</div>
    </section>
    <section className="governance-section" id="governance"><div><span className="eyebrow">HUMAN-GOVERNED BY DESIGN</span><h2>Clinical decisions stay with clinicians.</h2><p>Patient scope checks, read-only SQL, evidence citations, explicit approval, secret redaction, and immutable audit events are present across the product. The system helps prepare decisions; it does not make them quietly in the background.</p></div><button className="button primary large" onClick={() => void enter()}>Start clinical workspace</button></section>
  </main>;
}

export function RoleSelection() {
  const navigate = useNavigate();
  const { setRole } = useClinical();
  const enter = (role: Role) => { setRole(role); navigate(role === "admin" ? "/app/admin" : "/app/dashboard"); };

  return <main className="role-page">
    <header><div className="product-lockup"><span className="product-symbol"><Icon name="brain" size={22}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div><StatusBadge tone="info">Synthetic clinical data</StatusBadge></header>
    <section className="role-intro"><span className="eyebrow accent">SELECT WORKSPACE</span><h1>How are you working today?</h1><p>The same identity can switch roles at any time. Active patient and workflow context follows you.</p></section>
    <div className="role-dashboard"><section className="role-cards"><button onClick={() => enter("clinician")}><span className="role-icon"><Icon name="activity" size={28}/></span><div><small>CLINICAL OPERATIONS</small><strong>Clinician workspace</strong><p>Patient queue, sessions, extraction, cited Q&A, database intelligence, review, and audit.</p><b>Enter clinician workspace</b></div></button><button onClick={() => enter("admin")}><span className="role-icon"><Icon name="settings" size={28}/></span><div><small>PLATFORM CONTROL</small><strong>Administrator workspace</strong><p>Users, agents, routing, pipelines, storage, indexes, relational data, health, and compliance.</p><b>Enter admin workspace</b></div></button></section><aside><section><h2>Recent agent runs</h2>{[["Image Extraction", "PT-8829", "Completed"], ["Patient Q&A", "PT-1029", "Review"], ["Database Intelligence", "Cohort", "Completed"]].map(([agent, entity, status]) => <div className="role-activity" key={agent}><span className="pulse"/><span><strong>{agent}</strong><small>{entity} moments ago</small></span><StatusBadge tone={status === "Completed" ? "success" : "review"}>{status}</StatusBadge></div>)}</section><section><h2>System status</h2><div className="role-status"><span>ADK orchestrator <StatusBadge tone="success">Ready</StatusBadge></span><span>Clinical data stores <StatusBadge tone="success">Synchronized</StatusBadge></span><span>Audit pipeline <StatusBadge tone="success">Recording</StatusBadge></span></div></section></aside></div>
  </main>;
}
