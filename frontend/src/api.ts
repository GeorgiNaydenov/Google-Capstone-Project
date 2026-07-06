import type { AgentCatalog, AgentConfig, AgentMonitorRow, AgentRun, AuditEvent, AuditEventDetail, ClinicalNotification, ClinicalSession, ClinicalUser, DashboardData, EvidenceItem, ExtractionSource, KnowledgeBaseAsset, OrchestrationPlan, Patient, PermissionRow, Permissions, Role, SchemaTable, StorageData, SystemHealth, WorkspaceSummary } from "./types";
import { fallbackAudits, fallbackCatalog, fallbackConfig, fallbackDashboard, fallbackEvidence, fallbackExtractionRun, fallbackKnowledgeBase, fallbackKnowledgeBaseUpload, fallbackMonitoring, fallbackNotifications, fallbackPatients, fallbackPermissions, fallbackQaRun, fallbackReviewRun, fallbackSchema, fallbackSessions, fallbackSqlExecute, fallbackSqlPreview, fallbackStorage, fallbackSummary, fallbackSystemHealth, fallbackUpload, fallbackUsers, syntheticExtractionOptions } from "./fallbackData";

// Runs minted by the deterministic client-side fallbacks never exist on the
// backend, so their follow-up calls must resolve locally instead of 404ing.
const isLocalRun = (id: string) => id.includes("-LOCAL-");

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json");
  headers.set("X-Demo-Session", sessionStorage.getItem("demoSession") ?? "public-demo");
  headers.set("X-Clinical-Role", localStorage.getItem("clinicalRole") ?? "clinician");
  headers.set("X-Tenant", sessionStorage.getItem("tenant") ?? "research-clinic");
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string };
    throw new ApiError(response.status, body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function shouldUseFailover(reason: unknown) {
  if (reason instanceof ApiError) return reason.status === 502 || reason.status === 503 || reason.status === 504;
  return reason instanceof TypeError;
}

function failover<T>(load: () => Promise<T>, fallback: () => T): Promise<T> {
  return load().catch(reason => {
    if (shouldUseFailover(reason)) return fallback();
    throw reason;
  });
}

function isDemoTenant() {
  return (sessionStorage.getItem("tenant") ?? "research-clinic") !== "capstone";
}

function demoMutationFailover<T>(load: () => Promise<T>, fallback: () => Promise<T> | T): Promise<T> {
  return load().catch(reason => {
    if (isDemoTenant() && shouldUseFailover(reason)) return fallback();
    throw reason;
  });
}

export const api = {
  startDemo: () => request<{ sessionId: string }>("/demo/session", { method: "POST" }),
  orchestrate: (query: string, patientId?: string) => request<OrchestrationPlan>("/orchestrate", { method: "POST", body: JSON.stringify({ query, ...(patientId ? { patientId } : {}) }) }),
  resetDemo: () => request<void>("/demo/reset", { method: "POST" }),
  dashboard: (role: Role) => failover(() => request<DashboardData>(`/dashboard?role=${role}`), () => fallbackDashboard(role)),
  patients: (query = "") => failover(() => request<Patient[]>(`/patients?query=${encodeURIComponent(query)}`), () => {
    const term = query.trim().toLowerCase();
    return term ? fallbackPatients.filter(patient => [patient.id, patient.name, patient.mrn, patient.condition].some(value => String(value ?? "").toLowerCase().includes(term))) : fallbackPatients;
  }),
  patient: (id: string) => failover(() => request<Patient>(`/patients/${id}`), () => fallbackPatients.find(patient => patient.id === id) ?? fallbackPatients[0]),
  sessions: (patientId?: string) => failover(() => request<ClinicalSession[]>(`/sessions${patientId ? `?patient_id=${patientId}` : ""}`), () => patientId ? fallbackSessions.filter(session => session.patientId === patientId) : fallbackSessions),
  session: (id: string) => failover(() => request<ClinicalSession>(`/sessions/${id}`), () => fallbackSessions.find(session => session.id === id) ?? fallbackSessions[0]),
  inbox: () => failover(() => request<AgentRun[]>("/reviews"), () => []),
  audits: () => failover(() => request<AuditEvent[]>("/audit"), () => fallbackAudits),
  auditEvent: (id: string) => request<AuditEventDetail>(`/audit/${id}`),
  upload: (file: File, patientId: string) => {
    const body = new FormData(); body.append("file", file); body.append("patient_id", patientId);
    return demoMutationFailover(() => request<{ assetId: string; previewUrl?: string; extracted?: Record<string, unknown> }>("/assets", { method: "POST", body }), () => fallbackUpload(file, patientId));
  },
  uploadKnowledgeBase: (file: File, patientId: string) => {
    const body = new FormData(); body.append("file", file); body.append("patient_id", patientId);
    return demoMutationFailover(() => request<{ assetId: string; patientId?: string; previewUrl?: string; evidenceId: string; extracted?: Record<string, unknown> }>("/knowledge-base/assets", { method: "POST", body }), () => fallbackKnowledgeBaseUpload(file, patientId));
  },
  knowledgeBase: (patientId?: string) => failover(() => request<KnowledgeBaseAsset[]>(`/knowledge-base/assets${patientId ? `?patient_id=${encodeURIComponent(patientId)}` : ""}`), () => fallbackKnowledgeBase(patientId)),
  extractionSources: () => failover(() => request<ExtractionSource[]>("/extraction/sources"), () => syntheticExtractionOptions),
  runExtraction: (assetId: string, patientId: string) => demoMutationFailover(() => request<AgentRun>("/runs/extraction", { method: "POST", body: JSON.stringify({ assetId, patientId }) }), () => fallbackExtractionRun(assetId, patientId)),
  runSyntheticExtraction: (assetId: string, patientId: string) => demoMutationFailover(() => request<AgentRun>("/runs/extraction", { method: "POST", body: JSON.stringify({ assetId, patientId }) }), () => fallbackExtractionRun(assetId, patientId)),
  runQa: (payload: { patientId: string; question: string; source_types: Array<"text" | "image" | "lab" | "document" | "pdf" | "json" | "knowledge_base">; filters: { dateRange: string; session?: string } }) => demoMutationFailover(() => request<AgentRun>("/runs/qa", { method: "POST", body: JSON.stringify(payload) }), () => fallbackQaRun(payload.patientId, payload.question, payload.source_types)),
  generateSql: (question: string) => demoMutationFailover(() => request<AgentRun>("/runs/database/preview", { method: "POST", body: JSON.stringify({ question }) }), () => fallbackSqlPreview(question)),
  executeSql: (runId: string) => isLocalRun(runId) ? Promise.resolve(fallbackSqlExecute(runId)) : demoMutationFailover(() => request<AgentRun>(`/runs/database/${runId}/execute`, { method: "POST" }), () => fallbackSqlExecute(runId)),
  run: (id: string) => request<AgentRun>(`/runs/${id}`),
  runs: (workflow?: "extraction" | "qa" | "database", patientId?: string) => {
    const params = new URLSearchParams({ ...(workflow ? { workflow } : {}), ...(patientId ? { patient_id: patientId } : {}) }).toString();
    return failover(() => request<AgentRun[]>(`/runs${params ? `?${params}` : ""}`), () => []);
  },
  review: (id: string, decision: "approved" | "rejected", fields?: object) => isLocalRun(id) ? Promise.resolve(fallbackReviewRun(id, decision, fields)) : demoMutationFailover(() => request<AgentRun>(`/runs/${id}/review`, { method: "POST", body: JSON.stringify({ decision, fields }) }), () => fallbackReviewRun(id, decision, fields)),
  storage: () => failover(() => request<StorageData>("/storage"), () => fallbackStorage),
  users: () => failover(() => request<ClinicalUser[]>("/users"), () => fallbackUsers),
  config: () => failover(() => request<AgentConfig>("/agent-config"), () => fallbackConfig),
  saveConfig: (config: AgentConfig) => demoMutationFailover(() => request<AgentConfig>("/agent-config", { method: "PUT", body: JSON.stringify(config) }), () => { Object.assign(fallbackConfig, config); fallbackConfig.version += 1; return { ...fallbackConfig }; }),
  agents: () => failover(() => request<AgentCatalog>("/agents"), () => fallbackCatalog),
  notifications: () => failover(() => request<ClinicalNotification[]>("/notifications"), () => fallbackNotifications),
  systemHealth: () => failover(() => request<SystemHealth>("/system/health"), () => fallbackSystemHealth),
  monitoring: () => failover(() => request<AgentMonitorRow[]>("/agents/monitoring"), () => fallbackMonitoring),
  permissions: () => failover(() => request<Permissions>("/permissions"), () => fallbackPermissions),
  savePermissions: (matrix: PermissionRow[]) => request<Permissions>("/permissions", { method: "PUT", body: JSON.stringify({ matrix }) }),
  schema: () => failover(() => request<SchemaTable[]>("/database/schema"), () => fallbackSchema),
  summary: () => failover(() => request<WorkspaceSummary>("/summary"), () => fallbackSummary),
  patientEvidence: (id: string) => failover(() => request<EvidenceItem[]>(`/patients/${id}/evidence`), () => fallbackEvidence(id)),
  readNotification: (id: string) => request<ClinicalNotification>(`/notifications/${id}/read`, { method: "POST" }),
  v2Health: () => failover(() => request<any>("/v2/health"), () => ({ status: "degraded", databaseConnected: false, storageAccessible: false, timestamp: new Date().toISOString() })),
  mcpTools: () => failover(() => request<{ tools: any[]; total: number }>("/v2/mcp/tools"), () => ({ tools: [], total: 0 })),
  executeMcpTool: (toolName: string, args: Record<string, any>) => request<any>("/v2/mcp/execute", { method: "POST", body: JSON.stringify({ toolName, arguments: args }) }),
  a2aCard: () => failover(() => request<any>("/v2/a2a/card"), () => ({ name: "clinical_orchestrator", description: "Failover Agent Card placeholder", pipelines: {}, tools: [] })),
  getOpenApiSchema: () => failover(() => fetch("/openapi.json").then(r => {
    if (!r.ok) throw new ApiError(r.status, `Failed to fetch OpenAPI schema (${r.status})`);
    return r.json();
  }), () => ({ openapi: "3.1.0", info: { title: "Clinician AI Kit API unavailable", version: "failover" }, paths: {} })),
  docsList: () => failover(() => request<{ obsidian: Array<{ path: string; title: string }>; karpathy: Array<{ path: string; title: string }> }>("/v2/docs/list"), () => ({ obsidian: [], karpathy: [] })),
  docsFile: (type: string, path: string) => failover(() => request<{ content: string }>(`/v2/docs/file?type=${type}&path=${path}`), () => ({ content: `# Document unavailable\n\nThe ${type} document ${path} could not be loaded because the API gateway is unavailable.` })),
};
