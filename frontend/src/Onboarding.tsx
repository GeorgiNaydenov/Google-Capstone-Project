import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";

// First-run onboarding tour. The real application stays visible behind the
// panel, and each step navigates to the actual screen it describes.
export const ONBOARDING_KEY = "clinicalOnboardingV2";

type TourStep = {
  id: string;
  route: string;
  eyebrow: string;
  screen: string;
  title: string;
  body: string;
  visual?: ReactNode;
};

const EXTRACTION_STAGES = ["Quality", "OCR", "Vision", "Structuring", "Validation", "Review", "Storage", "Vector", "Audit"];

function SimPipeline() {
  const [lit, setLit] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => setLit(current => current >= EXTRACTION_STAGES.length ? current : current + 1), 380);
    return () => window.clearInterval(timer);
  }, []);
  return <div className="tour-sim" aria-hidden="true">
    <div className="tour-chip-row">{EXTRACTION_STAGES.map((stage, index) => <span key={stage} className={index < lit ? "lit" : ""}><i>{index < lit ? "ok" : index + 1}</i>{stage}</span>)}</div>
    <p>{lit < EXTRACTION_STAGES.length ? `${EXTRACTION_STAGES[lit]} agent is checking evidence.` : "Structured fields are ready. No values are persisted until review."}</p>
  </div>;
}

function ChipRow({ chips, flow = false }: { chips: string[]; flow?: boolean }) {
  return <div className="tour-sim" aria-hidden="true"><div className={flow ? "tour-chip-row flow" : "tour-chip-row"}>{chips.map(chip => <span key={chip} className="lit">{chip}</span>)}</div></div>;
}

const steps: TourStep[] = [
  {
    id: "welcome", route: "/app/dashboard", eyebrow: "WELCOME TO CLINICAL HUB", screen: "The dashboard behind this panel is the live workspace.",
    title: "Every patient source in one place you can trust.",
    body: "You bring the clinical judgment. Clinical Hub brings the scattered evidence together, lets specialist agents read it, and keeps every write behind your review. This tour follows the same screens your team will use: triage, extraction, patient Q&A, database insight, and audit.",
    visual: <ChipRow chips={["Multimodal ingestion", "Cited answers", "Clinician approval", "Audit trail"]}/>,
  },
  {
    id: "dashboard", route: "/app/dashboard", eyebrow: "YOUR MORNING, TRIAGED", screen: "Dashboard",
    title: "Start with the patients who need attention first.",
    body: "The dashboard turns the day into a prioritized clinical view. Every number is live from the API: high-risk patients, pending verifications, and agent alerts with confidence, source links, and quick actions in reach.",
  },
  {
    id: "tenants", route: "/app/dashboard", eyebrow: "DEMO AND LIVE TENANTS", screen: "Organization switcher",
    title: "Two demo tenants to explore, one live tenant for real work.",
    body: "The organization switcher in the top bar moves between Research Clinic and Northstar Health, two seeded demo tenants that show the product with realistic data. Switch to the Capstone tenant to work for real: it starts empty and fills only with what you upload and approve.",
    visual: <ChipRow flow chips={["Research Clinic (demo)", "Northstar Health (demo)", "Capstone (live)"]}/>,
  },
  {
    id: "record", route: "/app/queue", eyebrow: "ONE PATIENT RECORD", screen: "Patient queue",
    title: "Search once and see the full clinical picture.",
    body: "The queue brings structured fields, notes, imaging metadata, and indexed evidence into the same record view. Filters for risk, review state, and completeness help the right patient rise to the top.",
  },
  {
    id: "extraction", route: "/app/extraction", eyebrow: "AI WORKFLOW 1: MULTIMODAL EXTRACTION", screen: "Extraction workspace",
    title: "Upload a report and let the specialist agents read it.",
    body: "Use a photographed lab slip, referral, MRI report, PNG, JPEG, or PDF. The agents check quality, read text and images, structure findings, score confidence, and pause for your review before anything reaches the patient record.",
    visual: <SimPipeline/>,
  },
  {
    id: "qa", route: `/app/qa?query=${encodeURIComponent("What changed between the last two sessions?")}`, eyebrow: "AI WORKFLOW 2: MULTIMODAL Q&A", screen: "Patient Q&A",
    title: "Ask the record a clinical question.",
    body: "The question field behind this panel is already filled in. Close or step past this panel and press \"Ask Nexus agents\" to see the real agents retrieve across notes, labs, and images, with citations to the exact scan, note, or value.",
  },
  {
    id: "database", route: `/app/database?query=${encodeURIComponent("Count patients by risk level")}`, eyebrow: "AI WORKFLOW 3: POPULATION INTELLIGENCE", screen: "Database intelligence",
    title: "Turn a cohort question into a governed answer.",
    body: "The population question behind this panel is already filled in. Step past this panel and press \"Generate SQL preview\" to see the real read-only SQL, safety review, and — once you approve execution — governed results, charts, and a written insight.",
  },
  {
    id: "governance", route: "/app/inbox", eyebrow: "HUMAN-GOVERNED BY DESIGN", screen: "Clinical inbox",
    title: "You decide what becomes part of the record.",
    body: "Consequential outputs land in the inbox with the proposed change, evidence, confidence, and source trail. Approve it and the write is recorded. Reject it and it goes nowhere.",
  },
  {
    id: "orchestrator", route: "/app/inbox", eyebrow: "ONE COMMAND BAR", screen: "Workflow planning",
    title: "Describe the task and inspect the plan before it runs.",
    body: "From any screen, the orchestrator maps your intent to a workflow, agents, permissions, and expected output. The plan is visible first, so clinical context stays under your control.",
    visual: <ChipRow flow chips={["Intent", "Workflow", "Agents", "Permissions", "Run"]}/>,
  },
  {
    id: "atlas", route: "/app/dashboard", eyebrow: "SEE THE WHOLE SYSTEM", screen: "System atlas",
    title: "The architecture is documented right where you work.",
    body: "The System atlas at the bottom of the dashboard holds the full architecture as pan-and-zoom diagrams, grouped into categories. For the complete story, the Documentation hub opens the wikis and API reference as standalone reading, separate from this workspace.",
    visual: <ChipRow flow chips={["System", "Agents", "Security", "Processes", "Data", "Deployment"]}/>,
  },
  {
    id: "ready", route: "/app/dashboard", eyebrow: "READY TO WORK", screen: "Dashboard",
    title: "The full loop is now visible.",
    body: "Evidence comes in, agents extract it, you verify it, the record answers questions, the database reveals trends, and every step is auditable. The workspace is responsive, so it works on a tablet at the bedside too. Start with the queue. It is already prioritized.",
    visual: <ChipRow flow chips={["Evidence", "Extraction", "Review", "Q&A", "Insight", "Audit"]}/>,
  },
];

