import type { AgentCatalog, AgentConfig, AgentMonitorRow, AgentRun, AuditEvent, ClinicalNotification, ClinicalSession, ClinicalUser, DashboardData, EvidenceItem, KnowledgeBaseAsset, Patient, Permissions, SchemaTable, StorageData, SystemHealth, WorkspaceSummary } from "./types";

const now = () => new Date().toISOString();

export const fallbackPatients: Patient[] = [
  { id: "PT-8829", name: "Maya Chen", mrn: "MRN-8829", age: 62, sex: "F", condition: "Pulmonary nodule follow-up", risk: "high", aiStatus: "needs_review", completeness: 0.84, lastEncounter: "2026-06-15", assignedClinician: "Dr. Sarah Miller", openIssues: 2, dataSources: 7, lastAiReview: "2026-07-04" },
  { id: "PT-1029", name: "Eleanor Kim", mrn: "MRN-1029", age: 67, sex: "F", condition: "Chronic kidney disease", risk: "medium", aiStatus: "verified", completeness: 0.91, lastEncounter: "2026-06-21", assignedClinician: "Dr. Sarah Miller", openIssues: 1, dataSources: 5, lastAiReview: "2026-07-03" },
  { id: "PT-8650", name: "Mateo Silva", mrn: "MRN-8650", age: 54, sex: "M", condition: "Obstructive sleep apnea", risk: "low", aiStatus: "verified", completeness: 0.96, lastEncounter: "2026-06-28", assignedClinician: "Dr. Sarah Miller", openIssues: 0, dataSources: 4, lastAiReview: "2026-07-02" },
];

export const fallbackSessions: ClinicalSession[] = [
  { id: "SES-001", patientId: "PT-8829", title: "CT chest follow-up", occurredAt: "2026-06-15", status: "review", summary: "Synthetic failover session pending review.", uploadedImageCount: 2, extractionConfidence: 0.88, jsonSyncStatus: "pending", relationalSyncStatus: "pending", vectorSyncStatus: "pending", auditStatus: "recorded" },
  { id: "SES-002", patientId: "PT-1029", title: "Renal panel note bundle", occurredAt: "2026-06-21", status: "verified", summary: "Synthetic failover session synchronized.", uploadedImageCount: 1, extractionConfidence: 0.93, jsonSyncStatus: "synced", relationalSyncStatus: "synced", vectorSyncStatus: "synced", auditStatus: "recorded" },
];

export const fallbackAudits: AuditEvent[] = [
  { id: "AUD-FB-1", timestamp: now(), event: "failover_snapshot_loaded", actor: "Frontend failover", entity: "read-only route", result: "shown" },
  { id: "AUD-FB-2", timestamp: now(), event: "api_gateway_unavailable", actor: "Vite proxy", entity: "/api", result: "degraded" },
];

export const fallbackDashboard = (role: "clinician" | "admin"): DashboardData => ({
  metrics: role === "admin"
    ? { totalUsers: 8, activeClinicians: 4, patients: fallbackPatients.length, agentRuns24h: 0, failedExtractions: 0, pendingActions: 1, agentRuns: 0, storedAssets: 0, auditEvents: fallbackAudits.length }
    : { patients: fallbackPatients.length, highRisk: 1, pendingReview: 1, completeness: "90%", agentRuns: 0 },
  patients: fallbackPatients,
  sessions: fallbackSessions,
  activity: fallbackAudits,
});

export const fallbackCatalog: AgentCatalog = {
  executionMode: "local",
  orchestrator: "clinical_orchestrator",
  framework: "Google ADK",
  pipelines: [
    { id: "extraction", name: "Clinical evidence extraction", route: "/app/extraction", agents: ["quality_assessor_agent", "ocr_processor_agent", "vision_analyzer_agent", "clinical_structuring_agent", "validation_agent", "clinical_review_gate_agent", "storage_agent", "vector_indexing_agent", "audit_agent"] },
    { id: "qa", name: "Patient Q&A", route: "/app/qa", agents: ["context_assembly_agent", "evidence_retrieval_agent", "image_evidence_agent", "citation_builder_agent", "answer_synthesis_agent", "qa_audit_agent"] },
    { id: "database", name: "Population insights", route: "/app/database", agents: ["schema_discovery_agent", "nl_to_sql_agent", "sql_validator_agent", "query_executor_agent", "insight_chart_agent", "audit_agent"] },
  ],
};

