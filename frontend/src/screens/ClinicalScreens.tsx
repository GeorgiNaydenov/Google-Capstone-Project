import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { AuditDetailModal, AuditTimeline, Card, CompletenessBadge, ConfidenceMeter, DenseTable, EmptyState, ErrorState, JsonViewer, KpiStrip, LoadingState, RiskBadge, SourceViewer, StatusBadge } from "../components";
import { DiagramAtlas } from "../components/DiagramAtlas";
import { InlineDiagram } from "../components/InlineDiagram";
import { useClinical } from "../context";
import type { AgentRun, AuditEvent, ClinicalSession, Evidence, Patient } from "../types";
import { useApi } from "../useApi";

const TABLE_PREVIEW_LIMIT = 160;

function PageHead({ eyebrow, title, detail, actions }: { eyebrow?: string; title: string; detail?: string; actions?: React.ReactNode }) {
  return <header className="page-head"><div>{eyebrow && <span className="eyebrow accent">{eyebrow}</span>}<h1>{title}</h1>{detail && <p>{detail}</p>}</div>{actions && <div className="button-row">{actions}</div>}</header>;
}

const patientCell = (row: Record<string, unknown>) => <div className="patient-cell"><span>{String(row.name).split(" ").map(part => part[0]).join("")}</span><div><strong>{String(row.name)}</strong><small>{String(row.id)}</small></div></div>;

const patientColumns = [
  { key: "name", label: "Patient", render: patientCell },
  { key: "age", label: "Age" },
  { key: "risk", label: "Risk", render: (row: Record<string, unknown>) => <RiskBadge risk={row.risk as Patient["risk"]}/> },
  { key: "condition", label: "Diagnosis" },
  { key: "lastEncounter", label: "Last Session" },
  { key: "openIssues", label: "Open Issues" },
  { key: "dataSources", label: "Sources" },
  { key: "aiStatus", label: "Last AI Review", render: (row: Record<string, unknown>) => <StatusBadge tone={row.aiStatus === "verified" ? "success" : "review"}>{String(row.aiStatus).replaceAll("_", " ")}</StatusBadge> },
  { key: "assignedClinician", label: "Assigned Clinician" },
];

const alertTone = { critical: "critical", warning: "warning", info: "info" } as const;

