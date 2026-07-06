# Production-Ready Polish + Kaggle Submission Plan

> Living document. Check items off (`[x]`) as they complete; any session (human or agent)
> resumes from here. Approved 2026-07-05. Companion: `PRODUCTION_TEST_PLAN.md` (already
> implemented — live-mode seam fixes verified in `clinical_app/live_bridge.py` / `app.py`).

## Context

Much of the app *feels* stubbed: admin screens render hardcoded constants, dashboards fall
back to literals like `?? 24`, buttons navigate nowhere, and the real (capstone) tenant shows
the same fake numbers as the demo. Goal: production-ready for both demo and real usage —
honest data, proper UX patterns, revamped home with a categorized diagram atlas (tabs +
sub-tabs), contextual embedded diagrams, updated onboarding, responsive layout, verified
container — **and ready for Kaggle submission**.

### Kaggle competition facts (verified 2026-07-05)

- **Deadline: July 6, 2026, 11:59 PM PT.** Un-submitted/draft writeups are not considered.
- Deliverables: Kaggle Writeup ≤2,500 words + cover image + media gallery + YouTube video
  ≤5 min + **public project link** (working demo or GitHub repo with setup instructions).
- Rubric (100): Technical Implementation **50** · Documentation **20** · Core Concept **10** ·
  Video **10** · Writeup **10**.
- Must demonstrate ≥3 of: ADK multi-agent, MCP server, Antigravity, Security, Deployability,
  Agent Skills. This project demonstrates 5 (ADK 22-agent pipelines, MCP server, 3-layer
  security, Cloud Run deployability, agent skills).
- Shared code must carry an **OSI-approved license permitting commercial use**.
- Repo `GeorgiNaydenov/nexus-clinical-ai-capstone` is currently **PRIVATE, no LICENSE** — both
  must change before judges follow the link.

### User-fixed decisions

1. Users & roles (real tenant): read-only directory from new `users` table in `capstone.db`;
   permission-matrix edits ARE persisted; no CRUD/invite flows.
2. **No authentication** anywhere — capstone requirement. Keep client-side role selection.
3. Diagrams: SVG exports + React zoom/pan/fullscreen viewer; **remove "open .drawio source"
   links** (view-only in app).
4. Fully responsive — tablet baseline pre-submission (Phase 5), full phone polish post
   cut-line (Phase 7).

**Cut-line rule:** Phases 0–6 land before submission. Phase 7 only if time remains.

---

## Phase 0 — Submission blockers

- [x] Persist this plan as `SUBMISSION_POLISH_PLAN.md` + memory pointer
- [x] Commit current working tree (staged by name) and push to `origin/main`
- [x] Add `LICENSE` (Apache-2.0), reference in README
- [x] README top section = judge path: problem → solution → 5 concepts with file pointers →
      demo quickstart (no API key) → live-mode setup; verify agent counts (22, 9/7/6)
- [ ] `gh repo edit --visibility public` — **only on user go-ahead at submission time**

## Phase 1 — Backend: honest data endpoints

Demo tenants: seeded-but-plausible via `DemoRepository`. Real tenant: derived/persisted truth.
Existing endpoint shapes change only additively.

### 1a. Repository/tenancy
- [x] `DemoDataset` gains `users` (5-6 per dataset), `monitor_baseline`, `pipeline_baseline`;
      deep-copied on `reset()` (`clinical_app/repository.py`, `tenancy.py`)
- [x] Both repos: `permissions` + `save_permissions(matrix, actor)` (demo session-scoped;
      live `role_permissions` table, default matrix inserted on first read, persisted + audited)
- [x] Both repos: `list_users()` (demo dataset / live `users` table)
- [x] Both repos: `agent_monitoring()` (demo baseline+session runs; live derived from
      `repo.runs` + `audit_log`, honest `[]` when empty)
- [x] New `clinical_app/system.py`: `component_checks(repo)` — real checks with latency
      (SQLite SELECT 1, capstone_agent importable, uploads writable, model env configured
      [never calls model], frontend/dist present, MCP importable)
- [x] `clinical_app/system.py`: `seed_users(db_path)` — idempotent users + role_permissions
      seeding in capstone.db from Pydantic-validated DEFAULT_USERS; called from
      `LiveRepository._hydrate_from_database()`
- [x] `LiveRepository._load_rows` joins `extracted_fields` into sessions; add
      `build_notifications()` (awaiting review → critical, failed → warning)

