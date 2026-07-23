import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App, primaryRoutes } from "./App";
import { ONBOARDING_KEY } from "./Onboarding";

describe("clinical product shell", () => {
  beforeEach(() => { localStorage.setItem(ONBOARDING_KEY, "done"); });
  afterEach(() => { vi.restoreAllMocks(); localStorage.clear(); sessionStorage.clear(); });
  function mockPendingMutation(endpoint: RegExp) {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = String(input);
      if (init?.method === "POST" && endpoint.test(url)) return new Promise<Response>(() => undefined);
      return Promise.resolve(new Response(JSON.stringify({ detail: "Gateway unavailable" }), { status: 502, headers: { "Content-Type": "application/json" } }));
    });
  }
  it("declares the current primary screen inventory", () => {
    expect(primaryRoutes).toHaveLength(19);
    expect(primaryRoutes).toContain("/app/console");
    expect(primaryRoutes).toContain("/docs-viewer");
    expect(primaryRoutes).toContain("/docs-access");
  });
  it("renders public synthetic demo landing", () => {
    render(<MemoryRouter initialEntries={["/"]}><App/></MemoryRouter>);
    expect(screen.getByRole("heading", { name: /turn fragmented clinical evidence/i })).toBeInTheDocument();
    expect(screen.getByText(/synthetic patient records/i)).toBeInTheDocument();
    expect(screen.getByText(/architecture diagram atlas/i)).toBeInTheDocument();
    const categoryTabs = within(screen.getByRole("tablist", { name: /diagram categories/i }));
    expect(categoryTabs.getByRole("tab", { name: /^System/i })).toHaveAttribute("aria-selected", "true");
    expect(categoryTabs.getByRole("tab", { name: /Agents & Pipelines/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /C4 containers/i })).toBeInTheDocument();
    expect(screen.queryByText(/open draw\.io/i)).not.toBeInTheDocument();
  });
  it("uses synthetic extraction choices in demo mode", async () => {
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    expect(screen.getByRole("button", { name: /run selected packet/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue("PT-D00008")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /packet/i }).length).toBeGreaterThanOrEqual(10);
    expect(document.querySelector('input[type="file"]')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /run selected packet/i }));
    expect(await screen.findByDisplayValue(/Enterprise five-patient clinical packet/i)).toBeInTheDocument();
    expect(await screen.findByText(/Five-patient packet map/i)).toBeInTheDocument();
    expect(screen.getAllByText(/In packet/i)).toHaveLength(4);
    expect(screen.getByText(/^Selected$/i)).toBeInTheDocument();
    expect(await screen.findByText(/Visual extraction board/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Extraction confidence visualization/i)).toBeInTheDocument();
    expect(await screen.findByText(/Evidence sources for this run/i)).toBeInTheDocument();
    const citations = screen.getByLabelText("Inline evidence citations");
    fireEvent.click(within(citations).getAllByRole("button", { name: /PKT-EXT-0002\.pdf/i })[0]);
    expect(await screen.findByRole("dialog", { name: /evidence source/i })).toBeInTheDocument();
  });
  it("shows extraction agent progress while the selected packet is running", async () => {
    mockPendingMutation(/\/runs\/extraction$/);
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /run selected packet/i }));
    expect(await screen.findByRole("status", { name: /extraction agents are working/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Quality Assessment/i).length).toBeGreaterThan(0);
  });
  it("keeps real upload input for the live tenant", () => {
    sessionStorage.setItem("tenant", "capstone");
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    expect(document.querySelector('input[type="file"]')).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /process document/i })).toBeInTheDocument();
  });
  it("opens orchestration with keyboard and reviews all plan fields", () => {
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog", { name: /plan a clinical task/i })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/what should nexus do/i), { target: { value: "Extract this image" } });
    fireEvent.click(screen.getByRole("button", { name: /image extraction.*manual workflow/i }));
    for (const label of ["Intent", "Workflow", "Agents", "Data sources", "Permissions", "Expected output"]) expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /run workflow/i })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: /population insights.*manual workflow/i }));
    fireEvent.click(screen.getByRole("button", { name: /run workflow/i }));
    expect(screen.getByRole("heading", { name: /population insights/i })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "k", metaKey: true });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
  it("shows database schema context only to admins", async () => {
    render(<MemoryRouter initialEntries={["/app/database"]}><App/></MemoryRouter>);
    expect(screen.queryByText(/Schema explorer/i)).not.toBeInTheDocument();
    localStorage.setItem("clinicalRole", "admin");
    render(<MemoryRouter initialEntries={["/app/database"]}><App/></MemoryRouter>);
    expect(await screen.findByText(/Schema explorer/i)).toBeInTheDocument();
  });
  it("edits and saves the live agent configuration contract", async () => {
    localStorage.setItem("clinicalRole", "admin");
    const config = { version: 1, autoApprovalThreshold: 90, reviewThreshold: 75, maxConcurrentRuns: 8, databaseEnabled: true };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/notifications")) return new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/agents")) return new Response(JSON.stringify({ executionMode: "local", orchestrator: "clinical_orchestrator", framework: "Google ADK", pipelines: [] }), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/agent-config") && init?.method === "PUT") return new Response(JSON.stringify({ ...config, version: 2, maxConcurrentRuns: 12 }), { status: 200, headers: { "Content-Type": "application/json" } });
      return new Response(JSON.stringify(config), { status: 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/app/configuration"]}><App/></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: /safety settings/i }));
    expect(await screen.findByLabelText(/automatic approval threshold/i)).toHaveValue("90");
    fireEvent.change(screen.getByLabelText(/maximum concurrent agent runs/i), { target: { value: "12" } });
    fireEvent.click(screen.getByRole("button", { name: /save new version/i }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => init?.method === "PUT")).toBe(true));
    const request = fetchMock.mock.calls.find(([, init]) => init?.method === "PUT")?.[1] as RequestInit;
    expect(JSON.parse(String(request.body))).toMatchObject({ autoApprovalThreshold: 90, reviewThreshold: 75, maxConcurrentRuns: 12, databaseEnabled: true });
  });
  it("shows agent configuration read-only for clinicians", async () => {
    localStorage.setItem("clinicalRole", "clinician");
    render(<MemoryRouter initialEntries={["/app/configuration"]}><App/></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: /agent configuration and monitoring/i })).toBeInTheDocument();
    expect(screen.getByText(/read-only view/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /save new version/i })).not.toBeInTheDocument();
  });
  it("keeps the admin dashboard usable when read APIs return gateway errors", async () => {
    localStorage.setItem("clinicalRole", "admin");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "Gateway unavailable" }), { status: 502, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter initialEntries={["/app/admin"]}><App/></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: /admin dashboard/i })).toBeInTheDocument();
    expect(screen.getByText(/Clinical database/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Object storage/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/System atlas/i)).toBeInTheDocument();
    expect(screen.queryByText(/Unable to load this view/i)).not.toBeInTheDocument();
  });
  it("renders storage subtabs with concrete provider rows and hides the keyboard hint", async () => {
    localStorage.setItem("clinicalRole", "admin");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "Gateway unavailable" }), { status: 502, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter initialEntries={["/app/storage"]}><App/></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: /data and storage management/i })).toBeInTheDocument();
    expect(screen.queryByText(/Ctrl K/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /vector search index/i }));
    expect(await screen.findByText(/Vector Search Index -/i)).toBeInTheDocument();
    expect(screen.getAllByText(/clinical-evidence/i).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /sync failures/i }));
    expect(await screen.findByText(/Sync Failures - 1 record/i)).toBeInTheDocument();
    expect(screen.getByText(/Refresh provider after API gateway recovers/i)).toBeInTheDocument();
  });
  it("keeps Q&A agent output usable when demo mutations return gateway errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "Gateway unavailable" }), { status: 502, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter initialEntries={["/app/qa"]}><App/></MemoryRouter>);
    fireEvent.change(await screen.findByPlaceholderText(/ask a longitudinal/i), { target: { value: "What changed between the last two sessions?" } });
    fireEvent.click(screen.getByRole("button", { name: /ask about this patient/i }));
    expect(await screen.findByText(/Answer \+ table \+ visual evidence/i)).toBeInTheDocument();
    expect(await screen.findByText(/Visual retrieval map/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Retrieved source mix/i)).toBeInTheDocument();
    expect(screen.getByText(/stored knowledge base indicates stable follow-up/i)).toBeInTheDocument();
    expect(screen.getByText(/Evidence cited in this answer/i)).toBeInTheDocument();
    const evidenceImage = screen.getByAltText(/cited visual evidence/i) as HTMLImageElement;
    expect(evidenceImage.getAttribute("src")).toContain("/evidence/demo-retinopathy-intake.png");
    expect(evidenceImage.getAttribute("src")).not.toContain("/diagrams/");
    expect(screen.queryByText(/Request failed \(502\)/i)).not.toBeInTheDocument();
  });
  it("shows Q&A agent progress while a patient answer is being assembled", async () => {
    mockPendingMutation(/\/runs\/qa$/);
    render(<MemoryRouter initialEntries={["/app/qa"]}><App/></MemoryRouter>);
    fireEvent.change(await screen.findByPlaceholderText(/ask a longitudinal/i), { target: { value: "What changed between the last two sessions?" } });
    fireEvent.click(screen.getByRole("button", { name: /ask about this patient/i }));
    expect(await screen.findByRole("status", { name: /q&a agents are working/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Evidence Retrieval/i).length).toBeGreaterThan(0);
  });
  it("shows population insight progress while SQL is being drafted", async () => {
    mockPendingMutation(/\/runs\/database\/preview$/);
    render(<MemoryRouter initialEntries={["/app/database"]}><App/></MemoryRouter>);
    fireEvent.change(await screen.findByPlaceholderText(/ask a governed question/i), { target: { value: "Show high risk patients by age band" } });
    fireEvent.click(screen.getByRole("button", { name: /draft query for review/i }));
    expect(await screen.findByRole("status", { name: /population insights agents are working/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Natural Language to SQL/i).length).toBeGreaterThan(0);
  });
  it("shows stored multimodal files from the synthetic knowledge base", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "Gateway unavailable" }), { status: 502, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter initialEntries={["/app/qa"]}><App/></MemoryRouter>);
    const syntheticTab = await screen.findByRole("button", { name: /document library/i });
    expect(syntheticTab).toBeInTheDocument();
    expect(document.querySelector('input[type="file"]')).not.toBeInTheDocument();
    fireEvent.click(syntheticTab);
    expect(await screen.findByText(/Patient document library/i)).toBeInTheDocument();
    expect(screen.getAllByText(/ct-followup-summary\.pdf/i).length).toBeGreaterThan(0);
    expect(document.body.innerHTML).not.toContain("/diagrams/16-document-ingestion-flow.png");
    expect(screen.queryByText(/Request failed \(502\)/i)).not.toBeInTheDocument();
  });
  it("renders grouped navigation, searches patients, and opens actionable notifications", async () => {
    localStorage.setItem("clinicalRole", "clinician");
    const patient = { id: "PT-1029", name: "Eleanor Kim", mrn: "MRN-1029", age: 67, risk: "high", condition: "Chronic kidney disease", aiStatus: "needs_review" };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      const json = (value: unknown) => new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.includes("/patients?query=")) return json([patient]);
      if (url.endsWith("/notifications") && !init?.method) return json([{ id: "NTF-001", title: "Verification required", detail: "Review the extraction", severity: "critical", agent: "Validation Agent", createdAt: "now", read: false, route: "/app/inbox" }]);
      if (url.includes("/notifications/NTF-001/read")) return json({ id: "NTF-001", title: "Verification required", detail: "Review the extraction", severity: "critical", agent: "Validation Agent", createdAt: "now", read: true, route: "/app/inbox" });
      if (url.endsWith("/reviews")) return json([]);
      if (url.endsWith("/agents")) return json({ executionMode: "local", orchestrator: "clinical_orchestrator", framework: "Google ADK", pipelines: [] });
      return json([]);
    });
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    expect(screen.getByRole("link", { name: /sessions/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /reports/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /audit trail/i })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/global patient search/i), { target: { value: "Eleanor" } });
    expect(await screen.findByText("Eleanor Kim")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Notifications" }));
    fireEvent.click(await screen.findByRole("button", { name: /verification required/i }));
    expect(await screen.findByRole("heading", { name: "Clinical inbox" })).toBeInTheDocument();
  });
  it("switches tenants, refetches with the new header, and flags the real tenant", async () => {
    localStorage.setItem("clinicalRole", "clinician");
    sessionStorage.removeItem("tenant");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const json = (value: unknown) => new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/agents")) return json({ executionMode: "local", orchestrator: "clinical_orchestrator", framework: "Google ADK", pipelines: [] });
      return json([]);
    });
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    const select = screen.getByLabelText("Organization") as HTMLSelectElement;
    expect([...select.options].map(option => option.value)).toEqual(["research-clinic", "northstar-health", "capstone"]);
    expect(select.value).toBe("research-clinic");
    expect(screen.getByText("Demo")).toBeInTheDocument();
    fetchMock.mockClear();
    fireEvent.change(select, { target: { value: "northstar-health" } });
    expect(sessionStorage.getItem("tenant")).toBe("northstar-health");
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const tenants = fetchMock.mock.calls.map(([, init]) => new Headers(init?.headers).get("X-Tenant"));
    expect(tenants).toContain("northstar-health");
    fireEvent.change(select, { target: { value: "capstone" } });
    expect(sessionStorage.getItem("tenant")).toBe("capstone");
    expect(await screen.findByText("Live")).toBeInTheDocument();
  });
});