export function OnboardingTour({ open, onClose }: { open: boolean; onClose: () => void }) {
  const navigate = useNavigate();
  const dialogRef = useRef<HTMLElement>(null);
  const [step, setStep] = useState(0);
  const active = steps[step];
  const finish = useCallback((destination: string) => {
    localStorage.setItem(ONBOARDING_KEY, "done");
    onClose();
    navigate(destination);
  }, [navigate, onClose]);
  useEffect(() => { if (open) setStep(0); }, [open]);
  useEffect(() => { if (open) navigate(steps[step].route, { replace: true }); }, [open, step, navigate]);
  useEffect(() => { if (open) dialogRef.current?.focus(); }, [open, step]);
  useEffect(() => {
    if (!open) {
      delete document.body.dataset.tourStep;
      return;
    }
    document.body.dataset.tourStep = active.id;
    return () => { delete document.body.dataset.tourStep; };
  }, [open, active.id]);
  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = ""; };
  }, [open]);
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "ArrowRight") setStep(current => Math.min(current + 1, steps.length - 1));
      if (event.key === "ArrowLeft") setStep(current => Math.max(current - 1, 0));
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);
  if (!open) return null;
  return <div className="tour-backdrop">
    <section ref={dialogRef} tabIndex={-1} className="tour-modal" role="dialog" aria-modal="true" aria-labelledby="tour-title">
      <header>
        <div><span className="eyebrow accent">{active.eyebrow}</span><small className="tour-screen-note">{active.screen}</small></div>
        <div className="tour-actions"><button className="tour-skip" onClick={() => finish("/app/dashboard")}>Skip onboarding</button><button className="tour-close" aria-label="Close onboarding" onClick={() => finish(active.route)}>x</button></div>
      </header>
      <h2 id="tour-title">{active.title}</h2>
      <p className="tour-body">{active.body}</p>
      {active.visual}
      <footer>
        <div className="tour-progress" aria-label={`Step ${step + 1} of ${steps.length}`}>{steps.map((item, index) => <i key={item.id} className={index === step ? "current" : index < step ? "done" : ""}/>)}<span>Step {step + 1} of {steps.length}</span></div>
        <div className="button-row">
          {step > 0 && <button className="button subtle" onClick={() => setStep(step - 1)}>Back</button>}
          {step < steps.length - 1
            ? <button className="button primary" onClick={() => setStep(step + 1)}>{step === 0 ? "Show me around" : "Next"}</button>
            : <button className="button primary" onClick={() => finish("/app/queue")}>Open patient queue</button>}
        </div>
      </footer>
    </section>
  </div>;
}