export const fallbackSystemHealth: SystemHealth = {
  checkedAt: now(),
  components: [
    { name: "Clinical database", status: "unavailable", detail: "API unavailable; showing deterministic read-only snapshot.", latencyMs: 0 },
    { name: "Agent runtime", status: "unavailable", detail: "No live runtime response from gateway.", latencyMs: 0 },
    { name: "Upload storage", status: "unavailable", detail: "Storage state not refreshed.", latencyMs: 0 },
    { name: "Frontend bundle", status: "operational", detail: "Local UI rendered failover state.", latencyMs: 0 },
  ],
};

export const fallbackMonitoring: AgentMonitorRow[] = fallbackCatalog.pipelines.flatMap(pipeline =>
  pipeline.agents.slice(0, 3).map(agent => ({ agent, pipeline: pipeline.id, lastRun: now(), status: "degraded", avgConfidence: 0, failureRate: 0, reviewRate: 0, avgDurationMs: 0, linkedPatients: 0 })),
);

export const fallbackStorage: StorageData = {
  assets: [
    { assetId: "AST-DEMO-001", filename: "ct-followup-summary.pdf", contentType: "application/pdf", sizeBytes: 184000, createdAt: now(), patientId: "PT-8829", bucket: "local-demo-assets", objectPath: "research-clinic/PT-8829/ct-followup-summary.pdf", checksum: "sha256:demo-ct-001" },
    { assetId: "AST-DEMO-002", filename: "ct-followup-trend-evidence.png", contentType: "image/png", sizeBytes: 142000, createdAt: now(), patientId: "PT-8829", bucket: "local-demo-assets", objectPath: "research-clinic/PT-8829/ct-followup-trend-evidence.png", checksum: "sha256:demo-img-002" },
    { assetId: "AST-DEMO-003", filename: "renal-panel-note-bundle.pdf", contentType: "application/pdf", sizeBytes: 96000, createdAt: now(), patientId: "PT-1029", bucket: "local-demo-assets", objectPath: "research-clinic/PT-1029/renal-panel-note-bundle.pdf", checksum: "sha256:demo-renal-003" },
  ],
  persistedExtractions: [
    { runId: "RUN-DEMO-101", patientId: "PT-8829", sessionId: "SES-001", jsonReceipt: "JSON-DEMO-101", relationalReceipt: "SQL-DEMO-101", vectorReceipt: "VEC-DEMO-101", reviewState: "approved", confidence: 0.93 },
    { runId: "RUN-DEMO-102", patientId: "PT-1029", sessionId: "SES-002", jsonReceipt: "JSON-DEMO-102", relationalReceipt: "SQL-DEMO-102", vectorReceipt: "VEC-DEMO-102", reviewState: "approved", confidence: 0.91 },
  ],
  records: [
    { id: "OBJ-DEMO-001", source: "ct-followup-summary.pdf", destination: "Object storage", status: "synced", updated: now(), owner: "Upload service", patientId: "PT-8829", sessionId: "SES-001", error: "" },
    { id: "OBJ-DEMO-002", source: "ct-followup-trend-evidence.png", destination: "Object storage", status: "synced", updated: now(), owner: "Upload service", patientId: "PT-8829", sessionId: "SES-001", error: "" },
    { id: "JSON-DEMO-101", source: "Extraction RUN-DEMO-101", destination: "JSON document store", status: "synced", updated: now(), owner: "Storage Agent", patientId: "PT-8829", sessionId: "SES-001", error: "" },
    { id: "SQL-DEMO-101", source: "Extraction RUN-DEMO-101", destination: "Relational database", status: "synced", updated: now(), owner: "Storage Agent", patientId: "PT-8829", sessionId: "SES-001", error: "" },
    { id: "VEC-DEMO-101", source: "Extraction RUN-DEMO-101", destination: "Vector search index", status: "synced", updated: now(), owner: "Vector Indexing Agent", patientId: "PT-8829", sessionId: "SES-001", error: "" },
    { id: "SYNC-DEMO-201", source: "Knowledge base refresh", destination: "Vector search index", status: "pending", updated: now(), owner: "Storage Agent", patientId: "PT-8829", sessionId: "", error: "" },
    { id: "FAIL-DEMO-001", source: "Live storage endpoint", destination: "Provider refresh", status: "failed", updated: now(), owner: "Frontend failover", patientId: "", sessionId: "", error: "Live provider state unavailable; deterministic read-only snapshot is active." },
  ],
  assetCount: 3,
  persistedCount: 2,
  cloudCount: 3,
  jsonCount: 2,
  sqlCount: 2,
  vectorCount: 2,
  auditCount: fallbackAudits.length,
};

