import type { AgentCatalog, AgentConfig, AgentMonitorRow, AgentRun, AuditEvent, ClinicalNotification, ClinicalSession, ClinicalUser, DashboardData, EvidenceItem, ExtractionSource, KnowledgeBaseAsset, Patient, Permissions, SchemaTable, StorageData, SystemHealth, WorkspaceSummary } from "./types";

const now = () => new Date().toISOString();

export const fallbackPatients: Patient[] = [
  { id: "PT-D00008", name: "Nora Rodriguez", mrn: "MRN-D000008", age: 89, sex: "F", condition: "Heart failure with reduced EF", risk: "high", aiStatus: "needs_review", completeness: 0.97, lastEncounter: "2026-06-29", assignedClinician: "Dr. James Lewis", openIssues: 4, dataSources: 7, lastAiReview: "2026-07-04" },
  { id: "PT-D00002", name: "Mark Rossi", mrn: "MRN-D000002", age: 50, sex: "M", condition: "Complex multimorbidity (DM, HF, CKD)", risk: "medium", aiStatus: "needs_review", completeness: 0.65, lastEncounter: "2026-06-23", assignedClinician: "Dr. Noah Nair", openIssues: 1, dataSources: 5, lastAiReview: "2026-07-03" },
  { id: "PT-D00006", name: "Fatima Jones", mrn: "MRN-D000006", age: 51, sex: "F", condition: "Oncology surveillance post-treatment", risk: "low", aiStatus: "verified", completeness: 0.76, lastEncounter: "2026-06-19", assignedClinician: "Dr. Isabella Nair", openIssues: 0, dataSources: 4, lastAiReview: "2026-07-02" },
];

