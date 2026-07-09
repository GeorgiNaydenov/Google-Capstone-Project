import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";
import { AuditDetailModal, AuditTimeline, Card, DenseTable, EmptyState, ErrorState, Icon, JsonViewer, KpiStrip, LoadingState, StatusBadge, useToast } from "../components";
import { useClinical } from "../context";
import { DiagramAtlas } from "../components/DiagramAtlas";
import { InlineDiagram } from "../components/InlineDiagram";
import { useApi } from "../useApi";
import type { AgentMonitorRow, AuditEvent, ClinicalUser, ComponentHealth } from "../types";

const asArray = <T,>(value: unknown): T[] => Array.isArray(value) ? value as T[] : [];
const TABLE_PREVIEW_LIMIT = 160;

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
    ...(onInspect ? [{ key: "action", label: "Action", render: (row: Record<string, unknown>) => <button className="table-action" onClick={() => onInspect(String(row.pipeline))}>Inspect</button> }] : []),
  ]} rows={rows.map(row => ({ id: row.agent, agent: row.agent, pipeline: row.pipeline, lastRun: row.lastRun, status: row.status, confidence: percent(row.avgConfidence), failure: percent(row.failureRate), review: percent(row.reviewRate), duration: seconds(row.avgDurationMs) }))}/>;
}

export function AdminDashboard() {
  const [params] = useSearchParams();
  const [selectedAudit, setSelectedAudit] = useState<AuditEvent | null>(null);
  const dashboard = useApi(() => api.dashboard("admin"), []);
  const audits = useApi(() => api.audits(), []);
  const catalog = useApi(() => api.agents(), []);
  const health = useApi(() => api.systemHealth(), []);
  const monitoring = useApi(() => api.monitoring(), []);
  const storage = useApi(() => api.storage(), []);
  if (dashboard.loading) return <LoadingState/>;
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
  const generatedKpis = [
    { label: "Total users", value: Number(metrics.totalUsers ?? 0) },
    { label: "Active clinicians", value: Number(metrics.activeClinicians ?? 0) },
    { label: "Total patients", value: Number(metrics.patients ?? 0) },
    { label: "Agent runs today", value: Number(metrics.agentRuns24h ?? 0), tone: "success" },
    { label: "Stored assets", value: Number(metrics.storedAssets ?? storage.data?.cloudCount ?? 0), tone: "success" },
    { label: "Database rows", value: Number(metrics.databaseRows ?? storage.data?.sqlCount ?? 0), tone: "success" },
    { label: "KB documents", value: Number(metrics.knowledgeBaseDocuments ?? 0) },
    { label: "Query examples", value: Number(metrics.queryExamples ?? 0) },
    { label: "Failed extractions", value: Number(metrics.failedExtractions ?? 0), tone: Number(metrics.failedExtractions ?? 0) > 0 ? "critical" : undefined },
    { label: "Pending actions", value: Number(metrics.pendingActions ?? 0), tone: Number(metrics.pendingActions ?? 0) > 0 ? "warning" : undefined },
  ];
  if (params.get("view") === "health") return <><Head title="System health" detail="Measured status for the database, agent runtime, MCP server, storage, model credentials, and frontend bundle." action={<button className="button subtle" onClick={() => void health.refresh()}>Refresh health</button>}/><Card title={`Service health, checked ${health.data ? shortTime(health.data.checkedAt) : "loading"}`}>{health.loading ? <LoadingState/> : health.error ? <ErrorState error={health.error} retry={health.refresh}/> : <HealthTable components={components}/>}</Card><div className="grid two"><Card title="Runtime"><JsonViewer value={catalog.data ?? { status: "loading" }}/></Card><Card title="Session activity"><div className="metric-bars">{[["Agent runs", Number(metrics.agentRuns ?? 0), Math.max(10, Number(metrics.agentRuns ?? 0))], ["Stored assets", Number(metrics.storedAssets ?? 0), Math.max(10, Number(metrics.storedAssets ?? 0))], ["Audit events", Number(metrics.auditEvents ?? 0), Math.max(20, Number(metrics.auditEvents ?? 0))]].map(([label, value, max]) => <label key={String(label)}><span>{label}<b>{value} / {max}</b></span><progress max={Number(max)} value={Number(value)}/></label>)}</div></Card></div></>;
  return <><Head title="Admin dashboard" detail="Operational control for users, agent systems, governed data pipelines, compliance, and health."/>{dashboard.error && <div className="notice warning" role="status">Live dashboard metrics are unavailable. Showing the rest of the workspace from failover-capable services.</div>}<KpiStrip values={generatedKpis}/><div className="admin-grid"><Card title="System health">{health.loading ? <LoadingState/> : health.error ? <ErrorState error={health.error} retry={health.refresh}/> : <HealthTable components={components.slice(0, 4)} compact/>}</Card><Card title="Agent performance"><div className="agent-performance">{pipelinePerformance.length ? pipelinePerformance.map(pipeline => <div key={pipeline.id}><span><strong>{pipeline.name}</strong><small>{pipeline.agents.length} specialist agents</small></span><b>{pipeline.confidence === null ? "not measured" : percent(pipeline.confidence)}</b><StatusBadge tone={pipeline.confidence === null ? "info" : pipeline.healthy ? "success" : "review"}>{pipeline.confidence === null ? "No runs" : pipeline.healthy ? "Healthy" : "Degraded"}</StatusBadge></div>) : <EmptyState title="Agent catalog unavailable" detail="Agent performance appears when the catalog or failover snapshot is available."/>}</div></Card><Card title="Data pipeline status">{storage.loading ? <LoadingState/> : records.length ? <div className="pipeline-health">{records.slice(0, 5).map(record => <div key={String(record.id)}><span><strong>{String(record.destination)}</strong><small>{String(record.source)}</small></span><StatusBadge tone={record.status === "failed" ? "danger" : record.status === "pending" ? "review" : "success"}>{String(record.status)}</StatusBadge></div>)}</div> : <EmptyState title="No pipeline records" detail="Upload evidence and approve an extraction to see storage synchronization."/>}</Card><Card title="Recent audit events" className="span-two">{audits.loading ? <LoadingState/> : audits.error ? <ErrorState error={audits.error} retry={audits.refresh}/> : <AuditTimeline events={auditEvents} onSelect={setSelectedAudit}/>}</Card></div><details className="dashboard-atlas" open><summary><span><strong>System atlas</strong><small>Architecture views for platform operations</small></span></summary><DiagramAtlas defaultCategory="system" compact/></details><AuditDetailModal event={selectedAudit} onClose={() => setSelectedAudit(null)}/></>;
}