### 1b. Endpoints (`clinical_app/app.py`, Pydantic models in `clinical_app/models.py`)
- [x] GET `/api/system/health` — `{components:[{name,status,latencyMs,detail}],checkedAt}`
- [x] GET `/api/agents/monitoring` (admin) — per-agent stats
- [x] GET `/api/users` — + `memberCounts` per role
- [x] GET/PUT `/api/permissions` (admin) — `{roles,matrix,version}`; PUT persists + audits
- [x] GET `/api/database/schema` — parsed from `clinical_schemas.SCHEMA_DDL`
- [x] GET `/api/summary` — `{queueCount,inboxCount,unreadNotifications,patients}`
- [x] GET `/api/patients/{id}/evidence`
- [x] GET `/api/storage` — extend with derived `records:[...]`
- [x] GET `/api/sessions/{id}` — extend with `extractedFields`
- [x] GET `/api/dashboard` — extend metrics: failedExtractions, totalUsers, activeClinicians,
      pendingActions
- [x] Real-tenant `/api/notifications` → `repo.build_notifications()`
- [x] `capstone_agent/tools.py` `compose_clinical_answer`: deterministic synthesis replacing
      TODO pass-through (no LLM call; keep ToolResponse contract)

### 1c. Frontend wiring — delete every hardcoded constant
- [x] `api.ts` new calls: systemHealth, monitoring, permissions, savePermissions, schema,
      summary, patientEvidence; `types.ts` metrics required
- [x] `AdminScreens.tsx`: delete serviceHealth/monitorRows/objectRows/permissionSeed/mock
      role rows/[98.6,97.9,99.1]/"214/214"/static logs/"Total users: 48" — wire to endpoints,
      empty states for real tenant
- [x] `ClinicalScreens.tsx`: delete dashboardAlerts, fallbackActivity, all `?? N` fallbacks;
      PatientOverview derived; PatientProfile evidence tabs ← patientEvidence(); AI Summary ←
      latest QA run or CTA; SessionDetail ← extractedFields; ReportsView real navigation
- [x] `WorkflowScreens.tsx`: schemaTables ← api.schema(); DB Answer tab derived from rows;
      relevance ← run confidence; QA source counts ← patientEvidence()
- [x] `Shell.tsx`: nav badges ← api.summary(); profile button → popover (no PT-8829 /
      "Dr. Sarah Miller" hardcode)
- [x] `EntryScreens.tsx` RoleSelection: real health/summary instead of fake "Ready" badges
- [x] Quick filters "new"/"flagged"/"followup" implemented client-side with aria-pressed

### 1d. Tests
- [x] `test_clinical_api.py`: update users `== 2`; add system-health, schema, permissions,
      monitoring tests (all pass without GOOGLE_API_KEY)
- [x] `test_product_integration.py`: capstone users seeded; permissions persist across
      fresh sessions; monitoring `[]` before runs; notifications derived from run state

## Phase 2 — Diagram atlas + home revamp

- [x] 2a. Export all 28 `.drawio` → `frontend/public/diagrams/svg/` via draw.io CLI
      (`drawio -x -f svg -e -o out.svg in.drawio`; C4 via `--page-index 0/1/2`); copy PNGs
      08-28 as fallbacks; optional `scripts/export_diagrams.py`
- [x] 2b. `frontend/src/diagrams.ts` catalog `{id,title,category,summary,svg,png,points}`.
      Tabs→sub-tabs: System (01,02-p1/p2/p3,03,05,25) · Agents & Pipelines (06,07,08,09,12,28)
      · Security & Memory (10,11,22,26) · Processes (14-17,19-21,29) · Data & API (23,24) ·
      Deployment & Quality (04,13,18,27)
- [x] 2b. `components/DiagramViewer.tsx` — pointer pan, wheel+pinch zoom, zoom/reset/
      fullscreen, keyboard +/-/0, SVG `<img>` with PNG onError fallback, touch-first
- [x] 2b. `components/DiagramAtlas.tsx` (tablist + sub-tabs + viewer + summary; props
      defaultCategory, compact) and `components/InlineDiagram.tsx` (collapsible embed)
- [x] 2c. Atlas section on ClinicianDashboard + AdminDashboard (collapsible)
- [x] 2c. Landing refactor onto viewer/catalog; REMOVE "Open draw.io source" links; fix
      07-a2a card; update `App.test.tsx`
- [x] 2c. Contextual embeds: Config/Safety←11, Config/monitoring←06, DB schema←23-ERD,
      Storage←10, Inbox←15-HITL, Extraction←16, QA←19
- [x] 2d. ClinicianDashboard: derived greeting/counts, quick-action row, atlas
- [x] 2d. AdminDashboard: metric-driven KPIs, health card, monitoring performance, pipeline
      status from storage records, atlas

## Documentation hub (user-added scope, done)

- [x] Standalone docs pages at `/documentation` (hub + Karpathy LLM Wiki + Obsidian
      Project Wiki rendered HTML + links to Swagger/ReDoc/OpenAPI/API console),
      built by `scripts/build_docs_site.py`, mounted ahead of the SPA fallback,
      each page with home icon, "Back to main page", and "Enter the application"
      buttons; app entry points link out instead of embedding wikis

