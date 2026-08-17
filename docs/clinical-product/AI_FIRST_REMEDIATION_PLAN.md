# AI-First Remediation Plan

## Purpose

Make the product feel and behave like an AI clinical command center first, not
a general dashboard with agent labels. This plan targets weak design patterns,
optimization debt, harness drift, agent wiring gaps across the three guided
workflows, and document ingestion for PDFs and images under a 10 MB boundary.

## Current Evidence Snapshot

- `clinical_app/app.py` already enforces `10_000_000` bytes on `/api/assets`.
- `frontend/src/screens/WorkflowScreens.tsx` also blocks files above 10 MB and
  accepts PNG, JPEG, WEBP, and PDF.
- `clinical_app/document.py` parses PDFs with PyMuPDF when installed and images
  with Pillow when installed.
- `requirements.txt` does not include PyMuPDF or Pillow, so parser capability is
  optional in code but not guaranteed by setup.
- `clinical_app/document.py` extracts PDF text, page count, image count, and a
  first-page thumbnail, but not tables, per-page images, OCR text, image regions,
  or structured extraction blocks.
- `clinical_app/models.py` still allows `UploadRequest.size_bytes` up to
  `100_000_000`, which conflicts with the actual API boundary.
- `frontend/src/screens/WorkflowScreens.tsx` displays a small parsed-content
  summary, but the main workflow still privileges extracted fields over raw
  text, image, table, and provenance inspection.
- `docs/clinical-product/REQUIREMENTS_MATRIX.md` is stale in places: it still
  calls upload decorative and full-stack runtime missing, while current code has
  real upload, API routes, and guided workflow contracts.
- Largest concentration risks are `capstone_agent/tools.py`, `clinical_app/app.py`,
  and long frontend screen files. They make agent behavior harder to audit and
  optimize than the harness intends.

## Problem Map

| Area | Bad pattern | Risk | First fix |
|---|---|---|---|
| Product focus | AI trace is present but competes with generic dashboard panels. | Demo reads like admin software, not agent work. | Make agent run, evidence, review, and storage state primary in all three workflows. |
| Document parsing | Parser is optional, shallow, and mostly metadata-oriented. | PDFs/JPGs can upload but fail to produce useful clinical evidence. | Add required parser dependencies, typed parsed-document contract, OCR path, table extraction, and tests. |
| Upload limits | 10 MB is enforced in route/UI but not centralized. | Future code can drift to 100 MB or inconsistent errors. | Add one `MAX_UPLOAD_BYTES` config value and use it in model, API, UI contract docs, and tests. |
| Agent wiring | Demo runs call deterministic tools directly; live mode uses bridge fallback. | User cannot always tell whether ADK orchestration, tool calls, or fallback code produced output. | Normalize run events so every run exposes mode, graph node, tool input/output, fallback reason, and evidence lineage. |
| Harness use | Requirements matrix and delivery docs lag current code. | Agents may re-fix solved gaps or miss real gaps. | Refresh matrix with evidence-backed statuses before next implementation wave. |
| Optimization | Parser reads whole file into memory, app routes are monolithic, frontend casts loose data. | Larger docs, more sessions, and UI changes become fragile. | Stream or bounded-read uploads, split services/components, and type parsed outputs. |
| Display | Text preview is capped and tables/images are not first-class. | User cannot verify what AI saw before approving fields. | Add document inspector: pages, OCR text, tables, image thumbnails, selected regions, and extraction provenance. |
| Safety | MIME trust and OCR prompt injection are not fully modeled. | Malicious files or embedded text can steer agent prompts. | Validate by MIME plus file signature, isolate extracted text as untrusted data, scan before model/tool use. |

## Audit Passes

### 1. AI-First Design Audit

Inspect every routed screen and classify visible UI by purpose:

- `AI primary`: agent run, evidence, confidence, review, tool trace, storage,
  audit, prompt-safe rationale.
- `Clinical support`: patient details, queue, sessions, filters, role context.
- `Dashboard filler`: KPI or marketing blocks that do not change a decision.

Actions:

1. Move agent status, orchestration plan, current run, and evidence rail above
   generic dashboard content on workflow screens.
2. Replace vague labels like "real AI agent execution" in deterministic mode
   with exact mode labels: demo tool trace, live ADK run, or live fallback.
3. Require every primary CTA to start, inspect, approve, reject, rerun, cite,
   export, or audit an agent-backed action.
4. Remove or demote static preview cards that do not derive from API state.

Acceptance proof:

- Browser walkthrough shows extraction, Q&A, and database screens with agent
  trace and evidence visible in first viewport.
- No workflow primary control is inert or static-only.
- UI text accurately states demo versus live execution mode.

### 2. Document Ingestion Audit

Replace "file uploaded" with a typed evidence-ingestion pipeline:

1. Centralize upload policy:
   - `MAX_UPLOAD_BYTES = 10_000_000`
   - allowed MIME: `application/pdf`, `image/jpeg`, `image/png`, `image/webp`
   - allowed extensions match MIME and file signature
2. Guarantee dependencies:
   - add PyMuPDF for PDF text, page images, and embedded image counts
   - add Pillow for image metadata and thumbnails
   - choose OCR path for JPG/PNG screenshots and scanned PDFs