export function UsersRoles() {
  const users = useApi(() => api.users(), []);
  const permissionsState = useApi(() => api.permissions(), []);
  const [role, setRole] = useState("Clinician");
  const [tab, setTab] = useState("Users");
  const [saving, setSaving] = useState(false);
  const [saveNotice, setSaveNotice] = useState("");
  const toast = useToast();
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
      toast(`Permission matrix v${saved.version} saved`);
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "Unable to save permissions";
      setSaveNotice(message);
      toast(message, "error");
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
  const [selectedJson, setSelectedJson] = useState<Record<string, unknown> | null>(null);
  const storage = useApi(() => api.storage(), []);
  const selected = params.get("view") ?? "overview";
  const tabs = [
    ["overview", "Overview"],
    ["objects", "Object Storage"],
    ["pipelines", "Data Pipelines"],
    ["json", "JSON Document Store"],
    ["relational", "Relational Database"],
    ["vector", "Vector Search Index"],
    ["lineage", "Data Lineage"],
    ["failed", "Sync Failures"],
  ];
  const records = asArray<Record<string, unknown>>(storage.data?.records);
  const assets = asArray<Record<string, unknown>>(storage.data?.assets);
  const persisted = asArray<Record<string, unknown>>(storage.data?.persistedExtractions);
  const objectRows = assets.length ? assets.map(asset => ({ id: asset.assetId ?? asset.id, file: asset.filename ?? asset.source, type: asset.contentType ?? "clinical evidence", size: `${Math.max(1, Math.round(Number(asset.sizeBytes ?? 0) / 1024))} KB`, patient: asset.patientId ?? "-", location: asset.objectPath ?? asset.bucket ?? "Object storage", stored: shortTime(String(asset.createdAt ?? "")) })) : records.filter(row => String(row.destination).toLowerCase().includes("object")).map(row => ({ id: row.id, file: row.source, type: "clinical evidence", size: "-", patient: row.patientId, location: row.destination, stored: shortTime(String(row.updated)) }));
  const jsonRows = persisted.length ? persisted.map(row => ({ id: row.jsonReceipt ?? row.runId, run: row.runId, patient: row.patientId ?? "-", session: row.sessionId ?? "-", receipt: row.jsonReceipt ?? "pending", status: "synced", confidence: row.confidence != null ? percent(Number(row.confidence)) : "-" })) : records.filter(row => String(row.destination).toLowerCase().includes("json")).map(row => ({ id: row.id, run: row.source, patient: row.patientId, session: row.sessionId, receipt: row.id, status: row.status, confidence: "-" }));
  const relationalRows = records.filter(row => String(row.destination).toLowerCase().includes("relational")).map(row => ({ id: row.id, table: "clinical_sessions", source: row.source, patient: row.patientId, session: row.sessionId || "-", status: row.status, updated: shortTime(String(row.updated)) }));
  const vectorRows = records.filter(row => String(row.destination).toLowerCase().includes("vector")).map(row => ({ id: row.id, index: "clinical-evidence", namespace: row.patientId || "tenant", source: row.source, chunks: row.status === "pending" ? "queued" : "3 text + image chunks", status: row.status, updated: shortTime(String(row.updated)) }));
  const pipelineRows = records.map(row => ({ id: row.id, source: row.source, target: row.destination, owner: row.owner, patient: row.patientId || "-", state: row.status, updated: shortTime(String(row.updated)) }));
  const failedCount = records.filter(row => row.status === "failed").length;
  const failedRows = records.filter(row => row.status === "failed").map(row => ({ id: row.id, source: row.source, target: row.destination, owner: row.owner, impact: "Read-only fallback active", action: "Refresh provider after API gateway recovers", error: row.error || "No error detail" }));
  
  const formatVal = (val: number) => new Intl.NumberFormat().format(val);
  const statusCell = (row: Record<string, unknown>) => <StatusBadge tone={row.status === "failed" || row.state === "failed" ? "danger" : row.status === "pending" || row.state === "pending" ? "review" : "success"}>{String(row.status ?? row.state)}</StatusBadge>;
  const renderTable = (title: string, rows: Array<Record<string, unknown>>, columns: Array<{ key: string; label: string; render?: (row: Record<string, unknown>) => React.ReactNode }>, detail: string, onRow?: (row: Record<string, unknown>) => void) => <Card title={`${title} - ${formatVal(rows.length)} ${rows.length === 1 ? "record" : "records"}`} className="storage-panel">{rows.length ? <DenseTable columns={columns} rows={rows} limit={TABLE_PREVIEW_LIMIT} onRow={onRow}/> : <EmptyState title={`No ${title.toLowerCase()}`} detail={detail}/>}</Card>;
  
  const cloudCount = Number(storage.data?.cloudCount ?? objectRows.length);
  const jsonCount = Number(storage.data?.jsonCount ?? jsonRows.length);
  const sqlCount = Number(storage.data?.sqlCount ?? relationalRows.length);
  const vectorCount = Number(storage.data?.vectorCount ?? vectorRows.length);
  const auditCount = Number(storage.data?.auditCount ?? 0);
  const seededFailedCount = Number(storage.data?.failedCount ?? failedCount);
  const providerRows = [
    { id: "cloud", provider: "Object storage", count: cloudCount, state: cloudCount ? "synced" : "empty", responsibility: "Original uploads and generated visual evidence" },
    { id: "json", provider: "JSON document store", count: jsonCount, state: jsonCount ? "synced" : "empty", responsibility: "Reviewed structured extraction payloads" },
    { id: "relational", provider: "Relational database", count: sqlCount, state: sqlCount ? "synced" : "empty", responsibility: "Queryable patient/session facts" },
    { id: "vector", provider: "Vector search", count: vectorCount, state: vectorRows.some(row => row.status === "pending") ? "pending" : vectorCount ? "synced" : "empty", responsibility: "Q&A retrieval over text and image evidence" },
    { id: "audit", provider: "Audit log", count: auditCount, state: "recording", responsibility: "Immutable user and agent events" },
  ];

  const iconMap: Record<string, string> = {
    "Cloud Storage": "cloud",
    "JSON documents": "report",
    "Relational rows": "database",
    "Vector records": "vector",
    "Audit events": "shield",
    "Failed records": "pulse"
  };

  const topologyIcons = ["upload", "cloud", "report", "database", "vector", "shield"];

  return <><Head title="Data and storage management" detail="Inspect source objects, structured outputs, relational rows, vector indexes, synchronization, failures, and lineage." action={<button className="button subtle" onClick={() => void storage.refresh()}>Refresh providers</button>}/><nav className="tabs storage-tabs">{tabs.map(([value, label]) => <button key={value} className={selected === value ? "active" : ""} onClick={() => setParams({ view: value })}>{label}</button>)}</nav>{storage.loading ? <LoadingState/> : storage.error ? <ErrorState error={storage.error} retry={storage.refresh}/> : selected === "overview" ? <><div className="storage-grid">{[["Cloud Storage", cloudCount, "Original and processed uploads", "success"], ["JSON documents", jsonCount, "Reviewed structured extraction", "success"], ["Relational rows", sqlCount, "Patients, sessions, findings", "success"], ["Vector records", vectorCount, "Text and image embeddings", vectorRows.some(row => row.status === "pending") ? "review" : "success"], ["Audit events", auditCount, "Immutable workflow trail", "success"], ["Failed records", seededFailedCount, seededFailedCount ? "Provider refresh needs attention" : "No failures recorded", seededFailedCount ? "critical" : "success"]].map(([title, value, detail, tone]) => <Card key={String(title)}><div className="storage-card-head"><span className="storage-icon" style={{ background: tone === "critical" ? "#fee2e2" : tone === "review" ? "#fef3c7" : "#dbeafe", color: tone === "critical" ? "#991b1b" : tone === "review" ? "#92400e" : "var(--blue-dark)" }}><Icon name={iconMap[String(title)] || "cloud"} size={16}/></span><StatusBadge tone={String(tone)}>{tone === "critical" ? "Action" : tone === "review" ? "Pending" : "Healthy"}</StatusBadge></div><h3>{String(title)}</h3><strong>{formatVal(Number(value))}</strong><p>{String(detail)}</p></Card>)}</div><div className="grid two"><Card title="Provider topology"><div className="topology-flow">{["Clinical upload", "Object storage", "Reviewed JSON", "Relational database", "Vector index", "Audit log"].map((item, index) => <div key={item}><span><Icon name={topologyIcons[index]} size={15}/></span><strong>{item}</strong>{index < 5 && <b>to</b>}</div>)}</div></Card><Card title="Provider inventory"><DenseTable columns={[{ key: "provider", label: "Provider" }, { key: "count", label: "Records", render: (row: Record<string, unknown>) => <span>{formatVal(Number(row.count))}</span> }, { key: "state", label: "State", render: statusCell }, { key: "responsibility", label: "Responsibility" }]} rows={providerRows}/></Card></div><InlineDiagram id="16-document-ingestion-flow" title="Evidence ingestion and storage flow"/></> : selected === "objects" ? renderTable("Object Storage", objectRows, [{ key: "file", label: "File" }, { key: "type", label: "Type" }, { key: "size", label: "Size" }, { key: "patient", label: "Patient" }, { key: "location", label: "Storage location" }, { key: "stored", label: "Stored" }], "Upload evidence to populate object storage.") : selected === "json" ? renderTable("JSON Document Store", jsonRows, [{ key: "run", label: "Run" }, { key: "patient", label: "Patient" }, { key: "session", label: "Session" }, { key: "receipt", label: "Receipt" }, { key: "confidence", label: "Confidence" }, { key: "status", label: "Status", render: statusCell }], "Approve an extraction to create structured JSON receipts.", row => setSelectedJson(persisted.find(entry => (entry.jsonReceipt ?? entry.runId) === row.id) ?? row)) : selected === "relational" ? renderTable("Relational Database", relationalRows, [{ key: "table", label: "Table" }, { key: "source", label: "Source" }, { key: "patient", label: "Patient" }, { key: "session", label: "Session" }, { key: "status", label: "Status", render: statusCell }, { key: "updated", label: "Updated" }], "Approved extraction fields appear as relational rows.") : selected === "vector" ? renderTable("Vector Search Index", vectorRows, [{ key: "index", label: "Index" }, { key: "namespace", label: "Namespace" }, { key: "source", label: "Source" }, { key: "chunks", label: "Chunks" }, { key: "status", label: "Status", render: statusCell }, { key: "updated", label: "Updated" }], "Indexed text and image evidence appears after vector synchronization.") : selected === "pipelines" ? renderTable("Data Pipelines", pipelineRows, [{ key: "source", label: "Source" }, { key: "target", label: "Target" }, { key: "owner", label: "Owner" }, { key: "patient", label: "Patient" }, { key: "state", label: "State", render: statusCell }, { key: "updated", label: "Updated" }], "Pipeline jobs appear after uploads, review decisions, and provider syncs.") : selected === "failed" ? renderTable("Sync Failures", failedRows, [{ key: "source", label: "Source" }, { key: "target", label: "Target" }, { key: "owner", label: "Owner" }, { key: "impact", label: "Impact" }, { key: "action", label: "Next action" }, { key: "error", label: "Error detail" }], "No failed storage records are currently present.") : <LineageView records={records} patient={params.get("patient")}/>}{selectedJson && <div className="modal-backdrop" onClick={() => setSelectedJson(null)}><section className="source-viewer" role="dialog" aria-modal="true" aria-label="Structured JSON record" onClick={event => event.stopPropagation()}>
    <header><div><span className="eyebrow">JSON document store</span><h2>Structured extraction payload</h2></div><button className="icon-button" onClick={() => setSelectedJson(null)} aria-label="Close record">x</button></header>
    <div className="agent-meta"><div><span className="eyebrow">Run</span><code>{String(selectedJson.runId ?? selectedJson.run ?? "-")}</code></div><div><span className="eyebrow">Patient</span><code>{String(selectedJson.patientId ?? selectedJson.patient ?? "-")}</code></div><div><span className="eyebrow">Session</span><code>{String(selectedJson.sessionId ?? selectedJson.session ?? "-")}</code></div><div><span className="eyebrow">Confidence</span><strong>{selectedJson.confidence != null ? percent(Number(selectedJson.confidence)) : "-"}</strong></div></div>
    <JsonViewer value={selectedJson.fields ?? selectedJson}/>
    {Array.isArray(selectedJson.receipts) && <div className="receipt-list">{(selectedJson.receipts as Array<Record<string, unknown>>).map(receipt => <div key={String(receipt.target)}><span>{String(receipt.target)}</span><StatusBadge tone={receipt.status === "synced" ? "success" : "review"}>{String(receipt.status)}</StatusBadge><code>{String(receipt.receiptId ?? "pending")}</code></div>)}</div>}
    <footer><code>{String(selectedJson.jsonReceipt ?? selectedJson.runId ?? "")}</code></footer>
  </section></div>}</>;
}

