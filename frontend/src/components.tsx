import { Component, createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "./api";
import type { AgentRun, AuditEvent, AuditEventDetail, Evidence, Patient, Role, ToolCall } from "./types";

export class ErrorBoundary extends Component<{ children: ReactNode; label?: string }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return <div className="error" role="alert">
        <strong>{this.props.label ?? "This view"} hit an unexpected error</strong>
        <span>{this.state.error.message}</span>
        <button className="button subtle" onClick={() => this.setState({ error: null })}>Try again</button>
      </div>;
    }
    return this.props.children;
  }
}

type Toast = { id: number; message: string; tone: "success" | "error" | "info" };
const ToastContext = createContext<(message: string, tone?: Toast["tone"]) => void>(() => undefined);

export function useToast() { return useContext(ToastContext); }

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((message: string, tone: Toast["tone"] = "success") => {
    const id = Date.now() + Math.random();
    setToasts(current => [...current.slice(-3), { id, message, tone }]);
    window.setTimeout(() => setToasts(current => current.filter(item => item.id !== id)), 4600);
  }, []);
  return <ToastContext.Provider value={push}>
    {children}
    <div className="toast-stack" role="status" aria-live="polite">{toasts.map(toast => <div key={toast.id} className={`toast ${toast.tone}`}><span>{toast.message}</span><button aria-label="Dismiss notification" onClick={() => setToasts(current => current.filter(item => item.id !== toast.id))}>x</button></div>)}</div>
  </ToastContext.Provider>;
}

export function ConfirmDialog({ open, title, detail, confirmLabel = "Confirm", tone = "danger", onConfirm, onCancel }: { open: boolean; title: string; detail: string; confirmLabel?: string; tone?: "danger" | "primary"; onConfirm: () => void; onCancel: () => void }) {
  const confirmRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    confirmRef.current?.focus();
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onCancel(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onCancel]);
  if (!open) return null;
  return <div className="modal-backdrop" onClick={onCancel}>
    <section className="confirm-dialog" role="alertdialog" aria-modal="true" aria-label={title} onClick={event => event.stopPropagation()}>
      <h2>{title}</h2>
      <p>{detail}</p>
      <div className="button-row">
        <button className="button subtle" onClick={onCancel}>Cancel</button>
        <button ref={confirmRef} className={`button ${tone}`} onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </section>
  </div>;
}

