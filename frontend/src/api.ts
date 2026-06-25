import type { AgentCatalog, AgentConfig, AgentRun, AuditEvent, ClinicalNotification, ClinicalSession, ClinicalUser, DashboardData, OrchestrationPlan, Patient, Role } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api";

class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData)) headers.set("Content-Type", "application/json");
  headers.set("X-Demo-Session", sessionStorage.getItem("demoSession") ?? "public-demo");
  headers.set("X-Clinical-Role", localStorage.getItem("clinicalRole") ?? "clinician");
  headers.set("X-Tenant", sessionStorage.getItem("tenant") ?? "local");
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string };
    throw new ApiError(response.status, body.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  startDemo: () => request<{ sessionId: string }>("/demo/session", { method: "POST" }),
  orchestrate: (query: string, patientId?: string) => request<OrchestrationPlan>("/orchestrate", { method: "POST", body: JSON.stringify({ query, ...(patientId ? { patientId } : {}) }) }),
  resetDemo: () => request<void>("/demo/reset", { method: "POST" }),
  dashboard: (role: Role) => request<DashboardData>(`/dashboard?role=${role}`),
  patients: (query = "") => request<Patient[]>(`/patients?query=${encodeURIComponent(query)}`),
  patient: (id: string) => request<Patient>(`/patients/${id}`),
  sessions: (patientId?: string) => request<ClinicalSession[]>(`/sessions${patientId ? `?patient_id=${patientId}` : ""}`),
  session: (id: string) => request<ClinicalSession>(`/sessions/${id}`),
  inbox: () => request<AgentRun[]>("/reviews"),
  audits: () => request<AuditEvent[]>("/audit"),
  upload: (file: File, patientId: string) => {
    const body = new FormData(); body.append("file", file); body.append("patient_id", patientId);
    return request<{ assetId: string; previewUrl?: string; extracted?: Record<string, unknown> }>("/assets", { method: "POST", body });
  },
  runExtraction: (assetId: string, patientId: string) => request<AgentRun>("/runs/extraction", { method: "POST", body: JSON.stringify({ assetId, patientId }) }),
  runQa: (payload: { patientId: string; question: string; source_types: Array<"text" | "image" | "lab">; filters: { dateRange: string; session?: string } }) => request<AgentRun>("/runs/qa", { method: "POST", body: JSON.stringify(payload) }),
  generateSql: (question: string) => request<AgentRun>("/runs/database/preview", { method: "POST", body: JSON.stringify({ question }) }),
  executeSql: (runId: string) => request<AgentRun>(`/runs/database/${runId}/execute`, { method: "POST" }),
  run: (id: string) => request<AgentRun>(`/runs/${id}`),
  review: (id: string, decision: "approved" | "rejected", fields?: object) => request<AgentRun>(`/runs/${id}/review`, { method: "POST", body: JSON.stringify({ decision, fields }) }),
  storage: () => request<Record<string, unknown>>("/storage"),
  users: () => request<ClinicalUser[]>("/users"),
  config: () => request<AgentConfig>("/agent-config"),
  saveConfig: (config: AgentConfig) => request<AgentConfig>("/agent-config", { method: "PUT", body: JSON.stringify(config) }),
  agents: () => request<AgentCatalog>("/agents"),
  notifications: () => request<ClinicalNotification[]>("/notifications"),
  readNotification: (id: string) => request<ClinicalNotification>(`/notifications/${id}/read`, { method: "POST" }),
};
