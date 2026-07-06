import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { DiagramAtlas } from "../components/DiagramAtlas";
import { Icon, StatusBadge, useToast } from "../components";
import { useClinical } from "../context";
import type { Role } from "../types";

export function Landing() {
  const navigate = useNavigate();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const enter = async () => {
    setBusy(true);
    if (!sessionStorage.getItem("tenant")) sessionStorage.setItem("tenant", "research-clinic");
    try {
      // A demo session isolates this browser's state, but the API also
      // accepts the default "public-demo" session, so entry never depends on
      // this call succeeding — a transient failure must not trap the user on
      // the landing page.
      const session = await api.startDemo();
      sessionStorage.setItem("demoSession", session.sessionId);
    } catch {
      toast("Could not reach the demo API; continuing with a shared session.", "info");
    } finally {
      setBusy(false);
      navigate("/roles");
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
      title: "Population insights",
      copy: "A population insight flow for cohort questions. Natural language becomes inspectable read-only SQL, then approved tables, charts, and written findings.",
      count: "6 agents",
    },
  ];
  return <main className="landing-page">
    <header className="landing-nav">
      <div className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div>
      <nav>
        <a href="#workflows">Agent workflows</a>
        <a href="#architecture">Architecture diagrams</a>
        <Link to="/docs-access">How to Access Documentation</Link>
      </nav>
      <StatusBadge tone="info">Synthetic patient records - no real PHI</StatusBadge>
    </header>
    <section className="landing-hero">
      <div className="hero-copy">
        <span className="eyebrow accent">CLINICAL AI COMMAND CENTER</span>
        <h1>Turn fragmented clinical evidence into decisions clinicians can verify.</h1>
        <p>Clinician AI KIT gives care teams one workspace for document extraction, cited patient Q&A, cohort analytics, review, storage, and audit. The agents do the heavy reading while every consequential action stays visible and clinician-approved.</p>
        <div className="button-row"><button className="button primary large" disabled={busy} onClick={() => void enter()}>{busy ? "Preparing workspace" : "Start clinical workspace"}</button><button className="button subtle large" onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })}>Inspect architecture</button></div>
        <div className="trust-row"><span>No login needed</span><span>Transparent AI reasoning traces</span><span>Clinician-gated writes</span><span>Synthetic demo records</span></div>
      </div>
      <div className="product-preview" aria-label="Application preview">
        <header><span>Clinician dashboard</span><StatusBadge tone="success">Agents operational</StatusBadge></header>
        <div className="preview-kpis">{[["Assigned", "1,500"], ["Verifications", "918"], ["Extractions", "48"], ["Alerts", "976"]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div>
        <div className="preview-body"><section><strong>Priority patient queue</strong>{["Wei Brooks needs high-risk review", "Ingrid Smith needs high-risk review", "Elizabeth Rodriguez has pending evidence", "Amir Hassan has pending evidence"].map(item => <p key={item}><i/>{item}<span>Review</span></p>)}</section><aside><strong>Agent recommendations</strong><p>Review fields below 80% confidence</p><p>High-risk cohort is increasing</p><p>Vector evidence sync is complete</p></aside></div>
      </div>
    </section>
    <section className="landing-section" id="workflows"><header><span className="eyebrow accent">THREE GUIDED WORKFLOWS</span><h2>The agents work in the open.</h2><p>Each workflow shows the plan, specialist agents, tools, evidence, confidence, approval point, storage receipt, and audit event. The product is built for clinical review, not blind automation.</p></header><div className="workflow-showcase">{workflowCards.map(({ number, title, copy, count }) => <article key={number}><span>{number}</span><h3>{title}</h3><p>{copy}</p><StatusBadge tone="info">{count}</StatusBadge></article>)}</div></section>
    <section className="architecture-section" id="architecture">
      <header><span className="eyebrow accent">VISIBLE ARCHITECTURE</span><h2>From clinician intent to governed output.</h2><p>Explore the prepared architecture views from the product surface down to agents, modules, deployment, and protocol boundaries.</p></header>
      <div className="architecture-flow">{[["Clinician UI", "Role-aware workflow"], ["AI orchestration", "Intent and routing"], ["Specialist agents", "Reasoning and tools"], ["Google services", "Object, JSON, SQL, Vector"], ["Verified outputs", "Evidence and audit"]].map(([title, detail], index) => <div key={title}><span>{index + 1}</span><strong>{title}</strong><small>{detail}</small>{index < 4 && <b>feeds</b>}</div>)}</div>
      <div className="diagram-atlas-intro"><div><strong>Architecture diagram atlas</strong><small>Six categories with pan, zoom, fullscreen, SVG rendering, and PNG fallback.</small></div><StatusBadge tone="info">31 views</StatusBadge></div>
      <DiagramAtlas defaultCategory="system"/>
    </section>
  </main>;
}

export function RoleSelection() {
  const navigate = useNavigate();
  const { setRole } = useClinical();
  const enter = (role: Role) => { setRole(role); navigate(role === "admin" ? "/app/admin" : "/app/dashboard"); };

  return <main className="role-page">
    <header><div className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div><StatusBadge tone="info">Synthetic patient records - no real PHI</StatusBadge></header>
    <section className="role-intro"><span className="eyebrow accent">SELECT WORKSPACE</span><h1>How are you working today?</h1><p>The same identity can switch roles at any time. Active patient and workflow context follows you.</p></section>
    <div className="role-dashboard"><section className="role-cards"><button onClick={() => enter("clinician")}><span className="role-icon"><Icon name="activity" size={28}/></span><div><small>CLINICAL OPERATIONS</small><strong>Clinician workspace</strong><p>Patient queue, sessions, extraction, cited Q&A, population insights, review, and audit.</p><b>Enter clinician workspace</b></div></button><button onClick={() => enter("admin")}><span className="role-icon"><Icon name="settings" size={28}/></span><div><small>PLATFORM CONTROL</small><strong>Administrator workspace</strong><p>Users, care teams, routing, storage, records, system health, and compliance.</p><b>Enter admin workspace</b></div></button></section><aside><section><h2>Recent agent runs</h2>{[["Image Extraction", "PT-D00008", "Completed"], ["Patient Q&A", "PT-D00002", "Review"], ["Population Insights", "Cohort", "Completed"]].map(([agent, entity, status]) => <div className="role-activity" key={agent}><span className="pulse"/><span><strong>{agent}</strong><small>{entity} moments ago</small></span><StatusBadge tone={status === "Completed" ? "success" : "review"}>{status}</StatusBadge></div>)}</section><section><h2>System status</h2><div className="role-status"><span>AI orchestration <StatusBadge tone="success">Ready</StatusBadge></span><span>Clinical data stores <StatusBadge tone="success">Synchronized</StatusBadge></span><span>Audit trail <StatusBadge tone="success">Recording</StatusBadge></span></div></section></aside></div>
  </main>;
}

type DocsGuide = {
  id: string;
  title: string;
  what: string;
  prerequisites: string[];
  steps: string[];
  // Origin-relative path so the link resolves against wherever the app is
  // served — localhost during development and the Cloud Run URL once deployed.
  path: string;
  note?: string;
};

const docsGuides: DocsGuide[] = [
  {
    id: "swagger",
    title: "1. Swagger UI — interactive API console",
    what: "Auto-generated, styled OpenAPI console for every /api/v1 and /api/v2 REST endpoint. Lets you send real requests to the running backend from the browser.",
    prerequisites: ["Python 3.11+", "uv (or pip)", "Packages from requirements.txt — fastapi and uvicorn are already listed there"],
    steps: [
      "Open a terminal and cd into the repo root — the folder that directly contains capstone_agent/, clinical_app/, frontend/, and requirements.txt.",
      "Create the virtual environment: uv venv .venv --python 3.11",
      "Install dependencies into it: uv pip install --python .venv\\Scripts\\python.exe -r requirements.txt",
      "Start the backend: uv run uvicorn clinical_app.app:app --reload --port 8000",
      "Leave that terminal running, then open http://localhost:8000/docs in a browser.",
    ],
    path: "/docs",
    note: "Works the same in demo or live mode — only the backend process needs to be running. After deployment the same page is at <your-service-url>/docs.",
  },
  {
    id: "redoc",
    title: "2. ReDoc — readable API reference",
    what: "The same OpenAPI contract as Swagger, rendered as a structured, read-only reference organized by tag. Better for skimming the schema than for firing test requests.",
    prerequisites: ["Same backend process as Swagger — no extra install"],
    steps: [
      "If the backend from step 1 above is not already running, start it: uv run uvicorn clinical_app.app:app --reload --port 8000",
      "Open http://localhost:8000/redoc in a browser.",
      "Optional — to read the raw machine-readable contract instead, open http://localhost:8000/openapi.json on the same running server.",
    ],
    path: "/redoc",
    note: "The raw machine-readable contract is also available at /openapi.json on the same server.",
  },
  {
    id: "obsidian",
    title: "3. Obsidian Project Wiki — engineering vault",
    what: "The full engineering vault: architecture notes, security and memory design, operations runbooks, and generated inventories, sourced from the Project Wiki/ folder at the repo root.",
    prerequisites: ["None to read the pre-rendered pages — they already ship in frontend/public/documentation/project-wiki/", "Obsidian desktop app (free, obsidian.md) only if you want the real vault with backlinks, graph view, and search", "To rebuild the static pages after editing Project Wiki/*.md: Python 3.11+ and the markdown-it-py package"],
    steps: [
      "Fastest path (no install) — with the backend running (see step 1), open http://localhost:8000/documentation/project-wiki/Home.html in a browser. Every note is a linked static page under that same /documentation/project-wiki/ path.",
      "To browse without running the backend at all, open the file directly from the repo: frontend/public/documentation/project-wiki/Home.html.",
      "To edit or explore the live vault instead of the static export: download Obsidian from obsidian.md and install it.",
      "Launch Obsidian, choose 'Open folder as vault' on the welcome screen (or File > Open Vault).",
      "In the folder picker, navigate to the repo root and select the Project Wiki folder — exact path: <repo-root>\\Project Wiki.",
      "If Obsidian asks whether to trust the vault's plugins/settings, choose Trust — this repo's .obsidian config only sets up appearance and core plugins.",
      "The vault opens with Home.md as the entry note; use the left sidebar file tree, the search icon, or the graph view to navigate the numbered folders (01 Overview, 02 Architecture, 03 Processes, 04 Security, 05 Memory, 06 Operations, 07 Harness).",
      "After editing any Project Wiki/*.md file, regenerate the static pages so the /documentation site matches: uv pip install markdown-it-py, then uv run python scripts/build_docs_site.py from the repo root.",
    ],
    path: "/documentation/project-wiki/Home.html",
    note: "Served on the same origin as the app: locally at localhost:8000/documentation/... and, once deployed, at <your-service-url>/documentation/...",
  },
  {
    id: "karpathy",
    title: "4. Karpathy LLM Wiki — distilled knowledge base",
    what: "One distilled article per topic, summarized and categorized for fast reading, compiled from the same Obsidian vault by the same build script.",
    prerequisites: ["None to just read it — already committed under frontend/public/documentation/llm-wiki/", "To rebuild after editing wiki/*.md: Python 3.11+ and the markdown-it-py package"],
    steps: [
      "Fastest path — with the backend running (see step 1 above), open http://localhost:8000/documentation/llm-wiki/index.html in a browser.",
      "To browse without a running server, open the file directly from the repo: frontend/public/documentation/llm-wiki/index.html.",
      "The index page links every article; each is grouped under a stable category folder (overview, architecture, processes, operations, security-memory, harness) that mirrors the Project Wiki numbering.",
      "The source markdown for these articles lives in wiki/*.md at the repo root — edit there, not in frontend/public/documentation/, which is generated output.",
      "After editing wiki/*.md or Project Wiki/*.md, rebuild both wikis in one pass: uv pip install markdown-it-py, then uv run python scripts/build_docs_site.py from the repo root.",
    ],
    path: "/documentation/llm-wiki/index.html",
    note: "Same origin as the app, both locally and after deployment.",
  },
];

export function DocsAccess() {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  return <main className="docs-access-page">
    <header className="landing-nav">
      <div className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></div>
      <nav><Link to="/">Back to main page</Link></nav>
    </header>
    <section className="docs-access-intro">
      <span className="eyebrow accent">DEVELOPER REFERENCE</span>
      <h1>How to access documentation</h1>
      <p>Start from a freshly cloned repo. Four surfaces cover this project's documentation: two live API consoles generated straight from the code, and two pre-rendered knowledge bases (one of which is also a real Obsidian vault you can open directly). Each entry below is a numbered walkthrough — dependencies first, then exact steps in order, then the exact URL or file path to open.</p>
      <p className="docs-access-note">Fastest overall entry point once the backend is running: open <code>http://localhost:8000/documentation</code> — the documentation hub links to all four surfaces below in one place.</p>
    </section>
    <section className="docs-access-list">
      {docsGuides.map(guide => <article className="docs-access-card" key={guide.id}>
        <h2>{guide.title}</h2>
        <p>{guide.what}</p>
        <h3>Dependencies</h3>
        <ul>{guide.prerequisites.map(item => <li key={item}>{item}</li>)}</ul>
        <h3>Steps</h3>
        <ol>{guide.steps.map(item => <li key={item}>{item}</li>)}</ol>
        <h3>Open it</h3>
        <a href={guide.path} target="_blank" rel="noreferrer">{origin ? `${origin}${guide.path}` : guide.path}</a>
        {guide.note && <p className="docs-access-note">{guide.note}</p>}
      </article>)}
    </section>
  </main>;
}
