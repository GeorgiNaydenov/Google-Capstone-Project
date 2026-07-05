import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DiagramAtlas } from "./DiagramAtlas";
import { ErrorBoundary } from "../components";

describe("DiagramAtlas", () => {
  it("renders category tabs and switches the active category and diagram", () => {
    render(<DiagramAtlas defaultCategory="system"/>);
    const categories = within(screen.getByRole("tablist", { name: /diagram categories/i }));
    const systemTab = categories.getByRole("tab", { name: /^System/i });
    expect(systemTab).toHaveAttribute("aria-selected", "true");

    // The system category shows the system-architecture diagram first.
    expect(screen.getByRole("img", { name: /system architecture diagram/i })).toBeInTheDocument();

    fireEvent.click(categories.getByRole("tab", { name: /Agents & Pipelines/i }));
    expect(categories.getByRole("tab", { name: /Agents & Pipelines/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("img", { name: /agent hierarchy diagram/i })).toBeInTheDocument();
  });

  it("switches sub-tabs within a category", () => {
    render(<DiagramAtlas defaultCategory="system"/>);
    const subtabs = within(screen.getByRole("tablist", { name: /system diagrams/i }));
    fireEvent.click(subtabs.getByRole("tab", { name: /C4 containers/i }));
    expect(screen.getByRole("img", { name: /c4 containers diagram/i })).toBeInTheDocument();
  });
});

describe("ErrorBoundary", () => {
  function Boom(): never { throw new Error("boom"); }
  it("catches a thrown child and shows a recoverable error state", () => {
    render(<ErrorBoundary label="Test view"><Boom/></ErrorBoundary>);
    expect(screen.getByRole("alert")).toHaveTextContent(/hit an unexpected error/i);
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });
});
