import { useMemo, useState } from "react";
import { diagramCategories, diagramsByCategory, type DiagramCategoryId } from "../diagrams";
import { DiagramViewer } from "./DiagramViewer";

export function DiagramAtlas({ defaultCategory = "system", compact = false }: { defaultCategory?: DiagramCategoryId; compact?: boolean }) {
  const initialCategory = diagramCategories.some(category => category.id === defaultCategory) ? defaultCategory : "system";
  const [categoryId, setCategoryId] = useState<DiagramCategoryId>(initialCategory);
  const [activeByCategory, setActiveByCategory] = useState<Record<string, string>>({});
  const activeCategory = useMemo(() => diagramsByCategory.find(category => category.id === categoryId) ?? diagramsByCategory[0], [categoryId]);
  const activeDiagram = activeCategory.diagrams.find(diagram => diagram.id === activeByCategory[categoryId]) ?? activeCategory.diagrams[0];
  const selectCategory = (id: DiagramCategoryId) => {
    setCategoryId(id);
    setActiveByCategory(current => ({ ...current, [id]: current[id] ?? diagramsByCategory.find(category => category.id === id)?.diagrams[0]?.id ?? "" }));
  };

  return <section className={compact ? "diagram-atlas compact" : "diagram-atlas"}>
    <div className="diagram-category-tabs" role="tablist" aria-label="Diagram categories">
      {diagramsByCategory.map(category => <button
        key={category.id}
        type="button"
        role="tab"
        aria-selected={category.id === categoryId}
        className={category.id === categoryId ? "active" : ""}
        onClick={() => selectCategory(category.id)}
      >
        <strong>{category.title}</strong>
        {!compact && <small>{category.diagrams.length} views</small>}
      </button>)}
    </div>
    <div className="diagram-subtabs" role="tablist" aria-label={`${activeCategory.title} diagrams`}>
      {activeCategory.diagrams.map(diagram => <button
        key={diagram.id}
        type="button"
        role="tab"
        aria-selected={diagram.id === activeDiagram.id}
        className={diagram.id === activeDiagram.id ? "active" : ""}
        onClick={() => setActiveByCategory(current => ({ ...current, [categoryId]: diagram.id }))}
      >
        {diagram.title}
      </button>)}
    </div>
    <div className="diagram-atlas-body">
      <DiagramViewer diagram={activeDiagram} compact={compact}/>
      <aside className="diagram-reading-panel">
        <span className="eyebrow accent">{activeCategory.title}</span>
        <h3>{activeDiagram.title}</h3>
        <p>{activeDiagram.summary}</p>
        <ul>{activeDiagram.points.map(point => <li key={point}>{point}</li>)}</ul>
      </aside>
    </div>
  </section>;
}