export const fallbackUsers: ClinicalUser[] = [
  { id: "USR-1", name: "Admin Demo", email: "admin.demo@example.test", roles: ["Admin"], scope: "Organization", status: "active" },
  { id: "USR-2", name: "Dr. Sarah Miller", email: "sarah.miller@example.test", roles: ["Clinician"], scope: "Assigned patients", status: "active" },
];

export const fallbackPermissions: Permissions = {
  roles: ["Admin", "Clinician", "Reviewer", "Read-only Viewer", "Data Manager"],
  version: 1,
  matrix: [
    { permission: "Review clinical outputs", grants: { Admin: true, Clinician: true, Reviewer: true, "Read-only Viewer": false, "Data Manager": false } },
    { permission: "Run database intelligence", grants: { Admin: true, Clinician: false, Reviewer: false, "Read-only Viewer": false, "Data Manager": true } },
    { permission: "Manage storage and indexes", grants: { Admin: true, Clinician: false, Reviewer: false, "Read-only Viewer": false, "Data Manager": true } },
  ],
};

export const fallbackConfig: AgentConfig = { version: 1, autoApprovalThreshold: 90, reviewThreshold: 75, maxConcurrentRuns: 8, databaseEnabled: true };

export const fallbackNotifications: ClinicalNotification[] = [
  { id: "NTF-FB-1", title: "API gateway degraded", detail: "Read-only failover data is being shown until the product API responds.", severity: "warning", agent: "Frontend failover", createdAt: now(), read: false, route: "/app/admin?view=health" },
];

export const fallbackSchema: SchemaTable[] = [
  { table: "patients_core", columns: [{ name: "patient_id", type: "TEXT" }, { name: "age", type: "INTEGER" }, { name: "sex", type: "TEXT" }, { name: "race_ethnicity", type: "TEXT" }, { name: "preferred_language", type: "TEXT" }, { name: "risk_level", type: "TEXT" }, { name: "primary_diagnosis", type: "TEXT" }] },
  { table: "patient_conditions", columns: [{ name: "condition_name", type: "TEXT" }, { name: "category", type: "TEXT" }, { name: "severity", type: "TEXT" }, { name: "is_primary", type: "BOOLEAN" }] },
  { table: "medications", columns: [{ name: "medication_name", type: "TEXT" }, { name: "medication_class", type: "TEXT" }, { name: "status", type: "TEXT" }, { name: "adherence_score", type: "FLOAT" }] },
  { table: "encounters", columns: [{ name: "encounter_date", type: "DATE" }, { name: "department", type: "TEXT" }, { name: "reason", type: "TEXT" }] },
  { table: "vital_signs", columns: [{ name: "systolic_bp", type: "INTEGER" }, { name: "oxygen_saturation", type: "FLOAT" }, { name: "bmi", type: "FLOAT" }] },
  { table: "care_gaps", columns: [{ name: "gap_type", type: "TEXT" }, { name: "priority", type: "TEXT" }, { name: "status", type: "TEXT" }] },
  { table: "clinical_notes", columns: [{ name: "note_id", type: "TEXT" }, { name: "patient_id", type: "TEXT" }, { name: "note_text", type: "TEXT" }] },
  { table: "lab_results", columns: [{ name: "component", type: "TEXT" }, { name: "value", type: "TEXT" }, { name: "flag", type: "TEXT" }] },
];

