import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { AuditTimeline, Card, DenseTable, EmptyState, ErrorState, JsonViewer, KpiStrip, LoadingState, StatusBadge } from "../components";
import { DiagramAtlas } from "../components/DiagramAtlas";
import { InlineDiagram } from "../components/InlineDiagram";
import { useApi } from "../useApi";
import type { AgentMonitorRow, AuditEvent, ClinicalUser, ComponentHealth } from "../types";

const asArray = <T,>(value: unknown): T[] => Array.isArray(value) ? value as T[] : [];

function Head({ title, detail, action }: { title: string; detail: string; action?: React.ReactNode }) {
  return <header className="page-head"><div><span className="eyebrow accent">ADMINISTRATION</span><h1>{title}</h1><p>{detail}</p></div>{action && <div className="button-row">{action}</div>}</header>;
}

const healthTone = (status: string) => status === "operational" ? "success" : "danger";
const percent = (value: number) => `${Math.round(value * 100)}%`;
const seconds = (ms: number) => ms ? `${(ms / 1000).toFixed(1)}s` : "not measured";
const shortTime = (value: string) => value.includes("T") ? value.slice(11, 19) || value : value;

function HealthTable({ components, compact }: { components: ComponentHealth[]; compact?: boolean }) {
  const columns = [
    { key: "name", label: "Component" },
    { key: "status", label: "Status", render: (row: Record<string, unknown>) => <StatusBadge tone={healthTone(String(row.status))}>{String(row.status)}</StatusBadge> },
    { key: "latency", label: "Measured latency" },
    ...(compact ? [] : [{ key: "detail", label: "Detail" }]),
  ];
  return <DenseTable columns={columns} rows={components.map(component => ({ id: component.name, name: component.name, status: component.status, latency: `${component.latencyMs.toFixed(1)} ms`, detail: component.detail }))}/>;
}

function MonitoringTable({ rows, onInspect }: { rows: AgentMonitorRow[]; onInspect?: (agent: string) => void }) {
  if (!rows.length) return <EmptyState title="No agent runs yet" detail="Agent statistics appear after the first pipeline run in this session."/>;
  return <DenseTable columns={[
    { key: "agent", label: "Agent" },
    { key: "pipeline", label: "Pipeline" },
    { key: "lastRun", label: "Last run", render: row => <span>{shortTime(String(row.lastRun))}</span> },
    { key: "status", label: "Status", render: row => <StatusBadge tone={row.status === "healthy" ? "success" : "review"}>{String(row.status)}</StatusBadge> },
    { key: "confidence", label: "Avg confidence" },
    { key: "failure", label: "Failure rate" },
    { key: "review", label: "Human review" },
    { key: "duration", label: "Avg time" },
    ...(onInspect ? [{ key: "action", label: "Action", render: (row: Record<string, unknown>) => <button className="table-action" onClick={() => onInspect(String(row.agent))}>Inspect</button> }] : []),
  ]} rows={rows.map(row => ({ id: row.agent, agent: row.agent, pipeline: row.pipeline, lastRun: row.lastRun, status: row.status, confidence: percent(row.avgConfidence), failure: percent(row.failureRate), review: percent(row.reviewRate), duration: seconds(row.avgDurationMs) }))}/>;
}