export function ClinicianDashboard() {
  const { data, error, loading, refresh } = useApi(() => api.dashboard("clinician"), []);
  const alerts = useApi(() => api.notifications(), []);
  const navigate = useNavigate();
  if (loading) return <LoadingState/>;
  if (error) return <ErrorState error={error} retry={refresh}/>;
  const metrics = data?.metrics ?? {};
  const queue = data?.patients ?? [];
  const alertRows = alerts.data ?? [];
  const criticalAlerts = alertRows.filter(alert => alert.severity === "critical").length;
  const openOrchestrator = () => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));
  const highRisk = queue.filter(patient => patient.risk === "high").length;
  const pendingVerification = queue.filter(patient => patient.aiStatus === "needs_review").length;
  const belowThreshold = (data?.sessions ?? []).filter(session => (session.extractionConfidence ?? 1) < 0.8).length;
  const clinicianName = queue.find(patient => patient.assignedClinician)?.assignedClinician?.replace(/^Dr\.\s+/i, "").split(" ")[0] ?? "clinician";
  const queueColumns = [patientColumns[0], patientColumns[2], patientColumns[3], patientColumns[7], { key: "action", label: "Action", render: (row: Record<string, unknown>) => <button className="table-action" onClick={event => { event.stopPropagation(); navigate(`/app/patient/${row.id}`); }}>Review</button> }];
  return <>
    <PageHead title="Clinician dashboard" detail={`Good morning, ${clinicianName}. ${highRisk} high-risk patient${highRisk === 1 ? "" : "s"} and ${pendingVerification} verification${pendingVerification === 1 ? "" : "s"} need attention across your active queue.`} actions={<button className="button primary" onClick={openOrchestrator}>Run an agent</button>}/>
    <div className="quick-action-row" aria-label="Dashboard quick actions">
      <button onClick={() => navigate("/app/extraction")}>New session</button>
      <button onClick={() => navigate("/app/qa")}>Ask Q&A</button>
      <button onClick={() => navigate("/app/database")}>Run query</button>
      <button onClick={() => navigate("/app/inbox")}>Review inbox</button>
    </div>
    <KpiStrip values={[
      { label: "Assigned patients", value: Number(metrics.assignedPatients ?? 0), meta: `${highRisk} high risk` },
      { label: "Pending verifications", value: Number(metrics.pendingVerifications ?? 0), meta: `${belowThreshold} below threshold`, tone: pendingVerification ? "warning" : undefined },
      { label: "Image extractions today", value: Number(metrics.imageExtractionsToday ?? 0), meta: `${(data?.sessions ?? []).filter(session => session.status !== "verified").length} awaiting review` },
      { label: "Open AI alerts", value: Number(metrics.openAiAlerts ?? 0), meta: `${criticalAlerts} high priority`, tone: criticalAlerts ? "critical" : undefined },
      { label: "Agent runs, 24h", value: Number(metrics.agentRuns24h ?? 0), meta: `${Number(metrics.failedExtractions ?? 0)} failed`, tone: "success" },
    ]}/>
    <div className="dashboard-grid">
      <Card title="Today's patient queue" className="queue-panel" action={<button className="link" onClick={() => navigate("/app/queue")}>View all</button>}>{queue.length ? <DenseTable columns={queueColumns} rows={queue.slice(0, 7) as unknown as Array<Record<string, unknown>>} onRow={row => navigate(`/app/patient/${row.id}`)}/> : <EmptyState title="No patients yet" detail="This tenant has no patient records. Run an extraction to register the first patient."/>}</Card>
      <div className="dashboard-rail">
        <Card title="AI recommendations and alerts" className="recommendation-panel">{alertRows.length ? alertRows.slice(0, 4).map(alert => <button key={alert.id} className="recommendation" onClick={() => navigate(alert.route)}><div><code>{alert.agent}</code><StatusBadge tone={alertTone[alert.severity] ?? "info"}>{alert.severity.toUpperCase()}</StatusBadge></div><strong>{alert.title}</strong><p>{alert.detail}</p><small>{alert.agent}</small></button>) : <EmptyState title="No active alerts" detail="Agent recommendations appear here when workflows need attention."/>}</Card>
        <Card title="Recent agent activity">{data?.activity?.length ? <AuditTimeline events={data.activity.slice(0, 5)}/> : <EmptyState title="No activity yet" detail="Workflow and review events appear here as they happen."/>}</Card>
      </div>
    </div>
    <Card title="Today's sessions and clinical tasks"><DenseTable columns={[{ key: "title", label: "Session" }, { key: "patientId", label: "Patient" }, { key: "occurredAt", label: "Date" }, { key: "status", label: "Verification", render: row => <StatusBadge tone={row.status === "verified" ? "success" : "review"}>{String(row.status)}</StatusBadge> }]} rows={(data?.sessions ?? []).slice(0, 6) as unknown as Array<Record<string, unknown>>} onRow={row => navigate(`/app/session/${row.id}`)}/></Card>
    <details className="dashboard-atlas" open>
      <summary><span><strong>System atlas</strong><small>Architecture views for this workspace</small></span></summary>
      <DiagramAtlas defaultCategory="system" compact/>
    </details>
  </>;
}

