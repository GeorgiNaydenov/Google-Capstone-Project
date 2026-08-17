# Clinical Product Requirements Matrix

## Status Scale

- `Satisfied`: current evidence proves the requirement.
- `Partial`: visual or backend pieces exist, but the behavior is incomplete.
- `Missing`: no product implementation exists.

## Dependency Key

- `D1`: production frontend runtime, router, and reusable components
- `D2`: typed API contracts and one mutable demo repository
- `D3`: persisted agent-run, step, and event model connecting ADK to UI
- `D4`: upload, asset, evidence, and citation storage
- `D5`: review, persistence, sync, timeline, and audit transactions
- `D6`: identity, RBAC, organization, and patient scope
- `D7`: chart, file, and export services
- `D8`: API, browser, accessibility, and visual verification harness

## Cross-Cutting Findings

| ID | Requirement | Status | Priority | Evidence and gap | Dependencies | Acceptance proof |
|---|---|---|---|---|---|---|
| C01 | Full-stack product runtime | Missing | P0 | Only the `.dc.html` prototype exists; there is no frontend manifest or product API. Docker starts `adk web`. | D1-D3 | One install/build/start path serves the routed UI and typed API. |
| C02 | Shared mutable state | Missing | P0 | UI fixture arrays and Python mock data are separate. Row navigation does not carry patient identity. | D2,D5 | Mutations survive reload and reconcile across queue, profile, storage, and audit. |
| C03 | Functional controls | Missing | P0 | Prototype has 28 buttons, 13 wired buttons, four inputs, zero file inputs, and three simulated timers. | D1-D5 | Every primary control performs a real transition or is explicitly disabled. |
| C04 | Clinical design system | Partial | P1 | Dense panel/table layout is strong, but palette and production component architecture differ from the brief. | D1,D8 | Token audit and 1440px visual regression match the approved design. |
| C05 | Top navigation | Partial | P1 | Command, search, role, demo, and notification visuals exist. Organization and avatar behavior are absent. | D1,D6 | All required controls work and scope data correctly. |
| C06 | Navigation inventory | Partial | P1 | Several clinician and admin destinations are omitted or only implied by consolidated screens. | D1 | Every required destination has a route or explicit deep-linked subsection. |
| C07 | Role and context continuity | Partial | P0 | Role is local UI state. Patient/session identity and permission context are not preserved. | D2,D6 | Switching roles opens the related governance/clinical view for the same entity. |
| C08 | Visible agent metadata | Partial | P0 | Static confidence, evidence, sync, and audit fragments exist but are not one consistent output contract. | D3,D5 | Every generated output shows agent, confidence, evidence, review, timestamp, sync, and audit ID. |
| C09 | Reusable product components | Missing | P1 | Uploaded design-system examples exist; the actual product is one monolithic component. | D1 | Required components are reused, tested, semantic, and keyboard accessible. |
| C10 | Coherent demo graph | Partial | P0 | Fixtures are realistic but contain conflicting identities and no first-class run/evidence records. | D2 | Seed graph links patients, sessions, runs, evidence, reviews, storage, and audits consistently. |
| C11 | Public no-login demo | Partial | P0 | Landing and demo notice exist, but none of the three guided workflows completes. | D1-D5 | Fresh browser completes all workflows without login or exposed keys. |
| C12 | Accessibility | Partial | P1 | Many controls are styled div/span/anchor elements; upload is decorative. | D1,D8 | Semantic controls, labels, focus behavior, keyboard operation, and WCAG AA checks pass. |

## Required Screens