export function AdminDashboard() {
  const [params] = useSearchParams();
  const dashboard = useApi(() => api.dashboard("admin"), []);
  const audits = useApi(() => api.audits(), []);
  const catalog = useApi(() => api.agents(), []);
  const health = useApi(() => api.systemHealth(), []);
  const monitoring = useApi(() => api.monitoring(), []);
  const storage = useApi(() => api.storage(), []);
  if (dashboard.loading) return <LoadingState/>;
  if (dashboard.error) return <ErrorState error={dashboard.error} retry={dashboard.refresh}/>;
  const metrics = dashboard.data?.metrics ?? {};
  const components = health.data?.components ?? [];
  const monitorData = asArray<AgentMonitorRow>(monitoring.data);
  const records = asArray<Record<string, unknown>>(storage.data?.records);
  const auditEvents = asArray<AuditEvent>(audits.data);
  const pipelinePerformance = (catalog.data?.pipelines ?? []).map(pipeline => {
    const rows = monitorData.filter(row => row.pipeline === pipeline.id);
    const confidence = rows.length ? rows.reduce((total, row) => total + row.avgConfidence, 0) / rows.length : null;
    return { ...pipeline, confidence, healthy: rows.every(row => row.status === "healthy") };
  });
  if (params.get("view") === "health") return <><Head title="System health" detail="Measured status for the database, agent runtime, MCP server, storage, model credentials, and frontend bundle." action={<button className="button subtle" onClick={() => void health.refresh()}>Refresh health</button>}/><Card title={`Service health, checked ${health.data ? shortTime(health.data.checkedAt) : "loading"}`}>{health.loading ? <LoadingState/> : health.error ? <ErrorState error={health.error} retry={health.refresh}/> : <HealthTable components={components}/>}</Card><div className="grid two"><Card title="Runtime"><JsonViewer value={catalog.data ?? { status: "loading" }}/></Card><Card title="Session activity"><div className="metric-bars">{[["Agent runs", Number(metrics.agentRuns ?? 0), Math.max(10, Number(metrics.agentRuns ?? 0))], ["Stored assets", Number(metrics.storedAssets ?? 0), Math.max(10, Number(metrics.storedAssets ?? 0))], ["Audit events", Number(metrics.auditEvents ?? 0), Math.max(20, Number(metrics.auditEvents ?? 0))]].map(([label, value, max]) => <label key={String(label)}><span>{label}<b>{value} / {max}</b></span><progress max={Number(max)} value={Number(value)}/></label>)}</div></Card></div></>;
  return <><Head title="Admin dashboard" detail="Operational control for users, agent systems, governed data pipelines, compliance, and health."/><KpiStrip values={[{ label: "Total users", value: Number(metrics.totalUsers ?? 0) }, { label: "Active clinicians", value: Number(metrics.activeClinicians ?? 0) }, { label: "Total patients", value: Number(metrics.patients ?? 0) }, { label: "Agent runs today", value: Number(metrics.agentRuns24h ?? 0), tone: "success" }, { label: "Failed extractions", value: Number(metrics.failedExtractions ?? 0), tone: Number(metrics.failedExtractions ?? 0) > 0 ? "critical" : undefined }, { label: "Pending actions", value: Number(metrics.pendingActions ?? 0), tone: Number(metrics.pendingActions ?? 0) > 0 ? "warning" : undefined }]}/><div className="admin-grid"><Card title="System health">{health.loading ? <LoadingState/> : health.error ? <ErrorState error={health.error} retry={health.refresh}/> : <HealthTable components={components.slice(0, 4)} compact/>}</Card><Card title="Agent performance"><div className="agent-performance">{pipelinePerformance.length ? pipelinePerformance.map(pipeline => <div key={pipeline.id}><span><strong>{pipeline.name}</strong><small>{pipeline.agents.length} specialist agents</small></span><b>{pipeline.confidence === null ? "not measured" : percent(pipeline.confidence)}</b><StatusBadge tone={pipeline.confidence === null ? "info" : pipeline.healthy ? "success" : "review"}>{pipeline.confidence === null ? "No runs" : pipeline.healthy ? "Healthy" : "Degraded"}</StatusBadge></div>) : <LoadingState/>}</div></Card><Card title="Data pipeline status">{storage.loading ? <LoadingState/> : records.length ? <div className="pipeline-health">{records.slice(0, 5).map(record => <div key={String(record.id)}><span><strong>{String(record.destination)}</strong><small>{String(record.source)}</small></span><StatusBadge tone={record.status === "failed" ? "danger" : record.status === "pending" ? "review" : "success"}>{String(record.status)}</StatusBadge></div>)}</div> : <EmptyState title="No pipeline records" detail="Upload evidence and approve an extraction to see storage synchronization."/>}</Card><Card title="Recent audit events" className="span-two">{audits.loading ? <LoadingState/> : <AuditTimeline events={auditEvents}/>}</Card></div><details className="dashboard-atlas" open><summary><span><strong>System atlas</strong><small>Architecture views for platform operations</small></span></summary><DiagramAtlas defaultCategory="system" compact/></details></>;
}