export function PatientSearch({ queue = false }: { queue?: boolean }) {
  const [params, setParams] = useSearchParams();
  const initialQuery = params.get("q") ?? "";
  const view = params.get("view") ?? "patients";
  const [query, setQuery] = useState(initialQuery);
  const [submitted, setSubmitted] = useState(initialQuery);
  const [risk, setRisk] = useState(params.get("risk") ?? "all");
  const [review, setReview] = useState("all");
  const [completeness, setCompleteness] = useState("all");
  const patientState = useApi(() => api.patients(submitted), [submitted]);
  const dashboardState = useApi(() => api.dashboard("clinician"), []);
  const sessionState = useApi(() => api.sessions(), []);
  const navigate = useNavigate();
  const { setPatient } = useClinical();
  const [quickFilters, setQuickFilters] = useState<string[]>([]);
  const dashboardPatients = dashboardState.data?.patients ?? [];
  const allPatients = useMemo(() => {
    const byId = new Map<string, Patient>();
    for (const patient of dashboardPatients) byId.set(patient.id, patient);
    for (const patient of patientState.data ?? []) byId.set(patient.id, patient);
    return Array.from(byId.values());
  }, [dashboardPatients, patientState.data]);
  const rows = useMemo(() => allPatients.filter(patient => {
    const riskMatch = risk === "all" || patient.risk === risk;
    const reviewMatch = review === "all" || patient.aiStatus === review;
    const score = Math.round((patient.completeness ?? 0) * 100);
    const completenessMatch = completeness === "all" || (completeness === "incomplete" ? score < 85 : score >= 85);
    const recentCutoff = new Date(Date.now() - 7 * 24 * 3600 * 1000);
    const quickMatch = quickFilters.every(filter =>
      filter === "new" ? Boolean(patient.lastEncounter && new Date(patient.lastEncounter) >= recentCutoff)
      : filter === "flagged" ? patient.aiStatus === "needs_review"
      : filter === "followup" ? Number(patient.openIssues ?? 0) > 0
      : true);
    return riskMatch && reviewMatch && completenessMatch && quickMatch;
  }), [allPatients, risk, review, completeness, quickFilters]);
  const rowStats = useMemo(() => ({
    high: rows.filter(item => item.risk === "high").length,
    imageEvidence: rows.filter(item => (item.dataSources ?? 0) > 3).length,
    reviewRequired: rows.filter(item => item.aiStatus === "needs_review").length,
  }), [rows]);
  const open = (row: Record<string, unknown>) => {
    const selected = allPatients.find(item => item.id === row.id);
    if (selected) setPatient(selected);
    navigate(`/app/patient/${row.id}`);
  };
  const quickActive = (value: string) =>
    value === "high" ? risk === "high" : value === "review" ? review === "needs_review" : value === "missing" ? completeness === "incomplete" : quickFilters.includes(value);
  const applyQuickFilter = (next: string) => {
    if (next === "high") setRisk(current => current === "high" ? "all" : "high");
    else if (next === "review") setReview(current => current === "needs_review" ? "all" : "needs_review");
    else if (next === "missing") setCompleteness(current => current === "incomplete" ? "all" : "incomplete");
    else setQuickFilters(current => current.includes(next) ? current.filter(item => item !== next) : [...current, next]);
  };
  if (view === "sessions") return <SessionRegistry sessions={sessionState.data ?? []} loading={sessionState.loading} error={sessionState.error} onRetry={sessionState.refresh} onOpen={id => navigate(`/app/session/${id}`)}/>;
  return <>
    <PageHead eyebrow={queue ? "PRIORITIZED WORKLIST" : "GLOBAL PATIENT SEARCH"} title={queue ? "Patient queue" : "Patient search results"} detail={queue ? "Agent-prioritized cases, verification tasks, and follow-up work." : "Search structured records, clinical notes, image evidence, and vectorized content."} actions={<button className="button subtle" onClick={() => exportRows(rows)}>Export CSV</button>}/>
    {queue && <div className="quick-filters">{[["high", "High risk"], ["review", "Needs review"], ["new", "Recent session"], ["missing", "Missing evidence"], ["flagged", "AI flagged"], ["followup", "Follow-up due"]].map(([value, label]) => <button key={value} aria-pressed={quickActive(value)} className={quickActive(value) ? "active" : ""} onClick={() => applyQuickFilter(value)}>{label}</button>)}</div>}
    <div className="search-layout">
      <Card title="Filters" className="filter-panel">
        <label>Risk level<select value={risk} onChange={event => setRisk(event.target.value)}><option value="all">All risk levels</option><option value="high">High risk</option><option value="medium">Needs review</option><option value="low">Stable</option></select></label>
        <label>Agent review<select value={review} onChange={event => setReview(event.target.value)}><option value="all">All review states</option><option value="needs_review">Pending review</option><option value="verified">Clinician verified</option></select></label>
        <label>Data completeness<select value={completeness} onChange={event => setCompleteness(event.target.value)}><option value="all">Any completeness</option><option value="incomplete">Below 85%</option><option value="complete">85% and above</option></select></label>
        <label>Last session<select><option>Any date</option><option>Last 7 days</option><option>Last 30 days</option><option>Last 90 days</option></select></label>
        <label>Evidence type<select><option>All evidence</option><option>Imaging</option><option>Clinical notes</option><option>Structured data</option><option>Similar-case matches</option></select></label>
        <button className="button subtle full" onClick={() => { setRisk("all"); setReview("all"); setCompleteness("all"); }}>Clear filters</button>
      </Card>
      <div className="results-column">
        <Card className="search-toolbar"><form onSubmit={event => { event.preventDefault(); setSubmitted(query); setParams(current => { current.set("q", query); return current; }); }}><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Name, patient ID, diagnosis, note, or imaging finding"/><button className="button primary" type="submit">Search all evidence</button></form><small>{rows.length} patients match the current filters</small></Card>
        <Card>{patientState.loading || dashboardState.loading ? <LoadingState/> : patientState.error && dashboardState.error ? <ErrorState error={patientState.error} retry={() => { void patientState.refresh(); void dashboardState.refresh(); }}/> : <DenseTable columns={queue ? [...patientColumns.slice(0, 6), { key: "confidence", label: "AI Confidence", render: row => `${Math.round(Number(row.completeness) * 100)}%` }, patientColumns[8]] : patientColumns} rows={rows as unknown as Array<Record<string, unknown>>} onRow={open} limit={TABLE_PREVIEW_LIMIT}/>}</Card>
      </div>
      <Card title={queue ? "Queue intelligence" : "AI search explanation"} className="intelligence-panel"><span className="agent-kicker">Retrieval Agent</span><h3>{queue ? `${rowStats.high} urgent cases surfaced` : "Hybrid retrieval active"}</h3><p>The result set combines patient demographics, structured diagnoses, clinical notes, imaging metadata, and similar historical cases within your authorized scope.</p><dl><div><dt>Structured matches</dt><dd>{rows.length}</dd></div><div><dt>Image evidence</dt><dd>{rowStats.imageEvidence}</dd></div><div><dt>Review required</dt><dd>{rowStats.reviewRequired}</dd></div></dl><button className="button primary full" onClick={() => navigate("/app/qa")}>Ask about these results</button></Card>
    </div>
  </>;
}

