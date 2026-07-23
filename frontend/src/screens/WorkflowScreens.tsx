import { CSSProperties, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { AgentMeta, AgentStepper, Card, ChartPanel, ConfidenceMeter, ConfirmDialog, DenseTable, EmptyState, ErrorState, JsonViewer, LoadingState, pipelineDisplayName, ReviewChecklist, SourceViewer, SqlPreview, StatusBadge, useToast } from "../components";
import { InlineDiagram } from "../components/InlineDiagram";
import { useClinical } from "../context";
import { fallbackDatabaseExamples, syntheticExtractionOptionsForTenant } from "../fallbackData";
import { historyKey, loadTurns, saveTurns, WorkflowTurn } from "../runHistory";
import type { AgentRun, Evidence, ExtractionSource, SchemaTable, ToolCall } from "../types";
import { useApi } from "../useApi";

/** Anchor patient per demo tenant: a real generated-cohort record with
 * evidence across all three workflows (extraction, Q&A, database). */
const TENANT_DEFAULT_PATIENT: Record<string, string> = { "research-clinic": "PT-D00008", northstar: "PT-N00003" };

/** Resolve the workflow's starting patient: URL param, then the active
 * patient, then the demo showcase patient — real tenants start blank. */
function useDefaultPatient(param: string | null): string {
  const { patient, tenant } = useClinical();
  return param ?? patient?.id ?? (tenant.kind === "demo" ? TENANT_DEFAULT_PATIENT[tenant.id] ?? "" : "");
}

/** Patient ids differ across tenants, so a tenant switch while the screen is
 * mounted resets the selection instead of carrying a foreign id over. */
function useTenantPatientReset(setPatientId: (id: string) => void) {
  const { tenant } = useClinical();
  const previous = useRef(tenant.id);
  useEffect(() => {
    if (previous.current === tenant.id) return;
    previous.current = tenant.id;
    setPatientId(tenant.kind === "demo" ? TENANT_DEFAULT_PATIENT[tenant.id] ?? "" : "");
  }, [tenant.id]);
}

function preferredExtractionSource(options: ExtractionSource[], patientId: string): ExtractionSource | null {
  return options.find(option => option.patientId === patientId) ?? options[0] ?? null;
}

function WorkflowHead({ number, title, detail, mode = "local" }: { number: number; title: string; detail: string; mode?: string }) {
  return <header className="page-head workflow-head"><div><span className="eyebrow accent">GUIDED WORKFLOW {number}</span><h1>{title}</h1><p>{detail}</p></div><div className="runtime-state"><span className="pulse"/><div><strong>Nexus clinical AI</strong><small>{mode === "live" ? "Live AI execution" : "Deterministic demo mode"}</small></div></div></header>;
}

function useRunPolling(run: AgentRun | null, setRun: (run: AgentRun) => void) {
  useEffect(() => {
    if (!run || !["queued", "running"].includes(run.status)) return;
    const timer = window.setInterval(() => { void api.run(run.id).then(setRun).catch(() => undefined); }, 1200);
    return () => window.clearInterval(timer);
  }, [run?.id, run?.status, setRun]);
}

/** Live pipeline runs start "running" and update in place as useRunPolling
 * refetches them; without this, a turn logged from the initial response
 * would freeze at that snapshot instead of showing the run's real progress
 * and eventual answer. */
function useSyncRunIntoTurns<T extends { id: string; run: AgentRun }>(run: AgentRun | null, setTurns: (updater: (current: T[]) => T[]) => void, threadKey: string) {
  useEffect(() => {
    if (!run) return;
    setTurns(current => {
      if (!current.some(turn => turn.id === run.id)) return current;
      const updated = current.map(turn => turn.id === run.id ? { ...turn, run } : turn);
      saveTurns(threadKey, updated as unknown as WorkflowTurn[]);
      return updated;
    });
  }, [run]);
}

/** Restore a workflow's conversation thread when the screen mounts or its
 * scope changes: the in-memory store answers instantly for this browser
 * session, and backend GET /runs re-hydrates API-backed runs after reloads. */
function useTurnHistory(key: string, workflow: "extraction" | "qa" | "database", patientId: string | undefined, setTurns: (turns: WorkflowTurn[]) => void, setRun: (run: AgentRun | null) => void, hydrate = true) {
  useEffect(() => {
    const cached = loadTurns(key);
    setTurns(cached);
    setRun(cached.length ? cached[cached.length - 1].run : null);
    if (!hydrate) return;
    let cancelled = false;
    void api.runs(workflow, patientId).then(rows => {
      if (cancelled) return;
      const byId = new Map(cached.map(turn => [turn.id, turn]));
      rows.forEach(row => byId.set(row.id, { id: row.id, question: String(row.result?.question ?? ""), run: row }));
      const restored = [...byId.values()].sort((left, right) => String(left.run.createdAt ?? "").localeCompare(String(right.run.createdAt ?? "")));
      saveTurns(key, restored);
      setTurns(restored);
      setRun(restored.length ? restored[restored.length - 1].run : null);
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [key]);
}

const MAX_UPLOAD_BYTES = 10_000_000;
const ACCEPTED_UPLOAD_TYPES = "image/png,image/jpeg,image/webp,application/pdf";
const KB_UPLOAD_TYPES = ".pdf,.docx,.md,.txt,.json,.png,.jpg,.jpeg,.webp,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/markdown,text/plain,application/json,image/png,image/jpeg,image/webp";
const isObjectUrl = (value: string) => value.startsWith("blob:");

/** Human-authored titles and one-line descriptions for every specialist agent
 * across the extraction, Q&A, and database pipelines. Keyed without the
 * trailing "_agent" suffix so both full and short agent ids resolve. */
const AGENT_INFO: Record<string, { title: string; detail: string }> = {
  quality_assessor: { title: "Quality Assessment", detail: "Confirms the upload meets clarity and format thresholds before processing continues." },
  ocr_processor: { title: "OCR Processing", detail: "Extracts raw text and page layout from scanned or photographed documents." },
  vision_analyzer: { title: "Vision Analysis", detail: "Applies Gemini vision to interpret embedded images, charts, and annotations." },
  clinical_structuring: { title: "Clinical Structuring", detail: "Maps extracted text and image findings into structured clinical fields." },
  validation: { title: "Field Validation", detail: "Cross-checks structured fields against confidence thresholds and schemas." },
  extraction_critic: { title: "Extraction Critic", detail: "Cross-checks structured fields against the source evidence and confidence thresholds." },
  extraction_refiner: { title: "Extraction Refiner", detail: "Re-queries low-confidence fields against the source evidence to refine them." },
  clinical_review_gate: { title: "Clinician Review Gate", detail: "Holds every output for human approval before anything is persisted." },
  storage: { title: "Governed Storage", detail: "Writes approved fields to the relational store with full provenance." },
  vector_indexing: { title: "Vector Indexing", detail: "Adds approved findings to the patient's searchable record." },
  extraction_persistence: { title: "Extraction Persistence", detail: "Writes clinician-approved fields to the relational and vector stores." },
  audit: { title: "Audit Logging", detail: "Records an immutable audit trail entry for the completed run." },
  extraction_audit: { title: "Extraction Audit", detail: "Records an immutable audit trail entry for the completed run." },
  context_assembly: { title: "Context Assembly", detail: "Validates request scope and assembles the patient's longitudinal context." },
  evidence_retrieval: { title: "Evidence Retrieval", detail: "Searches the chart, clinical notes, and documents for evidence relevant to the question." },
  image_evidence: { title: "Image Evidence", detail: "Locates and attaches supporting visual evidence such as scans or charts." },
  citation_builder: { title: "Citation Builder", detail: "Builds traceable citations linking each claim back to its source evidence." },
  answer_synthesis: { title: "Answer Synthesis", detail: "Synthesizes a grounded, evidence-cited answer to the clinical question." },
  qa_audit: { title: "Audit Logging", detail: "Records the question, evidence, and answer to the audit trail." },
  schema_discovery: { title: "Schema Discovery", detail: "Identifies the approved tables and columns relevant to the question." },
  nl_to_sql: { title: "Natural Language to SQL", detail: "Translates the population question into a read-only SQL draft." },
  sql_validator: { title: "SQL Safety Validation", detail: "Confirms the query is SELECT-only and touches only authorized tables." },
  sql_preview_approval: { title: "SQL Preview Approval", detail: "Holds the drafted query for explicit approval before anything executes." },
  query_executor: { title: "Query Execution", detail: "Runs the approved query against the governed clinical database." },
  insight_chart: { title: "Insight & Charting", detail: "Summarizes results and renders the governed visualization." },
};

function describeAgent(agentId: string): { title: string; detail: string } {
  const key = agentId.replace(/_agent$/, "");
  return AGENT_INFO[key] ?? { title: key.split("_").map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" "), detail: "Specialist agent step in this workflow." };
}

function PipelineBand({ agents, run }: { agents: string[]; run: AgentRun | null }) {
  const stepStatuses = run?.steps?.map(step => step.status) ?? [];
  return <div className="pipeline-band">{agents.map((agent, index) => {
    // A step with no entry yet hasn't started — that's true regardless of
    // the overall run status, so it must never inherit "running"/"review"
    // from the run as a whole (every remaining agent would otherwise show
    // as active at once instead of one at a time as the run progresses).
    const status = stepStatuses[index] ?? (run?.status === "completed" ? "completed" : index === 0 && !run ? "queued" : "waiting");
    const state = status === "completed" ? "complete" : status === "running" ? "active" : status === "review" ? "review" : index === 0 && !run ? "ready" : "waiting";
    const label = state === "complete" ? "Complete" : state === "active" ? "Running" : state === "review" ? "Review" : state === "ready" ? "Ready" : "Waiting";
    const { title, detail } = describeAgent(agent);
    return <div key={agent} className={state}><span aria-label={label}/><strong>{title}</strong><small>{detail}</small></div>;
  })}</div>;
}

function WorkflowRunSpinner({ label, agents, detail }: { label: string; agents: string[]; detail: string }) {
  return <div className="workflow-run-spinner" role="status" aria-label={`${label} agents are working`}>
    <div className="workflow-spinner-orbit" aria-hidden="true"><span/><span/><span/></div>
    <div>
      <strong>{label} agents are working</strong>
      <p>{detail}</p>
      <div className="workflow-spinner-agents">{agents.slice(0, 6).map(agent => <span key={agent}>{describeAgent(agent).title}</span>)}</div>
    </div>
  </div>;
}

type ParsedPage = { pageNumber?: number; text?: string; imageCount?: number; tableCount?: number; textBlocks?: Array<{ text?: string; bbox?: number[] }> };
type ParsedTable = { tableId?: string; pageNumber?: number; rowCount?: number; columnCount?: number; rows?: unknown[][] };
type ParsedImage = { imageId?: string; pageNumber?: number | null; mimeType?: string; width?: number; height?: number; format?: string; role?: string };
type PacketRecord = { patientId?: string; patientName?: string; encounterDate?: string; fields?: Array<Record<string, unknown>> };

function readArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

function ParsedEvidencePanel({ extracted }: { extracted: Record<string, unknown> }) {
  const pages = readArray<ParsedPage>(extracted.pages);
  const tables = readArray<ParsedTable>(extracted.tables);
  const images = readArray<ParsedImage>(extracted.images);
  const packetRecords = readArray<PacketRecord>(extracted.packetRecords);
  const warnings = readArray<string>(extracted.warnings);
  const dimensions = extracted.dimensions as { width?: number; height?: number } | undefined;
  const tableRows = tables.flatMap(table => (table.rows ?? []).map((row, rowIndex) => ({ id: `${table.tableId ?? "table"}-${rowIndex}`, table: table.tableId ?? "table", page: table.pageNumber ?? "-", row: rowIndex + 1, cells: row.map(cell => String(cell ?? "")).join(" | ") })));
  return <Card title="Parsed evidence"><dl className="compact-facts">{extracted.type != null && <div><dt>Type</dt><dd>{String(extracted.type)}</dd></div>}{extracted.pageCount != null && <div><dt>Pages</dt><dd>{String(extracted.pageCount)}</dd></div>}{extracted.imageCount != null && <div><dt>Images</dt><dd>{String(extracted.imageCount)}</dd></div>}{tables.length > 0 && <div><dt>Tables</dt><dd>{tables.length}</dd></div>}{dimensions && <div><dt>Dimensions</dt><dd>{String(dimensions.width ?? "-")}x{String(dimensions.height ?? "-")}</dd></div>}</dl>{warnings.length > 0 && <div className="parse-warnings">{warnings.map(warning => <StatusBadge key={warning} tone="warning">{warning.replaceAll("_", " ")}</StatusBadge>)}</div>}{extracted.thumbnail != null && String(extracted.thumbnail) && <img className="parsed-thumb" src={`data:image/png;base64,${String(extracted.thumbnail)}`} alt="Document thumbnail"/>}{packetRecords.length > 0 && <details className="parsed-section" open><summary>Five-patient packet map</summary><DenseTable columns={[{ key: "record", label: "Record" }, { key: "patient", label: "Patient" }, { key: "encounter", label: "Encounter" }, { key: "fields", label: "Fields" }, { key: "scope", label: "Review scope" }]} rows={packetRecords.map((record, index) => ({ id: record.patientId ?? index, record: index + 1, patient: `${record.patientName ?? "Patient"} (${record.patientId ?? "-"})`, encounter: record.encounterDate ?? "-", fields: record.fields?.length ?? 0, scope: record.patientId === extracted.selectedPatientId ? "Selected" : "In packet" }))}/></details>}{extracted.textPreview != null && String(extracted.textPreview) && <details className="text-preview-details" open><summary>Selected patient text</summary><pre className="text-preview">{String(extracted.textPreview)}</pre></details>}{pages.length > 0 && <details className="parsed-section"><summary>Page text and blocks</summary>{pages.map(page => <article key={page.pageNumber ?? page.text} className="parsed-page"><header><strong>Page {page.pageNumber ?? "-"}</strong><span>{page.imageCount ?? 0} images - {page.tableCount ?? 0} tables</span></header>{page.text && <pre>{page.text}</pre>}{readArray<{ text?: string }>(page.textBlocks).slice(0, 4).map((block, index) => <p key={index}>{block.text}</p>)}</article>)}</details>}{images.length > 0 && <details className="parsed-section"><summary>Image metadata</summary><DenseTable columns={[{ key: "imageId", label: "Image" }, { key: "pageNumber", label: "Page" }, { key: "mimeType", label: "Type" }, { key: "size", label: "Size" }, { key: "role", label: "Role" }]} rows={images.map((image, index) => ({ id: image.imageId ?? index, imageId: image.imageId ?? "source", pageNumber: image.pageNumber ?? "-", mimeType: image.mimeType ?? image.format ?? "-", size: image.width && image.height ? `${image.width}x${image.height}` : "-", role: image.role ?? "embedded" }))}/></details>}{tableRows.length > 0 && <details className="parsed-section" open><summary>Extracted tables</summary><DenseTable columns={[{ key: "table", label: "Table" }, { key: "page", label: "Page" }, { key: "row", label: "Row" }, { key: "cells", label: "Cells" }]} rows={tableRows}/></details>}</Card>;
}

function confidenceForField(field: string, extracted: Record<string, unknown> | null, fallback: number): number {
  const extractedFields = readArray<Record<string, unknown>>(extracted?.fields);
  const match = extractedFields.find(item => item.field_name === field || item.label === field || item.name === field);
  const raw = Number(match?.confidence ?? fallback / 100);
  if (!Number.isFinite(raw)) return fallback;
  return Math.max(0, Math.min(100, raw <= 1 ? Math.round(raw * 100) : Math.round(raw)));
}

function ExtractionVisualBoard({ preview, sourceLabel, sourceIsImage, run, extracted, fieldRows, onOpen }: { preview: string; sourceLabel: string; sourceIsImage: boolean; run: AgentRun | null; extracted: Record<string, unknown> | null; fieldRows: Array<Record<string, unknown>>; onOpen: (item: Evidence) => void }) {
  const pages = readArray<ParsedPage>(extracted?.pages);
  const tables = readArray<ParsedTable>(extracted?.tables);
  const images = readArray<ParsedImage>(extracted?.images);
  const confidence = Math.round((run?.confidence ?? 0.88) * 100);
  const visualFields = fieldRows.slice(0, 7).map(row => ({ id: String(row.id), field: String(row.field), value: String(row.value ?? ""), confidence: confidenceForField(String(row.field), extracted, confidence) }));
  const evidence = run?.evidence ?? [];
  return <Card title="Visual extraction board" className="visual-board extraction-visual-board">
    <div className="visual-board-grid">
      <figure className="source-frame">{sourceIsImage && preview ? <img src={preview} alt={sourceLabel}/> : <div className="document-visual"><span>PDF</span><strong>{sourceLabel || "Clinical packet"}</strong><small>{pages.length || Number(extracted?.pageCount ?? 1)} page source</small></div>}<figcaption>{sourceLabel || "Selected evidence source"}</figcaption></figure>
      <div className="visual-stat-stack">
        <div><strong>{pages.length || Number(extracted?.pageCount ?? 1)}</strong><span>Pages</span></div>
        <div><strong>{tables.length || Number(extracted?.tableCount ?? 0)}</strong><span>Tables</span></div>
        <div><strong>{images.length || Number(extracted?.imageCount ?? 0)}</strong><span>Images</span></div>
        <div><strong>{confidence}%</strong><span>Confidence</span></div>
      </div>
    </div>
    <div className="field-confidence-map" aria-label="Extraction confidence visualization">{visualFields.length ? visualFields.map(item => <div key={item.id}><label><span>{item.field}</span><b>{item.confidence}%</b></label><i style={{ "--bar": `${item.confidence}%` } as CSSProperties}/><small>{item.value}</small></div>) : <EmptyState title="No fields visualized yet" detail="Run extraction to populate field confidence bars."/>}</div>
    {evidence.length > 0 && <div className="visual-citation-strip">{evidence.map(item => <button key={item.id} onClick={() => onOpen(item)}><span>{item.kind}</span>{item.label}</button>)}</div>}
  </Card>;
}

function QaVisualBoard({ evidence, showImage, kbRows, summaryRows, onOpen }: { evidence: Evidence[]; showImage: string; kbRows: Array<Record<string, unknown>>; summaryRows: Array<Record<string, unknown>>; onOpen: (item: Evidence) => void }) {
  const sourceKinds = evidence.reduce<Record<string, number>>((acc, item) => {
    acc[item.kind] = (acc[item.kind] ?? 0) + 1;
    return acc;
  }, {});
  const totalSources = Math.max(1, evidence.length);
  const sourceMix = Object.entries(sourceKinds).map(([kind, count]) => ({ kind, count, percent: Math.max(8, Math.round((count / totalSources) * 100)) }));
  return <Card title="Visual retrieval map" className="visual-board qa-visual-board">
    <div className="qa-visual-map">
      <figure className="source-frame qa-visual-source">{showImage ? <img src={showImage} alt="Primary cited visual source"/> : <div className="document-visual"><span>QA</span><strong>Patient record</strong><small>{kbRows.length || evidence.length} indexed source{(kbRows.length || evidence.length) === 1 ? "" : "s"}</small></div>}<figcaption>Primary cited evidence</figcaption></figure>
      <div className="visual-stat-stack">
        <div><strong>{evidence.length}</strong><span>Citations</span></div>
        <div><strong>{kbRows.length}</strong><span>Indexed files</span></div>
        <div><strong>{summaryRows.length}</strong><span>Findings</span></div>
        <div><strong>{sourceMix.length || 1}</strong><span>Source types</span></div>
      </div>
    </div>
    <div className="source-mix-bars" aria-label="Retrieved source mix">{sourceMix.length ? sourceMix.map(item => <div key={item.kind}><label><span>{item.kind}</span><b>{item.count}</b></label><i style={{ "--bar": `${item.percent}%` } as CSSProperties}/></div>) : <EmptyState title="No retrieved sources visualized yet" detail="Ask a patient-scoped question to populate the retrieval map."/>}</div>
    {evidence.length > 0 && <div className="citation-flow" aria-label="Citation path">{evidence.slice(0, 5).map((item, index) => <button key={item.id} onClick={() => onOpen(item)}><span>{index + 1}</span><strong>{item.label}</strong><small>{item.kind}</small></button>)}</div>}
  </Card>;
}

export function Extraction() {
  const [params] = useSearchParams();
  const { tenant } = useClinical();
  const catalog = useApi(() => api.agents(), [tenant.id]);
  const demoMode = tenant.kind === "demo";
  const sourceCatalog = useApi(() => demoMode ? api.extractionSources() : Promise.resolve([] as ExtractionSource[]), [tenant.id, demoMode]);
  const tenantSyntheticOptions = syntheticExtractionOptionsForTenant(tenant.id);
  const defaultPatientId = useDefaultPatient(params.get("patient"));
  const initialSyntheticSource = preferredExtractionSource(tenantSyntheticOptions, defaultPatientId);
  const [patientId, setPatientId] = useState(defaultPatientId || initialSyntheticSource?.patientId || "");
  useTenantPatientReset(setPatientId);
  const [file, setFile] = useState<File | null>(null);
  const [syntheticSource, setSyntheticSource] = useState<ExtractionSource | null>(initialSyntheticSource);
  const [preview, setPreview] = useState("");
  const [run, setRun] = useState<AgentRun | null>(null);
  const [fieldEdits, setFieldEdits] = useState<Record<string, unknown>>({});
  const [outputTab, setOutputTab] = useState("Extracted fields");
  const [wizardStep, setWizardStep] = useState<"source" | "execution" | "review">("source");
  const [extracted, setExtracted] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const [confirmReject, setConfirmReject] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const toast = useToast();
  const sourceOptions = demoMode && sourceCatalog.data?.length ? sourceCatalog.data : tenantSyntheticOptions;
  const threadKey = historyKey(tenant.id, "extraction");
  useRunPolling(run, setRun);
  useTurnHistory(threadKey, "extraction", undefined, () => undefined, restored => {
    setRun(restored);
    const content = restored?.result?.extractedContent;
    if (content && typeof content === "object") setExtracted(content as Record<string, unknown>);
    else if (!restored) setExtracted(null);
  });
  const record = (next: AgentRun) => {
    const others = loadTurns(threadKey).filter(turn => turn.id !== next.id);
    saveTurns(threadKey, [...others, { id: next.id, question: String(next.result?.patientId ?? patientId), run: next }]);
  };
  useEffect(() => {
    const fields = run?.result?.fields;
    if (fields && typeof fields === "object" && !Array.isArray(fields)) setFieldEdits(fields as Record<string, unknown>);
  }, [run?.id, run?.status]);
  useEffect(() => () => { if (isObjectUrl(preview)) URL.revokeObjectURL(preview); }, [preview]);
  const select = (next: File | null) => {
    if (isObjectUrl(preview)) URL.revokeObjectURL(preview);
    if (next && next.size > MAX_UPLOAD_BYTES) { setError("File exceeds 10 MB limit"); setFile(null); setPreview(""); return; }
    setError(""); setFile(next); setPreview(next ? URL.createObjectURL(next) : ""); setRun(null); setFieldEdits({}); setExtracted(null); setWizardStep("source");
  };
  const drop = (event: DragEvent<HTMLLabelElement>) => { event.preventDefault(); setDragging(false); select(event.dataTransfer.files?.[0] ?? null); };
  const extractedFromSource = (option: ExtractionSource) => option.extracted ?? {
    type: option.contentType === "application/pdf" ? "document" : "image",
    documentType: "Enterprise five-patient clinical packet",
    filename: option.filename,
    pageCount: option.patientsInFile ?? 1,
    textPreview: `${option.filename} contains ${option.patientsInFile ?? 1} patient records for governed extraction review.`,
    fields: option.expectedFields ?? [],
  };
  const selectSynthetic = (option: ExtractionSource) => {
    setSyntheticSource(option);
    setPatientId(option.patientId);
    setPreview(option.previewUrl);
    setExtracted(extractedFromSource(option));
    setRun(null);
    setFieldEdits({});
    setError("");
    setWizardStep("source");
  };
  useEffect(() => {
    if (!demoMode) return;
    const first = sourceOptions[0];
    if (!first) return;
    const preferred = preferredExtractionSource(sourceOptions, defaultPatientId) ?? first;
    if (syntheticSource && sourceOptions.some(option => option.assetId === syntheticSource.assetId)) {
      if (patientId !== syntheticSource.patientId) setPatientId(syntheticSource.patientId);
      return;
    }
    setSyntheticSource(preferred);
    setPatientId(preferred.patientId);
    setPreview(preferred.previewUrl);
    setExtracted(extractedFromSource(preferred));
  }, [demoMode, sourceCatalog.data?.length, tenant.id]);
  const start = async () => {
    if (demoMode) {
      const source = syntheticSource ?? sourceOptions[0];
      if (!source) return;
      setBusy(true); setError("");
      setWizardStep("execution");
      try {
        setExtracted(extractedFromSource(source));
        setPatientId(source.patientId);
        const next = await api.runSyntheticExtraction(source.assetId, source.patientId);
        const content = next.result?.extractedContent;
        if (content && typeof content === "object") setExtracted(content as Record<string, unknown>);
        setRun(next); record(next); setWizardStep("execution");
      }
      catch (reason) { setError(reason instanceof Error ? reason.message : "Document processing failed"); }
      finally { setBusy(false); }
      return;
    }
    if (!file) return;
    setBusy(true); setError("");
    setWizardStep("execution");
    try {
      const asset = await api.upload(file, patientId.trim());
      if (asset.extracted) setExtracted(asset.extracted as Record<string, unknown>);
      // Live uploads may resolve the patient from the document itself (blank
      // field + detected on-document id); adopt the effective id so the run,
      // the field edits, and the visible input stay aligned.
      const effectivePatientId = asset.patientId || patientId;
      if (effectivePatientId !== patientId) { setPatientId(effectivePatientId); toast(`Patient ID ${effectivePatientId} detected from document`, "info"); }
      const next = await api.runExtraction(asset.assetId, effectivePatientId);
      setRun(next); record(next); setWizardStep("execution");
    }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Extraction failed"); }
    finally { setBusy(false); }
  };
  const decide = async (decision: "approved" | "rejected") => {
    if (!run) return;
    setBusy(true); setError("");
    try {
      const next = await api.review(run.id, decision, fieldEdits);
      setRun(next); record(next);
      toast(decision === "approved" ? "Extraction approved and synced" : "Extraction rejected; nothing persisted", decision === "approved" ? "success" : "info");
    }
    catch (reason) { const message = reason instanceof Error ? reason.message : "Review decision failed"; setError(message); toast(message, "error"); }
    finally { setBusy(false); }
  };
  const onDecision = (decision: "approved" | "rejected") => {
    if (decision === "rejected") { setConfirmReject(true); return; }
    void decide(decision);
  };
  const extractionPipeline = catalog.data?.pipelines.find(item => item.id === "extraction");
  const agents = extractionPipeline?.agents ?? ["quality_assessor_agent", "ocr_processor_agent", "vision_analyzer_agent", "clinical_structuring_agent", "extraction_critic_agent", "extraction_refiner_agent", "clinical_review_gate_agent", "extraction_persistence_agent", "extraction_audit_agent"];
  const runConfidence = Math.round((run?.confidence ?? 0.88) * 100);
  const fieldRows = Object.entries(fieldEdits).map(([field, value]) => ({ id: field, field, value, confidence: runConfidence, review: runConfidence < 75 ? "Review" : "Pass" }));
  const receipts = (run?.result?.storageReceipts ?? []) as Array<{ target: string; status: string; receiptId?: string }>;
  const extractionWaiting = busy || ["queued", "running"].includes(run?.status ?? "");
  // Once the pipeline reaches the clinician gate (or finishes), jump the
  // wizard forward automatically. Tracked against the *previous* status so
  // this only fires on the queued/running -> review transition - otherwise
  // a manual step-back to re-check the agent run would get bounced forward
  // again on the next status poll.
  const previousRunStatus = useRef<string | undefined>(undefined);
  useEffect(() => {
    const previous = previousRunStatus.current;
    previousRunStatus.current = run?.status;
    if (run && previous !== "review" && previous !== "completed" && ["review", "completed", "failed"].includes(run.status)) setWizardStep("review");
  }, [run?.status]);
  const wizardSteps = [
    { id: "source", label: "Source", detail: demoMode ? syntheticSource?.filename ?? "Choose source" : file?.name ?? "Upload evidence", disabled: false },
    { id: "execution", label: "Agents", detail: run ? run.status : "Run source first", disabled: !run },
    { id: "review", label: "Review & approve", detail: run ? (run.status === "completed" ? "Synced" : `${fieldRows.length} fields`) : "Awaiting run", disabled: !run },
  ] as const;
  return <>
    <WorkflowHead number={1} title="Clinical evidence extraction" detail="Upload or select enterprise clinical packets, inspect every specialist agent, edit structured fields, and approve governed persistence." mode={catalog.data?.executionMode}/>
    {catalog.error && <ErrorState error={catalog.error} retry={catalog.refresh}/>}
    <nav className="wizard-steps" aria-label="Extraction wizard progress">{wizardSteps.map((step, index) => <button key={step.id} className={wizardStep === step.id ? "active" : ""} disabled={step.disabled} onClick={() => setWizardStep(step.id)}><span>{index + 1}</span><strong>{step.label}</strong><small>{step.detail}</small></button>)}</nav>
    <div className={`extraction-layout wizard-layout step-${wizardStep}`}>
      <aside className="extraction-source">
        <Card title="1. Source and patient"><label>Patient ID<input value={patientId} onChange={event => setPatientId(event.target.value)} placeholder="Patient ID (auto-detected when blank)" disabled={demoMode}/></label>{demoMode ? <div className="synthetic-source-panel"><div className="synthetic-preview">{syntheticSource ? <img src={syntheticSource.previewUrl} onError={event => { event.currentTarget.src = syntheticSource.fallbackPreviewUrl ?? "/evidence/demo-retinopathy-intake.png"; }} alt={syntheticSource.label}/> : <EmptyState title="No record packet selected"/>}</div><div className="synthetic-source-grid">{sourceOptions.map(option => <button key={option.assetId} className={syntheticSource?.assetId === option.assetId ? "active" : ""} onClick={() => selectSynthetic(option)}><strong>{option.label}</strong><small>{option.patientId} - {option.packetFilename ?? option.filename}</small><small>{option.contentType} - {option.patientsInFile ?? 1} patients/file</small></button>)}</div><p className="muted">Demo mode uses generated enterprise PDF packets with five patients per source file and patient-level previews.</p></div> : <><label className={`upload-zone ${preview ? "has-file" : ""} ${dragging ? "dragging" : ""}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={drop}><input type="file" accept={ACCEPTED_UPLOAD_TYPES} onChange={event => select(event.target.files?.[0] ?? null)}/>{preview ? <img src={preview} alt="Selected clinical source preview"/> : <><span className="upload-icon">Upload</span><strong>Drop image or PDF here</strong><small>or click to browse. PNG, JPEG, WEBP, PDF. 10 MB max.</small></>}</label>{file && <div className="file-row"><span><strong>{file.name}</strong><small>{Math.round(file.size / 1024)} KB. Ready for quality assessment.</small></span><button className="link" onClick={() => select(null)}>Remove</button></div>}</>}<button className="button primary full" disabled={demoMode ? !syntheticSource || busy : !file || busy} onClick={() => void start()}>{busy ? "Running specialist agents" : demoMode ? "Run selected packet" : "Process document"}</button>{error && <p className="form-error" role="alert">{error}</p>}</Card>
        <Card title="Source controls"><dl className="compact-facts"><div><dt>Authorization</dt><dd>Patient scoped</dd></div><div><dt>Retention</dt><dd>Session only</dd></div><div><dt>Input mode</dt><dd>Multimodal</dd></div><div><dt>PHI</dt><dd>Synthetic only</dd></div></dl></Card>
        <InlineDiagram id="16-document-ingestion-flow" title="Extraction architecture"/>
        {extracted && <ParsedEvidencePanel extracted={extracted}/>}
      </aside>
      <section className="extraction-center">
        {extractionWaiting && <WorkflowRunSpinner label="Extraction" agents={agents} detail="Quality, OCR, vision, structuring, validation, and review agents are preparing the clinical evidence package."/>}
        <Card title="2. Agent execution" action={run && <StatusBadge tone={run.status}>{run.status}</StatusBadge>}>{run ? <><PipelineBand agents={agents} run={run}/><AgentMeta run={run}/><AgentStepper steps={run.steps} toolCalls={(run.result?.toolCalls ?? []) as ToolCall[]}/></> : <EmptyState title="Pipeline ready" detail="Select a document to check its quality, read the contents, structure the findings, and route them for clinician review."/>}</Card>
        <ExtractionVisualBoard preview={preview || syntheticSource?.previewUrl || ""} sourceLabel={demoMode ? syntheticSource?.filename ?? "Clinical packet" : file?.name ?? "Uploaded evidence"} sourceIsImage={demoMode || Boolean(file?.type.startsWith("image/"))} run={run} extracted={extracted} fieldRows={fieldRows} onOpen={setSelectedEvidence}/>
        <nav className="tabs output-tabs">{["Extracted fields", "Structured JSON", "Relational mapping", "Vector status"].map(name => <button key={name} className={outputTab === name ? "active" : ""} onClick={() => setOutputTab(name)}>{name}</button>)}</nav>
        <Card title="3. Structured clinical output">{!run ? <EmptyState title="Awaiting agent output"/> : outputTab === "Extracted fields" ? <div className="editable-fields"><DenseTable columns={[{ key: "field", label: "Clinical field" }, { key: "value", label: "Extracted value", render: row => <input aria-label={`Edit ${String(row.field)}`} disabled={run.status === "completed"} value={String(fieldEdits[String(row.field)] ?? "")} onChange={event => setFieldEdits(current => ({ ...current, [String(row.field)]: event.target.value }))}/> }, { key: "confidence", label: "Confidence", render: row => { const c = Number(row.confidence); return <span className={c < 75 ? "confidence-low" : c < 90 ? "confidence-mid" : "confidence-high"}>{c}%</span>; } }, { key: "review", label: "Validation", render: row => <StatusBadge tone={row.review === "Pass" ? "success" : "review"}>{String(row.review)}</StatusBadge> }]} rows={fieldRows}/></div> : outputTab === "Structured JSON" ? <JsonViewer value={{ patientId, source: demoMode ? syntheticSource?.filename : file?.name, fields: fieldEdits, confidence: run.confidence, humanReview: run.status }}/>: outputTab === "Relational mapping" ? <DenseTable columns={[{ key: "field", label: "JSON field" }, { key: "table", label: "Table" }, { key: "column", label: "Column" }, { key: "status", label: "Mapping" }]} rows={fieldRows.map(row => ({ id: row.id, field: row.field, table: "session_extractions", column: row.field.replaceAll(/([A-Z])/g, "_$1").toLowerCase(), status: "Ready" }))}/>: <div className="vector-preview"><StatusBadge tone={run.status === "completed" ? "success" : "review"}>{run.status === "completed" ? "Indexed" : "Waiting for approval"}</StatusBadge><code>vertex://clinical-evidence/{run.id}</code><p>Text and image embeddings · 768 dimensions · patient-scoped namespace</p></div>}</Card>
      </section>
      <aside className="extraction-review">
        {run ? <><Card title="Confidence and provenance"><ConfidenceMeter value={run.confidence}/><dl className="compact-facts"><div><dt>Agent system</dt><dd>{pipelineDisplayName(run.agentName)}</dd></div><div><dt>Audit ID</dt><dd>{run.auditId}</dd></div><div><dt>Trace ID</dt><dd>{run.traceId}</dd></div><div><dt>Evidence</dt><dd>{run.evidence?.length ?? 0} source</dd></div></dl><EvidenceCitationList evidence={run.evidence ?? []} onOpen={setSelectedEvidence} title="Evidence sources for this run"/></Card><ReviewChecklist disabled={run.status === "completed" || busy} onRerun={() => void start()} onDecision={onDecision}/><Card title="Storage and audit"><div className="receipt-list">{["json", "relational", "vector", "audit"].map(target => { const receipt = receipts.find(item => item.target === target); const synced = run.status === "completed" && (target === "audit" || receipt?.status === "synced"); return <div key={target}><span>{target}</span><StatusBadge tone={synced ? "success" : "review"}>{synced ? "synced" : "pending review"}</StatusBadge>{receipt?.receiptId && <code>{receipt.receiptId}</code>}</div>; })}</div></Card></> : <Card title="Human review boundary"><p>Extracted values remain editable and unpersisted until all verification checks are complete.</p><ul className="policy-list"><li>No automatic clinical decisions</li><li>Field-level confidence visible</li><li>Evidence remains reopenable</li><li>Every action is audited</li></ul></Card>}
      </aside>
    </div>
    <ConfirmDialog open={confirmReject} title="Reject this extraction?" detail="The extracted values will be discarded and nothing is persisted to clinical storage. This is logged to the audit trail." confirmLabel="Reject output" onConfirm={() => { setConfirmReject(false); void decide("rejected"); }} onCancel={() => setConfirmReject(false)}/>
    <SourceViewer evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)}/>
  </>;
}

const exampleQuestions =["What changed in this patient's condition over the last 90 days?", "Which recent lab results are outside their reference ranges?", "Is the medication list consistent with the documented diagnoses?", "Summarize the imaging findings and their impact on the care plan."];

function EvidenceCitationList({ evidence, onOpen, title = "Evidence cited in this answer" }: { evidence: Evidence[]; onOpen: (item: Evidence) => void; title?: string }) {
  if (!evidence.length) return null;
  return <div className="inline-citations" aria-label="Inline evidence citations">
    <h4>{title}</h4>
    <div className="citation-chip-row">{evidence.map((item, index) => <button key={item.id} onClick={() => onOpen(item)}><span>[{index + 1}]</span>{item.label}</button>)}</div>
    <div className="citation-detail-list">{evidence.map((item, index) => <button key={item.id} className="citation-detail" onClick={() => onOpen(item)}><strong>[{index + 1}] {item.label}</strong><small>{item.kind}</small><p>{item.excerpt ?? "Source available for review."}</p></button>)}</div>
  </div>;
}

type QaTab = "Ask" | "Knowledge base" | "Document library" | "Response evidence";

export function PatientQa() {
  const [params] = useSearchParams();
  const { tenant } = useClinical();
  const catalog = useApi(() => api.agents(), [tenant.id]);
  const patientList = useApi(() => api.patients(), [tenant.id]);
  const [patientId, setPatientId] = useState(useDefaultPatient(params.get("patient")));
  useTenantPatientReset(setPatientId);
  const [question, setQuestion] = useState(params.get("query") ?? "");
  const [dateRange, setDateRange] = useState("all");
  const [source, setSource] = useState<"all" | "text" | "image" | "lab" | "document">("all");
  const [sessionScope, setSessionScope] = useState("all");
  const [qaTab, setQaTab] = useState<QaTab>("Ask");
  const [kbFile, setKbFile] = useState<File | null>(null);
  const [kbBusy, setKbBusy] = useState(false);
  const [kbDragging, setKbDragging] = useState(false);
  const [run, setRun] = useState<AgentRun | null>(null);
  const [turns, setTurns] = useState<WorkflowTurn[]>([]);
  const [selected, setSelected] = useState<Evidence | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const demoMode = tenant.kind === "demo";
  const kbAssets = useApi(() => api.knowledgeBase(demoMode ? undefined : patientId), [demoMode, patientId]);
  const qaTabs: QaTab[] = demoMode ? ["Ask", "Document library", "Response evidence"] : ["Ask", "Knowledge base", "Response evidence"];
  const threadKey = historyKey(tenant.id, "qa", patientId);
  // Tenants ship different patient rosters; snap the selection to a real
  // patient whenever the loaded list no longer contains the current id.
  // Live tenants accept free-typed ids (new patients enter through Q&A and
  // extraction uploads), so only an empty selection snaps to the roster.
  useEffect(() => {
    const list = patientList.data ?? [];
    if (list.length && (demoMode ? !list.some(item => item.id === patientId) : !patientId)) setPatientId(list[0].id);
  }, [patientList.data]);
  useRunPolling(run, setRun);
  useSyncRunIntoTurns(run, setTurns, threadKey);
  // Threads are patient-scoped: without a patient there is nothing to
  // hydrate, and restoring unscoped runs would blend patients' threads.
  useTurnHistory(threadKey, "qa", patientId || undefined, setTurns, setRun, Boolean(patientId));
  const selectKbFile = (next: File | null) => {
    if (next && next.size > MAX_UPLOAD_BYTES) { setError("File exceeds 10 MB limit"); setKbFile(null); return; }
    setError(""); setKbFile(next);
  };
  const dropKb = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault(); setKbDragging(false); selectKbFile(event.dataTransfer.files?.[0] ?? null);
  };
  const uploadKb = async () => {
    if (demoMode) return;
    if (!kbFile || !patientId) return;
    if (kbFile.size > MAX_UPLOAD_BYTES) { setError("File exceeds 10 MB limit"); return; }
    setKbBusy(true); setError("");
    try {
      await api.uploadKnowledgeBase(kbFile, patientId);
      setSource(kbFile.type.startsWith("image/") ? "image" : "document");
      setKbFile(null);
      setQaTab("Knowledge base");
      await kbAssets.refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Knowledge base upload failed"); }
    finally { setKbBusy(false); }
  };
  const ask = async () => {
    if (!patientId || !question) return;
    setBusy(true); setError("");
    try {
      const next = await api.runQa({ patientId, question, source_types: source === "all" ? [] : [source], filters: { dateRange, session: sessionScope } });
      setRun(next);
      setTurns(current => { const updated = [...current, { id: next.id, question, run: next }]; saveTurns(threadKey, updated); return updated; });
      setQaTab("Response evidence");
    }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to answer the clinical question"); }
    finally { setBusy(false); }
  };
  const qaPipeline = catalog.data?.pipelines.find(item => item.id === "qa");
  const answer = String(run?.result?.answer ?? "");
  const evidence = run?.evidence ?? [];
  const kbRows = (kbAssets.data ?? []).map(asset => ({ id: asset.assetId, file: asset.filename, type: asset.contentType.split("/").pop() ?? "file", size: `${Math.max(1, Math.round(asset.sizeBytes / 1024))} KB`, indexed: asset.createdAt.slice(0, 10), patient: asset.patientId, preview: asset.previewUrl ? "Open" : "Parsed text" }));
  // Demo mode fetches the whole workspace's knowledge base (not patient-scoped
  // like the live tenant's call), so the Ask tab's "indexed for this patient"
  // note must filter by patientId itself rather than trusting kbAssets.data.length.
  const patientKbCount = (kbAssets.data ?? []).filter(asset => asset.patientId === patientId).length;
  const summaryRows = ((run?.result?.summaryRows ?? []) as Array<Record<string, unknown>>);
  const imageEvidence = run?.result?.imageEvidence as Evidence | undefined;
  const answerSections = (run?.result?.answerSections ?? {}) as { keyEvidence?: string; recommendedAction?: string; limitations?: string };
  const showImage = imageEvidence?.sourceUrl || evidence.find(item => item.kind === "image" && item.sourceUrl)?.sourceUrl;
  const qaAgents = qaPipeline?.agents ?? ["context_assembly_agent", "evidence_retrieval_agent", "image_evidence_agent", "citation_builder_agent", "answer_synthesis_agent", "qa_audit_agent"];
  const qaWaiting = busy || ["queued", "running"].includes(run?.status ?? "");
  const responseEvidence = run ? <><Card title="Response package" action={<StatusBadge tone="info">Answer + table + visual evidence</StatusBadge>}><AgentMeta run={run}/><p className="answer">{answer || "The answer agent completed and returned cited evidence for review."}</p>{showImage && <figure className="answer-image"><img src={showImage} alt="Cited visual evidence"/><figcaption>Visual evidence returned with the answer</figcaption></figure>}{summaryRows.length > 0 ? <DenseTable columns={[{ key: "citation", label: "Citation" }, { key: "file", label: "File" }, { key: "type", label: "Type" }, { key: "finding", label: "Finding" }]} rows={summaryRows}/> : <EmptyState title="No structured evidence table" detail="The answer did not return tabular evidence for this run."/>}<EvidenceCitationList evidence={evidence} onOpen={setSelected}/></Card><QaVisualBoard evidence={evidence} showImage={showImage ?? ""} kbRows={kbRows} summaryRows={summaryRows} onOpen={setSelected}/><Card title="Stored files used for retrieval">{kbRows.length ? <DenseTable columns={[{ key: "file", label: "File" }, { key: "type", label: "Type" }, { key: "size", label: "Size" }, { key: "indexed", label: "Indexed" }]} rows={kbRows}/> : <EmptyState title="No indexed files for this patient" detail="Index a PDF, Word document, text file, JSON file, or image to expand the retrieval base."/>}</Card><Card title="Agent execution"><AgentStepper steps={run.steps} toolCalls={(run.result?.toolCalls ?? []) as ToolCall[]}/></Card></> : <Card><EmptyState title="No answer evidence yet" detail="Ask a patient-scoped question to see the answer, cited table, visual evidence, source files, and agent audit."/></Card>;
  return <>
    <WorkflowHead number={2} title="Patient Q&A" detail="Ask questions about one patient across the chart, notes, documents, and imaging - every answer cites the evidence behind it." mode={catalog.data?.executionMode}/>
    <PipelineBand agents={qaAgents} run={run}/>
    <div className="qa-workspace">
      <aside>
        <Card title="Patient context and filters"><label>Patient{demoMode ? <select value={patientId} onChange={event => setPatientId(event.target.value)}>{(patientList.data ?? []).map(p => <option key={p.id} value={p.id}>{p.name} ({p.id})</option>)}{!patientList.data?.length && <option value={patientId}>{patientId}</option>}</select> : <><input list="qa-patient-roster" value={patientId} onChange={event => setPatientId(event.target.value)} placeholder="Select or type a patient ID"/><datalist id="qa-patient-roster">{(patientList.data ?? []).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</datalist></>}</label><label>Session<select value={sessionScope} onChange={event => setSessionScope(event.target.value)}><option value="all">All sessions</option><option value="latest">Latest session</option><option value="previous">Previous session</option></select></label><label>Date range<select value={dateRange} onChange={event => setDateRange(event.target.value)}><option value="all">All available evidence</option><option value="30d">Last 30 days</option><option value="1y">Last year</option></select></label><label>Evidence type<select value={source} onChange={event => setSource(event.target.value as typeof source)}><option value="all">Combined evidence</option><option value="image">Images only</option><option value="text">Clinical notes</option><option value="lab">Structured labs</option><option value="document">Knowledge base</option></select></label></Card>
        {!demoMode && <Card title="Knowledge base intake"><label className={`upload-zone kb-upload-zone ${kbDragging ? "dragging" : ""}`} onDragOver={event => { event.preventDefault(); setKbDragging(true); }} onDragLeave={() => setKbDragging(false)} onDrop={dropKb}><input type="file" accept={KB_UPLOAD_TYPES} onChange={event => selectKbFile(event.target.files?.[0] ?? null)}/><span className="upload-icon">KB</span><strong>{kbFile ? kbFile.name : "Drop patient files here"}</strong><small>PDF, DOCX, MD, TXT, JSON, PNG, JPEG, WEBP. Indexed for cited multimodal answers.</small></label>{kbFile && <div className="file-row"><span><strong>{kbFile.name}</strong><small>{Math.round(kbFile.size / 1024)} KB ready to index</small></span><button className="link" onClick={() => setKbFile(null)}>Remove</button></div>}<button className="button primary full" disabled={!kbFile || kbBusy} onClick={() => void uploadKb()}>{kbBusy ? "Indexing into evidence store" : "Index file for Q&A"}</button></Card>}
        <Card title="Authorized sources"><div className="source-status"><span>Structured record <StatusBadge tone="success">Ready</StatusBadge></span><span>Clinical notes <StatusBadge tone="success">Indexed</StatusBadge></span><span>Image evidence <StatusBadge tone="success">6 sources</StatusBadge></span><span>Knowledge base <StatusBadge tone={(kbAssets.data ?? []).length ? "success" : "info"}>{(kbAssets.data ?? []).length} files</StatusBadge></span></div></Card>
        <InlineDiagram id="19-chat-turn-sequence" title="Q&A architecture"/>
      </aside>
      <section className="qa-answer-column"><nav className="tabs qa-subtabs">{qaTabs.map(name => <button key={name} className={qaTab === name ? "active" : ""} onClick={() => setQaTab(name)}>{name}</button>)}</nav>{qaWaiting && <WorkflowRunSpinner label="Q&A" agents={qaAgents} detail="Context, retrieval, image evidence, citation, synthesis, and audit agents are assembling a cited patient answer."/>}{qaTab === "Ask" && turns.length > 0 && <div className="chat-thread qa-thread" aria-label="Conversation history">{turns.map((turn, index) => <article key={turn.id} className="chat-exchange"><div className="chat-message user"><p>{turn.question}</p></div><div className="chat-message assistant"><header><div><strong>{pipelineDisplayName(turn.run.agentName ?? "patient_qa_pipeline")}</strong><small>Turn {index + 1} - {String(turn.run.createdAt ?? "").slice(0, 19).replace("T", " ")}</small></div><StatusBadge tone={turn.run.status === "completed" ? "success" : turn.run.status}>{turn.run.status}</StatusBadge></header><p>{String(turn.run.result?.answer ?? "Answer recorded for this turn.")}</p><div className="button-row end"><button className="button subtle" onClick={() => { setRun(turn.run); setQaTab("Response evidence"); }}>Open evidence package</button></div></div></article>)}</div>}{qaTab === "Knowledge base" || qaTab === "Document library" ? <Card title={demoMode ? "Patient document library" : "Patient document library"} action={<button className="button subtle" onClick={() => void kbAssets.refresh()}>Refresh files</button>}>{kbAssets.loading ? <LoadingState/> : kbAssets.error ? <ErrorState error={kbAssets.error} retry={kbAssets.refresh}/> : kbRows.length ? <><div className="kb-file-grid">{(kbAssets.data ?? []).map(asset => <button key={asset.assetId} onClick={() => asset.previewUrl ? setSelected({ id: asset.assetId, label: asset.filename, kind: asset.contentType.startsWith("image/") ? "image" : "document", sourceUrl: asset.previewUrl, excerpt: String(asset.extracted?.textPreview ?? "Stored file") }) : undefined}><span>{asset.contentType.startsWith("image/") ? "IMG" : asset.filename.split(".").pop()?.toUpperCase() ?? "DOC"}</span><strong>{asset.filename}</strong><small>{asset.patientId} - {Math.max(1, Math.round(asset.sizeBytes / 1024))} KB - {String(asset.extracted?.type ?? "indexed")}</small><p>{String(asset.extracted?.textPreview ?? "Ready for Q&A retrieval.").slice(0, 150)}</p></button>)}</div><DenseTable columns={[{ key: "file", label: "File" }, { key: "patient", label: "Patient" }, { key: "type", label: "Type" }, { key: "size", label: "Size" }, { key: "indexed", label: "Indexed" }, { key: "preview", label: "Preview" }]} rows={kbRows}/></> : <EmptyState title="No stored files yet" detail={demoMode ? "No documents are indexed for this workspace yet. Upload patient files, or ask your administrator to load the demo dataset." : "Use the knowledge-base intake panel to index PDFs, Word docs, text, JSON, and images for this patient."}/>}</Card> : qaTab === "Response evidence" ? responseEvidence : <><Card title="Clinical question" className="question-composer">{patientKbCount > 0 && <p className="kb-indexed-note"><StatusBadge tone="success">{patientKbCount} document{patientKbCount === 1 ? "" : "s"} indexed</StatusBadge> included in retrieval for this patient</p>}<textarea rows={4} value={question} onChange={event => setQuestion(event.target.value)} placeholder="Ask a longitudinal, evidence-grounded question about this patient"/><div className="question-examples">{exampleQuestions.map(example => <button key={example} onClick={() => setQuestion(example)}>{example}</button>)}</div><div className="button-row end"><span>Patient scope and authorization are validated before retrieval.</span><button className="button primary" disabled={!patientId || question.length < 3 || busy} onClick={() => void ask()}>{busy ? "Searching the record" : "Ask about this patient"}</button></div>{error && <p className="form-error" role="alert">{error}</p>}</Card>{run ? <><Card title="Direct answer" action={<StatusBadge tone="info">AI generated - review</StatusBadge>}><AgentMeta run={run}/><ConfidenceMeter value={run.confidence}/><p className="answer">{answer}{evidence.length ? <span className="answer-citation-trail"> {evidence.slice(0, 3).map((item, index) => <button key={item.id} onClick={() => setSelected(item)}>[{index + 1}]</button>)}</span> : null}</p>{showImage && <figure className="answer-image"><img src={showImage} alt="Cited visual evidence"/><figcaption>Visual evidence returned with the answer</figcaption></figure>}{summaryRows.length > 0 && <DenseTable columns={[{ key: "citation", label: "Citation" }, { key: "file", label: "File" }, { key: "type", label: "Type" }, { key: "finding", label: "Finding" }]} rows={summaryRows}/>}<EvidenceCitationList evidence={evidence} onOpen={setSelected}/><div className="answer-sections"><section><h4>Key evidence</h4><p>{evidence[0]?.excerpt ?? "Evidence retrieval completed."}</p></section><section><h4>Relevant patient data</h4><p>{patientId} - combined longitudinal record - {evidence.length} cited sources</p></section><section><h4>Recommended next action</h4><p>Review the cited images and confirm the finding against the authored clinical note before changing the care plan.</p></section><section><h4>Human review state</h4><StatusBadge tone="review">Clinician review recommended</StatusBadge></section></div></Card><Card title="Agent execution">{run ? <AgentStepper steps={run.steps} toolCalls={(run.result?.toolCalls ?? []) as ToolCall[]}/> : <p className="muted">Processing steps appear here once the question has been checked and routed.</p>}</Card></> : <Card><EmptyState title="Ask a patient-scoped question" detail="Nexus confirms you are authorized for this patient, gathers evidence across notes, labs, documents, and imaging, and returns a cited, auditable answer."/></Card>}</>}</section>
    </div><SourceViewer evidence={selected} onClose={() => setSelected(null)}/>
  </>;
}

const fallbackSchemaTables = [
  { table: "patients_core", columns: [{ name: "patient_id", type: "TEXT" }, { name: "age", type: "INTEGER" }, { name: "sex", type: "TEXT" }, { name: "risk_level", type: "TEXT" }, { name: "primary_diagnosis", type: "TEXT" }] },
  { table: "patient_conditions", columns: [{ name: "condition_name", type: "TEXT" }, { name: "category", type: "TEXT" }, { name: "severity", type: "TEXT" }] },
  { table: "medications", columns: [{ name: "medication_name", type: "TEXT" }, { name: "medication_class", type: "TEXT" }, { name: "adherence_score", type: "FLOAT" }] },
  { table: "vital_signs", columns: [{ name: "systolic_bp", type: "INTEGER" }, { name: "oxygen_saturation", type: "FLOAT" }, { name: "bmi", type: "FLOAT" }] },
  { table: "care_gaps", columns: [{ name: "gap_type", type: "TEXT" }, { name: "priority", type: "TEXT" }, { name: "status", type: "TEXT" }] },
] satisfies SchemaTable[];
type DatabaseTurn = { id: string; question: string; run: AgentRun };
type DatabaseCitation = { id: string; label: string; detail: string };

function InlineDbCitation({ cite }: { cite: DatabaseCitation }) {
  return <a className="inline-db-citation" href={`#${cite.id}`} aria-label={cite.detail}>{cite.label}</a>;
}

export function DatabaseIntelligence() {
  const [params] = useSearchParams();
  const { role, tenant } = useClinical();
  const catalog = useApi(() => api.agents(), [tenant.id]);
  const schema = useApi(() => role === "admin" ? api.schema() : Promise.resolve([]), [tenant.id, role]);
  // Example questions are computed server-side from the tenant's actual
  // database contents, so every suggestion is answerable with real rows.
  const examples = useApi(() => api.databaseExamples(), [tenant.id]);
  const exampleQuestions = examples.data?.length ? examples.data : fallbackDatabaseExamples;
  const [question, setQuestion] = useState(params.get("query") ?? "");
  const [run, setRun] = useState<AgentRun | null>(null);
  const [turns, setTurns] = useState<DatabaseTurn[]>([]);
  const [chartType, setChartType] = useState("Bar chart");
  const [busy, setBusy] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");
  const threadKey = historyKey(tenant.id, "database");
  useRunPolling(run, setRun);
  useSyncRunIntoTurns(run, setTurns, threadKey);
  useTurnHistory(threadKey, "database", undefined, setTurns, setRun);
  const appendTurn = (id: string, submitted: string, turnRun: AgentRun) => {
    setTurns(current => { const updated = [...current, { id, question: submitted, run: turnRun }]; saveTurns(threadKey, updated); return updated; });
  };
  // Live runs come back "running" and only reach "review" once useRunPolling
  // catches up (real Gemini calls, up to a few minutes) — auto-execute has
  // to wait for that instead of chaining straight off the initial response,
  // which used to work only because demo-mode previews returned complete.
  const autoExecuted = useRef(new Set<string>());
  useEffect(() => {
    if (!run || run.status !== "review" || autoExecuted.current.has(run.id) || run.result?.safe === false) return;
    autoExecuted.current.add(run.id);
    void (async () => {
      setExecuting(true);
      try { setRun(await api.executeSql(run.id)); }
      catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to execute the approved query"); }
      finally { setExecuting(false); }
    })();
  }, [run?.id, run?.status]);
  const preview = async () => {
    const submitted = question.trim();
    if (!submitted) return;
    setBusy(true); setError("");
    try {
      const draft = await api.generateSql(submitted);
      setRun(draft);
      appendTurn(draft.id, submitted, draft);
      setQuestion("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to generate SQL preview"); }
    finally { setBusy(false); }
  };
  const latestRows = (run?.result?.rows ?? []) as Array<Record<string, unknown>>;
  const latestColumns = useMemo(() => Object.keys(latestRows[0] ?? {}).map(key => ({ key, label: key.replaceAll("_", " ") })), [latestRows]);
  const exportCsv = (targetRun = run) => {
    const rows = (targetRun?.result?.rows ?? []) as Array<Record<string, unknown>>;
    const columns = Object.keys(rows[0] ?? {}).map(key => ({ key, label: key.replaceAll("_", " ") }));
    if (!rows.length) return;
    const csv = [columns.map(column => column.key).join(","), ...rows.map(row => columns.map(column => `"${String(row[column.key] ?? "").replaceAll('"', '""')}"`).join(","))].join("\n");
    const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); link.download = `query-${targetRun?.id}.csv`; link.click(); URL.revokeObjectURL(link.href);
  };
  const dbPipeline = catalog.data?.pipelines.find(item => item.id === "database");
  const dbAgents = dbPipeline?.agents ?? ["schema_discovery_agent", "nl_to_sql_agent", "sql_validator_agent", "query_executor_agent", "insight_chart_agent", "audit_agent"];
  const databaseWaiting = busy || executing || ["queued", "running"].includes(run?.status ?? "");
  const schemaTables = schema.data?.length ? schema.data : fallbackSchemaTables;
  return <>
    <WorkflowHead number={3} title="Population insights" detail="Ask population health questions in plain language - every query is reviewed before it runs, and results arrive with charts and a full audit trail." mode={catalog.data?.executionMode}/>
    <PipelineBand agents={dbAgents} run={run}/>
    {role === "admin" && <section className="database-admin-context" aria-label="Database admin context"><Card title="Schema explorer">{schemaTables.map(table => <details key={table.table} open={table.table === "patients_core"}><summary>{table.table}<span>{table.columns.length} columns</span></summary><code>{table.columns.map(column => `${column.name} ${column.type}`).join(", ")}</code></details>)}</Card><Card title="Query policy"><ul className="policy-list"><li>SELECT statements only</li><li>Recognized tables only</li><li>No system catalog access</li><li>Explicit execution approval</li><li>Every query audited</li></ul></Card></section>}
    <div className="database-workspace">
      <section className="database-chat">
        {turns.length > 0 && <div className="chat-thread">{turns.map(turn => {
          const turnRows = (turn.run.result?.rows ?? []) as Array<Record<string, unknown>>;
          const turnColumns = Object.keys(turnRows[0] ?? {}).map(key => ({ key, label: key.replaceAll("_", " ") }));
          const sql = String(turn.run.result?.sql ?? "");
          const safe = turn.run.result?.safe !== false;
          const auditRows = [{ id: `${turn.id}-audit`, event: "database_intelligence_run", run: turn.run.id, status: turn.run.status, audit: turn.run.auditId ?? "pending", trace: turn.run.traceId ?? "pending" }];
          // Fixed role labels: live and demo runs report different step
          // lists, so naming agents by step index misattributed stages
          // ("Schema Discovery Agent generated the SQL").
          const citations = [
            { id: `${turn.id}-sql`, label: "[sql]", detail: "Read-only SQL drafted by the NL-to-SQL agent and safety-checked before execution." },
            { id: `${turn.id}-results`, label: "[clinical]", detail: `${String(turn.run.result?.clinicalSummary ?? `Query execution returned ${turnRows.length} governed row${turnRows.length === 1 ? "" : "s"}.`)} ${String(turn.run.result?.recommendedAction ?? "")}`.trim() },
            { id: `${turn.id}-chart`, label: "[chart]", detail: "Visualization rendered directly from the executed query rows." },
            { id: `${turn.id}-audit`, label: "[audit]", detail: `Audit trail recorded event ${turn.run.auditId ?? "pending"} for this run.` },
          ];
          return <article key={turn.id} className="chat-exchange"><div className="chat-message user"><p>{turn.question}</p></div><div className="chat-message assistant"><header><div><strong>{pipelineDisplayName(turn.run.agentName) ?? "Population insights"}</strong><small>{(turn.run.steps ?? []).map(step => step.name).join(" -> ")}</small></div><StatusBadge tone={turnRows.length ? "success" : "review"}>{turnRows.length ? "Answered" : "Preview only"}</StatusBadge></header><section className="chat-answer-section"><h3>Answer</h3><p>{turnRows.length ? <>The governed SQL result returned {turnRows.length} cohort segment{turnRows.length === 1 ? "" : "s"} <InlineDbCitation cite={citations[1]}/> from a safety-checked read-only query <InlineDbCitation cite={citations[0]}/>. The chart below is rendered directly from those rows <InlineDbCitation cite={citations[2]}/>, and the run is traceable in audit <InlineDbCitation cite={citations[3]}/>.</> : <>The SQL preview is ready <InlineDbCitation cite={citations[0]}/>, but no result rows were returned <InlineDbCitation cite={citations[1]}/>.</>}</p><div className="db-citation-strip">{citations.map(cite => <a key={cite.id} href={`#${cite.id}`}><span>{cite.label}</span>{cite.detail}</a>)}</div><div id={`${turn.id}-chart`} className="embedded-chart-builder"><label>Visualization<select value={chartType} onChange={event => setChartType(event.target.value)}>{["Bar chart", "Line chart", "Area chart", "Scatter plot", "Histogram", "Box plot", "Heatmap", "Pie chart", "Treemap", "Cohort chart", "Risk distribution", "Time-series trend"].map(type => <option key={type}>{type}</option>)}</select></label>{turnRows.length ? <ChartPanel rows={turnRows} variant={chartType}/> : <div className="chart-empty">No chart rows returned.</div>}</div></section><section id={`${turn.id}-sql`} className="chat-answer-section"><h3>Generated SQL</h3><SqlPreview sql={sql} safe={safe}/></section><section id={`${turn.id}-results`} className="chat-answer-section"><h3>Query results</h3>{turnRows.length ? <><button className="button subtle export-inline" onClick={() => exportCsv(turn.run)}>Export CSV</button><DenseTable columns={turnColumns} rows={turnRows}/></> : <EmptyState title="No rows returned"/>}</section><section className="chat-answer-section"><h3>Query history</h3><DenseTable columns={[{ key: "question", label: "Question" }, { key: "run", label: "Run" }, { key: "status", label: "Status" }, { key: "actor", label: "Executed by" }]} rows={[{ id: turn.run.id, question: turn.question, run: turn.run.id, status: turn.run.status, actor: "Dr. Sarah Miller" }]}/></section><section id={`${turn.id}-audit`} className="chat-answer-section"><h3>Audit trail</h3><DenseTable columns={[{ key: "event", label: "Event" }, { key: "run", label: "Run" }, { key: "status", label: "Status" }, { key: "audit", label: "Audit ID" }, { key: "trace", label: "Trace ID" }]} rows={auditRows}/><AgentStepper steps={turn.run.steps} toolCalls={(turn.run.result?.toolCalls ?? []) as ToolCall[]}/></section></div></article>;
        })}</div>}
        {databaseWaiting && <WorkflowRunSpinner label="Population insights" agents={dbAgents} detail="Schema discovery, SQL drafting, safety validation, execution, charting, and audit agents are preparing the governed answer."/>}
        <Card className={`database-query chat-composer ${turns.length ? "" : "initial"}`}><label>Ask a question about your patient population<textarea rows={turns.length ? 3 : 5} value={question} onChange={event => setQuestion(event.target.value)} onKeyDown={event => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") void preview(); }} placeholder="Ask a governed question across the authorized clinical database"/></label><div className="question-examples">{exampleQuestions.map(example => <button key={example} onClick={() => setQuestion(example)}>{example}</button>)}</div><div className="button-row end"><span>Your question is translated to a read-only query you approve before it touches patient data.</span><button className="button primary" disabled={question.trim().length < 3 || busy || executing} onClick={() => void preview()}>{busy ? "Analyzing the database" : executing ? "Executing approved query" : turns.length ? "Send follow-up" : "Draft query for review"}</button></div>{error && <p className="form-error" role="alert">{error}</p>}</Card>
      </section>
    </div>
  </>;
}
