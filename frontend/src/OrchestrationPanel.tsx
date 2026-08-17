import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "./api";
import { StatusBadge } from "./components";
import { useClinical } from "./context";
import type { OrchestrationPlan } from "./types";

const manualPlans: Record<OrchestrationPlan["workflow"], OrchestrationPlan> = {
  extraction: {
    intent: "Extract structured clinical data from a source image",
    workflow: "extraction", route: "/app/extraction",
    agents: ["Image Quality", "Vision", "OCR", "Structuring", "Validation", "Storage", "Audit"],
    dataSources: ["Uploaded source", "Patient record"], permissions: ["Read patient context", "Write reviewed clinical data"],
    expectedOutput: "Editable structured fields, confidence, evidence, storage receipts, and audit event",
  },
  qa: {
    intent: "Answer a patient-scoped clinical question",
    workflow: "qa", route: "/app/qa",
    agents: ["Retrieval", "Patient Context", "Image Evidence", "Citation", "Clinical Answer", "Validation", "Audit"],
    dataSources: ["Patient record", "Clinical notes", "Imaging", "Vector evidence"], permissions: ["Read authorized patient evidence"],
    expectedOutput: "Cited clinical answer with confidence and reopenable source evidence",
  },
  database: {
    intent: "Analyze a clinical population using read-only SQL",
    workflow: "database", route: "/app/database",
    agents: ["Schema Understanding", "SQL Generation", "Query Validation", "Database Query", "Chart Generation", "Insight", "Audit"],
    dataSources: ["Authorized relational clinical data"], permissions: ["Read aggregate clinical data", "Execute validated read-only query"],
    expectedOutput: "Safety-reviewed SQL, result table, chart, CSV, and audit event",
  },
};

export function OrchestrationPanel({ open, onClose, initialQuery = "" }: { open: boolean; onClose: () => void; initialQuery?: string }) {
  const { patient } = useClinical(); const navigate = useNavigate(); const inputRef = useRef<HTMLTextAreaElement>(null);
  const [query, setQuery] = useState(""); const [mode, setMode] = useState<"auto" | OrchestrationPlan["workflow"]>("auto"); const [plan, setPlan] = useState<OrchestrationPlan | null>(null); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  useEffect(() => { if (!open) return; inputRef.current?.focus(); const escape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); }; document.addEventListener("keydown", escape); return () => document.removeEventListener("keydown", escape); }, [open, onClose]);
  useEffect(() => { if (open && initialQuery) { setQuery(initialQuery); setMode("auto"); setPlan(null); } }, [open, initialQuery]);
  useEffect(() => { if (mode === "auto") setPlan(null); else setPlan(manualPlans[mode]); }, [mode]);
  if (!open) return null;
  const createPlan = async () => { setLoading(true); setError(""); try { setPlan(await api.orchestrate(query, patient?.id)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to create orchestration plan"); } finally { setLoading(false); } };
  const run = () => { if (!plan) return; const route = { extraction: "/app/extraction", qa: "/app/qa", database: "/app/database" }[plan.workflow]; const params = new URLSearchParams(); if (patient?.id) params.set("patient", patient.id); if (query) params.set("query", query); onClose(); navigate(`${route}?${params.toString()}`); };
  return <div className="modal-backdrop command-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}><section className="orchestration-panel" role="dialog" aria-modal="true" aria-labelledby="orchestration-title">
    <header><div><span className="eyebrow accent">AGENT ORCHESTRATION</span><h2 id="orchestration-title">Plan a clinical task</h2></div>{patient && <StatusBadge tone="neutral">Patient: {patient.name}</StatusBadge>}</header>
    <div className="orchestration-body"><label>What should Nexus do?<textarea ref={inputRef} rows={3} value={query} onChange={event => { setQuery(event.target.value); if (mode === "auto") setPlan(null); }} placeholder="Ask about a patient, extract a source image, or analyze a population"/></label>
      <fieldset><legend>Routing mode</legend><div className="workflow-choices"><button className={mode === "auto" ? "active" : ""} onClick={() => setMode("auto")}><strong>Auto Orchestrate</strong><small>Nexus selects workflow and agents</small></button>{(["extraction", "qa", "database"] as const).map(workflow => <button key={workflow} className={mode === workflow ? "active" : ""} onClick={() => setMode(workflow)}><strong>{workflow === "qa" ? "Patient Q&A" : workflow === "database" ? "Population insights" : "Image extraction"}</strong><small>Manual workflow</small></button>)}</div></fieldset>
      {mode === "auto" && !plan && <button className="button primary full" disabled={!query.trim() || loading} onClick={() => void createPlan()}>{loading ? "Planning specialist agents" : "Create orchestration plan"}</button>}{error && <p className="form-error" role="alert">{error}</p>}
      {plan && <section className="plan-review" aria-label="Orchestration plan"><div><span className="eyebrow">Intent</span><p>{plan.intent}</p></div><div><span className="eyebrow">Workflow</span><p>{plan.workflow}</p></div><div><span className="eyebrow">Agents</span><p>{plan.agents.join(" · ")}</p></div><div><span className="eyebrow">Data sources</span><p>{plan.dataSources.join(" · ")}</p></div><div><span className="eyebrow">Permissions</span><p>{plan.permissions.join(" · ")}</p></div><div><span className="eyebrow">Expected output</span><p>{plan.expectedOutput}</p></div></section>}
    </div><footer><span>Nothing runs until explicitly confirmed.</span><div className="button-row"><button className="button subtle" onClick={onClose}>Cancel</button><button className="button primary" disabled={!plan || !query.trim()} onClick={run}>Run workflow</button></div></footer>
  </section></div>;
}