export const fallbackSessions: ClinicalSession[] = [
  { id: "SES-001", patientId: "PT-D00008", title: "Heart failure follow-up", occurredAt: "2026-06-29", status: "review", summary: "Synthetic failover session pending review.", uploadedImageCount: 2, extractionConfidence: 0.88, jsonSyncStatus: "pending", relationalSyncStatus: "pending", vectorSyncStatus: "pending", auditStatus: "recorded" },
  { id: "SES-002", patientId: "PT-D00002", title: "Multimorbidity note bundle", occurredAt: "2026-06-23", status: "verified", summary: "Synthetic failover session synchronized.", uploadedImageCount: 1, extractionConfidence: 0.93, jsonSyncStatus: "synced", relationalSyncStatus: "synced", vectorSyncStatus: "synced", auditStatus: "recorded" },
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
    { assetId: "AST-DEMO-001", filename: "ct-followup-summary.pdf", contentType: "application/pdf", sizeBytes: 184000, createdAt: now(), patientId: "PT-D00008", bucket: "local-demo-assets", objectPath: "research-clinic/PT-D00008/ct-followup-summary.pdf", checksum: "sha256:demo-ct-001" },
    { assetId: "AST-DEMO-002", filename: "ct-followup-trend-evidence.png", contentType: "image/png", sizeBytes: 142000, createdAt: now(), patientId: "PT-D00008", bucket: "local-demo-assets", objectPath: "research-clinic/PT-D00008/ct-followup-trend-evidence.png", checksum: "sha256:demo-img-002" },
    { assetId: "AST-DEMO-003", filename: "renal-panel-note-bundle.pdf", contentType: "application/pdf", sizeBytes: 96000, createdAt: now(), patientId: "PT-D00002", bucket: "local-demo-assets", objectPath: "research-clinic/PT-D00002/renal-panel-note-bundle.pdf", checksum: "sha256:demo-renal-003" },
  ],
  persistedExtractions: [
    { runId: "RUN-DEMO-101", patientId: "PT-D00008", sessionId: "SES-001", jsonReceipt: "JSON-DEMO-101", relationalReceipt: "SQL-DEMO-101", vectorReceipt: "VEC-DEMO-101", reviewState: "approved", confidence: 0.93 },
    { runId: "RUN-DEMO-102", patientId: "PT-D00002", sessionId: "SES-002", jsonReceipt: "JSON-DEMO-102", relationalReceipt: "SQL-DEMO-102", vectorReceipt: "VEC-DEMO-102", reviewState: "approved", confidence: 0.91 },
  ],
  records: [
    { id: "OBJ-DEMO-001", source: "ct-followup-summary.pdf", destination: "Object storage", status: "synced", updated: now(), owner: "Upload service", patientId: "PT-D00008", sessionId: "SES-001", error: "" },
    { id: "OBJ-DEMO-002", source: "ct-followup-trend-evidence.png", destination: "Object storage", status: "synced", updated: now(), owner: "Upload service", patientId: "PT-D00008", sessionId: "SES-001", error: "" },
    { id: "JSON-DEMO-101", source: "Extraction RUN-DEMO-101", destination: "JSON document store", status: "synced", updated: now(), owner: "Storage Agent", patientId: "PT-D00008", sessionId: "SES-001", error: "" },
    { id: "SQL-DEMO-101", source: "Extraction RUN-DEMO-101", destination: "Relational database", status: "synced", updated: now(), owner: "Storage Agent", patientId: "PT-D00008", sessionId: "SES-001", error: "" },
    { id: "VEC-DEMO-101", source: "Extraction RUN-DEMO-101", destination: "Vector search index", status: "synced", updated: now(), owner: "Vector Indexing Agent", patientId: "PT-D00008", sessionId: "SES-001", error: "" },
    { id: "SYNC-DEMO-201", source: "Knowledge base refresh", destination: "Vector search index", status: "pending", updated: now(), owner: "Storage Agent", patientId: "PT-D00008", sessionId: "", error: "" },
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

export const syntheticExtractionOptionsPrimary: ExtractionSource[] = [
  {
    "id": "EXT-0001",
    "assetId": "EXT-0001",
    "patientId": "PT-D00001",
    "patientName": "Patient DEID-09469410",
    "label": "Type 2 diabetes with hypertension packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00001",
      "PT-D00002",
      "PT-D00003",
      "PT-D00004",
      "PT-D00005"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0001.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0001.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Type 2 diabetes with hypertension. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0001",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "ldl_cholesterol",
          "label": "LDL Cholesterol",
          "panel": "Lab",
          "value": 116.7,
          "unit": "mg/dL",
          "referenceRange": "0.0-100.0",
          "loinc": "13457-7",
          "flag": "high",
          "confidence": 0.92,
          "needs_review": true
        },
        {
          "field_name": "fasting_glucose",
          "label": "Fasting Glucose",
          "panel": "Lab",
          "value": 259.5,
          "unit": "mg/dL",
          "referenceRange": "70.0-99.0",
          "loinc": "1558-6",
          "flag": "critical_high",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 42.77,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.86,
          "needs_review": false
        },
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 8.7,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "critical_high",
          "confidence": 0.85,
          "needs_review": true
        },
        {
          "field_name": "triglycerides",
          "label": "Triglycerides",
          "panel": "Lab",
          "value": 118.73,
          "unit": "mg/dL",
          "referenceRange": "0.0-150.0",
          "loinc": "2571-8",
          "flag": "normal",
          "confidence": 0.87,
          "needs_review": false
        },
        {
          "field_name": "sodium",
          "label": "Sodium",
          "panel": "Lab",
          "value": 143.15,
          "unit": "mEq/L",
          "referenceRange": "136.0-145.0",
          "loinc": "2951-2",
          "flag": "normal",
          "confidence": 0.76,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0002",
    "assetId": "EXT-0002",
    "patientId": "PT-D00002",
    "patientName": "Mark Rossi",
    "label": "Complex multimorbidity (DM, HF, CKD) packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00001",
      "PT-D00002",
      "PT-D00003",
      "PT-D00004",
      "PT-D00005"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0002.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0002.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Complex multimorbidity (DM, HF, CKD). Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0002",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "uric_acid",
          "label": "Uric Acid",
          "panel": "Lab",
          "value": 8.48,
          "unit": "mg/dL",
          "referenceRange": "2.6-7.2",
          "loinc": "3084-1",
          "flag": "high",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "creatinine",
          "label": "Creatinine",
          "panel": "Lab",
          "value": 2.79,
          "unit": "mg/dL",
          "referenceRange": "0.6-1.2",
          "loinc": "2160-0",
          "flag": "critical_high",
          "confidence": 0.83,
          "needs_review": true
        },
        {
          "field_name": "fasting_glucose",
          "label": "Fasting Glucose",
          "panel": "Lab",
          "value": 159.9,
          "unit": "mg/dL",
          "referenceRange": "70.0-99.0",
          "loinc": "1558-6",
          "flag": "critical_high",
          "confidence": 0.84,
          "needs_review": true
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 4.99,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 5.61,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "low",
          "confidence": 0.95,
          "needs_review": true
        },
        {
          "field_name": "bun",
          "label": "BUN",
          "panel": "Lab",
          "value": 25.72,
          "unit": "mg/dL",
          "referenceRange": "7.0-25.0",
          "loinc": "3094-0",
          "flag": "high",
          "confidence": 0.88,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0003",
    "assetId": "EXT-0003",
    "patientId": "PT-D00003",
    "patientName": "Patient DEID-F9DEB942",
    "label": "Generalized anxiety with recurrent depression packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00001",
      "PT-D00002",
      "PT-D00003",
      "PT-D00004",
      "PT-D00005"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0003.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0003.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Generalized anxiety with recurrent depression. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0003",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "inr",
          "label": "INR",
          "panel": "Lab",
          "value": 1.57,
          "unit": "ratio",
          "referenceRange": "0.8-1.2",
          "loinc": "34714-6",
          "flag": "critical_high",
          "confidence": 0.77,
          "needs_review": true
        },
        {
          "field_name": "sodium",
          "label": "Sodium",
          "panel": "Lab",
          "value": 139.97,
          "unit": "mEq/L",
          "referenceRange": "136.0-145.0",
          "loinc": "2951-2",
          "flag": "normal",
          "confidence": 0.85,
          "needs_review": false
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 32.99,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.97,
          "needs_review": false
        },
        {
          "field_name": "free_t4",
          "label": "Free T4",
          "panel": "Lab",
          "value": 0.7,
          "unit": "ng/dL",
          "referenceRange": "0.8-1.8",
          "loinc": "3024-7",
          "flag": "low",
          "confidence": 0.87,
          "needs_review": true
        },
        {
          "field_name": "chloride",
          "label": "Chloride",
          "panel": "Lab",
          "value": 101.28,
          "unit": "mEq/L",
          "referenceRange": "98.0-106.0",
          "loinc": "2075-0",
          "flag": "normal",
          "confidence": 0.78,
          "needs_review": true
        },
        {
          "field_name": "pt",
          "label": "PT",
          "panel": "Lab",
          "value": 11.24,
          "unit": "seconds",
          "referenceRange": "11.0-13.5",
          "loinc": "5902-2",
          "flag": "normal",
          "confidence": 0.83,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0004",
    "assetId": "EXT-0004",
    "patientId": "PT-D00004",
    "patientName": "Patient DEID-BD26382C",
    "label": "Type 2 diabetes with hypertension packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00001",
      "PT-D00002",
      "PT-D00003",
      "PT-D00004",
      "PT-D00005"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0004.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0004.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Type 2 diabetes with hypertension. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0004",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "hdl_cholesterol",
          "label": "HDL Cholesterol",
          "panel": "Lab",
          "value": 388.08,
          "unit": "mg/dL",
          "referenceRange": "40.0-999.0",
          "loinc": "2085-9",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        },
        {
          "field_name": "total_cholesterol",
          "label": "Total Cholesterol",
          "panel": "Lab",
          "value": 0.0,
          "unit": "mg/dL",
          "referenceRange": "0.0-200.0",
          "loinc": "2093-3",
          "flag": "normal",
          "confidence": 0.88,
          "needs_review": false
        },
        {
          "field_name": "glucose",
          "label": "Glucose",
          "panel": "Lab",
          "value": 251.9,
          "unit": "mg/dL",
          "referenceRange": "70.0-100.0",
          "loinc": "2345-7",
          "flag": "critical_high",
          "confidence": 0.72,
          "needs_review": true
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 3.88,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.88,
          "needs_review": false
        },
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 8.4,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "critical_high",
          "confidence": 0.92,
          "needs_review": true
        },
        {
          "field_name": "triglycerides",
          "label": "Triglycerides",
          "panel": "Lab",
          "value": 90.75,
          "unit": "mg/dL",
          "referenceRange": "0.0-150.0",
          "loinc": "2571-8",
          "flag": "normal",
          "confidence": 0.78,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0005",
    "assetId": "EXT-0005",
    "patientId": "PT-D00005",
    "patientName": "Patient DEID-794B2BC6",
    "label": "Oncology surveillance post-treatment packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00001",
      "PT-D00002",
      "PT-D00003",
      "PT-D00004",
      "PT-D00005"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0005.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0005.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Oncology surveillance post-treatment. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0005",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "hematocrit",
          "label": "Hematocrit",
          "panel": "Lab",
          "value": 50.84,
          "unit": "%",
          "referenceRange": "36.0-52.0",
          "loinc": "4544-3",
          "flag": "normal",
          "confidence": 0.9,
          "needs_review": false
        },
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 22.08,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.82,
          "needs_review": false
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 4.64,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.83,
          "needs_review": false
        },
        {
          "field_name": "inr",
          "label": "INR",
          "panel": "Lab",
          "value": 0.81,
          "unit": "ratio",
          "referenceRange": "0.8-1.2",
          "loinc": "34714-6",
          "flag": "normal",
          "confidence": 0.82,
          "needs_review": false
        },
        {
          "field_name": "sodium",
          "label": "Sodium",
          "panel": "Lab",
          "value": 139.39,
          "unit": "mEq/L",
          "referenceRange": "136.0-145.0",
          "loinc": "2951-2",
          "flag": "normal",
          "confidence": 0.79,
          "needs_review": true
        },
        {
          "field_name": "calcium",
          "label": "Calcium",
          "panel": "Lab",
          "value": 9.82,
          "unit": "mg/dL",
          "referenceRange": "8.5-10.5",
          "loinc": "17861-6",
          "flag": "normal",
          "confidence": 0.84,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0006",
    "assetId": "EXT-0006",
    "patientId": "PT-D00006",
    "patientName": "Fatima Jones",
    "label": "Oncology surveillance post-treatment packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00006",
      "PT-D00007",
      "PT-D00008",
      "PT-D00009",
      "PT-D00010"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0006.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0006.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Oncology surveillance post-treatment. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0006",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "bun",
          "label": "BUN",
          "panel": "Lab",
          "value": 18.78,
          "unit": "mg/dL",
          "referenceRange": "7.0-25.0",
          "loinc": "3094-0",
          "flag": "normal",
          "confidence": 0.97,
          "needs_review": false
        },
        {
          "field_name": "esr",
          "label": "ESR",
          "panel": "Lab",
          "value": 2.89,
          "unit": "mm/hr",
          "referenceRange": "0.0-20.0",
          "loinc": "4537-7",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 26.22,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.9,
          "needs_review": false
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 22.51,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "vitamin_b12",
          "label": "Vitamin B12",
          "panel": "Lab",
          "value": 770.06,
          "unit": "pg/mL",
          "referenceRange": "200.0-900.0",
          "loinc": "2132-9",
          "flag": "normal",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "crp",
          "label": "CRP",
          "panel": "Lab",
          "value": 4.09,
          "unit": "mg/L",
          "referenceRange": "0.0-10.0",
          "loinc": "1988-5",
          "flag": "normal",
          "confidence": 0.97,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0007",
    "assetId": "EXT-0007",
    "patientId": "PT-D00007",
    "patientName": "Lisa Martin",
    "label": "Chronic low back pain with osteoarthritis packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00006",
      "PT-D00007",
      "PT-D00008",
      "PT-D00009",
      "PT-D00010"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0007.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0007.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Chronic low back pain with osteoarthritis. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0007",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 16.09,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 50.91,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.82,
          "needs_review": false
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 26.32,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.81,
          "needs_review": true
        },
        {
          "field_name": "ferritin",
          "label": "Ferritin",
          "panel": "Lab",
          "value": 109.12,
          "unit": "ng/mL",
          "referenceRange": "12.0-300.0",
          "loinc": "2276-4",
          "flag": "normal",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "calcium",
          "label": "Calcium",
          "panel": "Lab",
          "value": 10.46,
          "unit": "mg/dL",
          "referenceRange": "8.5-10.5",
          "loinc": "17861-6",
          "flag": "normal",
          "confidence": 0.83,
          "needs_review": false
        },
        {
          "field_name": "pt",
          "label": "PT",
          "panel": "Lab",
          "value": 12.64,
          "unit": "seconds",
          "referenceRange": "11.0-13.5",
          "loinc": "5902-2",
          "flag": "normal",
          "confidence": 0.72,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0008",
    "assetId": "EXT-0008",
    "patientId": "PT-D00008",
    "patientName": "Nora Rodriguez",
    "label": "Heart failure with reduced EF packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00006",
      "PT-D00007",
      "PT-D00008",
      "PT-D00009",
      "PT-D00010"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0008.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0008.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Heart failure with reduced EF. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0008",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "ferritin",
          "label": "Ferritin",
          "panel": "Lab",
          "value": 232.37,
          "unit": "ng/mL",
          "referenceRange": "12.0-300.0",
          "loinc": "2276-4",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "albumin",
          "label": "Albumin",
          "panel": "Lab",
          "value": 4.3,
          "unit": "g/dL",
          "referenceRange": "3.4-5.4",
          "loinc": "1751-7",
          "flag": "normal",
          "confidence": 0.96,
          "needs_review": false
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 30.17,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.72,
          "needs_review": true
        },
        {
          "field_name": "pt",
          "label": "PT",
          "panel": "Lab",
          "value": 11.6,
          "unit": "seconds",
          "referenceRange": "11.0-13.5",
          "loinc": "5902-2",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        },
        {
          "field_name": "calcium",
          "label": "Calcium",
          "panel": "Lab",
          "value": 9.74,
          "unit": "mg/dL",
          "referenceRange": "8.5-10.5",
          "loinc": "17861-6",
          "flag": "normal",
          "confidence": 0.83,
          "needs_review": false
        },
        {
          "field_name": "inr",
          "label": "INR",
          "panel": "Lab",
          "value": 2.31,
          "unit": "ratio",
          "referenceRange": "0.8-1.2",
          "loinc": "34714-6",
          "flag": "critical_high",
          "confidence": 0.94,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0009",
    "assetId": "EXT-0009",
    "patientId": "PT-D00009",
    "patientName": "Barbara Silva",
    "label": "COPD with acute exacerbation packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00006",
      "PT-D00007",
      "PT-D00008",
      "PT-D00009",
      "PT-D00010"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0009.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0009.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. COPD with acute exacerbation. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0009",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "albumin",
          "label": "Albumin",
          "panel": "Lab",
          "value": 3.7,
          "unit": "g/dL",
          "referenceRange": "3.4-5.4",
          "loinc": "1751-7",
          "flag": "normal",
          "confidence": 0.86,
          "needs_review": false
        },
        {
          "field_name": "bun",
          "label": "BUN",
          "panel": "Lab",
          "value": 14.87,
          "unit": "mg/dL",
          "referenceRange": "7.0-25.0",
          "loinc": "3094-0",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "hemoglobin",
          "label": "Hemoglobin",
          "panel": "Lab",
          "value": 17.01,
          "unit": "g/dL",
          "referenceRange": "12.0-17.5",
          "loinc": "718-7",
          "flag": "normal",
          "confidence": 0.97,
          "needs_review": false
        },
        {
          "field_name": "platelet_count",
          "label": "Platelet Count",
          "panel": "Lab",
          "value": 292.0,
          "unit": "10^3/uL",
          "referenceRange": "150.0-400.0",
          "loinc": "777-3",
          "flag": "normal",
          "confidence": 0.77,
          "needs_review": true
        },
        {
          "field_name": "hematocrit",
          "label": "Hematocrit",
          "panel": "Lab",
          "value": 44.21,
          "unit": "%",
          "referenceRange": "36.0-52.0",
          "loinc": "4544-3",
          "flag": "normal",
          "confidence": 0.87,
          "needs_review": false
        },
        {
          "field_name": "red_blood_cell_count",
          "label": "Red Blood Cell Count",
          "panel": "Lab",
          "value": 4.69,
          "unit": "10^6/uL",
          "referenceRange": "4.2-5.9",
          "loinc": "789-8",
          "flag": "normal",
          "confidence": 0.85,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0010",
    "assetId": "EXT-0010",
    "patientId": "PT-D00010",
    "patientName": "Patient DEID-E9676D6D",
    "label": "Generalized anxiety with recurrent depression packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-D00006",
      "PT-D00007",
      "PT-D00008",
      "PT-D00009",
      "PT-D00010"
    ],
    "previewUrl": "/demo-data/extraction/primary/images/EXT-0010.png",
    "sourceUrl": "/demo-data/extraction/primary/images/EXT-0010.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Generalized anxiety with recurrent depression. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0010",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 25.61,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 37.37,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "critical_high",
          "confidence": 0.89,
          "needs_review": true
        },
        {
          "field_name": "hemoglobin",
          "label": "Hemoglobin",
          "panel": "Lab",
          "value": 16.01,
          "unit": "g/dL",
          "referenceRange": "12.0-17.5",
          "loinc": "718-7",
          "flag": "normal",
          "confidence": 0.76,
          "needs_review": true
        },
        {
          "field_name": "esr",
          "label": "ESR",
          "panel": "Lab",
          "value": 18.2,
          "unit": "mm/hr",
          "referenceRange": "0.0-20.0",
          "loinc": "4537-7",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "platelet_count",
          "label": "Platelet Count",
          "panel": "Lab",
          "value": 334.59,
          "unit": "10^3/uL",
          "referenceRange": "150.0-400.0",
          "loinc": "777-3",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "glucose",
          "label": "Glucose",
          "panel": "Lab",
          "value": 85.9,
          "unit": "mg/dL",
          "referenceRange": "70.0-100.0",
          "loinc": "2345-7",
          "flag": "normal",
          "confidence": 0.76,
          "needs_review": true
        }
      ]
    }
  }
];