| # | Screen | Status | Priority | Main gaps | Acceptance proof |
|---|---|---|---|---|---|
| 1 | Public Demo Landing | Partial | P1 | CTA opens only the prototype; architecture is not the deployed runtime. | CTA enters a functioning isolated demo and the diagram matches reality. |
| 2 | Role Selection | Partial | P1 | Activity and sync are static. | Cards enter API-backed workspaces; activity and sync reflect shared state. |
| 3 | Global Patient Search | Partial | P0 | Search, filters, pagination, export, columns, and patient identity flow are incomplete. | All filters query the API; required columns, pagination, export, and exact patient navigation work. |
| 4 | Patient Overview | Partial | P1 | Only part of the KPI set exists; segmentation and drill-down are incomplete. | All requested metrics derive from shared data and drill into matching patients. |
| 5 | Clinician Dashboard | Partial | P1 | Sessions, tasks, inbox, and reconciliation are incomplete. | All panels use shared data and link to exact records. |
| 6 | Patient Queue | Partial | P0 | Filters do not filter rows; assignment/action flow is absent. | Filter, sort, assign, act, and exact-patient navigation work. |
| 7 | Patient Profile | Partial | P0 | Tabs change labels only; several patient panels and copilot behavior are missing. | Every tab renders patient-scoped content; copilot returns cited evidence. |
| 8 | Session Detail | Partial | P0 | JSON, relational, vector previews and review persistence are missing. | Artifacts are session-scoped; edit/approve updates receipts, timeline, and audit. |
| 9 | Image Extraction Agent | Implemented | P0 | Packet and selected-patient lineage are explicit; review and storage transitions persist. | Upload, visible steps, editable extraction, review decisions, receipts, audit, and timeline persist. |
| 10 | Multimodal Patient Q&A | Implemented | P0 | Backend-ranked text and renderable image evidence return with clinician-oriented answer sections and restorable history. | Scoped question returns cited structured/image evidence and opens the correct source. |
| 11 | Database Intelligence | Implemented | P0 | Read-only SQL preview, explicit execution, rows, chart, prevalence, export, history, and audit share one result package. | Generate -> preview/safety -> explicit execute -> table/chart/CSV/history/audit succeeds. |
| 12 | Clinical Inbox | Partial | P0 | Selected context is not linked; verify/reject is inert. | Selection scopes context; decision updates review queues and audit. |
| 13 | Admin Dashboard | Partial | P1 | Required KPIs, user activity, compliance, and drill-down are incomplete. | All requested panels reconcile with runtime records and drill down. |
| 14 | Users and Roles | Partial | P1 | Roles, assignments, access scope, audit history, and enforcement are incomplete. | All five roles exist; multi-role changes persist and API permissions enforce them. |
| 15 | Data and Storage | Partial | P0 | Relational/vector/audit/sync/failed records and lineage actions are incomplete. | All storage layers show real receipts; failed sync can retry idempotently. |
| 16 | Agent Configuration and Monitoring | Partial | P1 | Settings are local, unsaved, and lack required actions/metrics. | Versioned settings persist, are role-protected, and changes/retries are audited. |

## Orchestration and Guided Workflows

| ID | Workflow | Status | Required end-to-end proof |
|---|---|---|---|
| W01 | Natural and manual orchestration | Partial | Persisted plan shows intent, workflow, agents, sources, permissions, expected output, and confirmation. Both routing modes create the same run model. |
| W02 | Session image extraction | Implemented | Upload -> quality/vision/OCR/structuring/validation -> review -> JSON/relational/vector writes -> audit -> timeline. |
| W03 | Multimodal patient Q&A | Implemented | Question -> scoped retrieval -> cited answer -> supporting image/chunk -> source navigation -> audit. |
| W04 | Database intelligence | Implemented | Question -> generated SQL -> safety result and preview -> explicit execution -> table/chart/CSV -> history/audit. |

## Demo Data Contract

The seed must contain linked first-class records for:

- patients and clinical attributes
- sessions and verification/sync status
- agent runs and steps
- evidence, image assets, vector chunks, and citations
- extraction fields with provenance, confidence, and version
- review requests and decisions
- storage receipts and failures
- audit events and trace/run correlation
- users, assigned roles, organizations, and access scope
- agent configuration versions

Every demo session gets an isolated mutable snapshot. Reset restores the exact
seed and invalidates prior transient run state.

## Required Reusable Components

The production frontend must include the brief's component inventory:

`RoleSwitcher`, `ClinicalTopNav`, `ClinicalSidebar`,
`GlobalAICommandBar`, `AgentOrchestrationPanel`, `AgentActivityPanel`,
`PatientRiskBadge`, `PatientDataCompletenessBadge`,
`EvidenceCitationCard`, `ImageEvidenceViewer`, `StructuredJsonViewer`,
`RelationalTablePreview`, `VectorIndexStatus`, `SQLPreviewBlock`,
`ChartResultPanel`, `AuditTimeline`, `ClinicianReviewChecklist`,
`PatientTimeline`, `DenseDataTable`, `ClinicalKpiStrip`,
`AgentConfidenceMeter`, `StorageSyncStatus`, `AgentStepper`, and
`RoleAwareWorkspace`.

## Recommended Build Order

1. D1 + D2: routed product shell, contracts, shared seed, reset/isolation.
2. D3-D5: extraction vertical slice through review, storage, audit, timeline.
3. Q&A slice with citation navigation.
4. Database slice with SQL preview, safety, chart, export, and history.
5. D6: role scope and context continuity.
6. Complete remaining screen breadth and admin operations.
7. D8: API, browser, accessibility, visual, and deployment verification.
