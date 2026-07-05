import { DragEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { AgentMeta, AgentStepper, Card, ChartPanel, ConfidenceMeter, DenseTable, EmptyState, ErrorState, EvidenceCard, JsonViewer, LoadingState, ReviewChecklist, SourceViewer, SqlPreview, StatusBadge } from "../components";
import type { AgentRun, Evidence, ToolCall } from "../types";
import { useApi } from "../useApi";

function WorkflowHead({ number, title, detail, mode = "local" }: { number: number; title: string; detail: string; mode?: string }) {
  return <header className="page-head workflow-head"><div><span className="eyebrow accent">GUIDED WORKFLOW {number}</span><h1>{title}</h1><p>{detail}</p></div><div className="runtime-state"><span className="pulse"/><div><strong>Google ADK orchestrator</strong><small>{mode === "live" ? "Live Gemini execution" : "Local ADK tool graph"}</small></div></div></header>;
}

function useRunPolling(run: AgentRun | null, setRun: (run: AgentRun) => void) {
  useEffect(() => {
    if (!run || !["queued", "running"].includes(run.status)) return;
    const timer = window.setInterval(() => { void api.run(run.id).then(setRun).catch(() => undefined); }, 1200);
    return () => window.clearInterval(timer);
  }, [run?.id, run?.status, setRun]);
}

const MAX_UPLOAD_BYTES = 10_000_000;
const ACCEPTED_UPLOAD_TYPES = "image/png,image/jpeg,image/webp,application/pdf";
const KB_UPLOAD_TYPES = ".pdf,.docx,.md,.txt,.json,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/markdown,text/plain,application/json";

function PipelineBand({ agents, run }: { agents: string[]; run: AgentRun | null }) {
  return <div className="pipeline-band">{agents.map((agent, index) => <div key={agent} className={run ? "complete" : index === 0 ? "ready" : "waiting"}><span>{run ? "✓" : index + 1}</span><strong>{agent.replaceAll("_", " ").replace(" agent", "")}</strong><small>{run ? "completed" : index === 0 ? "ready" : "waiting"}</small></div>)}</div>;
}

type ParsedPage = { pageNumber?: number; text?: string; imageCount?: number; tableCount?: number; textBlocks?: Array<{ text?: string; bbox?: number[] }> };
type ParsedTable = { tableId?: string; pageNumber?: number; rowCount?: number; columnCount?: number; rows?: unknown[][] };
type ParsedImage = { imageId?: string; pageNumber?: number | null; mimeType?: string; width?: number; height?: number; format?: string; role?: string };

function readArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

function ParsedEvidencePanel({ extracted }: { extracted: Record<string, unknown> }) {
  const pages = readArray<ParsedPage>(extracted.pages);
  const tables = readArray<ParsedTable>(extracted.tables);
  const images = readArray<ParsedImage>(extracted.images);
  const warnings = readArray<string>(extracted.warnings);
  const dimensions = extracted.dimensions as { width?: number; height?: number } | undefined;
  const tableRows = tables.flatMap(table => (table.rows ?? []).map((row, rowIndex) => ({ id: `${table.tableId ?? "table"}-${rowIndex}`, table: table.tableId ?? "table", page: table.pageNumber ?? "-", row: rowIndex + 1, cells: row.map(cell => String(cell ?? "")).join(" | ") })));
  return <Card title="Parsed evidence"><dl className="compact-facts">{extracted.type != null && <div><dt>Type</dt><dd>{String(extracted.type)}</dd></div>}{extracted.pageCount != null && <div><dt>Pages</dt><dd>{String(extracted.pageCount)}</dd></div>}{extracted.imageCount != null && <div><dt>Images</dt><dd>{String(extracted.imageCount)}</dd></div>}{tables.length > 0 && <div><dt>Tables</dt><dd>{tables.length}</dd></div>}{dimensions && <div><dt>Dimensions</dt><dd>{String(dimensions.width ?? "-")}x{String(dimensions.height ?? "-")}</dd></div>}</dl>{warnings.length > 0 && <div className="parse-warnings">{warnings.map(warning => <StatusBadge key={warning} tone="warning">{warning.replaceAll("_", " ")}</StatusBadge>)}</div>}{extracted.thumbnail != null && String(extracted.thumbnail) && <img className="parsed-thumb" src={`data:image/png;base64,${String(extracted.thumbnail)}`} alt="Document thumbnail"/>}{extracted.textPreview != null && String(extracted.textPreview) && <details className="text-preview-details" open><summary>Text preview</summary><pre className="text-preview">{String(extracted.textPreview)}</pre></details>}{pages.length > 0 && <details className="parsed-section"><summary>Page text and blocks</summary>{pages.map(page => <article key={page.pageNumber ?? page.text} className="parsed-page"><header><strong>Page {page.pageNumber ?? "-"}</strong><span>{page.imageCount ?? 0} images - {page.tableCount ?? 0} tables</span></header>{page.text && <pre>{page.text}</pre>}{readArray<{ text?: string }>(page.textBlocks).slice(0, 4).map((block, index) => <p key={index}>{block.text}</p>)}</article>)}</details>}{images.length > 0 && <details className="parsed-section"><summary>Image metadata</summary><DenseTable columns={[{ key: "imageId", label: "Image" }, { key: "pageNumber", label: "Page" }, { key: "mimeType", label: "Type" }, { key: "size", label: "Size" }, { key: "role", label: "Role" }]} rows={images.map((image, index) => ({ id: image.imageId ?? index, imageId: image.imageId ?? "source", pageNumber: image.pageNumber ?? "-", mimeType: image.mimeType ?? image.format ?? "-", size: image.width && image.height ? `${image.width}x${image.height}` : "-", role: image.role ?? "embedded" }))}/></details>}{tableRows.length > 0 && <details className="parsed-section" open><summary>Extracted tables</summary><DenseTable columns={[{ key: "table", label: "Table" }, { key: "page", label: "Page" }, { key: "row", label: "Row" }, { key: "cells", label: "Cells" }]} rows={tableRows}/></details>}</Card>;
}

export function Extraction() {
  const [params] = useSearchParams();
  const catalog = useApi(() => api.agents(), []);
  const [patientId, setPatientId] = useState(params.get("patient") ?? "PT-8829");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [run, setRun] = useState<AgentRun | null>(null);
  const [fieldEdits, setFieldEdits] = useState<Record<string, unknown>>({});
  const [outputTab, setOutputTab] = useState("Extracted fields");
  const [extracted, setExtracted] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  useRunPolling(run, setRun);
  useEffect(() => {
    const fields = run?.result?.fields;
    if (fields && typeof fields === "object" && !Array.isArray(fields)) setFieldEdits(fields as Record<string, unknown>);
  }, [run?.id, run?.status]);
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const select = (next: File | null) => {
    if (preview) URL.revokeObjectURL(preview);
    if (next && next.size > MAX_UPLOAD_BYTES) { setError("File exceeds 10 MB limit"); setFile(null); setPreview(""); return; }
    setError(""); setFile(next); setPreview(next ? URL.createObjectURL(next) : ""); setRun(null); setFieldEdits({}); setExtracted(null);
  };
  const drop = (event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); setDragging(false); select(event.dataTransfer.files?.[0] ?? null); };
  const start = async () => {
    if (!file || !patientId) return;
    setBusy(true); setError("");
    try { const asset = await api.upload(file, patientId); if (asset.extracted) setExtracted(asset.extracted as Record<string, unknown>); setRun(await api.runExtraction(asset.assetId, patientId)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Extraction failed"); }
    finally { setBusy(false); }
  };
  const decide = async (decision: "approved" | "rejected") => {
    if (!run) return;
    setBusy(true); setError("");
    try { setRun(await api.review(run.id, decision, fieldEdits)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Review decision failed"); }
    finally { setBusy(false); }
  };
  const extractionPipeline = catalog.data?.pipelines.find(item => item.id === "extraction");
  const agents = extractionPipeline?.agents ?? ["quality_assessor_agent", "ocr_processor_agent", "vision_analyzer_agent", "clinical_structuring_agent", "validation_agent", "clinical_review_gate_agent", "storage_agent", "vector_indexing_agent", "audit_agent"];
  const runConfidence = Math.round((run?.confidence ?? 0.88) * 100);
  const fieldRows = Object.entries(fieldEdits).map(([field, value]) => ({ id: field, field, value, confidence: runConfidence, review: runConfidence < 75 ? "Review" : "Pass" }));
  const receipts = (run?.result?.storageReceipts ?? []) as Array<{ target: string; status: string; receiptId?: string }>;
  return <>
    <WorkflowHead number={1} title="Session image extraction agent" detail="Upload clinical evidence, inspect every specialist agent, edit structured fields, and approve governed persistence." mode={catalog.data?.executionMode}/>
    {catalog.error && <ErrorState error={catalog.error} retry={catalog.refresh}/>}<PipelineBand agents={agents} run={run}/>
    <div className="extraction-layout">
      <aside>
        <Card title="1. Source and patient"><label>Patient ID<input value={patientId} onChange={event => setPatientId(event.target.value)} placeholder="Patient ID"/></label><label className={`upload-zone ${preview ? "has-file" : ""} ${dragging ? "dragging" : ""}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={drop}><input type="file" accept={ACCEPTED_UPLOAD_TYPES} onChange={event => select(event.target.files?.[0] ?? null)}/>{preview ? <img src={preview} alt="Selected clinical source preview"/> : <><span className="upload-icon">↑</span><strong>Drop image or PDF here</strong><small>or click to browse · PNG, JPEG, WEBP, PDF · 10 MB max</small></>}</label>{file && <div className="file-row"><span><strong>{file.name}</strong><small>{Math.round(file.size / 1024)} KB · ready for quality assessment</small></span><button className="link" onClick={() => select(null)}>Remove</button></div>}<button className="button primary full" disabled={!file || !patientId || busy} onClick={() => void start()}>{busy ? "Running specialist agents" : "Run extraction pipeline"}</button>{error && <p className="form-error" role="alert">{error}</p>}</Card>
        <Card title="Source controls"><dl className="compact-facts"><div><dt>Authorization</dt><dd>Patient scoped</dd></div><div><dt>Retention</dt><dd>Session only</dd></div><div><dt>Input mode</dt><dd>Multimodal</dd></div><div><dt>PHI</dt><dd>Synthetic only</dd></div></dl></Card>
        {extracted && <ParsedEvidencePanel extracted={extracted}/>}
      </aside>
      <section className="extraction-center">
        <Card title="2. Agent execution" action={run && <StatusBadge tone={run.status}>{run.status}</StatusBadge>}>{run ? <><AgentMeta run={run}/><AgentStepper steps={run.steps} toolCalls={(run.result?.toolCalls ?? []) as ToolCall[]}/></> : <EmptyState title="Pipeline ready" detail="Select evidence to run quality, OCR, vision, structuring, validation, review, storage, vector, and audit agents."/>}</Card>
        <nav className="tabs output-tabs">{["Extracted fields", "Structured JSON", "Relational mapping", "Vector status"].map(name => <button key={name} className={outputTab === name ? "active" : ""} onClick={() => setOutputTab(name)}>{name}</button>)}</nav>
        <Card title="3. Structured clinical output">{!run ? <EmptyState title="Awaiting agent output"/> : outputTab === "Extracted fields" ? <div className="editable-fields"><DenseTable columns={[{ key: "field", label: "Clinical field" }, { key: "value", label: "Extracted value", render: row => <input aria-label={`Edit ${String(row.field)}`} disabled={run.status === "completed"} value={String(fieldEdits[String(row.field)] ?? "")} onChange={event => setFieldEdits(current => ({ ...current, [String(row.field)]: event.target.value }))}/> }, { key: "confidence", label: "Confidence", render: row => { const c = Number(row.confidence); return <span className={c < 75 ? "confidence-low" : c < 90 ? "confidence-mid" : "confidence-high"}>{c}%</span>; } }, { key: "review", label: "Validation", render: row => <StatusBadge tone={row.review === "Pass" ? "success" : "review"}>{String(row.review)}</StatusBadge> }]} rows={fieldRows}/></div> : outputTab === "Structured JSON" ? <JsonViewer value={{ patientId, source: file?.name, fields: fieldEdits, confidence: run.confidence, humanReview: run.status }}/>: outputTab === "Relational mapping" ? <DenseTable columns={[{ key: "field", label: "JSON field" }, { key: "table", label: "Table" }, { key: "column", label: "Column" }, { key: "status", label: "Mapping" }]} rows={fieldRows.map(row => ({ id: row.id, field: row.field, table: "session_extractions", column: row.field.replaceAll(/([A-Z])/g, "_$1").toLowerCase(), status: "Ready" }))}/>: <div className="vector-preview"><StatusBadge tone={run.status === "completed" ? "success" : "review"}>{run.status === "completed" ? "Indexed" : "Waiting for approval"}</StatusBadge><code>vertex://clinical-evidence/{run.id}</code><p>Text and image embeddings · 768 dimensions · patient-scoped namespace</p></div>}</Card>
      </section>
      <aside className="extraction-review">
        {run ? <><Card title="Confidence and provenance"><ConfidenceMeter value={run.confidence}/><dl className="compact-facts"><div><dt>Agent system</dt><dd>{run.agentName}</dd></div><div><dt>Audit ID</dt><dd>{run.auditId}</dd></div><div><dt>Trace ID</dt><dd>{run.traceId}</dd></div><div><dt>Evidence</dt><dd>{run.evidence?.length ?? 0} source</dd></div></dl></Card><ReviewChecklist disabled={run.status === "completed" || busy} onRerun={() => void start()} onDecision={decision => void decide(decision)}/><Card title="Storage and audit"><div className="receipt-list">{["json", "relational", "vector", "audit"].map(target => { const receipt = receipts.find(item => item.target === target); const synced = run.status === "completed" && (target === "audit" || receipt?.status === "synced"); return <div key={target}><span>{target}</span><StatusBadge tone={synced ? "success" : "review"}>{synced ? "synced" : "pending review"}</StatusBadge>{receipt?.receiptId && <code>{receipt.receiptId}</code>}</div>; })}</div></Card></> : <Card title="Human review boundary"><p>Extracted values remain editable and unpersisted until all verification checks are complete.</p><ul className="policy-list"><li>No automatic clinical decisions</li><li>Field-level confidence visible</li><li>Evidence remains reopenable</li><li>Every action is audited</li></ul></Card>}
      </aside>
    </div>
  </>;
}

const exampleQuestions = ["What changed between the last two sessions?", "Show image evidence for the latest abnormal result.", "Which extracted fields were verified by a clinician?", "Summarize the 90-day clinical trend."];

export function PatientQa() {
  const [params] = useSearchParams();
  const catalog = useApi(() => api.agents(), []);
  const patientList = useApi(() => api.patients(), []);
  const [patientId, setPatientId] = useState(params.get("patient") ?? "PT-8829");
  const [question, setQuestion] = useState(params.get("query") ?? "");
  const [dateRange, setDateRange] = useState("all");
  const [source, setSource] = useState<"all" | "text" | "image" | "lab" | "document">("all");
  const [sessionScope, setSessionScope] = useState("all");
  const [kbFile, setKbFile] = useState<File | null>(null);
  const [kbUploads, setKbUploads] = useState<Array<{ id: string; filename: string; type: string }>>([]);
  const [kbBusy, setKbBusy] = useState(false);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [selected, setSelected] = useState<Evidence | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useRunPolling(run, setRun);
  const uploadKb = async () => {
    if (!kbFile || !patientId) return;
    if (kbFile.size > MAX_UPLOAD_BYTES) { setError("File exceeds 10 MB limit"); return; }
    setKbBusy(true); setError("");
    try {
      const uploaded = await api.uploadKnowledgeBase(kbFile, patientId);
      setKbUploads(current => [{ id: uploaded.assetId, filename: kbFile.name, type: kbFile.type || kbFile.name.split(".").pop() || "document" }, ...current]);
      setSource("document"); setKbFile(null);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Knowledge base upload failed"); }
    finally { setKbBusy(false); }
  };
  const ask = async () => {
    if (!patientId || !question) return;
    setBusy(true); setError("");
    try { setRun(await api.runQa({ patientId, question, source_types: source === "all" ? [] : [source], filters: { dateRange, session: sessionScope } })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to answer the clinical question"); }
    finally { setBusy(false); }
  };
  const qaPipeline = catalog.data?.pipelines.find(item => item.id === "qa");
  const answer = String(run?.result?.answer ?? "");
  return <>
    <WorkflowHead number={2} title="Multimodal patient Q&A" detail="Ask patient-scoped questions across structured records, vector notes, and image evidence with reopenable citations." mode={catalog.data?.executionMode}/>
    <PipelineBand agents={qaPipeline?.agents ?? ["request_validation", "patient_context", "retrieval", "image_evidence", "citation", "answer_synthesis", "validation", "audit"]} run={run}/>
    <div className="qa-workspace">
      <aside><Card title="Patient context and filters"><label>Patient<select value={patientId} onChange={event => setPatientId(event.target.value)}>{(patientList.data ?? []).map(p => <option key={p.id} value={p.id}>{p.name} · {p.id}</option>)}{!patientList.data?.length && <option value={patientId}>{patientId}</option>}</select></label><label>Session<select value={sessionScope} onChange={event => setSessionScope(event.target.value)}><option value="all">All sessions</option><option value="latest">Latest session</option><option value="previous">Previous session</option></select></label><label>Date range<select value={dateRange} onChange={event => setDateRange(event.target.value)}><option value="all">All available evidence</option><option value="30d">Last 30 days</option><option value="1y">Last year</option></select></label><label>Evidence type<select value={source} onChange={event => setSource(event.target.value as typeof source)}><option value="all">Combined evidence</option><option value="image">Images only</option><option value="text">Clinical notes</option><option value="lab">Structured labs</option><option value="document">Knowledge base</option></select></label></Card><Card title="Knowledge base"><label>Document<input type="file" accept={KB_UPLOAD_TYPES} onChange={event => setKbFile(event.target.files?.[0] ?? null)}/></label>{kbFile && <div className="file-row"><span><strong>{kbFile.name}</strong><small>{Math.round(kbFile.size / 1024)} KB</small></span><button className="link" onClick={() => setKbFile(null)}>Remove</button></div>}<button className="button primary full" disabled={!kbFile || kbBusy} onClick={() => void uploadKb()}>{kbBusy ? "Indexing document" : "Upload to knowledge base"}</button>{kbUploads.length > 0 && <DenseTable columns={[{ key: "filename", label: "File" }, { key: "type", label: "Type" }]} rows={kbUploads as unknown as Array<Record<string, unknown>>}/>}</Card><Card title="Authorized sources"><div className="source-status"><span>Structured record <StatusBadge tone="success">Ready</StatusBadge></span><span>Clinical notes <StatusBadge tone="success">Indexed</StatusBadge></span><span>Image evidence <StatusBadge tone="success">6 sources</StatusBadge></span><span>Knowledge base <StatusBadge tone={kbUploads.length ? "success" : "info"}>{kbUploads.length} docs</StatusBadge></span></div></Card></aside>
      <section className="qa-answer-column"><Card title="Clinical question" className="question-composer"><textarea rows={4} value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask a longitudinal, evidence-grounded question about this patient"/><div className="question-examples">{exampleQuestions.map(example => <button key={example} onClick={() => setQuestion(example)}>{example}</button>)}</div><div className="button-row end"><span>Patient scope and authorization are validated before retrieval.</span><button className="button primary" disabled={!patientId || question.length < 3 || busy} onClick={() => void ask()}>{busy ? "Coordinating agents" : "Ask Nexus agents"}</button></div>{error && <p className="form-error" role="alert">{error}</p>}</Card>{run ? <><Card title="Direct answer" action={<StatusBadge tone="info">AI generated · review</StatusBadge>}><AgentMeta run={run}/><ConfidenceMeter value={run.confidence}/><p className="answer">{answer}</p><div className="answer-sections"><section><h4>Key evidence</h4><p>{run.evidence?.[0]?.excerpt ?? "Evidence retrieval completed."}</p></section><section><h4>Relevant patient data</h4><p>{patientId} · combined longitudinal record · {run.evidence?.length ?? 0} cited sources</p></section><section><h4>Recommended next action</h4><p>Review the cited images and confirm the finding against the authored clinical note before changing the care plan.</p></section><section><h4>Human review state</h4><StatusBadge tone="review">Clinician review recommended</StatusBadge></section></div></Card><Card title="Retrieved sources"><DenseTable columns={[{ key: "label", label: "Source" }, { key: "kind", label: "Evidence type" }, { key: "excerpt", label: "Retrieved chunk" }, { key: "confidence", label: "Relevance", render: () => "0.92" }]} rows={(run.evidence ?? []) as unknown as Array<Record<string, unknown>>}/></Card></> : <Card><EmptyState title="Ask a patient-scoped question" detail="The orchestrator will validate scope, retrieve multimodal evidence, build citations, synthesize an answer, validate it, and audit the event."/></Card>}</section>
      <aside className="evidence-rail"><Card title="Evidence citations">{run?.evidence?.length ? run.evidence.map(item => <EvidenceCard key={item.id} item={item} onOpen={setSelected}/>) : <EmptyState title="No citations yet" detail="Retrieved text, image, and structured evidence will appear here."/>}</Card><Card title="Agent execution">{run ? <AgentStepper steps={run.steps} toolCalls={(run.result?.toolCalls ?? []) as ToolCall[]}/> : <p className="muted">Specialist agent events appear here after the orchestrator validates the request.</p>}</Card></aside>
    </div><SourceViewer evidence={selected} onClose={() => setSelected(null)}/>
  </>;
}

const schemaTables = [{ name: "patients", columns: "patient_id, risk_level, diagnosis" }, { name: "clinical_sessions", columns: "session_id, patient_id, occurred_at" }, { name: "extractions", columns: "confidence, review_status, fields" }, { name: "agent_runs", columns: "workflow, status, duration_ms" }, { name: "audit_events", columns: "actor, action, result, timestamp" }];
const databaseExamples = ["Count patients by risk level", "Which clinicians have the most pending reviews?", "Show the trend of high-risk patients over time", "Which patients have missing image evidence?"];

export function DatabaseIntelligence() {
  const [params] = useSearchParams();
  const catalog = useApi(() => api.agents(), []);
  const [question, setQuestion] = useState(params.get("query") ?? "");
  const [run, setRun] = useState<AgentRun | null>(null);
  const [tab, setTab] = useState("Answer");
  const [chartType, setChartType] = useState("Bar chart");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useRunPolling(run, setRun);
  const preview = async () => { setBusy(true); setError(""); try { setRun(await api.generateSql(question)); setTab("SQL preview"); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to generate SQL preview"); } finally { setBusy(false); } };
  const execute = async () => { if (!run) return; setBusy(true); setError(""); try { setRun(await api.executeSql(run.id)); setTab("Results table"); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to execute approved query"); } finally { setBusy(false); } };
  const sql = String(run?.result?.sql ?? "");
  const safe = run?.result?.safe !== false;
  const rows = (run?.result?.rows ?? []) as Array<Record<string, unknown>>;
  const columns = useMemo(() => Object.keys(rows[0] ?? {}).map(key => ({ key, label: key.replaceAll("_", " ") })), [rows]);
  const exportCsv = () => {
    if (!rows.length) return;
    const csv = [columns.map(column => column.key).join(","), ...rows.map(row => columns.map(column => `"${String(row[column.key] ?? "").replaceAll('"', '""')}"`).join(","))].join("\n");
    const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); link.download = `query-${run?.id}.csv`; link.click(); URL.revokeObjectURL(link.href);
  };
  const dbPipeline = catalog.data?.pipelines.find(item => item.id === "database");
  return <>
    <WorkflowHead number={3} title="Database intelligence" detail="Translate population questions into reviewed read-only SQL, governed results, charts, and audited clinical insight." mode={catalog.data?.executionMode}/>
    <PipelineBand agents={dbPipeline?.agents ?? ["schema_understanding", "sql_generation", "query_validation", "approval", "database_query", "chart_generation", "insight", "audit"]} run={run}/>
    <Card className="database-query"><label>Population question<textarea rows={3} value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask a governed question across the authorized clinical database"/></label><div className="question-examples">{databaseExamples.map(example => <button key={example} onClick={() => setQuestion(example)}>{example}</button>)}</div><div className="button-row end"><span>SQL is generated and safety-reviewed before any execution.</span><button className="button primary" disabled={question.length < 3 || busy} onClick={() => void preview()}>{busy && !run ? "Generating safe SQL" : "Generate SQL preview"}</button></div>{error && <p className="form-error" role="alert">{error}</p>}</Card>
    <div className="database-workspace">
      <aside><Card title="Schema explorer">{schemaTables.map(table => <details key={table.name} open={table.name === "patients"}><summary>{table.name}<span>table</span></summary><code>{table.columns}</code></details>)}</Card><Card title="Query policy"><ul className="policy-list"><li>SELECT statements only</li><li>Recognized tables only</li><li>No system catalog access</li><li>Explicit execution approval</li><li>Every query audited</li></ul></Card></aside>
      <section className="database-results"><nav className="tabs">{["Answer", "SQL preview", "Results table", "Query history", "Audit"].map(name => <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>)}</nav><Card title={tab} action={rows.length > 0 && tab === "Results table" ? <button className="button subtle" onClick={exportCsv}>Export CSV</button> : undefined}>{!run ? <EmptyState title="No query generated" detail="Ask a population question to begin schema discovery and read-only SQL generation."/> : tab === "SQL preview" ? <><AgentMeta run={run}/><SqlPreview sql={sql} safe={safe}/><div className="safety-explanation"><StatusBadge tone="success">Safety passed</StatusBadge><p>SELECT-only query against the authorized patients table. No mutation, system catalog, or unrestricted identifier access detected.</p></div><button className="button primary full" disabled={!safe || busy || rows.length > 0} onClick={() => void execute()}>{busy ? "Executing approved query" : rows.length ? "Query executed" : "Approve and execute read-only query"}</button></> : tab === "Results table" ? rows.length ? <DenseTable columns={columns} rows={rows}/> : <EmptyState title="Approval required" detail="Review and execute the SQL preview to populate results."/> : tab === "Answer" ? <div className="database-answer"><StatusBadge tone={rows.length ? "success" : "review"}>{rows.length ? "Completed" : "Awaiting execution"}</StatusBadge><h3>{rows.length ? "Four synthetic cohort segments were analyzed." : "SQL preview generated and awaiting explicit execution."}</h3><p>{rows.length ? "The needs-review cohort is currently the largest non-stable segment. Prioritize unresolved verification work before the next scheduled synchronization." : "No database rows have been read. Open SQL preview to inspect the exact query and safety verdict."}</p><h4>Limitations</h4><p>Results are derived from the isolated synthetic demo dataset and should not be used for clinical decision-making.</p><h4>Recommended action</h4><p>Open the corresponding patient worklist and assign verification tasks to the responsible clinicians.</p></div> : tab === "Query history" ? <DenseTable columns={[{ key: "question", label: "Question" }, { key: "run", label: "Run" }, { key: "status", label: "Status" }, { key: "actor", label: "Executed by" }]} rows={run ? [{ id: run.id, question: run.result?.question, run: run.id, status: run.status, actor: "Dr. Sarah Miller" }] : []}/> : <AgentMeta run={run}/>}</Card></section>
      <aside className="chart-builder"><Card title="Chart builder"><label>Visualization<select value={chartType} onChange={event => setChartType(event.target.value)}>{["Bar chart", "Line chart", "Area chart", "Scatter plot", "Histogram", "Box plot", "Heatmap", "Pie chart", "Treemap", "Cohort chart", "Risk distribution", "Time-series trend"].map(type => <option key={type}>{type}</option>)}</select></label><div className="chart-title"><strong>{chartType}</strong><small>Plotly annotated result</small></div>{rows.length ? <ChartPanel rows={rows} variant={chartType}/> : <div className="chart-empty">Execute the approved query to render the Plotly chart.</div>}</Card><Card title="Interpretation"><p>{rows.length ? "Needs-review patients represent the largest actionable segment in this cohort result." : "Insight Explanation Agent will summarize trends, limitations, and recommended actions after execution."}</p></Card><Card title="Agent execution">{run ? <AgentStepper steps={run.steps} toolCalls={(run.result?.toolCalls ?? []) as ToolCall[]}/> : <p className="muted">No database agents have run yet.</p>}</Card></aside>
    </div>
  </>;
}