function LineageView({ records, patient }: { records: Array<Record<string, unknown>>; patient: string | null }) {
  const [selectedPatient, setSelectedPatient] = useState<string>(patient ?? "");
  const patients = [...new Set(records.map(row => String(row.patientId ?? "")).filter(Boolean))];
  const scoped = selectedPatient ? records.filter(row => row.patientId === selectedPatient) : records;

  const lineageGroups = useMemo(() => {
    const groups: Array<{
      source: { id: string; name: string; destination: string; status: string; updated: string; patientId: string };
      pipeline: string;
      destinations: Array<{ id: string; destination: string; status: string; updated: string; owner: string }>;
    }> = [];

    const uploads = scoped.filter(r => r.destination === "Object storage");
    const receipts = scoped.filter(r => r.destination !== "Object storage");

    uploads.forEach(upload => {
      const uploadNum = String(upload.id).match(/\d+/)?.[0] || "";
      const matchingReceipts = receipts.filter(r => {
        const rNum = String(r.source).match(/\d+/)?.[0] || String(r.id).match(/\d+/)?.[0] || "";
        return r.patientId === upload.patientId && (uploadNum === "" || rNum === uploadNum);
      });

      groups.push({
        source: {
          id: String(upload.id),
          name: String(upload.source),
          destination: "Object storage",
          status: String(upload.status),
          updated: String(upload.updated),
          patientId: String(upload.patientId),
        },
        pipeline: matchingReceipts.length > 0 ? String(matchingReceipts[0].source) : "Ingestion & Sync",
        destinations: matchingReceipts.map(r => ({
          id: String(r.id),
          destination: String(r.destination),
          status: String(r.status),
          updated: String(r.updated),
          owner: String(r.owner),
        })),
      });
    });

    const sessionSources = Array.from(new Set(receipts.filter(r => String(r.source).startsWith("Session ")).map(r => r.source)));
    sessionSources.forEach(sourceName => {
      const sessionReceipts = receipts.filter(r => r.source === sourceName);
      if (sessionReceipts.length === 0) return;
      
      const first = sessionReceipts[0];
      const alreadyGrouped = groups.some(g => g.pipeline === sourceName || g.destinations.some(d => d.id === first.id));
      if (alreadyGrouped) return;

      groups.push({
        source: {
          id: String(first.sessionId || first.id),
          name: String(sourceName),
          destination: "Source Session",
          status: "synced",
          updated: String(first.updated),
          patientId: String(first.patientId),
        },
        pipeline: "Showcase Data Sync",
        destinations: sessionReceipts.map(r => ({
          id: String(r.id),
          destination: String(r.destination),
          status: String(r.status),
          updated: String(r.updated),
          owner: String(r.owner),
        })),
      });
    });

    return groups;
  }, [scoped]);

  return (
    <>
      <Card title="Patient data lineage" action={patients.length > 1 ? <select className="organization-select" aria-label="Scope lineage to patient" value={selectedPatient} onChange={event => setSelectedPatient(event.target.value)}><option value="">All patients</option>{patients.map(id => <option key={id} value={id}>{id}</option>)}</select> : undefined}>
        <p className="muted" style={{ margin: "0 16px 14px" }}>
          Tracing source assets and clinical evidence through ingestion, structuring agents, relational generation, and semantic vector indexing.
        </p>
      </Card>
      <div className="lineage-view">
        <div className="lineage-groups-list" style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1, minWidth: 0 }}>
          {lineageGroups.map(group => (
            <Card key={group.source.id} title={`${group.source.name} Lineage Flow`} className="lineage-flow-card">
              <div className="lineage-chain-flow">
                
                <div className="lineage-flow-node root-node">
                  <span className="node-icon"><Icon name="cloud" size={16}/></span>
                  <div className="node-info">
                    <span className="eyebrow">SOURCE</span>
                    <strong>{group.source.name}</strong>
                    <small>{group.source.destination} · {group.source.id}</small>
                  </div>
                  <StatusBadge tone="success">{group.source.status}</StatusBadge>
                </div>

                <div className="lineage-flow-arrow">
                  <Icon name="chevron" size={16}/>
                </div>

                <div className="lineage-flow-node pipeline-node">
                  <span className="node-icon"><Icon name="pulse" size={16}/></span>
                  <div className="node-info">
                    <span className="eyebrow">PIPELINE PROCESS</span>
                    <strong>{group.pipeline}</strong>
                    <small>Storage Agent</small>
                  </div>
                  <StatusBadge tone="success">processed</StatusBadge>
                </div>

                <div className="lineage-flow-arrow">
                  <Icon name="chevron" size={16}/>
                </div>

                <div className="lineage-destinations-column">
                  <span className="eyebrow">PERSISTED STORES</span>
                  <div className="lineage-destinations-list">
                    {group.destinations.map(dest => {
                      const destIcon = dest.destination.includes("JSON") ? "report" : dest.destination.includes("Relational") ? "database" : "vector";
                      return (
                        <div key={dest.id} className="lineage-flow-node dest-node">
                          <span className="node-icon"><Icon name={destIcon} size={14}/></span>
                          <div className="node-info">
                            <strong>{dest.destination}</strong>
                            <small>ID: {dest.id} · {dest.owner}</small>
                          </div>
                          <StatusBadge tone={dest.status === "failed" ? "danger" : "success"}>{dest.status}</StatusBadge>
                        </div>
                      );
                    })}
                    {group.destinations.length === 0 && (
                      <div className="lineage-flow-node dest-node empty-dest">
                        <small>No outputs found. Run extraction to sync.</small>
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </Card>
          ))}
          {lineageGroups.length === 0 && (
            <EmptyState title="No lineage paths" detail="Upload a clinical file or run a sync pipeline to generate lineage trees."/>
          )}
        </div>
        <Card title="Lineage policy" className="lineage-policy-card">
          <p>Each consequential clinical output retains its source asset, review identity, storage receipts, and immutable audit event.</p>
        </Card>
      </div>
    </>
  );
}

