import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Icon, StatusBadge } from "../components";
import { useClinical } from "../context";
import type { Role } from "../types";

export function Landing() {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const enter = async () => {
    setBusy(true);
    try {
      sessionStorage.setItem("tenant", "demo");
      const session = await api.startDemo();
      sessionStorage.setItem("demoSession", session.sessionId);
      navigate("/roles");
    } finally {
      setBusy(false);
    }
  };

  return <main className="landing-page">
    <header className="landing-nav">
      <div className="product-lockup"><span className="product-symbol"><Icon name="brain" size={22}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div>
      <nav><a href="#workflows">Agent workflows</a><a href="#architecture">Architecture</a><a href="#governance">Governance</a></nav>
      <StatusBadge tone="info">Synthetic clinical data</StatusBadge>
    </header>
    <section className="landing-hero">
      <div className="hero-copy">
        <span className="eyebrow accent">GOOGLE ADK MULTI-AGENT CLINICAL COMMAND CENTER</span>
        <h1>Turn fragmented clinical evidence into verified patient intelligence.</h1>
        <p>Clinician AI KIT coordinates specialist agents for multimodal extraction, cited patient Q&A, governed SQL analytics, structured storage, and complete auditability.</p>
        <div className="button-row"><button className="button primary large" disabled={busy} onClick={() => void enter()}>{busy ? "Preparing workspace" : "Start clinical workspace"}</button><button className="button subtle large" onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })}>Inspect architecture</button></div>
        <div className="trust-row"><span>No login</span><span>Visible ADK agent traces</span><span>No exposed keys</span><span>Isolated browser session</span></div>
      </div>
      <div className="product-preview" aria-label="Application preview">
        <header><span>Clinician dashboard</span><StatusBadge tone="success">Agents operational</StatusBadge></header>
        <div className="preview-kpis">{[["Assigned", "24"], ["Verifications", "7"], ["Extractions", "12"], ["Alerts", "5"]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div>
        <div className="preview-body"><section><strong>Priority patient queue</strong>{["Eleanor Kim - High risk", "David Okafor - High risk", "Jonathan Doe - Needs review", "Maria Garcia - Needs review"].map(item => <p key={item}><i/>{item}<span>Review</span></p>)}</section><aside><strong>Agent recommendations</strong><p>Validation required below 80%</p><p>High-risk cohort increased</p><p>Vector sync completed</p></aside></div>
      </div>
    </section>
    <section className="landing-section" id="workflows"><header><span className="eyebrow accent">THREE GUIDED WORKFLOWS</span><h2>The agents are the engine, not a hidden chatbot.</h2><p>Every workflow exposes its plan, specialist agents, tools, confidence, evidence, human gate, storage receipts, and audit event.</p></header><div className="workflow-showcase">{[["01", "Session image extraction", "Quality -> OCR -> Vision -> Structuring -> Validation -> Human review -> Storage -> Vector -> Audit", "9 agents"], ["02", "Multimodal patient Q&A", "Scope validation -> Context -> Retrieval -> Image evidence -> Citations -> Answer -> Audit", "7 agents"], ["03", "Database intelligence", "Schema -> SQL -> Safety -> Approval -> Query -> Plotly chart -> Insight -> Audit", "6 agents"]].map(([number, title, flow, count]) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{flow}</p><StatusBadge tone="info">{count}</StatusBadge></article>)}</div></section>
    <section className="architecture-section" id="architecture"><header><span className="eyebrow accent">VISIBLE ARCHITECTURE</span><h2>From clinician intent to governed output.</h2></header><div className="architecture-flow">{[["Clinician UI", "Role-aware workflow"], ["ADK orchestrator", "Intent and routing"], ["Specialist agents", "Reasoning and tools"], ["Google services", "Object, JSON, SQL, Vector"], ["Verified outputs", "Evidence and audit"]].map(([title, detail], index) => <div key={title}><span>{index + 1}</span><strong>{title}</strong><small>{detail}</small>{index < 4 && <b>to</b>}</div>)}</div></section>
    <section className="governance-section" id="governance"><div><span className="eyebrow">HUMAN-GOVERNED BY DESIGN</span><h2>Clinical decisions stay with clinicians.</h2><p>Confidence thresholds, patient scope, read-only SQL, evidence citations, explicit approval, secret redaction, and immutable audit events are enforced across the product.</p></div><button className="button primary large" onClick={() => void enter()}>Start clinical workspace</button></section>
  </main>;
}

export function RoleSelection() {
  const navigate = useNavigate();
  const { setRole } = useClinical();
  const enter = (role: Role) => { setRole(role); navigate(role === "admin" ? "/app/admin" : "/app/dashboard"); };

  return <main className="role-page">
    <header><div className="product-lockup"><span className="product-symbol"><Icon name="brain" size={22}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div><StatusBadge tone="info">Synthetic clinical data</StatusBadge></header>
    <section className="role-intro"><span className="eyebrow accent">SELECT WORKSPACE</span><h1>How are you working today?</h1><p>The same identity can switch roles at any time. Active patient and workflow context follows you.</p></section>
    <div className="role-dashboard"><section className="role-cards"><button onClick={() => enter("clinician")}><span className="role-icon"><Icon name="activity" size={28}/></span><div><small>CLINICAL OPERATIONS</small><strong>Clinician workspace</strong><p>Patient queue, sessions, extraction, cited Q&A, database intelligence, review, and audit.</p><b>Enter clinician workspace</b></div></button><button onClick={() => enter("admin")}><span className="role-icon"><Icon name="settings" size={28}/></span><div><small>PLATFORM CONTROL</small><strong>Administrator workspace</strong><p>Users, agents, routing, pipelines, storage, indexes, relational data, health, and compliance.</p><b>Enter admin workspace</b></div></button></section><aside><section><h2>Recent agent runs</h2>{[["Image Extraction", "PT-8829", "Completed"], ["Patient Q&A", "PT-1029", "Review"], ["Database Intelligence", "Cohort", "Completed"]].map(([agent, entity, status]) => <div className="role-activity" key={agent}><span className="pulse"/><span><strong>{agent}</strong><small>{entity} - moments ago</small></span><StatusBadge tone={status === "Completed" ? "success" : "review"}>{status}</StatusBadge></div>)}</section><section><h2>System status</h2><div className="role-status"><span>ADK orchestrator <StatusBadge tone="success">Ready</StatusBadge></span><span>Clinical data stores <StatusBadge tone="success">Synchronized</StatusBadge></span><span>Audit pipeline <StatusBadge tone="success">Recording</StatusBadge></span></div></section></aside></div>
  </main>;
}
