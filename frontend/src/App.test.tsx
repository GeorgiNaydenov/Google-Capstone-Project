import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App, primaryRoutes } from "./App";

describe("clinical product shell", () => {
  afterEach(() => { vi.restoreAllMocks(); localStorage.clear(); });
  it("declares exactly sixteen primary screens", () => { expect(primaryRoutes).toHaveLength(16); });
  it("renders public synthetic demo landing", () => {
    render(<MemoryRouter initialEntries={["/"]}><App/></MemoryRouter>);
    expect(screen.getByRole("heading", { name: /turn fragmented clinical evidence/i })).toBeInTheDocument();
    expect(screen.getByText(/synthetic clinical data/i)).toBeInTheDocument();
  });
  it("uses a real upload input", () => {
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    expect(document.querySelector('input[type="file"]')).toBeInTheDocument();
  });
  it("opens orchestration with keyboard and reviews all plan fields", () => {
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog", { name: /plan a clinical task/i })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/what should nexus do/i), { target: { value: "Extract this image" } });
    fireEvent.click(screen.getByRole("button", { name: /image extraction.*manual workflow/i }));
    for (const label of ["Intent", "Workflow", "Agents", "Data sources", "Permissions", "Expected output"]) expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /run workflow/i })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: /database intelligence.*manual workflow/i }));
    fireEvent.click(screen.getByRole("button", { name: /run workflow/i }));
    expect(screen.getByRole("heading", { name: /database intelligence/i })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "k", metaKey: true });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
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
});