function SessionRegistry({ sessions, loading, error, onRetry, onOpen }: { sessions: ClinicalSession[]; loading: boolean; error: unknown; onRetry: () => void; onOpen: (id: string) => void }) {
  return <><PageHead eyebrow="CLINICAL EVIDENCE" title="Sessions" detail="Uploaded evidence, extraction confidence, human verification, and storage synchronization." actions={<button className="button primary" onClick={() => location.assign("/app/extraction")}>New session</button>}/><Card>{loading ? <LoadingState/> : error ? <ErrorState error={error} retry={onRetry}/> : <DenseTable columns={[{ key: "id", label: "Session" }, { key: "patientId", label: "Patient" }, { key: "occurredAt", label: "Date" }, { key: "uploadedImageCount", label: "Images" }, { key: "extractionConfidence", label: "Confidence", render: row => `${Math.round(Number(row.extractionConfidence) * 100)}%` }, { key: "status", label: "Human Review", render: row => <StatusBadge tone={row.status === "verified" ? "success" : "review"}>{String(row.status)}</StatusBadge> }, { key: "vectorSyncStatus", label: "Vector", render: row => <StatusBadge tone="success">{String(row.vectorSyncStatus)}</StatusBadge> }]} rows={sessions as unknown as Array<Record<string, unknown>>} onRow={row => onOpen(String(row.id))} limit={TABLE_PREVIEW_LIMIT}/>}</Card></>;
}

function exportRows(rows: Patient[]) {
  const csv = ["id,name,risk,diagnosis,last_session,open_issues,assigned_clinician", ...rows.map(row => [row.id, row.name, row.risk, row.condition, row.lastEncounter, row.openIssues, row.assignedClinician].map(value => `"${String(value ?? "").replaceAll('"', '""')}"`).join(","))].join("\n");
  const link = document.createElement("a"); link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" })); link.download = "clinical-patients.csv"; link.click(); URL.revokeObjectURL(link.href);
}