export function UsersRoles() {
  const users = useApi(() => api.users(), []);
  const permissionsState = useApi(() => api.permissions(), []);
  const [role, setRole] = useState("Clinician");
  const [tab, setTab] = useState("Users");
  const [saving, setSaving] = useState(false);
  const [saveNotice, setSaveNotice] = useState("");
  const rows = asArray<ClinicalUser>(users.data);
  const roles = permissionsState.data?.roles ?? ["Admin", "Clinician", "Reviewer", "Read-only Viewer", "Data Manager"];
  const matrix = permissionsState.data?.matrix ?? [];
  const memberCount = (name: string) => rows.filter(user => user.roles.includes(name)).length;
  const togglePermission = (permission: string, name: string) => {
    if (!permissionsState.data) return;
    permissionsState.setData({
      ...permissionsState.data,
      matrix: matrix.map(row => row.permission === permission ? { ...row, grants: { ...row.grants, [name]: !row.grants[name] } } : row),
    });
  };
  const savePermissions = async () => {
    setSaving(true); setSaveNotice("");
    try {
      const saved = await api.savePermissions(matrix);
      permissionsState.setData(saved);
      setSaveNotice(`Permission matrix v${saved.version} saved and audit event recorded.`);
    } catch (reason) {
      setSaveNotice(reason instanceof Error ? reason.message : "Unable to save permissions");
    } finally { setSaving(false); }
  };
  const roleAssignments = rows.map((user, index) => ({ id: index + 1, user: user.name, roles: user.roles.join(", "), scope: user.scope, status: user.status }));
  return <><Head title="Users and roles" detail="Read-only user directory with persisted role permission policy, access scope, and audit identity."/><nav className="tabs">{["Users", "Role assignments", "Permission matrix", "Access audit"].map(name => <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>)}</nav>{tab === "Users" && <div className="users-layout"><Card title="Role directory">{roles.map(name => <button className={`role-row ${role === name ? "active" : ""}`} key={name} onClick={() => setRole(name)}><span>{name[0]}</span><div><strong>{name}</strong><small>{memberCount(name)} assigned {memberCount(name) === 1 ? "user" : "users"}</small></div></button>)}</Card><Card title="User directory">{users.loading ? <LoadingState/> : users.error ? <ErrorState error={users.error} retry={users.refresh}/> : <DenseTable columns={[{ key: "name", label: "User" }, { key: "email", label: "Email" }, { key: "roles", label: "Roles", render: row => <div className="tag-list">{(row.roles as string[]).map(item => <StatusBadge key={item} tone="info">{item}</StatusBadge>)}</div> }, { key: "scope", label: "Access scope" }, { key: "status", label: "Status", render: row => <StatusBadge tone="success">{String(row.status)}</StatusBadge> }]} rows={rows as unknown as Array<Record<string, unknown>>}/>}</Card><Card title={`${role} profile`}><div className="profile-summary"><span>{role[0]}</span><h3>{role}</h3><p>Role policy with patient and workflow-specific access controls.</p><dl className="compact-facts"><div><dt>Members</dt><dd>{memberCount(role)}</dd></div><div><dt>Default scope</dt><dd>{role === "Admin" ? "Organization" : role === "Data Manager" ? "Data platform" : "Assigned patients"}</dd></div><div><dt>Directory</dt><dd>Read-only</dd></div></dl></div></Card></div>}{tab === "Role assignments" && <Card title="Multi-role assignments">{users.loading ? <LoadingState/> : roleAssignments.length ? <DenseTable columns={[{ key: "user", label: "User" }, { key: "roles", label: "Assigned roles" }, { key: "scope", label: "Access scope" }, { key: "status", label: "Status" }]} rows={roleAssignments}/> : <EmptyState title="No users" detail="The tenant directory is empty."/>}</Card>}{tab === "Permission matrix" && <Card title={`Permission matrix v${permissionsState.data?.version ?? "pending"}`}>{permissionsState.loading ? <LoadingState/> : permissionsState.error ? <ErrorState error={permissionsState.error} retry={permissionsState.refresh}/> : <><DenseTable columns={[{ key: "permission", label: "Permission" }, ...roles.map(name => ({ key: name, label: name, render: (row: Record<string, unknown>) => <input type="checkbox" aria-label={`${String(row.permission)} for ${name}`} checked={Boolean((row.grants as Record<string, boolean>)[name])} onChange={() => togglePermission(String(row.permission), name)}/> }))]} rows={matrix.map(row => ({ id: row.permission, permission: row.permission, grants: row.grants }))}/><div className="button-row" style={{ marginTop: 12 }}><button className="button primary" disabled={saving} onClick={() => void savePermissions()}>{saving ? "Saving matrix" : "Save permission matrix"}</button>{saveNotice && <span className="muted" role="status">{saveNotice}</span>}</div></>}</Card>}{tab === "Access audit" && <AccessAudit/>}</>;
}