export const syntheticExtractionOptionsDemo2: ExtractionSource[] = [
  {
    "id": "EXT-0001",
    "assetId": "EXT-0001",
    "patientId": "PT-N00001",
    "patientName": "Patient DEID-9B399B83",
    "label": "Type 2 diabetes with hypertension packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00001",
      "PT-N00002",
      "PT-N00003",
      "PT-N00004",
      "PT-N00005"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0001.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0001.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Type 2 diabetes with hypertension. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0001",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "bnp",
          "label": "BNP",
          "panel": "Lab",
          "value": 11.13,
          "unit": "pg/mL",
          "referenceRange": "0.0-100.0",
          "loinc": "42637-9",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "albumin",
          "label": "Albumin",
          "panel": "Lab",
          "value": 4.65,
          "unit": "g/dL",
          "referenceRange": "3.4-5.4",
          "loinc": "1751-7",
          "flag": "normal",
          "confidence": 0.73,
          "needs_review": true
        },
        {
          "field_name": "total_cholesterol",
          "label": "Total Cholesterol",
          "panel": "Lab",
          "value": 0.0,
          "unit": "mg/dL",
          "referenceRange": "0.0-200.0",
          "loinc": "2093-3",
          "flag": "normal",
          "confidence": 0.84,
          "needs_review": false
        },
        {
          "field_name": "triglycerides",
          "label": "Triglycerides",
          "panel": "Lab",
          "value": 132.46,
          "unit": "mg/dL",
          "referenceRange": "0.0-150.0",
          "loinc": "2571-8",
          "flag": "normal",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "sodium",
          "label": "Sodium",
          "panel": "Lab",
          "value": 139.51,
          "unit": "mEq/L",
          "referenceRange": "136.0-145.0",
          "loinc": "2951-2",
          "flag": "normal",
          "confidence": 0.9,
          "needs_review": false
        },
        {
          "field_name": "hdl_cholesterol",
          "label": "HDL Cholesterol",
          "panel": "Lab",
          "value": 613.17,
          "unit": "mg/dL",
          "referenceRange": "40.0-999.0",
          "loinc": "2085-9",
          "flag": "normal",
          "confidence": 0.98,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0002",
    "assetId": "EXT-0002",
    "patientId": "PT-N00002",
    "patientName": "Jennifer Martin",
    "label": "Oncology surveillance post-treatment packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00001",
      "PT-N00002",
      "PT-N00003",
      "PT-N00004",
      "PT-N00005"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0002.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0002.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Oncology surveillance post-treatment. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0002",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "fasting_glucose",
          "label": "Fasting Glucose",
          "panel": "Lab",
          "value": 78.06,
          "unit": "mg/dL",
          "referenceRange": "70.0-99.0",
          "loinc": "1558-6",
          "flag": "normal",
          "confidence": 0.89,
          "needs_review": false
        },
        {
          "field_name": "calcium",
          "label": "Calcium",
          "panel": "Lab",
          "value": 8.98,
          "unit": "mg/dL",
          "referenceRange": "8.5-10.5",
          "loinc": "17861-6",
          "flag": "normal",
          "confidence": 0.76,
          "needs_review": true
        },
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 28.43,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.92,
          "needs_review": false
        },
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 4.48,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "normal",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "chloride",
          "label": "Chloride",
          "panel": "Lab",
          "value": 102.89,
          "unit": "mEq/L",
          "referenceRange": "98.0-106.0",
          "loinc": "2075-0",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 27.98,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.79,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0003",
    "assetId": "EXT-0003",
    "patientId": "PT-N00003",
    "patientName": "Matthew Davis",
    "label": "Preventive care and screening packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00001",
      "PT-N00002",
      "PT-N00003",
      "PT-N00004",
      "PT-N00005"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0003.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0003.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Preventive care and screening. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0003",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "creatinine",
          "label": "Creatinine",
          "panel": "Lab",
          "value": 0.77,
          "unit": "mg/dL",
          "referenceRange": "0.6-1.2",
          "loinc": "2160-0",
          "flag": "normal",
          "confidence": 0.95,
          "needs_review": false
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 27.58,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.85,
          "needs_review": false
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 5.0,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.73,
          "needs_review": true
        },
        {
          "field_name": "total_cholesterol",
          "label": "Total Cholesterol",
          "panel": "Lab",
          "value": 118.91,
          "unit": "mg/dL",
          "referenceRange": "0.0-200.0",
          "loinc": "2093-3",
          "flag": "normal",
          "confidence": 0.98,
          "needs_review": false
        },
        {
          "field_name": "triglycerides",
          "label": "Triglycerides",
          "panel": "Lab",
          "value": 20.91,
          "unit": "mg/dL",
          "referenceRange": "0.0-150.0",
          "loinc": "2571-8",
          "flag": "normal",
          "confidence": 0.9,
          "needs_review": false
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 27.78,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0004",
    "assetId": "EXT-0004",
    "patientId": "PT-N00004",
    "patientName": "Lisa Lewis",
    "label": "Complex multimorbidity (DM, HF, CKD) packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00001",
      "PT-N00002",
      "PT-N00003",
      "PT-N00004",
      "PT-N00005"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0004.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0004.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Complex multimorbidity (DM, HF, CKD). Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0004",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 29.71,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.93,
          "needs_review": false
        },
        {
          "field_name": "bnp",
          "label": "BNP",
          "panel": "Lab",
          "value": 628.0,
          "unit": "pg/mL",
          "referenceRange": "0.0-100.0",
          "loinc": "42637-9",
          "flag": "critical_high",
          "confidence": 0.92,
          "needs_review": true
        },
        {
          "field_name": "troponin_i",
          "label": "Troponin I",
          "panel": "Lab",
          "value": 0.0,
          "unit": "ng/mL",
          "referenceRange": "0.0-0.04",
          "loinc": "10839-9",
          "flag": "normal",
          "confidence": 0.79,
          "needs_review": true
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 3.98,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.73,
          "needs_review": true
        },
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 7.1,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "critical_high",
          "confidence": 0.92,
          "needs_review": true
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 23.12,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.89,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0005",
    "assetId": "EXT-0005",
    "patientId": "PT-N00005",
    "patientName": "Luis Lewis",
    "label": "Type 2 diabetes with hypertension packet PKT-EXT-0001",
    "filename": "PKT-EXT-0001.pdf",
    "packetFilename": "PKT-EXT-0001.pdf",
    "packetId": "PKT-EXT-0001",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00001",
      "PT-N00002",
      "PT-N00003",
      "PT-N00004",
      "PT-N00005"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0005.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0005.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0001.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0001.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0001. Type 2 diabetes with hypertension. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0005",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "egfr",
          "label": "eGFR",
          "panel": "Lab",
          "value": 393.67,
          "unit": "mL/min/1.73m2",
          "referenceRange": "60.0-999.0",
          "loinc": "69405-9",
          "flag": "normal",
          "confidence": 0.72,
          "needs_review": true
        },
        {
          "field_name": "bun",
          "label": "BUN",
          "panel": "Lab",
          "value": 23.26,
          "unit": "mg/dL",
          "referenceRange": "7.0-25.0",
          "loinc": "3094-0",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        },
        {
          "field_name": "glucose",
          "label": "Glucose",
          "panel": "Lab",
          "value": 225.7,
          "unit": "mg/dL",
          "referenceRange": "70.0-100.0",
          "loinc": "2345-7",
          "flag": "critical_high",
          "confidence": 0.94,
          "needs_review": true
        },
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 7.2,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "critical_high",
          "confidence": 0.76,
          "needs_review": true
        },
        {
          "field_name": "albumin",
          "label": "Albumin",
          "panel": "Lab",
          "value": 4.51,
          "unit": "g/dL",
          "referenceRange": "3.4-5.4",
          "loinc": "1751-7",
          "flag": "normal",
          "confidence": 0.86,
          "needs_review": false
        },
        {
          "field_name": "hdl_cholesterol",
          "label": "HDL Cholesterol",
          "panel": "Lab",
          "value": 1267.76,
          "unit": "mg/dL",
          "referenceRange": "40.0-999.0",
          "loinc": "2085-9",
          "flag": "critical_high",
          "confidence": 0.75,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0006",
    "assetId": "EXT-0006",
    "patientId": "PT-N00006",
    "patientName": "Robert Costa",
    "label": "Type 2 diabetes with hypertension packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00006",
      "PT-N00007",
      "PT-N00008",
      "PT-N00009",
      "PT-N00010"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0006.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0006.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Type 2 diabetes with hypertension. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0006",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 26.9,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.87,
          "needs_review": false
        },
        {
          "field_name": "total_cholesterol",
          "label": "Total Cholesterol",
          "panel": "Lab",
          "value": 0.0,
          "unit": "mg/dL",
          "referenceRange": "0.0-200.0",
          "loinc": "2093-3",
          "flag": "normal",
          "confidence": 0.72,
          "needs_review": true
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 26.74,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.85,
          "needs_review": false
        },
        {
          "field_name": "ldl_cholesterol",
          "label": "LDL Cholesterol",
          "panel": "Lab",
          "value": 168.2,
          "unit": "mg/dL",
          "referenceRange": "0.0-100.0",
          "loinc": "13457-7",
          "flag": "critical_high",
          "confidence": 0.8,
          "needs_review": true
        },
        {
          "field_name": "hdl_cholesterol",
          "label": "HDL Cholesterol",
          "panel": "Lab",
          "value": 24.82,
          "unit": "mg/dL",
          "referenceRange": "40.0-999.0",
          "loinc": "2085-9",
          "flag": "critical_low",
          "confidence": 0.78,
          "needs_review": true
        },
        {
          "field_name": "triglycerides",
          "label": "Triglycerides",
          "panel": "Lab",
          "value": 2.64,
          "unit": "mg/dL",
          "referenceRange": "0.0-150.0",
          "loinc": "2571-8",
          "flag": "normal",
          "confidence": 0.84,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0007",
    "assetId": "EXT-0007",
    "patientId": "PT-N00007",
    "patientName": "Daniel Martin",
    "label": "Generalized anxiety with recurrent depression packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00006",
      "PT-N00007",
      "PT-N00008",
      "PT-N00009",
      "PT-N00010"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0007.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0007.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Generalized anxiety with recurrent depression. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0007",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 28.62,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.88,
          "needs_review": false
        },
        {
          "field_name": "ast",
          "label": "AST",
          "panel": "Lab",
          "value": 18.83,
          "unit": "IU/L",
          "referenceRange": "10.0-40.0",
          "loinc": "1920-8",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 4.72,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "normal",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 3.69,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.83,
          "needs_review": false
        },
        {
          "field_name": "creatinine",
          "label": "Creatinine",
          "panel": "Lab",
          "value": 0.84,
          "unit": "mg/dL",
          "referenceRange": "0.6-1.2",
          "loinc": "2160-0",
          "flag": "normal",
          "confidence": 0.78,
          "needs_review": true
        },
        {
          "field_name": "sodium",
          "label": "Sodium",
          "panel": "Lab",
          "value": 143.77,
          "unit": "mEq/L",
          "referenceRange": "136.0-145.0",
          "loinc": "2951-2",
          "flag": "normal",
          "confidence": 0.77,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0008",
    "assetId": "EXT-0008",
    "patientId": "PT-N00008",
    "patientName": "Patient DEID-1504185A",
    "label": "Chronic kidney disease stage 3-4 packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00006",
      "PT-N00007",
      "PT-N00008",
      "PT-N00009",
      "PT-N00010"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0008.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0008.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Chronic kidney disease stage 3-4. Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0008",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "crp",
          "label": "CRP",
          "panel": "Lab",
          "value": 8.06,
          "unit": "mg/L",
          "referenceRange": "0.0-10.0",
          "loinc": "1988-5",
          "flag": "normal",
          "confidence": 0.76,
          "needs_review": true
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 49.75,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.84,
          "needs_review": false
        },
        {
          "field_name": "bnp",
          "label": "BNP",
          "panel": "Lab",
          "value": 37.31,
          "unit": "pg/mL",
          "referenceRange": "0.0-100.0",
          "loinc": "42637-9",
          "flag": "normal",
          "confidence": 0.92,
          "needs_review": false
        },
        {
          "field_name": "glucose",
          "label": "Glucose",
          "panel": "Lab",
          "value": 91.65,
          "unit": "mg/dL",
          "referenceRange": "70.0-100.0",
          "loinc": "2345-7",
          "flag": "normal",
          "confidence": 0.88,
          "needs_review": false
        },
        {
          "field_name": "co2_(bicarbonate)",
          "label": "CO2 (Bicarbonate)",
          "panel": "Lab",
          "value": 28.16,
          "unit": "mEq/L",
          "referenceRange": "22.0-29.0",
          "loinc": "2028-9",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        },
        {
          "field_name": "chloride",
          "label": "Chloride",
          "panel": "Lab",
          "value": 98.63,
          "unit": "mEq/L",
          "referenceRange": "98.0-106.0",
          "loinc": "2075-0",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        }
      ]
    }
  },
  {
    "id": "EXT-0009",
    "assetId": "EXT-0009",
    "patientId": "PT-N00009",
    "patientName": "Aisha Evans",
    "label": "Complex multimorbidity (DM, HF, CKD) packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00006",
      "PT-N00007",
      "PT-N00008",
      "PT-N00009",
      "PT-N00010"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0009.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0009.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Complex multimorbidity (DM, HF, CKD). Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0009",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "hba1c",
          "label": "HbA1c",
          "panel": "Lab",
          "value": 6.7,
          "unit": "%",
          "referenceRange": "4.0-5.6",
          "loinc": "4548-4",
          "flag": "high",
          "confidence": 0.89,
          "needs_review": true
        },
        {
          "field_name": "creatinine",
          "label": "Creatinine",
          "panel": "Lab",
          "value": 1.96,
          "unit": "mg/dL",
          "referenceRange": "0.6-1.2",
          "loinc": "2160-0",
          "flag": "critical_high",
          "confidence": 0.84,
          "needs_review": true
        },
        {
          "field_name": "sodium",
          "label": "Sodium",
          "panel": "Lab",
          "value": 144.69,
          "unit": "mEq/L",
          "referenceRange": "136.0-145.0",
          "loinc": "2951-2",
          "flag": "normal",
          "confidence": 0.88,
          "needs_review": false
        },
        {
          "field_name": "uric_acid",
          "label": "Uric Acid",
          "panel": "Lab",
          "value": 9.61,
          "unit": "mg/dL",
          "referenceRange": "2.6-7.2",
          "loinc": "3084-1",
          "flag": "critical_high",
          "confidence": 0.76,
          "needs_review": true
        },
        {
          "field_name": "bun",
          "label": "BUN",
          "panel": "Lab",
          "value": 5.5,
          "unit": "mg/dL",
          "referenceRange": "7.0-25.0",
          "loinc": "3094-0",
          "flag": "critical_low",
          "confidence": 0.74,
          "needs_review": true
        },
        {
          "field_name": "white_blood_cell_count",
          "label": "White Blood Cell Count",
          "panel": "Lab",
          "value": 7.87,
          "unit": "10^3/uL",
          "referenceRange": "4.5-11.0",
          "loinc": "6690-2",
          "flag": "normal",
          "confidence": 0.74,
          "needs_review": true
        }
      ]
    }
  },
  {
    "id": "EXT-0010",
    "assetId": "EXT-0010",
    "patientId": "PT-N00010",
    "patientName": "Patient DEID-918A23B1",
    "label": "Complex multimorbidity (DM, HF, CKD) packet PKT-EXT-0002",
    "filename": "PKT-EXT-0002.pdf",
    "packetFilename": "PKT-EXT-0002.pdf",
    "packetId": "PKT-EXT-0002",
    "patientsInFile": 5,
    "batchPatientIds": [
      "PT-N00006",
      "PT-N00007",
      "PT-N00008",
      "PT-N00009",
      "PT-N00010"
    ],
    "previewUrl": "/demo-data/extraction/demo2/images/EXT-0010.png",
    "sourceUrl": "/demo-data/extraction/demo2/images/EXT-0010.png",
    "fallbackPreviewUrl": "/evidence/demo-retinopathy-intake.png",
    "contentType": "application/pdf",
    "sourceContentType": "application/pdf",
    "previewContentType": "image/png",
    "extracted": {
      "type": "document",
      "documentType": "Enterprise five-patient clinical packet",
      "filename": "PKT-EXT-0002.pdf",
      "imageCount": 1,
      "pageCount": 5,
      "textPreview": "PKT-EXT-0002.pdf contains 5 de-identified patient records for governed extraction review.",
      "pages": [
        {
          "pageNumber": 1,
          "text": "Record packet 0002. Complex multimorbidity (DM, HF, CKD). Review extracted fields before saving to the chart."
        }
      ],
      "images": [
        {
          "imageId": "EXT-0010",
          "mimeType": "image/png",
          "role": "synthetic_demo_source"
        }
      ],
      "tables": [],
      "warnings": [],
      "fields": [
        {
          "field_name": "albumin",
          "label": "Albumin",
          "panel": "Lab",
          "value": 4.54,
          "unit": "g/dL",
          "referenceRange": "3.4-5.4",
          "loinc": "1751-7",
          "flag": "normal",
          "confidence": 0.92,
          "needs_review": false
        },
        {
          "field_name": "potassium",
          "label": "Potassium",
          "panel": "Lab",
          "value": 3.63,
          "unit": "mEq/L",
          "referenceRange": "3.5-5.1",
          "loinc": "2823-3",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        },
        {
          "field_name": "alt",
          "label": "ALT",
          "panel": "Lab",
          "value": 10.48,
          "unit": "IU/L",
          "referenceRange": "7.0-56.0",
          "loinc": "1742-6",
          "flag": "normal",
          "confidence": 0.91,
          "needs_review": false
        },
        {
          "field_name": "bnp",
          "label": "BNP",
          "panel": "Lab",
          "value": 1296.0,
          "unit": "pg/mL",
          "referenceRange": "0.0-100.0",
          "loinc": "42637-9",
          "flag": "critical_high",
          "confidence": 0.75,
          "needs_review": true
        },
        {
          "field_name": "troponin_i",
          "label": "Troponin I",
          "panel": "Lab",
          "value": 0.0,
          "unit": "ng/mL",
          "referenceRange": "0.0-0.04",
          "loinc": "10839-9",
          "flag": "normal",
          "confidence": 0.94,
          "needs_review": false
        },
        {
          "field_name": "calcium",
          "label": "Calcium",
          "panel": "Lab",
          "value": 9.64,
          "unit": "mg/dL",
          "referenceRange": "8.5-10.5",
          "loinc": "17861-6",
          "flag": "normal",
          "confidence": 0.96,
          "needs_review": false
        }
      ]
    }
  }
];

