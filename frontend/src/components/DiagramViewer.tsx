import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import type { DiagramView } from "../diagrams";

type Point = { x: number; y: number };

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function distance(points: Point[]) {
  if (points.length < 2) return 0;
  return Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
}

function ToolIcon({ name }: { name: "zoom-in" | "zoom-out" | "reset" | "fullscreen" }) {
  const paths = {
    "zoom-in": "M10 4a6 6 0 1 0 0 12 6 6 0 0 0 0-12M10 7v6M7 10h6M15 15l5 5",
    "zoom-out": "M10 4a6 6 0 1 0 0 12 6 6 0 0 0 0-12M7 10h6M15 15l5 5",
    reset: "M4 4v6h6M5 10a7 7 0 1 0 2-5",
    fullscreen: "M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5",
  };
  return <svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name]}/></svg>;
}

export function DiagramViewer({ diagram, compact = false }: { diagram: DiagramView; compact?: boolean }) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const pointers = useRef(new Map<number, Point>());
  const drag = useRef<Point | null>(null);
  const pinch = useRef<{ distance: number; scale: number } | null>(null);
  const scaleRef = useRef(1);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState<Point>({ x: 0, y: 0 });
  const [src, setSrc] = useState(diagram.svg);

  useEffect(() => {
    setScale(1);
    scaleRef.current = 1;
    setOffset({ x: 0, y: 0 });
    setSrc(diagram.svg);
    pointers.current.clear();
    drag.current = null;
    pinch.current = null;
  }, [diagram.id, diagram.svg]);

  useEffect(() => { scaleRef.current = scale; }, [scale]);

  const zoom = (delta: number) => setScale(current => clamp(Number((current + delta).toFixed(2)), 0.4, 3.5));
  const reset = () => { setScale(1); setOffset({ x: 0, y: 0 }); };
  const fullscreen = () => { void viewportRef.current?.requestFullscreen?.(); };

  // Non-passive wheel listener so preventDefault actually stops browser zoom/scroll.
  // Plain scroll zooms the diagram; Ctrl/Meta+scroll is passed through to the browser.
  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const handler = (event: WheelEvent) => {
      if (event.ctrlKey || event.metaKey) return; // let browser handle its own zoom
      event.preventDefault();
      const direction = event.deltaY > 0 ? -0.12 : 0.12;
      zoom(direction);
    };
    el.addEventListener("wheel", handler, { passive: false });
    return () => el.removeEventListener("wheel", handler);
  }, []);

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    event.currentTarget.setPointerCapture(event.pointerId);
    if (pointers.current.size === 1) drag.current = { x: event.clientX, y: event.clientY };
    if (pointers.current.size === 2) pinch.current = { distance: distance([...pointers.current.values()]), scale: scaleRef.current };
  };

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!pointers.current.has(event.pointerId)) return;
    const previous = pointers.current.get(event.pointerId)!;
    pointers.current.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointers.current.size >= 2 && pinch.current) {
      const nextDistance = distance([...pointers.current.values()]);
      if (nextDistance > 0) setScale(clamp(pinch.current.scale * (nextDistance / pinch.current.distance), 0.4, 3.5));
      return;
    }
    if (drag.current) {
      setOffset(current => ({ x: current.x + event.clientX - previous.x, y: current.y + event.clientY - previous.y }));
      drag.current = { x: event.clientX, y: event.clientY };
    }
  };

  const onPointerUp = (event: PointerEvent<HTMLDivElement>) => {
    pointers.current.delete(event.pointerId);
    pinch.current = null;
    const remaining = [...pointers.current.values()][0];
    drag.current = remaining ?? null;
  };

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "+" || event.key === "=") { event.preventDefault(); zoom(0.16); }
    if (event.key === "-") { event.preventDefault(); zoom(-0.16); }
    if (event.key === "0") { event.preventDefault(); reset(); }
  };

  return <section className={compact ? "diagram-viewer compact" : "diagram-viewer"}>
    <header className="diagram-toolbar">
      <div><strong>{diagram.title}</strong><small>{Math.round(scale * 100)}% zoom</small></div>
      <div className="diagram-tool-buttons">
        <button type="button" title="Zoom out" aria-label="Zoom out" onClick={() => zoom(-0.2)}><ToolIcon name="zoom-out"/></button>
        <button type="button" title="Reset view" aria-label="Reset diagram view" onClick={reset}><ToolIcon name="reset"/></button>
        <button type="button" title="Zoom in" aria-label="Zoom in" onClick={() => zoom(0.2)}><ToolIcon name="zoom-in"/></button>
        <button type="button" title="Fullscreen" aria-label="Fullscreen diagram" onClick={fullscreen}><ToolIcon name="fullscreen"/></button>
      </div>
    </header>
    <div
      ref={viewportRef}
      className="diagram-viewport"
      role="img"
      aria-label={`${diagram.title} diagram`}
      tabIndex={0}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onKeyDown={onKeyDown}
    >
      <img
        src={src}
        alt=""
        draggable={false}
        loading="lazy"
        onError={() => { if (diagram.png && src !== diagram.png) setSrc(diagram.png); }}
        style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}
      />
    </div>
  </section>;
}
