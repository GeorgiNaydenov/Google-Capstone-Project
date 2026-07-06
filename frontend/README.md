# frontend — React Clinical UI

A **React/Vite/TypeScript** single-page application providing the clinician-facing interface for Clinical AI Kit. Features clinician and admin views with role-based access.

---

## Tech Stack

- **React** (latest) with React Router for navigation
- **TypeScript** for type safety across all components
- **Vite** for development server and production builds
- **Plotly.js** for interactive data visualization (charts, analytics)
- **Vitest** + React Testing Library for unit tests

---

## Application Structure

```
src/
├── main.tsx              # Application entry point
├── App.tsx               # Root component with routing
├── Shell.tsx             # Application shell (sidebar, header, role switching)
├── api.ts                # API client for all /api/* endpoints
├── useApi.ts             # React hooks for data fetching
├── types.ts              # TypeScript interfaces (Patient, Session, AgentRun, etc.)
├── context.tsx           # React context providers (role, session state)
├── components.tsx        # Shared UI components
├── styles.css            # Global styles and clinical design tokens
├── OrchestrationPanel.tsx # Agent orchestration visualization
├── Onboarding.tsx        # First-run guided onboarding tour (full-takeover modal)
├── plotly.d.ts           # Plotly type declarations
├── screens/
│   ├── EntryScreens.tsx  # Landing, role selection, demo entry
│   ├── ClinicalScreens.tsx # Clinician dashboard, patient views, Q&A, extraction
│   ├── WorkflowScreens.tsx # Extraction workflow, DB intelligence, session detail
│   └── AdminScreens.tsx  # Admin dashboard, users, agent config, audit, storage
├── test/
│   └── setup.ts          # Test environment configuration
└── vite-env.d.ts         # Vite type declarations
```

---

## Key Features

### Clinician Views
- **Dashboard** — Patient overview, risk stratification, recent activity, AI review status
- **Patient Profile** — Demographics, sessions, timeline, clinical history
- **Image Extraction** — Step-by-step agent workflow with confidence meters, field review, storage receipts
- **Patient Q&A** — Multimodal question answering with evidence citations and source viewing
- **Clinical Inbox** — Notifications, alerts, and pending reviews

### Admin Views
- **Admin Dashboard** — System metrics, agent performance, usage analytics
- **Agent Configuration** — Pipeline settings, approval thresholds, model selection
- **User Management** — Role-based access control
- **Audit Trail** — Complete event history with filtering
- **Data Storage** — Database schema browser, storage metrics

### Agent Orchestration Panel
- Real-time visualization of agent pipeline execution
- Step-by-step progress with tool calls and timing
- Confidence indicators and evidence display

### Guided Onboarding Tour
- Full-takeover modal shown the first time a user enters the workspace (`/app/*`), with the real application dimmed behind it
- 9 clinician-voiced steps that navigate the actual screens: dashboard triage, patient record, the three AI workflows (multimodal extraction, cited Q&A, database intelligence), human-in-the-loop governance, and the Ctrl+K orchestrator
- Deterministic in-modal simulations (agent pipeline, cited answer, SQL-to-chart) — zero API calls, works without a backend
- Skippable at any step (button or Escape); arrow keys navigate; completion and skip both persist to `localStorage` (`clinicalOnboardingV1`)
- Replayable via the "Replay product tour" button in the topbar
- Tests must seed `localStorage.setItem("clinicalOnboardingV1", "done")` before rendering `/app` routes unless they exercise the tour itself

---

## Development

```powershell
# Install dependencies
npm ci

# Start development server (proxies /api to localhost:8000)
npm run dev

# Type checking
npm run typecheck

# Run tests
npm test

# Production build (output to dist/)
npm run build
```

### API Proxy

During development, Vite proxies `/api/*` requests to `http://localhost:8000` (the FastAPI backend). This is configured in `vite.config.ts`.

### Production Serving

The production build (`npm run build`) outputs to `dist/`. FastAPI serves this directory as static files, so the entire application is served from a single origin in production.

---

## Type System

All API contracts are defined in `types.ts`:

- `Patient` — Patient demographics, risk level, AI status
- `ClinicalSession` — Session metadata, extraction confidence, sync status
- `AgentRun` — Workflow execution state, steps, evidence, results
- `AgentStep` — Individual agent step with status and timing
- `Evidence` — Text, image, or structured evidence with citations
- `AuditEvent` — Timestamped audit trail entries
- `DashboardData` — Aggregated metrics for dashboard views
- `OrchestrationPlan` — Agent routing and permission plan
- `AgentCatalog` — Available pipelines and their agent compositions