## Phase 3 — UX polish / design patterns

- [x] ErrorBoundary (route-level keyed by pathname + app-level) → ErrorState with reset
- [x] Skeleton primitives; per-screen skeletons replace generic loading text
- [x] ToastProvider + useToast (`role="status"`): config/permissions saved, review actions,
      CSV export, notification errors (replace silent catches)
- [x] Shared ConfirmDialog (focus trap, Escape): review Reject, demo reset
- [x] Shared Tabs component (tablist/tab/tabpanel + arrow keys) replacing 6 hand-rolled rows;
      aria-pressed chips; aria-live steppers; label tenant Live/Demo badge
- [x] ChartPanel palette + badge tones → CSS variables; sweep stray hex literals
- [x] Dead "Inspect/Logs" buttons → audit filtered by agent; persist disabledAgents in
      agent-config PUT (update allowed-keys app.py:742 + PUT test together)

## Phase 4 — Onboarding V2

- [x] Bump key value → `"clinicalOnboardingV2"` (tests import ONBOARDING_KEY)
- [x] Updated dashboard step copy; NEW atlas step (`document.body.dataset.tourStep="atlas"`
      spotlight); ≤10 steps; keep sims/replay/test-seeding contracts

## Phase 5 — Responsive tablet baseline

- [x] Remove `min-width:1180px` (styles.css); breakpoints >1220 / 768-1220 / <768 shared rules
- [x] Shell: overlay drawer sidebar <1024px (hamburger, aria-expanded, closes on
      navigate/Escape/backdrop); search collapse <768px; tools overflow menu <640px
- [x] DenseTable: global `.table-scroll` wrapper
- [x] Layout grids → 1fr at tablet via grouped media queries; KpiStrip scroll-snap
- [x] ChartPanel ResizeObserver relayout; onboarding modal `min(560px, calc(100vw-24px))`

## Phase 6 — Container verification + submission pack

- [x] Root `.dockerignore` (node_modules, dist, .venv, __pycache__, *.db*, uploads*/,
      Project Wiki/, .claude/, docs/, eval/, logs) — never bake capstone.db
- [x] Optional `CLINICAL_DATA_DIR` env in repository.py + capstone_agent/database.py roots;
      document Cloud Run ephemeral FS + max-instances=1 in deployment/README.md
- [x] `/readyz` runs component_checks (DB/dist/uploads), 503 on DB failure
- [x] Verify: npm run build → docker build → run → /healthz /readyz / → capstone tenant →
      volume survival
- [x] `docs/submission/demo-script.md` — 5-min video shot list (onboarding → extraction HITL →
      Q&A citations → database SQL gate + chart → atlas → admin health → deploy slide)
- [x] `docs/submission/` media: app screenshots + best diagram exports (cover + gallery)
- [x] `docs/submission/writeup-facts.md` — verified numbers for ≤2,500-word writeup
- [x] Final commit + push; flip repo public on user go-ahead

## Phase 7 — Post-cut-line (only if time remains)

- [x] Card-collapse patient queue + inbox tables <640px; touch targets ≥40px; landing/roles
      stacking; manual 360px pass on all 16 routes
- [x] vitest: DiagramAtlas tabs, DiagramViewer zoom, ErrorBoundary, no-fallback-literal
      dashboard, drawer toggle (mock matchMedia), toast on save, onboarding V2
- [x] pytest: storage records after upload+approve, summary counts

## Verification matrix

| Area | Demo tenant | Real (capstone) |
|---|---|---|
| Dashboard KPIs | seeded metrics, no frontend literals | zeros/actuals only |
| Service health | real component checks | real component checks |
| Agent monitoring | baseline + session runs | empty → populated after run |
| Users/permissions | dataset users; matrix session-scoped | DB-seeded; persists across sessions |
| Notifications | seeded, actionable | derived from run state |
| Atlas | tabs/sub-tabs, zoom/pan/fullscreen | same |
| Onboarding | V2 incl. atlas step; replay | same |
| Container | builds; healthz/readyz; SPA served | volume persists capstone.db |
| Suites | `pytest tests/ -v`, `npm test`, `npm run typecheck` green (no GOOGLE_API_KEY) | — |
| Submission | LICENSE present, repo public, README judge path, media + facts pack | — |

## Risks

- **Deadline**: Phases 0–6 sized to fit; Phase 7 is the buffer. If tight mid-Phase 3, skip
  items 5–7 there and jump to Phase 4 → 6.
- Real tenant with no runs shows honest empty states on admin screens — expected.
- UI-copy changes break assertions (`/api/users == 2`, landing links, config PUT payload) —
  update tests in the same commit per phase.
- New `clinical_app/system.py` appears in wiki Drift Report until documented — expected.
- Never assert LLM semantic output; all tests pass without GOOGLE_API_KEY.