export const syntheticExtractionOptionsForTenant = (tenantId: string): ExtractionSource[] => tenantId === "northstar" ? syntheticExtractionOptionsDemo2 : syntheticExtractionOptionsPrimary;

export const localKnowledgeBaseAssets: KnowledgeBaseAsset[] = [
  {
    assetId: "KB-DEMO-001",
    patientId: "PT-D00008",
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
    patientId: "PT-D00008",
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
  const option = [...syntheticExtractionOptionsPrimary, ...syntheticExtractionOptionsDemo2].find(item => item.assetId === assetId && item.patientId === patientId) ?? [...syntheticExtractionOptionsPrimary, ...syntheticExtractionOptionsDemo2].find(item => item.assetId === assetId);
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
    evidence: [{ id: assetId, label: option?.filename ?? "Synthetic demo evidence", kind: "document", sourceUrl: option?.sourceUrl ?? option?.previewUrl ?? "", excerpt: String(option?.extracted?.textPreview ?? "Synthetic extraction catalog evidence.") }],
    result: { patientId, fields: { documentType: "Enterprise five-patient clinical packet", patientMatch: patientId, sourceFile: option?.filename, packetId: option?.packetId, batchPatients: option?.batchPatientIds, finding: option?.extracted?.textPreview ?? "Evidence ready for clinician verification" }, toolCalls: [], storageReceipts: [{ target: "json", status: "pending" }, { target: "relational", status: "pending" }, { target: "vector", status: "pending" }], persisted: false, extractedContent: option?.extracted },
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

// Shown when GET /database/examples is unreachable; the backend otherwise
// derives these from the tenant's real database contents.
export const fallbackDatabaseExamples = ["Count patients by risk level", "Which diabetic patients have an HbA1c above 9 percent?", "Which anticoagulated patients have no recent INR result?", "Which patients aged 65 and older are missing pneumococcal vaccination?", "Which patients are on 8 or more active medications?", "How does appointment no-show rate vary with housing stability?", "Show open care gaps by priority and owner"];

export function fallbackSqlPreview(question: string): AgentRun {
  const runId = demoId("RUN");
  return { id: runId, workflow: "database", status: "review", agentName: "db_intelligence_pipeline", confidence: 0.9, createdAt: now(), auditId: demoId("AUD"), traceId: demoId("TRACE"), steps: [{ id: `${runId}-S1`, name: "Schema Discovery Agent", status: "completed", detail: "Loaded deterministic fallback schema", timestamp: now() }, { id: `${runId}-S2`, name: "SQL Validator", status: "review", detail: "SELECT-only query awaits approval", timestamp: now() }], evidence: [], result: { question, sql: "SELECT risk_level, COUNT(*) AS patient_count FROM patients GROUP BY risk_level;", safe: true, toolCalls: [] } };
}

export function fallbackSqlExecute(runId: string): AgentRun {
  const rows = [{ risk_level: "High", patient_count: 4 }, { risk_level: "Needs review", patient_count: 7 }, { risk_level: "Stable", patient_count: 13 }];
  return { id: runId, workflow: "database", status: "completed", agentName: "db_intelligence_pipeline", confidence: 0.9, createdAt: now(), auditId: demoId("AUD"), traceId: demoId("TRACE"), steps: [{ id: `${runId}-S3`, name: "Query Executor", status: "completed", detail: "Executed deterministic fallback result set", timestamp: now() }, { id: `${runId}-S4`, name: "Insight Chart Agent", status: "completed", detail: "Rendered table and chart", timestamp: now() }], evidence: [], result: { rows, sql: "SELECT risk_level, COUNT(*) AS patient_count FROM patients GROUP BY risk_level;", chart: { type: "bar" }, toolCalls: [] } };
}