3. Return a structured parsed-document contract:
   - file metadata: filename, MIME, size, checksum
   - pages: page number, text blocks, thumbnail, image count
   - tables: page, rows, columns, confidence, source rectangle if available
   - images: page, thumbnail, dimensions, source rectangle
   - warnings: parser unavailable, scanned page, corrupt page, unsupported data
4. Treat extracted text as untrusted input:
   - run injection and secret scans before sending to model prompts
   - preserve raw text separately from model-produced fields

Acceptance proof:

- Tests cover PDF text, PDF table fixture, JPG/PNG image metadata, scanned-image
  OCR fixture or explicit OCR-unavailable warning, unsupported type rejection,
  exact 10 MB accepted, 10 MB plus 1 byte rejected.
- UI displays extracted text, images, tables, parser warnings, and page-level
  provenance before clinician approval.

### 3. Three Workflow Agent Audit

Audit extraction, Q&A, and database intelligence as separate run state machines.

Extraction:

- Intake -> quality -> OCR/vision -> structuring -> validation -> review ->
  storage receipts -> audit.
- Parsed document output must feed the same run that displays editable fields.
- Approval must show exactly which parsed text/table/image supported each field.

Patient Q&A:

- Question -> scope validation -> retrieval -> image/table/text evidence ->
  citation assembly -> answer -> audit.
- Citations must reopen the exact page, image, table row, or text block.
- Unsupported answer claims must be labeled, not hidden.

Database:

- Question -> schema discovery -> SQL generation -> deterministic safety ->
  preview -> explicit execution -> table -> chart -> CSV -> history/audit.
- Chart and CSV must derive from executed rows, not frontend-only mock shape.

Acceptance proof:

- Each workflow has a persisted run with mode, agent graph node, step status,
  tool calls, evidence IDs, confidence, review state, storage state, and audit ID.
- Tests assert the run contract, not just status code success.
- Frontend renders the same contract without `as unknown` casts for core fields.

### 4. Harness And Documentation Audit

Refresh docs and gates to match current source before more code work.

Actions:

1. Update `REQUIREMENTS_MATRIX.md` from "missing" to evidence-backed current
   statuses, keeping incomplete items explicit.
2. Add parser, upload, and AI-first display requirements to the matrix.
3. Add doc-ingestion fixtures to test ownership in `SWARM_DELIVERY_PLAN.md`.
4. Run `scripts/check_harness.py` after docs changes.
5. Keep `CLAUDE.md` and `AGENTS.md` synchronized if harness indexes change.

Acceptance proof:

- Matrix claims match inspected source.
- Harness check passes.
- Future agents can see parser and AI-first work as first-class scope.

### 5. Optimization Audit

Focus on bottlenecks that affect reliability, not premature polish:

- Avoid unbounded in-memory parsing beyond the 10 MB cap.
- Add parser timeouts or per-page limits for pathological PDFs.
- Cache parsed upload results by checksum inside the session repository.
- Split route/service boundaries so `clinical_app/app.py` stops owning parsing,
  workflow orchestration, storage, and rendering contracts at once.
- Split document inspector and workflow panels from `WorkflowScreens.tsx`.
- Replace brittle tool-call name matching in `AgentStepper` with explicit
  `stepId` or `agentStepId` on tool calls.

Acceptance proof:

- Parser has clear failure modes and cannot crash the upload route on corrupt
  files.
- Frontend document inspector can render large parsed payloads without layout
  shift.
- Unit tests cover parser and run-contract behavior separately.

## Delivery Waves

### Wave 0: Correct The Map

- Refresh stale requirement statuses.
- Add parser and AI-first acceptance criteria.
- Centralize upload limit constant and reconcile model contract.
- Add tests for current 10 MB behavior.

### Wave 1: Make Upload Evidence Real

- Install parser dependencies.
- Harden MIME/signature validation.
- Add typed parsed-document models.
- Add PDF/image fixtures and parser tests.
- Return text, pages, tables, images, thumbnails, warnings, and checksum.

### Wave 2: Build Document Inspector

- Add frontend parsed-document types.
- Render tabs for text, images, tables, and provenance.
- Let extraction fields link back to source blocks.
- Make parser warnings visible before running agents.

### Wave 3: Normalize Agent Runs

- Use one run event contract for demo, live ADK, and fallback.
- Attach tool calls to explicit step IDs.
- Add mode/fallback labels.
- Ensure all three workflows expose evidence lineage and audit state.

### Wave 4: Remove Non-AI Weight

- Reorder workflow screens around agent state.
- Demote static dashboard-only panels.
- Replace generic KPI panels with run, review, citation, and storage panels.
- Verify mobile and desktop first viewport framing.

### Wave 5: Prove It

- Run Python parser/unit/API tests.
- Run frontend typecheck, test, build, and targeted accessibility checks.
- Run browser smoke for the three workflows.
- Run ADK eval when valid model credentials exist.
- Update README/demo script with exact supported file types, 10 MB limit, and
  demo/live mode behavior.

## Definition Of Done

Done means current evidence proves all of this:

- Upload rejects files above 10 MB everywhere and documents that limit once.
- PDFs and JPG/PNG/WEBP files parse into typed text, image, table, page, warning,
  and provenance structures.
- UI displays extracted text, images, and tables before approval.
- Extraction, Q&A, and database intelligence all show agent graph, step trace,
  tool calls, evidence, confidence, review, storage, and audit state.
- Static dashboard content no longer hides the AI workflow.
- Harness docs match current behavior.
- Tests and browser checks cover the parser, workflow contracts, and UI display.