export function PatientOverview() {
  const [params] = useSearchParams();
  const { data, error, loading, refresh } = useApi(() => api.dashboard("admin"), []);
  if (loading) return <LoadingState/>;
  if (error) return <ErrorState error={error} retry={refresh}/>;
  if (params.get("view") === "reports") return <ReportsView/>;
  const metrics = data?.metrics ?? {};
  const patients = data?.patients ?? [];
  const sessions = data?.sessions ?? [];
  const high = patients.filter(patient => patient.risk === "high").length;
  const missing = patients.filter(patient => (patient.completeness ?? 0) < 0.85).length;
  const withImages = sessions.filter(session => (session.uploadedImageCount ?? 0) > 0).length;
  const lowConfidence = sessions.filter(session => (session.extractionConfidence ?? 1) < 0.8).length;
  const verifiedPatients = patients.filter(patient => patient.aiStatus === "verified").length;
  const verifiedSessions = sessions.filter(session => session.status === "verified").length;
  const totalPatients = Number(metrics.patients ?? patients.length);
  const totalSessions = Number(metrics.sessions ?? sessions.length);
  const highRisk = Number(metrics.highRisk ?? high);
  const pendingReview = Number(metrics.pendingReview ?? 0);
  const generatedImageSessions = Number(metrics.imageExtractionsToday ?? withImages);
  const databaseRows = Number(metrics.databaseRows ?? totalPatients);
  return <><PageHead eyebrow="POPULATION INTELLIGENCE" title="Patient population overview" detail="Coverage, risk, missing evidence, and agent-review status across the cohort."/><KpiStrip values={[{ label: "Total patients", value: totalPatients }, { label: "Recent sessions", value: totalSessions }, { label: "High risk", value: highRisk, tone: highRisk ? "critical" : undefined }, { label: "Needs review", value: pendingReview, tone: pendingReview ? "warning" : undefined }, { label: "Missing data", value: missing }, { label: "Sessions with imaging", value: generatedImageSessions }, { label: "Low-confidence extractions", value: lowConfidence }, { label: "AI coverage", value: `${metrics.completeness ?? 0}%`, tone: "success" }]}/><div className="population-grid"><Card title="Risk distribution">{patients.length ? <div className="risk-bars">{[["High risk", high, "critical"], ["Needs review", patients.filter(p => p.risk === "medium").length, "warning"], ["Stable", patients.filter(p => p.risk === "low").length, "success"]].map(([label, value, tone]) => <div key={String(label)}><span>{label}<b>{value}</b></span><progress className={String(tone)} max={Math.max(patients.length, 1)} value={Number(value)}/></div>)}</div> : <EmptyState title="No patients" detail="Risk distribution appears once patients exist in this tenant."/>}</Card><Card title="Agent coverage"><div className="coverage-grid">{[["Records indexed", `${databaseRows} rows`], ["Sessions with imaging", `${generatedImageSessions} / ${totalSessions}`], ["Sessions verified", `${verifiedSessions} / ${sessions.length}`], ["Patients verified", `${verifiedPatients} / ${patients.length}`]].map(([label, value]) => <div key={label}><strong>{value}</strong><small>{label}</small></div>)}</div></Card><Card title="Recent activity">{data?.activity?.length ? <AuditTimeline events={data.activity}/> : <EmptyState title="No activity yet" detail="Workflow and review events appear here as they happen."/>}</Card></div><Card title="Patient segmentation">{patients.length ? <DenseTable columns={patientColumns} rows={patients as unknown as Array<Record<string, unknown>>}/> : <EmptyState title="No patients yet" detail="Run an extraction to register the first patient in this tenant."/>}</Card></>;
}

function ReportsView() {
  const navigate = useNavigate();
  const reports: Array<[string, string, string, string]> = [
    ["Daily clinical command report", "Queue, high-risk changes, and pending verifications", "Live view", "/app/queue"],
    ["Extraction quality report", "Confidence, failures, and human review outcomes", "Live view", "/app/inbox"],
    ["Patient cohort risk report", "Risk distribution and population movement", "Live view", "/app/overview"],
    ["Storage and lineage report", "Object, JSON, relational, vector, and audit receipts", "Live view", "/app/inbox?view=audit"],
  ];
  return <><PageHead eyebrow="CLINICAL REPORTING" title="Reports" detail="Operational and clinical intelligence views generated from governed data."/><div className="report-grid">{reports.map(([title, detail, schedule, route]) => <Card key={title}><span className="report-icon">R</span><h3>{title}</h3><p>{detail}</p><small>{schedule}</small><button className="button subtle full" onClick={() => navigate(route)}>Open report</button></Card>)}</div></>;
}