export function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const paths: Record<string, string> = {
    dashboard: "M3 3h8v8H3zM13 3h8v5h-8zM13 10h8v11h-8zM3 13h8v8H3z",
    patients: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
    activity: "M3 12h4l3-9 4 18 3-9h4",
    database: "M4 6c0-2 16-2 16 0s-16 2-16 0v6c0 2 16 2 16 0V6v12c0 2-16 2-16 0z",
    settings: "M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2 3.46-.09-.03a1.7 1.7 0 0 0-1.84.23l-.53.3a1.7 1.7 0 0 0-1.1 1.52V22h-4v-.12a1.7 1.7 0 0 0-1.1-1.52l-.53-.3a1.7 1.7 0 0 0-1.84-.23l-.09.03-2-3.46.06-.06A1.7 1.7 0 0 0 5.08 15l-.3-.53a1.7 1.7 0 0 0-1.52-1.1H3v-4h.26a1.7 1.7 0 0 0 1.52-1.1l.3-.53a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2-3.46.09.03a1.7 1.7 0 0 0 1.84-.23l.53-.3A1.7 1.7 0 0 0 10.24.32V0h4v.32a1.7 1.7 0 0 0 1.1 1.52l.53.3a1.7 1.7 0 0 0 1.84.23l.09-.03 2 3.46-.06.06a1.7 1.7 0 0 0-.34 1.88l.3.53a1.7 1.7 0 0 0 1.52 1.1H22v4h-.78a1.7 1.7 0 0 0-1.52 1.1z",
    search: "M21 21l-4.35-4.35M19 11a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
    upload: "M12 16V3m0 0L7 8m5-5 5 5M4 15v5h16v-5",
    brain: "M9.5 4A3.5 3.5 0 0 0 6 7.5v1A3.5 3.5 0 0 0 4 12a3.5 3.5 0 0 0 2 3.5v1A3.5 3.5 0 0 0 9.5 20H12V4zM14 4h.5A3.5 3.5 0 0 1 18 7.5v1a3.5 3.5 0 0 1 2 3.5 3.5 3.5 0 0 1-2 3.5v1a3.5 3.5 0 0 1-3.5 3.5H12",
    list: "M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01",
    calendar: "M4 5h16v16H4zM8 3v4M16 3v4M4 10h16",
    chart: "M4 20V10m6 10V4m6 16v-7m5 7H2",
    inbox: "M4 4h16v16H4zM4 14h4l2 3h4l2-3h4",
    microscope: "M6 18h8M9 14a5 5 0 0 0 8-4M8 3l5 5-3 3-5-5zM17 3l3 3-7 7-3-3zM4 21h15",
    shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10zM9 12l2 2 4-5",
    report: "M5 3h14v18H5zM8 8h8M8 12h8M8 16h5",
    sliders: "M4 6h10M18 6h2M4 12h2M10 12h10M4 18h7M15 18h5M14 4v4M6 10v4M11 16v4",
    cloud: "M17.5 19H7a5 5 0 0 1-.5-9.98A7 7 0 0 1 20 11a4 4 0 0 1-2.5 8z",
    vector: "M5 4h4v4H5zM15 4h4v4h-4zM10 16h4v4h-4zM9 6h6M7 8l4 8M17 8l-4 8",
    pulse: "M3 12h4l2-5 4 10 3-7 2 2h3",
    plus: "M12 5v14M5 12h14",
    chevron: "M9 6l6 6-6 6",
    agent: "M5 7h14v11H5zM9 3h6v4M9 12h.01M15 12h.01M9 16h6",
    eye: "M2 12s4-7 10-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6",
    bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4",
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill={name === "dashboard" ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={paths[name] ?? paths.activity} /></svg>;
}

export function Card({ children, title, action, className = "" }: { children: ReactNode; title?: string; action?: ReactNode; className?: string }) {
  return <section className={`card ${className}`}>{title && <header className="card-head"><h2>{title}</h2>{action}</header>}{children}</section>;
}

export function EmptyState({ title = "No records", detail = "Nothing matches this view yet." }: { title?: string; detail?: string }) {
  return <div className="empty"><span className="empty-mark">+</span><strong>{title}</strong><p>{detail}</p></div>;
}

export function LoadingState() { return <div className="loading" role="status"><i /><i /><i /><span>Loading clinical data</span></div>; }

export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  return <div className="error" role="alert"><strong>Unable to load this view</strong><span>{error instanceof Error ? error.message : "Unexpected service error"}</span>{retry && <button className="button subtle" onClick={retry}>Retry</button>}</div>;
}

export function RoleSwitcher({ role, onChange }: { role: Role; onChange: (role: Role) => void }) {
  return <div className="role-switch" aria-label="Workspace role"><button className={role === "clinician" ? "active" : ""} onClick={() => onChange("clinician")}>Clinician</button><button className={role === "admin" ? "active" : ""} onClick={() => onChange("admin")}>Admin</button></div>;
}

