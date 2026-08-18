# 5-minute demo video — shot list

Target: ≤5 minutes, published to YouTube. Record at 1440-wide desktop unless a
shot calls for tablet. Use the deployed deterministic Research Clinic tenant
for the guided run and clearly identify the public build's disabled paid-agent boundary.

## 0:00 — 0:25 · Hook + problem
- Landing page (`/`). Read the headline: fragmented clinical evidence →
  verifiable decisions.
- One sentence: "A visible multi-agent system on Google ADK; every write stays
  clinician-approved."

## 0:25 — 0:55 · Onboarding + orientation
- Click **Start clinical workspace** → role selection → Clinician.
- Let the first-run tour advance two or three steps; call out the **tenant
  step** and the **atlas step**. State that the public Cloud Run build runs
  deterministic workflows, while a self-controlled deployment can enable the
  Capstone live tenant with Google credentials.

## 0:55 — 1:20 · Honest dashboard
- `/app/dashboard`. Point out live KPIs, the prioritized queue, alerts derived
  from real notifications, and the quick actions.

## 1:20 — 2:10 · Workflow 1 — Image Extraction (HITL)
- `/app/extraction`. Enter a patient, drop an image/PDF, **Run extraction
  pipeline**. Show the agent stepper.
- Land on the review gate; toggle the checklist; **Approve** → storage receipts
  flip to synced; note the audit event. (Optionally show the reject confirm.)

## 2:10 — 2:55 · Workflow 2 — Multimodal Q&A
- `/app/qa`. Ask a patient-scoped question. Show the cited answer and open one
  evidence source from the answer.

## 2:55 — 3:40 · Workflow 3 — Database Intelligence
- `/app/database`. Ask a cohort question → inspect the read-only SQL → **Approve
  and execute** → table + chart. Mention the server-side safety gate.

## 3:40 — 4:10 · Admin honesty + security
- `/app/admin`. Show measured component health, run-derived monitoring, and
  the execution-mode indicator. Call out that paid ADK/Gemini execution is
  intentionally disabled in the public build rather than presenting demo
  output as live model output.

## 4:10 — 4:40 · Architecture atlas + documentation
- Scroll to the dashboard **System atlas**; pan/zoom one diagram.
- Open `/documentation` in a new tab — standalone wikis + API docs, separate
  from the app.

## 4:40 — 5:00 · Deployability + close
- Show `deployment/Dockerfile` and `deployment/cloudbuild.yaml` briefly; state
  single-origin deterministic Cloud Run, canonical `/health` and `/ready`
  probes, and the separately documented self-controlled live path.
- Close on the repo URL and Apache-2.0 license.

## Screenshots to capture for the media gallery
- Landing hero · clinician dashboard + atlas · extraction review gate · Q&A
  cited answer · database chart · admin system health · documentation hub.
- Cover image: the system-architecture SVG (`frontend/public/diagrams/svg/01-system-architecture.svg`).