export function PatientProfile() {
  const { patientId = "" } = useParams();
  const { setPatient } = useClinical();
  const [tab, setTab] = useState("Timeline");
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const navigate = useNavigate();
  const patientState = useApi(() => api.patient(patientId), [patientId]);
  const sessionState = useApi(() => api.sessions(patientId), [patientId]);
  useEffect(() => { if (patientState.data) setPatient(patientState.data); }, [patientState.data, setPatient]);
  if (patientState.loading) return <LoadingState/>;
  if (patientState.error) return <ErrorState error={patientState.error} retry={patientState.refresh}/>;
  const patient = patientState.data!;
  const sessions = sessionState.data ?? [];
  const tabNames = ["Timeline", "Sessions", "Notes", "Images", "Metrics", "Care Plan", "AI Summary"];
  return <><PageHead eyebrow={`${patient.id} with MRN ${patient.mrn}`} title={patient.name} detail={`${patient.age} years. ${patient.sex}. Assigned to ${patient.assignedClinician}`} actions={<><RiskBadge risk={patient.risk}/><CompletenessBadge value={patient.completeness}/><button className="button primary" onClick={() => navigate(`/app/extraction?patient=${patient.id}`)}>New session</button></>}/><div className="diagnosis-tags"><span>{patient.condition}</span><span>Longitudinal record</span><span>Last session {patient.lastEncounter}</span></div><div className="patient-workspace">
    <aside className="patient-left"><Card title="Demographics"><dl className="compact-facts"><div><dt>Patient ID</dt><dd>{patient.id}</dd></div><div><dt>Age / sex</dt><dd>{patient.age} / {patient.sex}</dd></div><div><dt>Completeness</dt><dd>{Math.round((patient.completeness ?? 0) * 100)}%</dd></div><div><dt>Assigned clinician</dt><dd>{patient.assignedClinician}</dd></div></dl></Card><Card title="Clinical record"><h4>Active diagnoses</h4><p>{patient.condition}</p><h4>Medications</h4><ul><li>Medication reconciliation verified</li><li>Two active prescriptions</li></ul><h4>Allergies</h4><p>No known drug allergies</p></Card><Card title="Data sources"><div className="source-status"><span>Clinical notes <b>18</b></span><span>Images <b>6</b></span><span>Structured fields <b>42</b></span><span>Similar-case matches <b>96</b></span></div></Card></aside>
    <section className="patient-center"><nav className="tabs">{tabNames.map(name => <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>)}</nav><Card title={tab}>{tab === "Timeline" && <PatientTimeline sessions={sessions}/>} {tab === "Sessions" && <DenseTable columns={[{ key: "title", label: "Session" }, { key: "occurredAt", label: "Date" }, { key: "extractionConfidence", label: "AI Confidence", render: row => `${Math.round(Number(row.extractionConfidence) * 100)}%` }, { key: "status", label: "Review" }]} rows={sessions as unknown as Array<Record<string, unknown>>} onRow={row => navigate(`/app/session/${row.id}`)}/>} {tab === "Notes" && <RecordList items={["Oncology follow-up note", "Radiology comparison summary", "Medication reconciliation"]} kind="text" onOpen={setSelectedEvidence}/>} {tab === "Images" && <RecordList items={["CT chest follow-up", "CT abdomen series", "Prior PET reference"]} kind="image" onOpen={setSelectedEvidence}/>} {tab === "Metrics" && <div className="metric-summary"><ConfidenceMeter value={0.92}/><p>Data completeness and evidence coverage remain above the care-team threshold.</p></div>} {tab === "Care Plan" && <RecordList items={["Review hepatic lesion progression", "Confirm treatment response at next tumor board", "Repeat CT in 8 weeks"]} kind="text" onOpen={setSelectedEvidence}/>} {tab === "AI Summary" && <div className="ai-summary"><StatusBadge tone="info">AI generated. Human review required</StatusBadge><p>Longitudinal evidence indicates interval progression in the primary lesion with new hepatic findings. The latest extraction is supported by imaging and the authored clinical note.</p><small>Answer Synthesis Agent. 92% confidence. 4 cited sources</small></div>}</Card></section>
    <aside className="patient-right"><Card title="AI patient copilot"><span className="agent-kicker">Patient Context Agent</span><p>Ask a cited question using this patient's structured record, notes, and image evidence.</p><button className="button primary full" onClick={() => navigate(`/app/qa?patient=${patient.id}`)}>Ask about {patient.name.split(" ")[0]}</button></Card><Card title="Open tasks"><div className="task-list"><label><input type="checkbox"/> Verify latest extraction</label><label><input type="checkbox"/> Review image evidence</label><label><input type="checkbox"/> Confirm follow-up plan</label></div></Card><Card title="Evidence and audit"><button className="action-row" onClick={() => setTab("Images")}>6 image citations <span>View</span></button><button className="action-row" onClick={() => setTab("AI Summary")}>Latest AI summary <span>Read</span></button><button className="action-row" onClick={() => navigate("/app/inbox?view=audit")}>Patient audit trail <span>Open</span></button></Card></aside>
  </div><SourceViewer evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)}/></>;
}

