import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { DiagramAtlas } from "../components/DiagramAtlas";
import { Icon, StatusBadge } from "../components";
import { useClinical } from "../context";
import type { Role } from "../types";

export function Landing() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
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
  const [docsOpen, setDocsOpen] = useState(false);

  return <main className="landing-page">
    <header className="landing-nav">
      <div className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div>
      <nav>
        <a href="#workflows">Agent workflows</a>
        <a href="#architecture">Architecture diagrams</a>
        <a href="#governance">Governance</a>
        <div className="nav-dropdown" onMouseEnter={() => setDocsOpen(true)} onMouseLeave={() => setDocsOpen(false)}>
          <button type="button" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            Developer & Docs <Icon name="settings" size={14}/>
          </button>
          {docsOpen && (
            <div className="nav-dropdown-menu">
              <a href="/documentation/">Documentation hub</a>
              <a href="/documentation/llm-wiki/index.html">Karpathy LLM Wiki</a>
              <a href="/documentation/project-wiki/Home.html">Obsidian Wiki</a>
              <a href="/docs">Interactive API Docs</a>
              <button type="button" onClick={() => navigate("/docs-viewer?tab=api_runner")}>API Console</button>
            </div>
          )}
        </div>
      </nav>
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
      <header><span className="eyebrow accent">VISIBLE ARCHITECTURE</span><h2>From clinician intent to governed output.</h2><p>Explore the prepared architecture views from the product surface down to agents, modules, deployment, and protocol boundaries.</p></header>
      <div className="architecture-flow">{[["Clinician UI", "Role-aware workflow"], ["ADK orchestrator", "Intent and routing"], ["Specialist agents", "Reasoning and tools"], ["Google services", "Object, JSON, SQL, Vector"], ["Verified outputs", "Evidence and audit"]].map(([title, detail], index) => <div key={title}><span>{index + 1}</span><strong>{title}</strong><small>{detail}</small>{index < 4 && <b>feeds</b>}</div>)}</div>
      <div className="diagram-atlas-intro"><div><strong>Architecture diagram atlas</strong><small>Six categories with pan, zoom, fullscreen, SVG rendering, and PNG fallback.</small></div><StatusBadge tone="info">31 views</StatusBadge></div>
      <DiagramAtlas defaultCategory="system"/>
    </section>
    <section className="governance-section" id="governance"><div><span className="eyebrow">HUMAN-GOVERNED BY DESIGN</span><h2>Clinical decisions stay with clinicians.</h2><p>Patient scope checks, read-only SQL, evidence citations, explicit approval, secret redaction, and immutable audit events are present across the product. The system helps prepare decisions; it does not make them quietly in the background.</p></div><button className="button primary large" onClick={() => void enter()}>Start clinical workspace</button></section>
  </main>;
}

export function RoleSelection() {
  const navigate = useNavigate();
  const { setRole } = useClinical();
  const enter = (role: Role) => { setRole(role); navigate(role === "admin" ? "/app/admin" : "/app/dashboard"); };

  return <main className="role-page">
    <header><div className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div><StatusBadge tone="info">Synthetic clinical data</StatusBadge></header>
    <section className="role-intro"><span className="eyebrow accent">SELECT WORKSPACE</span><h1>How are you working today?</h1><p>The same identity can switch roles at any time. Active patient and workflow context follows you.</p></section>
    <div className="role-dashboard"><section className="role-cards"><button onClick={() => enter("clinician")}><span className="role-icon"><Icon name="activity" size={28}/></span><div><small>CLINICAL OPERATIONS</small><strong>Clinician workspace</strong><p>Patient queue, sessions, extraction, cited Q&A, database intelligence, review, and audit.</p><b>Enter clinician workspace</b></div></button><button onClick={() => enter("admin")}><span className="role-icon"><Icon name="settings" size={28}/></span><div><small>PLATFORM CONTROL</small><strong>Administrator workspace</strong><p>Users, agents, routing, pipelines, storage, indexes, relational data, health, and compliance.</p><b>Enter admin workspace</b></div></button></section><aside><section><h2>Recent agent runs</h2>{[["Image Extraction", "PT-8829", "Completed"], ["Patient Q&A", "PT-1029", "Review"], ["Database Intelligence", "Cohort", "Completed"]].map(([agent, entity, status]) => <div className="role-activity" key={agent}><span className="pulse"/><span><strong>{agent}</strong><small>{entity} moments ago</small></span><StatusBadge tone={status === "Completed" ? "success" : "review"}>{status}</StatusBadge></div>)}</section><section><h2>System status</h2><div className="role-status"><span>ADK orchestrator <StatusBadge tone="success">Ready</StatusBadge></span><span>Clinical data stores <StatusBadge tone="success">Synchronized</StatusBadge></span><span>Audit pipeline <StatusBadge tone="success">Recording</StatusBadge></span></div></section></aside></div>
  </main>;
}
