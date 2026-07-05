import { useState } from "react";
import { getDiagram } from "../diagrams";
import { DiagramViewer } from "./DiagramViewer";

export function InlineDiagram({ id, title, defaultOpen = false }: { id: string; title?: string; defaultOpen?: boolean }) {
  const diagram = getDiagram(id);
  const [open, setOpen] = useState(defaultOpen);
  return <section className={open ? "inline-diagram open" : "inline-diagram"}>
    <button type="button" aria-expanded={open} onClick={() => setOpen(current => !current)}>
      <span className="eyebrow accent">{title ?? "Relevant architecture"}</span>
      <strong>{diagram.title}</strong>
      <small>{diagram.summary}</small>
      <b>{open ? "Collapse" : "Expand"}</b>
    </button>
    {open && <div className="inline-diagram-body">
      <DiagramViewer diagram={diagram} compact/>
      <ul>{diagram.points.map(point => <li key={point}>{point}</li>)}</ul>
    </div>}
  </section>;
}