function PatientTimeline({ sessions }: { sessions: ClinicalSession[] }) {
  const events = sessions.flatMap(session => [{ id: `${session.id}-1`, date: session.occurredAt, type: "Session", title: session.title, detail: `${session.uploadedImageCount ?? 0} images. ${Math.round((session.extractionConfidence ?? 0) * 100)}% extraction confidence` }, { id: `${session.id}-2`, date: session.occurredAt, type: "Storage sync", title: "Verified outputs synchronized", detail: "JSON, relational, vector, and audit" }]);
  return <ol className="patient-timeline">{events.map(event => <li key={event.id}><time>{event.date}</time><i/><div><StatusBadge tone={event.type === "Storage sync" ? "success" : "info"}>{event.type}</StatusBadge><strong>{event.title}</strong><p>{event.detail}</p></div></li>)}</ol>;
}

function RecordList({ items, kind = "text", onOpen }: { items: string[]; kind?: Evidence["kind"]; onOpen: (evidence: Evidence) => void }) {
  return <div className="record-list">{items.map((item, index) => <button key={item} onClick={() => onOpen({ id: `EVID-${kind}-${index}`, label: item, kind, excerpt: `Verified clinical record. Source available for "${item}".` })}><span>{index + 1}</span><span><strong>{item}</strong><small>Verified clinical record. Source available</small></span><b>Open source</b></button>)}</div>;
}

