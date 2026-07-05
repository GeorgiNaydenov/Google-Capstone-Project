export type Role = "clinician" | "admin";
export type RunStatus = "queued" | "running" | "review" | "completed" | "failed";

export type TenantId = "research-clinic" | "northstar-health" | "capstone";

export interface Tenant {
  id: TenantId;
  name: string;
  kind: "demo" | "real";
}

// Static mirror of the backend registry (clinical_app/tenancy.py). The
// backend tolerates unknown values by falling back to the default demo
// tenant, so drift here is safe.
export const TENANTS: Tenant[] = [
  { id: "research-clinic", name: "Research Clinic", kind: "demo" },
  { id: "northstar-health", name: "Northstar Health", kind: "demo" },
  { id: "capstone", name: "Capstone", kind: "real" },
];

export interface Patient {
  id: string;
  name: string;
  mrn: string;
  age?: number;
  sex?: string;
  condition?: string;
  risk?: "high" | "medium" | "low";
  aiStatus?: string;
  completeness?: number;
  lastEncounter?: string;
  assignedClinician?: string;
  openIssues?: number;
  dataSources?: number;
  lastAiReview?: string;
}

export interface ExtractedField {
  name: string;
  value: string;
  confidence: number;
}

export interface ClinicalSession {
  id: string;
  patientId: string;
  title: string;
  occurredAt: string;
  status: string;
  summary?: string;
  uploadedImageCount?: number;
  extractionConfidence?: number;
  extractedFields?: ExtractedField[];
  jsonSyncStatus?: string;
  relationalSyncStatus?: string;
  vectorSyncStatus?: string;
  auditStatus?: string;
}

export interface ToolCall {
  toolName?: string;
  tool?: string;
  args?: Record<string, unknown>;
  output?: unknown;
  durationMs?: number;
}

export interface AgentStep {
  id: string;
  name: string;
  status: RunStatus;
  detail?: string;
  timestamp?: string;
}

export interface Evidence {
  id: string;
  label: string;
  kind: "text" | "image" | "structured" | "document";
  excerpt?: string;
  sourceUrl?: string;
  page?: number;
}

export interface AgentRun {
  id: string;
  workflow: "extraction" | "qa" | "database";
  status: RunStatus;
  agentName?: string;
  confidence?: number;
  createdAt?: string;
  auditId?: string;
  traceId?: string;
  steps?: AgentStep[];
  evidence?: Evidence[];
  result?: Record<string, unknown>;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  event: string;
  actor: string;
  entity: string;
  result: string;
}

export interface DashboardData {
  metrics?: Record<string, number | string>;
  patients?: Patient[];
  sessions?: ClinicalSession[];
  activity?: AuditEvent[];
}

export interface StorageData {
  assets?: Array<Record<string, unknown>>;
  persistedExtractions?: Array<Record<string, unknown>>;
  records?: Array<Record<string, unknown>>;
  assetCount?: number;
  persistedCount?: number;
  cloudCount?: number;
  jsonCount?: number;
  sqlCount?: number;
  vectorCount?: number;
  auditCount?: number;
}

export interface ClinicalUser {
  id: string;
  name: string;
  email: string;
  roles: string[];
  scope: string;
  status: string;
}

export interface AgentConfig {
  version: number;
  autoApprovalThreshold: number;
  reviewThreshold: number;
  maxConcurrentRuns: number;
  databaseEnabled: boolean;
}

export interface OrchestrationPlan {
  intent: string;
  workflow: "extraction" | "qa" | "database";
  route: string;
  agents: string[];
  dataSources: string[];
  permissions: string[];
  expectedOutput: string;
}

export interface ClinicalNotification {
  id: string;
  title: string;
  detail: string;
  severity: "critical" | "warning" | "info";
  agent: string;
  createdAt: string;
  read: boolean;
  route: string;
}

export interface AgentPipeline {
  id: "extraction" | "qa" | "database";
  name: string;
  route: string;
  agents: string[];
}

export interface AgentCatalog {
  executionMode: "local" | "live";
  orchestrator: string;
  framework: string;
  pipelines: AgentPipeline[];
}

export interface ComponentHealth {
  name: string;
  status: "operational" | "unavailable";
  detail: string;
  latencyMs: number;
}

export interface SystemHealth {
  components: ComponentHealth[];
  checkedAt: string;
}

export interface AgentMonitorRow {
  agent: string;
  pipeline: string;
  lastRun: string;
  status: "healthy" | "degraded";
  avgConfidence: number;
  failureRate: number;
  reviewRate: number;
  avgDurationMs: number;
  linkedPatients: number;
}

export interface PermissionRow {
  permission: string;
  grants: Record<string, boolean>;
}

export interface Permissions {
  roles: string[];
  matrix: PermissionRow[];
  version: number;
}

export interface SchemaColumn {
  name: string;
  type: string;
}

export interface SchemaTable {
  table: string;
  columns: SchemaColumn[];
}

export interface WorkspaceSummary {
  queueCount: number;
  inboxCount: number;
  unreadNotifications: number;
  patients: number;
  runs: number;
}

export interface EvidenceItem {
  id: string;
  kind: string;
  date: string;
  excerpt: string;
  sourceUrl?: string;
}