export const fallbackSummary: WorkspaceSummary = { queueCount: 0, inboxCount: 0, unreadNotifications: 1, patients: fallbackPatients.length, runs: fallbackSessions.length };

export const fallbackEvidence = (patientId: string): EvidenceItem[] => [
  { id: `EVD-${patientId}-FB`, kind: "document", date: "2026-07-05", excerpt: "Failover evidence placeholder. Live evidence will reload when the API returns." },
];

const demoAssetUrl = (file: File) => URL.createObjectURL(file);
const demoId = (prefix: string) => `${prefix}-LOCAL-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

export const syntheticExtractionOptions = Array.from({ length: 10 }, (_, index) => {
  const n = index + 1;
  const patient = fallbackPatients[index % fallbackPatients.length];
  const id = `SYN-EXT-${String(n).padStart(2, "0")}`;
  const previewFile = `EXT-${String(n).padStart(4, "0")}.png`;
  const packet = `PKT-EXT-${String(Math.ceil(n / 5)).padStart(4, "0")}.pdf`;
  return {
    id,
    assetId: id,
    patientId: patient.id,
    label: `${patient.condition} packet ${Math.ceil(n / 5)}`,
    filename: packet,
    packetFilename: packet,
    packetId: `PKT-EXT-${String(Math.ceil(n / 5)).padStart(4, "0")}`,
    patientsInFile: 5,
    batchPatientIds: fallbackPatients.slice(0, 5).map(item => item.id),
    previewUrl: `/demo-data/extraction/demo2/images/${previewFile}`,
    sourceUrl: `/demo-data/extraction/demo2/images/${previewFile}`,
    fallbackPreviewUrl: "/evidence/demo-retinopathy-intake.png",
    contentType: "application/pdf",
    sourceContentType: "application/pdf",
    previewContentType: "image/png",
    extracted: {
      type: "document",
      documentType: "Enterprise five-patient clinical packet",
      filename: packet,
      imageCount: 1,
      pageCount: 5,
      textPreview: `Clinical record packet ${Math.ceil(n / 5)} for ${patient.name}. Five de-identified patient summaries per PDF, ready for extraction review.`,
      pages: [{ pageNumber: 1, text: `Record packet ${Math.ceil(n / 5)}. ${patient.condition}. Review extracted fields before saving to the chart.` }],
      images: [{ imageId: id, mimeType: "image/png", role: "synthetic_demo_source" }],
      tables: [],
      warnings: [],
    },
  };
});

export const localKnowledgeBaseAssets: KnowledgeBaseAsset[] = [
  {
    assetId: "KB-DEMO-001",
    patientId: "PT-8829",
    filename: "ct-followup-summary.pdf",
    contentType: "application/pdf",
    sizeBytes: 184_000,
    previewUrl: "",
    evidenceId: "KB-DEMO-001",
    createdAt: now(),
    extracted: { type: "pdf", pageCount: 2, textPreview: "CT follow-up notes describe a stable right upper lobe nodule with no new suspicious lymphadenopathy." },
  },
  {
    assetId: "KB-DEMO-002",
    patientId: "PT-8829",
    filename: "ct-followup-trend-evidence.png",
    contentType: "image/png",
    sizeBytes: 142_000,
    previewUrl: "/evidence/demo-retinopathy-intake.png",
    evidenceId: "KB-DEMO-002",
    createdAt: now(),
    extracted: { type: "image", imageCount: 1, textPreview: "Synthetic clinical intake image with structured measurements and an attached trend visualization for visual evidence review." },
  },
];

export function fallbackUpload(file: File, patientId: string) {
  const assetId = demoId("AST");
  const previewUrl = file.type.startsWith("image/") ? demoAssetUrl(file) : "";
  return Promise.resolve({
    assetId,
    previewUrl,
    extracted: {
      type: file.type.includes("pdf") ? "pdf" : file.type.startsWith("image/") ? "image" : "document",
      filename: file.name,
      sizeBytes: file.size,
      textPreview: `${file.name} accepted by deterministic demo fallback for patient ${patientId}.`,
      imageCount: file.type.startsWith("image/") ? 1 : 0,
      pageCount: file.type.includes("pdf") ? 1 : 0,
      pages: [{ pageNumber: 1, text: `${file.name} demo extraction preview.` }],
      images: file.type.startsWith("image/") ? [{ imageId: assetId, mimeType: file.type, role: "uploaded_source" }] : [],
      tables: [],
      warnings: ["api_gateway_unavailable:demo_fallback_used"],
      thumbnail: "",
    },
  });
}

export function fallbackKnowledgeBaseUpload(file: File, patientId: string) {
  const assetId = demoId("KB");
  const previewUrl = file.type.startsWith("image/") ? demoAssetUrl(file) : "";
  const asset: KnowledgeBaseAsset = {
    assetId,
    patientId,
    filename: file.name,
    contentType: file.type || "application/octet-stream",
    sizeBytes: file.size,
    previewUrl,
    evidenceId: assetId,
    createdAt: now(),
    extracted: {
      type: file.type.startsWith("image/") ? "image" : file.name.endsWith(".docx") ? "docx" : file.name.endsWith(".json") ? "json" : file.name.endsWith(".md") ? "markdown" : file.name.endsWith(".txt") ? "text" : "pdf",
      knowledgeBase: true,
      textPreview: `${file.name} is indexed in the local deterministic demo knowledge base.`,
      imageCount: file.type.startsWith("image/") ? 1 : 0,
      pageCount: 1,
      pages: [{ pageNumber: 1, text: `${file.name} local knowledge-base preview.` }],
      images: file.type.startsWith("image/") ? [{ imageId: assetId, mimeType: file.type, role: "knowledge_base_image" }] : [],
      tables: [],
      warnings: ["api_gateway_unavailable:demo_fallback_used"],
    },
  };
  localKnowledgeBaseAssets.unshift(asset);
  return Promise.resolve({ ...asset, extracted: asset.extracted ?? {} });
}

export const fallbackKnowledgeBase = (patientId?: string) => localKnowledgeBaseAssets.filter(asset => !patientId || asset.patientId === patientId);

export function fallbackExtractionRun(assetId: string, patientId: string): AgentRun {
  const runId = demoId("RUN");
  const option = syntheticExtractionOptions.find(item => item.assetId === assetId);
  return {
    id: runId,
    workflow: "extraction",
    status: "review",
    agentName: "image_extraction_pipeline",
    confidence: 0.91,
    createdAt: now(),
    auditId: demoId("AUD"),
    traceId: demoId("TRACE"),
    steps: ["Source Quality Agent", "PDF Packet Parser", "Vision Agent", "Clinical Structuring Agent", "Validation Agent", "Clinical Review Gate"].map((name, index) => ({ id: `${runId}-S${index + 1}`, name, status: index === 5 ? "review" : "completed", detail: index === 5 ? "Awaiting clinician review" : "Deterministic demo fallback completed", timestamp: now() })),
    evidence: [{ id: assetId, label: option?.filename ?? "Synthetic demo evidence", kind: "document", sourceUrl: option?.sourceUrl ?? option?.previewUrl ?? "", excerpt: String(option?.extracted.textPreview ?? "Synthetic extraction catalog evidence.") }],
    result: { patientId, fields: { documentType: "Enterprise five-patient clinical packet", patientMatch: patientId, sourceFile: option?.filename, packetId: option?.packetId, batchPatients: option?.batchPatientIds, finding: option?.extracted.textPreview ?? "Evidence ready for clinician verification" }, toolCalls: [], storageReceipts: [{ target: "json", status: "pending" }, { target: "relational", status: "pending" }, { target: "vector", status: "pending" }], persisted: false, extractedContent: option?.extracted },
  };
}

export function fallbackReviewRun(runId: string, decision: "approved" | "rejected", fields?: object): AgentRun {
  return {
    id: runId,
    workflow: "extraction",
    status: "completed",
    agentName: "image_extraction_pipeline",
    confidence: 0.91,
    createdAt: now(),
    auditId: demoId("AUD"),
    traceId: demoId("TRACE"),
    steps: [{ id: `${runId}-S-review`, name: "Clinical review", status: "completed", detail: decision === "approved" ? "Approved in deterministic demo fallback" : "Rejected in deterministic demo fallback", timestamp: now() }],
    evidence: [],
    result: { fields: fields ?? {}, decision, persisted: decision === "approved", storageReceipts: decision === "approved" ? [{ target: "json", status: "synced" }, { target: "relational", status: "synced" }, { target: "vector", status: "synced" }] : [] },
  };
}

export function fallbackQaRun(patientId: string, question: string, sourceTypes: string[]): AgentRun {
  const runId = demoId("RUN");
  const kb = fallbackKnowledgeBase(patientId);
  const chosen = kb.length ? kb : localKnowledgeBaseAssets;
  const evidence = chosen.slice(0, 4).map((asset, index) => ({
    id: asset.assetId,
    label: asset.filename,
    kind: asset.contentType.startsWith("image/") ? "image" as const : "document" as const,
    excerpt: String(asset.extracted?.textPreview ?? `${asset.filename} indexed in knowledge base.`),
    sourceUrl: asset.previewUrl,
    page: index + 1,
  }));
  const image = evidence.find(item => item.kind === "image" && item.sourceUrl && !item.sourceUrl.includes("/diagrams/"));
  return {
    id: runId,
    workflow: "qa",
    status: "completed",
    agentName: "patient_qa_pipeline",
    confidence: 0.87,
    createdAt: now(),
    auditId: demoId("AUD"),
    traceId: demoId("TRACE"),
    steps: ["Request Validation Agent", "Patient Context Agent", "Evidence Retrieval Agent", "Image Evidence Agent", "Citation Builder", "Answer Synthesis", "QA Audit"].map((name, index) => ({ id: `${runId}-S${index + 1}`, name, status: "completed", detail: index === 2 ? `Retrieved ${evidence.length} stored files` : "Deterministic demo fallback completed", timestamp: now() })),
    evidence,
    result: {
      answer: `${patientId}: The stored knowledge base indicates stable follow-up evidence with one visual source available for review. The answer uses ${evidence.length} cited file${evidence.length === 1 ? "" : "s"} across ${sourceTypes.length ? sourceTypes.join(", ") : "combined evidence"}.`,
      question,
      patientId,
      toolCalls: [],
      imageEvidence: image,
      summaryRows: evidence.map((item, index) => ({ citation: `[${index + 1}]`, file: item.label, type: item.kind, finding: item.excerpt })),
      limitations: "Deterministic demo fallback is synthetic and should be replaced by live API output when the product server is available.",
    },
  };
}

export function fallbackSqlPreview(question: string): AgentRun {
  const runId = demoId("RUN");
  return { id: runId, workflow: "database", status: "review", agentName: "db_intelligence_pipeline", confidence: 0.9, createdAt: now(), auditId: demoId("AUD"), traceId: demoId("TRACE"), steps: [{ id: `${runId}-S1`, name: "Schema Discovery Agent", status: "completed", detail: "Loaded deterministic fallback schema", timestamp: now() }, { id: `${runId}-S2`, name: "SQL Validator", status: "review", detail: "SELECT-only query awaits approval", timestamp: now() }], evidence: [], result: { question, sql: "SELECT risk_level, COUNT(*) AS patient_count FROM patients GROUP BY risk_level;", safe: true, toolCalls: [] } };
}

export function fallbackSqlExecute(runId: string): AgentRun {
  const rows = [{ risk_level: "High", patient_count: 4 }, { risk_level: "Needs review", patient_count: 7 }, { risk_level: "Stable", patient_count: 13 }];
  return { id: runId, workflow: "database", status: "completed", agentName: "db_intelligence_pipeline", confidence: 0.9, createdAt: now(), auditId: demoId("AUD"), traceId: demoId("TRACE"), steps: [{ id: `${runId}-S3`, name: "Query Executor", status: "completed", detail: "Executed deterministic fallback result set", timestamp: now() }, { id: `${runId}-S4`, name: "Insight Chart Agent", status: "completed", detail: "Rendered table and chart", timestamp: now() }], evidence: [], result: { rows, sql: "SELECT risk_level, COUNT(*) AS patient_count FROM patients GROUP BY risk_level;", chart: { type: "bar" }, toolCalls: [] } };
}