export function AgentConfiguration() {
  const [params] = useSearchParams();
  // Clinicians can inspect every section but not change anything: controls
  // render disabled and the save action is replaced by a read-only badge.
  const { role } = useClinical();
  const readOnly = role !== "admin";
  const configState = useApi(() => api.config(), []);
  const catalog = useApi(() => api.agents(), []);
  const monitoring = useApi(() => api.monitoring(), []);
  const audits = useApi(() => api.audits(), []);
  const [section, setSection] = useState(params.get("view") === "settings" ? "Safety settings" : "Agent monitoring");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [saveError, setSaveError] = useState("");
  const [disabledAgents, setDisabledAgents] = useState<string[]>([]);
  const [logFilter, setLogFilter] = useState<string | null>(null);
  const [selectedAudit, setSelectedAudit] = useState<AuditEvent | null>(null);
  const toast = useToast();
  if (configState.loading) return <LoadingState/>;
  if (configState.error || !configState.data) return <ErrorState error={configState.error ?? new Error("Configuration unavailable")} retry={configState.refresh}/>;
  const config = configState.data;
  const update = <K extends keyof typeof config>(key: K, value: typeof config[K]) => configState.setData({ ...config, [key]: value });
  const save = async () => {
    setSaving(true); setNotice(""); setSaveError("");
    try {
      const saved = await api.saveConfig(config);
      configState.setData(saved);
      setNotice("Configuration version saved and audit event recorded.");
      toast(`Agent configuration v${saved.version} saved`);
    } catch (reason) {
      const message = reason instanceof Error ? reason.message : "Unable to save configuration";
      setSaveError(message);
      toast(message, "error");
    } finally {
      setSaving(false);
    }
  };
  const sections = ["Agent monitoring", "Natural Language Orchestrator", "Image Extraction", "Patient Q&A", "Population Insights", "Routing rules", "Safety settings", "Agent logs"];
  const currentPipeline = section === "Image Extraction" ? catalog.data?.pipelines.find(item => item.id === "extraction") : section === "Patient Q&A" ? catalog.data?.pipelines.find(item => item.id === "qa") : section === "Population Insights" ? catalog.data?.pipelines.find(item => item.id === "database") : undefined;
  const auditRows = asArray<AuditEvent>(audits.data);
  const monitorRows = asArray<AgentMonitorRow>(monitoring.data);
  // Workflow-specific vocabulary so "Logs" from a pipeline lands on that
  // pipeline's events instead of the generic unfiltered audit slice.
  const logKeywords: Record<string, string[]> = { extraction: ["extraction", "upload", "asset"], qa: ["question", "qa", "multimodal", "knowledge"], database: ["database", "query", "sql"] };
  const openLogs = (pipeline: string | null) => { setLogFilter(pipeline); setSection("Agent logs"); };
  const filteredAudits = logFilter ? auditRows.filter(event => (logKeywords[logFilter] ?? [logFilter.toLowerCase()]).some(keyword => event.event.toLowerCase().includes(keyword) || event.actor.toLowerCase().includes(keyword))) : auditRows;
  const logRows = filteredAudits.slice(0, 12).map(event => ({ id: event.id, time: shortTime(event.timestamp), agent: event.actor, event: event.event.replaceAll("_", " "), status: event.result, trace: event.entity }));

  const renderSection = () => {
    if (section === "Agent monitoring") return <><Card title="Agent monitoring">{monitoring.loading ? <LoadingState/> : monitoring.error ? <ErrorState error={monitoring.error} retry={monitoring.refresh}/> : <MonitoringTable rows={monitorRows} onInspect={pipeline => openLogs(pipeline)}/>}</Card><InlineDiagram id="06-agent-hierarchy" title="Monitoring architecture"/></>;
    if (currentPipeline) return <><Card title={currentPipeline.name}><div className="pipeline-config">{currentPipeline.agents.map((agent, index) => <div key={agent}><span>{index + 1}</span><div><strong>{agent.replaceAll("_", " ")}</strong><small>Google ADK specialist. Tool access governed.</small></div><label className="toggle"><input type="checkbox" disabled={readOnly} checked={!disabledAgents.includes(agent)} onChange={() => setDisabledAgents(current => current.includes(agent) ? current.filter(item => item !== agent) : [...current, agent])}/><span>Enabled</span></label><button className="button subtle" onClick={() => openLogs(currentPipeline.id)}>Logs</button></div>)}</div></Card><Card title="Pipeline controls"><label>Confidence threshold<div className="range-row"><input type="range" min="0" max="100" disabled={readOnly} value={config.reviewThreshold} onChange={event => update("reviewThreshold", Number(event.target.value))}/><strong>{config.reviewThreshold}%</strong></div></label><div className="locked-policy"><span><strong>Require human review</strong><small>Gate consequential persistence and execution</small></span><StatusBadge tone="review">Required</StatusBadge></div></Card></>;
    if (section === "Natural Language Orchestrator") return <Card title="Natural Language Orchestrator"><JsonViewer value={catalog.data ?? { framework: "Google ADK", status: "loading" }}/><h3>Routing precedence</h3><ol className="routing-rules"><li>Patient image, scan, OCR, or uploaded evidence to Session Image Extraction</li><li>Patient-scoped question, history, image evidence, or citation to Multimodal Q&A</li><li>Population count, trend, cohort, SQL, or chart to Population Insights</li></ol></Card>;
    if (section === "Routing rules") return <Card title="Agent routing rules"><DenseTable columns={[{ key: "priority", label: "Priority" }, { key: "intent", label: "Detected intent" }, { key: "workflow", label: "Selected workflow" }, { key: "permission", label: "Required permission" }]} rows={[{ id: 1, priority: 1, intent: "Uploaded clinical evidence", workflow: "Image Extraction", permission: "asset:write" }, { id: 2, priority: 2, intent: "Patient-scoped question", workflow: "Patient Q&A", permission: "patient:read" }, { id: 3, priority: 3, intent: "Population analytics", workflow: "Population Insights", permission: "database:read" }]}/></Card>;
    if (section === "Safety settings") return <div className="grid config"><Card title="Confidence policy"><label>Automatic approval threshold<div className="range-row"><input type="range" min="0" max="100" disabled={readOnly} value={config.autoApprovalThreshold} onChange={event => update("autoApprovalThreshold", Number(event.target.value))}/><strong>{config.autoApprovalThreshold}%</strong></div></label><label>Clinical review threshold<div className="range-row"><input type="range" min="0" max="100" disabled={readOnly} value={config.reviewThreshold} onChange={event => update("reviewThreshold", Number(event.target.value))}/><strong>{config.reviewThreshold}%</strong></div></label><label>Maximum concurrent agent runs<input type="number" min="1" max="50" disabled={readOnly} value={config.maxConcurrentRuns} onChange={event => update("maxConcurrentRuns", Number(event.target.value))}/></label></Card><Card title="Execution policy"><label className="toggle"><span><strong>Population insights enabled</strong><small>Allow reviewed SELECT-only population queries</small></span><input type="checkbox" disabled={readOnly} checked={config.databaseEnabled} onChange={event => update("databaseEnabled", event.target.checked)}/></label><div className="locked-policy"><span><strong>Mandatory human review</strong><small>Extraction persistence requires explicit clinician approval</small></span><StatusBadge tone="review">Required</StatusBadge></div><div className="locked-policy"><span><strong>PII and secret redaction</strong><small>Security callbacks before tools and output</small></span><StatusBadge tone="success">Active</StatusBadge></div></Card><Card title="Current version"><JsonViewer value={config}/></Card><InlineDiagram id="11-security-pipeline" title="Safety architecture"/></div>;
    return <Card title="Agent logs">{logFilter && <span className="log-filter-chip">Filtered by {logFilter} pipeline<button onClick={() => setLogFilter(null)} aria-label="Clear log filter">x</button></span>}{audits.loading ? <LoadingState/> : logRows.length ? <DenseTable columns={[{ key: "time", label: "Timestamp" }, { key: "agent", label: "Actor" }, { key: "event", label: "Event" }, { key: "status", label: "Status" }, { key: "trace", label: "Entity" }]} rows={logRows} onRow={row => setSelectedAudit(auditRows.find(event => event.id === row.id) ?? null)}/> : <EmptyState title={logFilter ? `No ${logFilter} events yet` : "No logged events yet"} detail={logFilter ? "Run this pipeline to record workflow events, or clear the filter." : "Workflow, review, and configuration events appear here as they happen."}/>}</Card>;
  };

  return <><Head title="Agent configuration and monitoring" detail="Inspect the multi-agent engine, routing, thresholds, safety gates, logs, and runtime performance." action={readOnly ? <StatusBadge tone="info">Read-only view. Switch to the admin workspace to change settings</StatusBadge> : <button className="button primary" disabled={saving} onClick={() => void save()}>{saving ? "Saving version" : "Save new version"}</button>}/>{notice && <div className="notice success">{notice}</div>}{saveError && <div className="notice error" role="alert">{saveError}</div>}<div className="configuration-layout"><Card title="Configuration sections">{sections.map(name => <button className={`config-nav-row ${section === name ? "active" : ""}`} key={name} onClick={() => setSection(name)}><span>{name}</span></button>)}</Card><section>{renderSection()}</section><Card title="Runtime status"><dl className="compact-facts"><div><dt>Framework</dt><dd>{catalog.data?.framework ?? "Google ADK"}</dd></div><div><dt>Mode</dt><dd>{catalog.data?.executionMode ?? "local"}</dd></div><div><dt>Orchestrator</dt><dd>{catalog.data?.orchestrator ?? "clinical_orchestrator"}</dd></div><div><dt>Config version</dt><dd>{config.version}</dd></div></dl><StatusBadge tone="success">All callbacks active</StatusBadge></Card></div><AuditDetailModal event={selectedAudit} onClose={() => setSelectedAudit(null)}/></>;
}