function AccessAudit() {
  const audits = useApi(() => api.audits(), []);
  const rows = asArray<{ event: string } & Record<string, unknown>>(audits.data).filter(event => event.event.includes("permission") || event.event.includes("config") || event.event.includes("notification"));
  return <Card title="Recent access and policy changes">{audits.loading ? <LoadingState/> : rows.length ? <DenseTable columns={[{ key: "timestamp", label: "Time", render: row => <span>{shortTime(String(row.timestamp))}</span> }, { key: "actor", label: "Actor" }, { key: "event", label: "Change" }, { key: "result", label: "Result" }]} rows={rows as unknown as Array<Record<string, unknown>>}/> : <EmptyState title="No access changes yet" detail="Permission and configuration edits appear here with their audit identity."/>}</Card>;
}

export function DataStorage() {
  const [params, setParams] = useSearchParams();
  const storage = useApi(() => api.storage(), []);
  const selected = params.get("view") ?? "overview";
  const tabs = [["overview", "Overview"], ["objects", "Cloud objects"], ["json", "JSON records"], ["relational", "Relational tables"], ["vector", "Vector indexes"], ["pipelines", "Sync jobs"], ["failed", "Failed records"], ["lineage", "Data lineage"]];
  const records = asArray<Record<string, unknown>>(storage.data?.records);
  const filtered = selected === "failed" ? records.filter(row => row.status === "failed")
    : selected === "vector" ? records.filter(row => String(row.destination).toLowerCase().includes("vector"))
    : selected === "relational" ? records.filter(row => String(row.destination).toLowerCase().includes("relational"))
    : selected === "json" ? records.filter(row => String(row.destination).toLowerCase().includes("json"))
    : selected === "objects" ? records.filter(row => String(row.destination).toLowerCase().includes("object"))
    : records;
  const failedCount = records.filter(row => row.status === "failed").length;
  return <><Head title="Data and storage management" detail="Inspect source objects, structured outputs, relational rows, vector indexes, synchronization, failures, and lineage." action={<button className="button subtle" onClick={() => void storage.refresh()}>Refresh providers</button>}/><nav className="tabs storage-tabs">{tabs.map(([value, label]) => <button key={value} className={selected === value ? "active" : ""} onClick={() => setParams({ view: value })}>{label}</button>)}</nav>{storage.loading ? <LoadingState/> : storage.error ? <ErrorState error={storage.error} retry={storage.refresh}/> : selected === "overview" ? <><div className="storage-grid">{[["Cloud Storage", Number(storage.data?.cloudCount ?? 0), "Original and processed uploads", "success"], ["JSON documents", Number(storage.data?.jsonCount ?? 0), "Verified structured extraction", "success"], ["Relational rows", Number(storage.data?.sqlCount ?? 0), "Patients, sessions, findings", "success"], ["Vector records", Number(storage.data?.vectorCount ?? 0), "Text and image embeddings", "success"], ["Audit events", Number(storage.data?.auditCount ?? 0), "Immutable workflow trail", "success"], ["Failed records", failedCount, failedCount ? "Requires administrator action" : "No failures recorded", failedCount ? "critical" : "success"]].map(([title, value, detail, tone]) => <Card key={String(title)}><div className="storage-card-head"><span className="storage-icon">{String(title).slice(0, 2).toUpperCase()}</span><StatusBadge tone={String(tone)}>{tone === "critical" ? "Action" : "Healthy"}</StatusBadge></div><h3>{String(title)}</h3><strong>{String(value)}</strong><p>{String(detail)}</p></Card>)}</div><div className="grid two"><Card title="Provider topology"><div className="topology-flow">{["Clinical source", "Cloud Storage", "Validated JSON", "Cloud SQL", "Vector Search", "Audit Logs"].map((item, index) => <div key={item}><span>{index + 1}</span><strong>{item}</strong>{index < 5 && <b>to</b>}</div>)}</div></Card><Card title="Live provider state"><JsonViewer value={storage.data}/></Card></div><InlineDiagram id="10-memory-architecture" title="Storage architecture"/></> : selected === "lineage" ? <LineageView records={records} patient={params.get("patient")}/> : <Card title={`${tabs.find(([value]) => value === selected)?.[1]} - ${filtered.length} records`}>{filtered.length ? <DenseTable columns={[{ key: "id", label: "Record" }, { key: "source", label: "Source" }, { key: "destination", label: "Destination" }, { key: "status", label: "Status", render: row => <StatusBadge tone={row.status === "failed" ? "danger" : row.status === "pending" ? "review" : "success"}>{String(row.status)}</StatusBadge> }, { key: "updated", label: "Updated", render: row => <span>{shortTime(String(row.updated))}</span> }, { key: "owner", label: "Owner" }, { key: "patientId", label: "Patient" }, { key: "sessionId", label: "Session" }, { key: "error", label: "Error details", render: row => <span>{String(row.error) || "none"}</span> }]} rows={filtered}/> : <EmptyState title="No records in this view" detail="Upload clinical evidence and approve an extraction to populate storage pipelines."/>}</Card>}</>;
}