export function SessionDetail() {
  const { sessionId = "" } = useParams();
  const { data, error, loading, refresh } = useApi(() => api.session(sessionId), [sessionId]);
  const [tab, setTab] = useState("Extracted fields");
  if (loading) return <LoadingState/>;
  if (error) return <ErrorState error={error} retry={refresh}/>;
  const session = data!;
  const fields = [{ field: "document_type", value: "Clinical evidence", confidence: "96%", status: "Verified" }, { field: "patient_match", value: session.patientId, confidence: "99%", status: "Verified" }, { field: "primary_finding", value: "Abnormal finding requiring follow-up", confidence: "87%", status: "Human reviewed" }];
  return <><PageHead eyebrow={`SESSION ${session.id}`} title={session.title} detail={`${session.occurredAt}. Patient ${session.patientId}`} actions={<StatusBadge tone={session.status === "verified" ? "success" : "review"}>{session.status}</StatusBadge>}/><div className="session-status-strip">{[["Image storage", "Synced"], ["JSON document", session.jsonSyncStatus], ["Relational row", session.relationalSyncStatus], ["Vector embedding", session.vectorSyncStatus], ["Audit event", session.auditStatus]].map(([label, status]) => <div key={label}><span>{label}</span><StatusBadge tone="success">{status}</StatusBadge></div>)}</div><div className="session-layout"><Card title="Session metadata"><dl className="compact-facts"><div><dt>Patient</dt><dd>{session.patientId}</dd></div><div><dt>Images</dt><dd>{session.uploadedImageCount}</dd></div><div><dt>Extraction confidence</dt><dd>{Math.round((session.extractionConfidence ?? 0) * 100)}%</dd></div><div><dt>Clinician review</dt><dd>{session.status}</dd></div></dl><div className="image-placeholder"><span>Clinical source image</span><small>Authorized preview</small></div></Card><section><nav className="tabs">{["Extracted fields", "Structured JSON", "Relational row", "Vector evidence", "Audit trail"].map(name => <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>)}</nav><Card>{tab === "Extracted fields" && <DenseTable columns={[{ key: "field", label: "Clinical field" }, { key: "value", label: "Extracted value" }, { key: "confidence", label: "Confidence" }, { key: "status", label: "Review state" }]} rows={fields}/>} {tab === "Structured JSON" && <JsonViewer value={{ sessionId: session.id, patientId: session.patientId, verification: session.status, fields }}/>} {tab === "Relational row" && <DenseTable columns={[{ key: "session_id", label: "session_id" }, { key: "patient_id", label: "patient_id" }, { key: "occurred_at", label: "occurred_at" }, { key: "review_status", label: "review_status" }]} rows={[{ session_id: session.id, patient_id: session.patientId, occurred_at: session.occurredAt, review_status: session.status }]}/>} {tab === "Vector evidence" && <div className="vector-preview"><StatusBadge tone="success">Indexed</StatusBadge><code>vertex://clinical-evidence/{session.id}</code><p>3 chunks. 768 dimensions. Cosine similarity.</p></div>} {tab === "Audit trail" && <AuditTimeline events={[{ id: "AUD-1", timestamp: session.occurredAt, event: "Session evidence synchronized", actor: "Audit Agent", entity: session.id, result: "recorded" }]}/>}</Card></section></div></>;
}

export function ClinicalInbox() {
  const [params] = useSearchParams();
  const auditMode = params.get("view") === "audit";
  const reviews = useApi(() => api.inbox(), []);
  const audits = useApi(() => api.audits(), []);
  const [selected, setSelected] = useState<AgentRun | null>(null);
  const [selectedAudit, setSelectedAudit] = useState<AuditEvent | null>(null);
  const decide = async (decision: "approved" | "rejected") => {
    if (!selected) return;
    const updated = await api.review(selected.id, decision);
    reviews.setData((reviews.data ?? []).filter(item => item.id !== updated.id));
    setSelected(null);
  };
  if (auditMode) return <><PageHead eyebrow="GOVERNANCE" title="Audit trail" detail="Immutable user, agent, review, query, and storage events from the active demo session."/><Card>{audits.loading ? <LoadingState/> : audits.error ? <ErrorState error={audits.error} retry={audits.refresh}/> : <DenseTable columns={[{ key: "timestamp", label: "Timestamp" }, { key: "event", label: "Event" }, { key: "actor", label: "Actor" }, { key: "entity", label: "Entity" }, { key: "result", label: "Result", render: row => <StatusBadge tone="success">{String(row.result)}</StatusBadge> }]} rows={(audits.data ?? []) as unknown as Array<Record<string, unknown>>} onRow={row => setSelectedAudit((audits.data ?? []).find(event => event.id === row.id) ?? null)}/>}</Card><AuditDetailModal event={selectedAudit} onClose={() => setSelectedAudit(null)}/></>;
  return <><PageHead eyebrow="HUMAN REVIEW" title="Clinical inbox" detail="AI outputs, evidence, and confidence requiring an explicit clinician decision."/><div className="inbox-layout"><Card title={`Pending reviews · ${(reviews.data ?? []).length}`}>{reviews.loading ? <LoadingState/> : reviews.error ? <ErrorState error={reviews.error} retry={reviews.refresh}/> : (reviews.data ?? []).length ? (reviews.data ?? []).map(run => <button key={run.id} className={`inbox-row ${selected?.id === run.id ? "active" : ""}`} onClick={() => setSelected(run)}><span><strong>{run.agentName}</strong><small>{run.id} · {String(run.result?.patientId)}</small></span><StatusBadge tone="review">Review</StatusBadge></button>) : <EmptyState title="Inbox clear" detail="No agent outputs currently require clinician review."/>}</Card><Card title="Review workspace">{selected ? <div className="review-workspace"><div className="agent-meta-inline"><StatusBadge tone="review">Human review required</StatusBadge><span>{Math.round((selected.confidence ?? 0) * 100)}% confidence</span><code>{selected.auditId}</code></div><h3>{String(selected.result?.patientId)} extraction output</h3><JsonViewer value={selected.result?.fields}/><h4>Evidence</h4>{selected.evidence?.map(item => <div className="evidence-line" key={item.id}><strong>{item.label}</strong><small>{item.kind} · {item.id}</small></div>)}<div className="button-row"><button className="button danger" onClick={() => void decide("rejected")}>Reject</button><button className="button primary" onClick={() => void decide("approved")}>Verify and synchronize</button></div></div> : <EmptyState title="Select a review" detail="Choose an agent output to inspect fields, evidence, confidence, and audit identity."/>}</Card><Card title="Review policy"><p>Outputs below the configured threshold require a named clinician decision before JSON, relational, or vector persistence.</p><dl className="compact-facts"><div><dt>Auto approval</dt><dd>90%</dd></div><div><dt>Review threshold</dt><dd>75%</dd></div><div><dt>Target SLA</dt><dd>4 min</dd></div></dl></Card></div><InlineDiagram id="15-human-in-the-loop-bpmn" title="Inbox process map"/></>;
}