export function RiskBadge({ risk = "low" }: { risk?: Patient["risk"] }) { return <span className={`badge risk-${risk}`}><i />{risk} risk</span>; }
export function CompletenessBadge({ value = 0 }: { value?: number }) { const percent = Math.round(value <= 1 ? value * 100 : value); return <span className="badge neutral">{percent}% complete</span>; }
export function StatusBadge({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) { return <span className={`badge ${tone}`}>{children}</span>; }

export function ConfidenceMeter({ value = 0 }: { value?: number }) {
  const pct = Math.round(value <= 1 ? value * 100 : value);
  return <div className="confidence"><div><span>Agent confidence</span><strong>{pct}%</strong></div><progress max="100" value={pct} aria-label={`Agent confidence ${pct}%`} /></div>;
}

export function KpiStrip({ values }: { values: Array<{ label: string; value: string | number; meta?: string; tone?: string }> }) {
  return <div className="kpi-strip">{values.map(item => {
    const formatted = typeof item.value === "number" ? new Intl.NumberFormat().format(item.value) : item.value;
    return <Card key={item.label} className={item.tone ? `kpi-${item.tone}` : ""}><span className="eyebrow">{item.label}</span><strong className="kpi-value">{formatted}</strong>{item.meta && <small>{item.meta}</small>}</Card>;
  })}</div>;
}

export function DenseTable({ columns, rows, onRow, limit }: { columns: Array<{ key: string; label: string; render?: (row: Record<string, unknown>) => ReactNode }>; rows: Array<Record<string, unknown>>; onRow?: (row: Record<string, unknown>) => void; limit?: number }) {
  if (!rows.length) return <EmptyState />;
  const visibleRows = limit ? rows.slice(0, limit) : rows;
  return <div className="table-wrap"><table><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{visibleRows.map((row, index) => <tr key={String(row.id ?? index)} onClick={() => onRow?.(row)} onKeyDown={event => { if (onRow && (event.key === "Enter" || event.key === " ")) onRow(row); }} tabIndex={onRow ? 0 : undefined} className={onRow ? "clickable" : ""}>{columns.map(c => <td key={c.key} title={c.render ? undefined : String(row[c.key] ?? "")}>{c.render ? c.render(row) : String(row[c.key] ?? "-")}</td>)}</tr>)}</tbody></table>{limit && rows.length > visibleRows.length && <small className="table-note">Showing {visibleRows.length} of {rows.length} records</small>}</div>;
}

export function AgentStepper({ steps = [], toolCalls = [] }: { steps?: AgentRun["steps"]; toolCalls?: ToolCall[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);
  return <ol className="stepper">{steps?.map((step, index) => {
    const isOpen = expanded === step.id;
    const stepTools = toolCalls.filter(tc => (tc.toolName ?? tc.tool ?? "").toLowerCase().includes(step.name.toLowerCase().split(" ")[0]));
    const hasDetail = stepTools.length > 0 || step.detail;
    const marker = step.status === "completed" ? "" : step.status === "running" ? "" : String(index + 1);
    return <li key={step.id} className={step.status}><button className="stepper-toggle" onClick={() => hasDetail && setExpanded(isOpen ? null : step.id)}><span aria-label={step.status}>{marker}</span><div><strong>{step.name}</strong><small>{step.detail ?? step.status}{stepTools.length > 0 && ` - ${stepTools.length} tool call${stepTools.length > 1 ? "s" : ""}`}</small></div>{hasDetail && <span className="stepper-chevron">{isOpen ? "v" : ">"}</span>}</button>{isOpen && stepTools.length > 0 && <div className="stepper-detail">{stepTools.map((tc, i) => <div key={i} className="tool-call-row"><code className="tool-name">{tc.toolName ?? tc.tool}</code>{tc.durationMs != null && <span className="tool-duration">{tc.durationMs}ms</span>}{tc.args && <details><summary>Input</summary><pre>{JSON.stringify(tc.args, null, 2)}</pre></details>}{tc.output != null && <details><summary>Output</summary><pre>{typeof tc.output === "string" ? tc.output : JSON.stringify(tc.output, null, 2)}</pre></details>}</div>)}</div>}</li>;
  })}</ol>;
}

export function AgentMeta({ run }: { run: AgentRun }) {
  return <div className="agent-meta"><div><span className="eyebrow">Run</span><code>{run.id}</code></div><div><span className="eyebrow">Agent</span><strong>{run.agentName ?? run.workflow}</strong></div><div><span className="eyebrow">Status</span><StatusBadge tone={run.status}>{run.status}</StatusBadge></div><div><span className="eyebrow">Audit</span><code>{run.auditId ?? "pending"}</code></div></div>;
}

export function EvidenceCard({ item, onOpen }: { item: Evidence; onOpen: (item: Evidence) => void }) {
  return <button className="evidence-card" onClick={() => onOpen(item)}>{item.kind === "image" && item.sourceUrl ? <img className="evidence-thumb" src={item.sourceUrl} alt={item.label} loading="lazy"/> : <span className="evidence-icon">{item.kind === "image" ? "IMG" : "TXT"}</span>}<span><strong>{item.label}</strong><small>{item.excerpt ?? `Source evidence${item.page ? `, page ${item.page}` : ""}`}</small></span><span>Open</span></button>;
}

export function SourceViewer({ evidence, onClose }: { evidence: Evidence | null; onClose: () => void }) {
  if (!evidence) return null;
  return <div className="modal-backdrop" onClick={onClose}><section className="source-viewer" role="dialog" aria-modal="true" aria-label="Evidence source" onClick={event => event.stopPropagation()}><header><div><span className="eyebrow">Authorized source</span><h2>{evidence.label}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close source">x</button></header>{evidence.kind === "image" && evidence.sourceUrl ? <img src={evidence.sourceUrl} alt={evidence.label} /> : <div className="source-text">{evidence.excerpt ?? "Source preview unavailable."}</div>}<footer><code>{evidence.id}</code><div>{evidence.page && <span>Page {evidence.page}</span>}{evidence.sourceUrl && <a className="button subtle" href={evidence.sourceUrl} target="_blank" rel="noreferrer">Open original source</a>}</div></footer></section></div>;
}

export function AuditTimeline({ events = [], onSelect }: { events?: AuditEvent[]; onSelect?: (event: AuditEvent) => void }) {
  return <ol className="timeline">{events.map(event => <li key={event.id} className={onSelect ? "clickable" : undefined} tabIndex={onSelect ? 0 : undefined} onClick={onSelect ? () => onSelect(event) : undefined} onKeyDown={event_ => { if (onSelect && (event_.key === "Enter" || event_.key === " ")) onSelect(event); }}><i /><div><span>{event.event}</span><small>{event.actor} - {event.entity}</small></div><div><StatusBadge tone="success">{event.result}</StatusBadge><time>{event.timestamp}</time></div></li>)}</ol>;
}

/** Modal drill-down for one audit event. Fetches the enriched detail (linked
 * run and patient) from GET /audit/{id}; when the backend cannot serve it
 * (e.g. failover snapshot rows), the modal degrades to the row's own fields. */
export function AuditDetailModal({ event, onClose }: { event: AuditEvent | null; onClose: () => void }) {
  const [detail, setDetail] = useState<AuditEventDetail | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!event) { setDetail(null); return; }
    let cancelled = false;
    setLoading(true);
    api.auditEvent(event.id)
      .then(payload => { if (!cancelled) setDetail(payload); })
      .catch(() => { if (!cancelled) setDetail(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [event?.id]);
  if (!event) return null;
  const run = detail?.run;
  return <div className="modal-backdrop" onClick={onClose}><section className="source-viewer" role="dialog" aria-modal="true" aria-label="Audit event detail" onClick={click => click.stopPropagation()}>
    <header><div><span className="eyebrow">Audit event</span><h2>{event.event.replaceAll("_", " ")}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close audit detail">x</button></header>
    <div className="agent-meta"><div><span className="eyebrow">Actor</span><strong>{event.actor}</strong></div><div><span className="eyebrow">Entity</span><code>{event.entity}</code></div><div><span className="eyebrow">Result</span><StatusBadge tone="success">{event.result}</StatusBadge></div><div><span className="eyebrow">Recorded</span><code>{event.timestamp}</code></div></div>
    {loading ? <div className="loading"><i/><i/><i/>Loading event detail</div> : <>
      <JsonViewer value={detail?.details ?? { id: event.id, event: event.event, actor: event.actor, entity: event.entity, result: event.result }}/>
      {run && <div className="audit-linked-run"><div><span className="eyebrow">Linked run</span><code>{run.id}</code><StatusBadge tone={run.status === "completed" ? "success" : run.status}>{run.status}</StatusBadge></div><small>{run.agentName} - {run.workflow} workflow{run.confidence != null ? ` - ${Math.round(run.confidence * 100)}% confidence` : ""}</small><ol>{run.steps.map(step => <li key={step.name}><strong>{step.name}</strong><span>{step.detail || step.status}</span></li>)}</ol></div>}
      {detail?.patient && <div className="audit-linked-run"><div><span className="eyebrow">Patient</span><code>{detail.patient.id}</code></div><small>{detail.patient.name}</small></div>}
    </>}
    <footer><code>{event.id}</code></footer>
  </section></div>;
}

export function SqlPreview({ sql, safe }: { sql: string; safe: boolean }) {
  return <div className="sql-block"><header><span>Generated SQL - read only</span><StatusBadge tone={safe ? "success" : "danger"}>{safe ? "Safety passed" : "Blocked"}</StatusBadge></header><pre><code>{sql}</code></pre></div>;
}

export function ChartPanel({ rows, variant = "Bar chart" }: { rows: Array<Record<string, unknown>>; variant?: string }) {
  const chartRef = useRef<HTMLDivElement>(null);
  const points = useMemo(() => rows.slice(0, 10).map((row, index) => {
    const entries = Object.entries(row);
    const valueEntry = entries.find(([, value]) => typeof value === "number") ?? entries.find(([, value]) => !Number.isNaN(Number(value)));
    const labelEntry = entries.find(([, value]) => typeof value === "string");
    return {
      id: String(row.id ?? labelEntry?.[1] ?? index),
      label: String(labelEntry?.[1] ?? `Row ${index + 1}`),
      value: Number(valueEntry?.[1] ?? 0),
    };
  }), [rows]);
  const total = points.reduce((sum, point) => sum + point.value, 0);
  const largest = points.reduce((top, point) => point.value > top.value ? point : top, points[0] ?? { label: "none", value: 0 });
  const chartKind = variant.toLowerCase();
  // When rows expose two or more numeric columns, heatmaps render a real
  // label-by-metric matrix instead of a single undifferentiated value strip.
  const matrix = useMemo(() => {
    const sample = rows.slice(0, 10);
    if (!sample.length) return null;
    const keys = Object.keys(sample[0]).filter(key => key !== "id" && sample.every(row => row[key] !== null && row[key] !== "" && !Number.isNaN(Number(row[key]))));
    return keys.length >= 2 ? { keys, z: sample.map(row => keys.map(key => Number(row[key]))) } : null;
  }, [rows]);

  useEffect(() => {
    if (!chartRef.current) return;
    let cancelled = false;
    const labels = points.map(point => point.label);
    const values = points.map(point => point.value);
    const colors = ["#2563eb", "#16a34a", "#b45309", "#dc2626", "#0284c7", "#7c3aed", "#0f766e"];
    const trace = chartKind.includes("pie") ? {
      type: "pie",
      labels,
      values,
      textinfo: "label+value",
      marker: { colors },
      hovertemplate: "%{label}<br>%{value} records<extra></extra>",
    } : chartKind.includes("treemap") ? {
      type: "treemap",
      labels: ["Total", ...labels],
      ids: ["total", ...points.map(point => point.id)],
      parents: ["", ...labels.map(() => "total")],
      values: [total, ...values],
      branchvalues: "total",
      textinfo: "label+value",
      marker: { colors },
      hovertemplate: "%{label}<br>%{value} records<extra></extra>",
    } : chartKind.includes("heatmap") ? (matrix ? {
      type: "heatmap",
      x: matrix.keys,
      y: labels,
      z: matrix.z,
      colorscale: "Blues",
      showscale: true,
      texttemplate: "%{z}",
      hovertemplate: "%{y} - %{x}<br>%{z}<extra></extra>",
    } : {
      type: "heatmap",
      x: labels,
      y: ["records"],
      z: [values],
      colorscale: "Blues",
      showscale: true,
      texttemplate: "%{z}",
      hovertemplate: "%{x}<br>%{z} records<extra></extra>",
    }) : chartKind.includes("box") ? {
      type: "box",
      y: values,
      x: labels,
      boxpoints: "all",
      marker: { color: "#2563eb" },
      hovertemplate: "%{x}<br>%{y} records<extra></extra>",
    } : chartKind.includes("histogram") ? {
      type: "histogram",
      x: values,
      marker: { color: "#2563eb" },
      hovertemplate: "%{x} records<extra></extra>",
    } : {
      type: chartKind.includes("line") || chartKind.includes("time") || chartKind.includes("area") || chartKind.includes("scatter") ? "scatter" : "bar",
      mode: chartKind.includes("scatter") ? "markers+text" : chartKind.includes("line") || chartKind.includes("time") || chartKind.includes("area") ? "lines+markers+text" : undefined,
      fill: chartKind.includes("area") ? "tozeroy" : undefined,
      x: labels,
      y: values,
      text: values.map(value => String(value)),
      textposition: "outside",
      marker: { color: chartKind.includes("line") || chartKind.includes("time") || chartKind.includes("area") || chartKind.includes("scatter") ? "#2563eb" : labels.map((_, index) => colors[index % colors.length]) },
      hovertemplate: "%{x}<br>%{y} records<extra></extra>",
    };
    const isCartesian = !["pie", "treemap", "heatmap"].some(type => chartKind.includes(type));
    void import("plotly.js-dist-min").then(({ default: Plotly }) => {
      if (cancelled || !chartRef.current) return;
      void Plotly.react(chartRef.current, [trace], {
      margin: chartKind.includes("treemap") || chartKind.includes("pie") ? { t: 12, r: 8, b: 12, l: 8 } : { t: 16, r: 12, b: 54, l: 44 },
      height: chartKind.includes("treemap") ? 300 : 250,
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "#f8fafc",
      font: { family: "Inter, system-ui, sans-serif", size: 11, color: "#334155" },
      yaxis: isCartesian ? { title: "Records", gridcolor: "#e2e8f0", zerolinecolor: "#cbd5e1" } : undefined,
      xaxis: isCartesian ? { tickangle: -24 } : undefined,
      annotations: isCartesian && !chartKind.includes("histogram") && !chartKind.includes("box") ? [{ x: largest.label, y: largest.value, text: "largest segment", showarrow: true, arrowhead: 2, ax: 0, ay: -34 }] : [],
      }, { displayModeBar: false, responsive: true });
    });
    return () => {
      cancelled = true;
      const element = chartRef.current;
      if (element) void import("plotly.js-dist-min").then(({ default: Plotly }) => Plotly.purge(element));
    };
  }, [chartKind, largest.label, largest.value, matrix, points, variant]);

  return <figure className="plotly-chart" aria-label="Annotated Plotly query result chart"><figcaption><strong>{variant} - executed SQL visualization</strong><span>{total} records across {points.length} segment{points.length === 1 ? "" : "s"}</span></figcaption><div ref={chartRef} className={chartKind.includes("treemap") ? "treemap-plot" : undefined}/><p>Largest segment: {largest.label} ({largest.value}). Values come from the executed query rows.</p></figure>;
}

export function JsonViewer({ value }: { value: unknown }) { return <pre className="json"><code>{JSON.stringify(value, null, 2)}</code></pre>; }

export function ReviewChecklist({ onDecision, onRerun, disabled = false }: { onDecision: (decision: "approved" | "rejected") => void; onRerun?: () => void; disabled?: boolean }) {
  const [checks, setChecks] = useState([false, false, false]);
  const toggle = (index: number) => setChecks(current => current.map((value, item) => item === index ? !value : value));
  return <Card title="Clinician verification" className="review"><p>Consequential output is never persisted until a clinician completes this gate.</p>{["Patient identity and source confirmed", "Evidence image and OCR inspected", "Extracted values clinically plausible"].map((label, index) => <label key={label}><input type="checkbox" checked={checks[index]} disabled={disabled} onChange={() => toggle(index)}/>{label}</label>)}<div className="button-row">{onRerun && <button className="button subtle" disabled={disabled} onClick={onRerun}>Re-run agents</button>}<button className="button danger" disabled={disabled} onClick={() => onDecision("rejected")}>Reject output</button><button className="button primary" disabled={disabled || !checks.every(Boolean)} onClick={() => onDecision("approved")}>Approve and sync</button></div></Card>;
}