function LineageView({ records, patient }: { records: Array<Record<string, unknown>>; patient: string | null }) {
  const scoped = patient ? records.filter(row => row.patientId === patient) : records;
  return <div className="lineage-view"><Card title={`Patient data lineage${patient ? ` - ${patient}` : ""}`}>{scoped.length ? <div className="lineage-nodes">{scoped.slice(0, 6).map((row, index) => <div key={String(row.id)}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{String(row.source)}</strong><code>{String(row.id)}</code><small>{String(row.destination)} - {String(row.status)}</small></div><StatusBadge tone={row.status === "failed" ? "danger" : "success"}>{row.status === "failed" ? "Failed" : "Verified"}</StatusBadge></div>)}</div> : <EmptyState title="No lineage yet" detail="Lineage nodes appear after uploads and approved extractions create storage records."/>}</Card><Card title="Lineage policy"><p>Each consequential clinical output retains its source asset, review identity, storage receipts, and immutable audit event.</p></Card></div>;
}

export function AgentConfiguration() {
  const [params] = useSearchParams();
  const configState = useApi(() => api.config(), []);
  const catalog = useApi(() => api.agents(), []);
  const monitoring = useApi(() => api.monitoring(), []);
  const audits = useApi(() => api.audits(), []);
  const [section, setSection] = useState(params.get("view") === "settings" ? "Safety settings" : "Agent monitoring");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [saveError, setSaveError] = useState("");
  const [disabledAgents, setDisabledAgents] = useState<string[]>([]);
  if (configState.loading) return <LoadingState/>;
  if (configState.error || !configState.data) return <ErrorState error={configState.error ?? new Error("Configuration unavailable")} retry={configState.refresh}/>;
  const config = configState.data;
  const update = <K extends keyof typeof config>(key: K, value: typeof config[K]) => configState.setData({ ...config, [key]: value });
  const save = async () => {
    setSaving(true); setNotice(""); setSaveError("");
    try {
      configState.setData(await api.saveConfig(config));
      setNotice("Configuration version saved and audit event recorded.");
    } catch (reason) {
      setSaveError(reason instanceof Error ? reason.message : "Unable to save configuration");
    } finally {
      setSaving(false);
    }
  };
  const sections = ["Agent monitoring", "Natural Language Orchestrator", "Image Extraction", "Patient Q&A", "Database Intelligence", "Routing rules", "Safety settings", "Agent logs"];
  const currentPipeline = section === "Image Extraction" ? catalog.data?.pipelines.find(item => item.id === "extraction") : section === "Patient Q&A" ? catalog.data?.pipelines.find(item => item.id === "qa") : section === "Database Intelligence" ? catalog.data?.pipelines.find(item => item.id === "database") : undefined;
  const auditRows = asArray<{ timestamp: string; actor: string; event: string; result: string; entity: string }>(audits.data);
  const monitorRows = asArray<AgentMonitorRow>(monitoring.data);
  const logRows = auditRows.slice(0, 12).map((event, index) => ({ id: index + 1, time: shortTime(event.timestamp), agent: event.actor, event: event.event.replaceAll("_", " "), status: event.result, trace: event.entity }));

  const renderSection = () => {
    if (section === "Agent monitoring") return <><Card title="Agent monitoring">{monitoring.loading ? <LoadingState/> : monitoring.error ? <ErrorState error={monitoring.error} retry={monitoring.refresh}/> : <MonitoringTable rows={monitorRows} onInspect={() => setSection("Agent logs")}/>}</Card><InlineDiagram id="06-agent-hierarchy" title="Monitoring architecture"/></>;
    if (currentPipeline) return <><Card title={currentPipeline.name}><div className="pipeline-config">{currentPipeline.agents.map((agent, index) => <div key={agent}><span>{index + 1}</span><div><strong>{agent.replaceAll("_", " ")}</strong><small>Google ADK specialist. Tool access governed.</small></div><label className="toggle"><input type="checkbox" checked={!disabledAgents.includes(agent)} onChange={() => setDisabledAgents(current => current.includes(agent) ? current.filter(item => item !== agent) : [...current, agent])}/><span>Enabled</span></label><button className="button subtle" onClick={() => setSection("Agent logs")}>Logs</button></div>)}</div></Card><Card title="Pipeline controls"><label>Confidence threshold<div className="range-row"><input type="range" min="0" max="100" value={config.reviewThreshold} onChange={event => update("reviewThreshold", Number(event.target.value))}/><strong>{config.reviewThreshold}%</strong></div></label><div className="locked-policy"><span><strong>Require human review</strong><small>Gate consequential persistence and execution</small></span><StatusBadge tone="review">Required</StatusBadge></div></Card></>;
    if (section === "Natural Language Orchestrator") return <Card title="Natural Language Orchestrator"><JsonViewer value={catalog.data ?? { framework: "Google ADK", status: "loading" }}/><h3>Routing precedence</h3><ol className="routing-rules"><li>Patient image, scan, OCR, or uploaded evidence to Session Image Extraction</li><li>Patient-scoped question, history, image evidence, or citation to Multimodal Q&A</li><li>Population count, trend, cohort, SQL, or chart to Database Intelligence</li></ol></Card>;
    if (section === "Routing rules") return <Card title="Agent routing rules"><DenseTable columns={[{ key: "priority", label: "Priority" }, { key: "intent", label: "Detected intent" }, { key: "workflow", label: "Selected workflow" }, { key: "permission", label: "Required permission" }]} rows={[{ id: 1, priority: 1, intent: "Uploaded clinical evidence", workflow: "Image Extraction", permission: "asset:write" }, { id: 2, priority: 2, intent: "Patient-scoped question", workflow: "Patient Q&A", permission: "patient:read" }, { id: 3, priority: 3, intent: "Population analytics", workflow: "Database Intelligence", permission: "database:read" }]}/></Card>;
    if (section === "Safety settings") return <div className="grid config"><Card title="Confidence policy"><label>Automatic approval threshold<div className="range-row"><input type="range" min="0" max="100" value={config.autoApprovalThreshold} onChange={event => update("autoApprovalThreshold", Number(event.target.value))}/><strong>{config.autoApprovalThreshold}%</strong></div></label><label>Clinical review threshold<div className="range-row"><input type="range" min="0" max="100" value={config.reviewThreshold} onChange={event => update("reviewThreshold", Number(event.target.value))}/><strong>{config.reviewThreshold}%</strong></div></label><label>Maximum concurrent agent runs<input type="number" min="1" max="50" value={config.maxConcurrentRuns} onChange={event => update("maxConcurrentRuns", Number(event.target.value))}/></label></Card><Card title="Execution policy"><label className="toggle"><span><strong>Database intelligence enabled</strong><small>Allow reviewed SELECT-only population queries</small></span><input type="checkbox" checked={config.databaseEnabled} onChange={event => update("databaseEnabled", event.target.checked)}/></label><div className="locked-policy"><span><strong>Mandatory human review</strong><small>Extraction persistence requires explicit clinician approval</small></span><StatusBadge tone="review">Required</StatusBadge></div><div className="locked-policy"><span><strong>PII and secret redaction</strong><small>Security callbacks before tools and output</small></span><StatusBadge tone="success">Active</StatusBadge></div></Card><Card title="Current version"><JsonViewer value={config}/></Card><InlineDiagram id="11-security-pipeline" title="Safety architecture"/></div>;
    return <Card title="Agent logs">{audits.loading ? <LoadingState/> : logRows.length ? <DenseTable columns={[{ key: "time", label: "Timestamp" }, { key: "agent", label: "Actor" }, { key: "event", label: "Event" }, { key: "status", label: "Status" }, { key: "trace", label: "Entity" }]} rows={logRows}/> : <EmptyState title="No logged events yet" detail="Workflow, review, and configuration events appear here as they happen."/>}</Card>;
  };

  return <><Head title="Agent configuration and monitoring" detail="Inspect the multi-agent engine, routing, thresholds, safety gates, logs, and runtime performance." action={<button className="button primary" disabled={saving} onClick={() => void save()}>{saving ? "Saving version" : "Save new version"}</button>}/>{notice && <div className="notice success">{notice}</div>}{saveError && <div className="notice error" role="alert">{saveError}</div>}<div className="configuration-layout"><Card title="Configuration sections">{sections.map(name => <button className={`config-nav-row ${section === name ? "active" : ""}`} key={name} onClick={() => setSection(name)}><span>{name}</span></button>)}</Card><section>{renderSection()}</section><Card title="Runtime status"><dl className="compact-facts"><div><dt>Framework</dt><dd>{catalog.data?.framework ?? "Google ADK"}</dd></div><div><dt>Mode</dt><dd>{catalog.data?.executionMode ?? "local"}</dd></div><div><dt>Orchestrator</dt><dd>{catalog.data?.orchestrator ?? "clinical_orchestrator"}</dd></div><div><dt>Config version</dt><dd>{config.version}</dd></div></dl><StatusBadge tone="success">All callbacks active</StatusBadge></Card></div></>;
}
