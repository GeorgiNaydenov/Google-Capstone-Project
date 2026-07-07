import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { ONBOARDING_KEY } from "./Onboarding";

function mockApi() {
  vi.spyOn(globalThis, "fetch").mockImplementation(async input => {
    const url = String(input);
    const json = (value: unknown) => new Response(JSON.stringify(value), { status: 200, headers: { "Content-Type": "application/json" } });
    if (url.includes("/dashboard")) return json({ metrics: {}, patients: [], sessions: [], activity: [] });
    if (url.endsWith("/agents")) return json({ executionMode: "local", orchestrator: "clinical_orchestrator", framework: "Google ADK", pipelines: [] });
    return json([]);
  });
}

describe("first-run onboarding tour", () => {
  afterEach(() => { vi.restoreAllMocks(); localStorage.clear(); });

  it("takes over the workspace on first visit and skip persists the dismissal", () => {
    mockApi();
    render(<MemoryRouter initialEntries={["/app/dashboard"]}><App/></MemoryRouter>);
    expect(screen.getByRole("dialog", { name: /every patient source/i })).toBeInTheDocument();
    expect(document.body.dataset.tourStep).toBe("welcome");
    fireEvent.click(screen.getByRole("button", { name: /skip onboarding/i }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(localStorage.getItem(ONBOARDING_KEY)).toBe("done");
    expect(document.body.dataset.tourStep).toBeUndefined();
  });

  it("can be closed from the explicit close button", () => {
    mockApi();
    render(<MemoryRouter initialEntries={["/app/dashboard"]}><App/></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: /close onboarding/i }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(localStorage.getItem(ONBOARDING_KEY)).toBe("done");
    expect(document.body.dataset.tourStep).toBeUndefined();
  });

  it("does not reappear once dismissed", () => {
    mockApi();
    localStorage.setItem(ONBOARDING_KEY, "done");
    render(<MemoryRouter initialEntries={["/app/dashboard"]}><App/></MemoryRouter>);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("does not hijack a first-visit workflow deep link", async () => {
    mockApi();
    render(<MemoryRouter initialEntries={["/app/extraction"]}><App/></MemoryRouter>);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: /clinical evidence extraction/i })).toBeInTheDocument();
  });

  it("walks the simulated journey across real screens and lands on the queue", async () => {
    mockApi();
    render(<MemoryRouter initialEntries={["/app/dashboard"]}><App/></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: /show me around/i }));
    expect(screen.getByRole("dialog", { name: /patients who need attention/i })).toBeInTheDocument();
    expect(document.body.dataset.tourStep).toBe("dashboard");
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /demo tenants to explore/i })).toBeInTheDocument();
    expect(document.body.dataset.tourStep).toBe("tenants");
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /full clinical picture/i })).toBeInTheDocument();
    expect(document.body.dataset.tourStep).toBe("record");
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /specialist agents read it/i })).toBeInTheDocument();
    expect(document.body.dataset.tourStep).toBe("extraction");
    expect(await screen.findByRole("heading", { name: /clinical evidence extraction/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /clinical question/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /governed answer/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /part of the record/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /inspect the plan/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    expect(screen.getByRole("dialog", { name: /architecture is documented/i })).toBeInTheDocument();
    expect(document.body.dataset.tourStep).toBe("atlas");
    fireEvent.click(screen.getByRole("button", { name: /^next$/i }));
    fireEvent.click(screen.getByRole("button", { name: /open patient queue/i }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(localStorage.getItem(ONBOARDING_KEY)).toBe("done");
    expect(await screen.findByRole("heading", { name: /patient queue/i })).toBeInTheDocument();
  });

  it("supports back navigation while escape keeps the tour open", () => {
    mockApi();
    render(<MemoryRouter initialEntries={["/app/dashboard"]}><App/></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: /show me around/i }));
    fireEvent.click(screen.getByRole("button", { name: /^back$/i }));
    expect(screen.getByRole("dialog", { name: /every patient source/i })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.getByRole("dialog", { name: /every patient source/i })).toBeInTheDocument();
    expect(localStorage.getItem(ONBOARDING_KEY)).toBeNull();
  });

  it("replays from the topbar after completion", () => {
    mockApi();
    localStorage.setItem(ONBOARDING_KEY, "done");
    render(<MemoryRouter initialEntries={["/app/dashboard"]}><App/></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: /replay product tour/i }));
    expect(screen.getByRole("dialog", { name: /every patient source/i })).toBeInTheDocument();
  });
});
