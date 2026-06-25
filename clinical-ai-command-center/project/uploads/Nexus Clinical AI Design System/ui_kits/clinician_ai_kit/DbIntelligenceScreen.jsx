// DbIntelligenceScreen — natural-language querying over clinical data.
const NDS_db = window.NexusClinicalAIDesignSystem_29a409;

function SchemaTable({ name, icon, iconColor, open, fields }) {
  const [expanded, setExpanded] = React.useState(open);
  return (
    <div style={{ marginBottom: "var(--space-sm)" }}>
      <div onClick={() => setExpanded(!expanded)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 6px", borderRadius: "var(--radius-sm)", cursor: "pointer", fontSize: 13, fontWeight: 600, color: "var(--on-surface)" }}>
        <span className="material-symbols-outlined" style={{ fontSize: 16, color: "var(--on-surface-variant)" }}>{expanded ? "keyboard_arrow_down" : "chevron_right"}</span>
        <span className="material-symbols-outlined" style={{ fontSize: 16, color: iconColor }}>{icon}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{name}</span>
      </div>
      {expanded && fields ? (
        <div style={{ paddingLeft: 28, marginTop: 2, display: "flex", flexDirection: "column", gap: 2 }}>
          {fields.map((f) => (
            <div key={f.name} style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--on-surface-variant)", padding: "1px 6px" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 4 }}>{f.key ? <span className="material-symbols-outlined" style={{ fontSize: 12, color: "var(--tertiary)" }}>key</span> : <span style={{ width: 12 }} />}{f.name}</span>
              <span style={{ color: "var(--outline)" }}>{f.type}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function MiniChart() {
  const bars = [40, 45, 35, 60, 55, 70, 65];
  const flagged = [false, false, false, true, false, true, false];
  return (
    <div style={{ position: "relative", height: 150, display: "flex", alignItems: "flex-end", gap: 8, padding: "8px 4px 0", borderLeft: "1px solid var(--outline)", borderBottom: "1px solid var(--outline)" }}>
      {bars.map((h, i) => (
        <div key={i} style={{ flex: 1, height: `${h}%`, background: flagged[i] ? "color-mix(in srgb, var(--error) 22%, transparent)" : "color-mix(in srgb, var(--primary) 22%, transparent)", borderTop: `2px solid ${flagged[i] ? "var(--error)" : "var(--primary)"}`, position: "relative" }}>
          <span style={{ position: "absolute", top: -5, left: "50%", transform: "translateX(-50%)", width: 7, height: 7, borderRadius: "var(--radius-full)", background: flagged[i] ? "var(--error)" : "var(--primary)" }} />
        </div>
      ))}
    </div>
  );
}

function DbIntelligenceScreen() {
  const { Panel, Button, Input, SQLPreview, DataTable, ConfidenceMeter, EvidenceCitation } = NDS_db;
  const resultCols = [
    { key: "date", header: "trend_date", mono: true, render: (r) => <span style={{ color: "var(--on-surface-variant)" }}>{r.date}</span> },
    { key: "count", header: "high_risk_count", mono: true, align: "right", render: (r) => <span style={{ fontWeight: 600 }}>{r.count}</span> },
    { key: "delta", header: "Change", align: "center", render: (r) => {
        const up = r.delta.startsWith("+"); const flat = r.delta === "0";
        const bg = flat ? "var(--surface-variant)" : up ? "var(--error-container)" : "var(--success-container)";
        const fg = flat ? "var(--on-surface-variant)" : up ? "var(--error)" : "var(--on-success-container)";
        return <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: "var(--radius-sm)", background: bg, color: fg, fontSize: 10, fontWeight: 700 }}>{flat ? "No change" : r.delta}</span>;
      } },
  ];
  const rows = [
    { date: "2023-10-01", count: 42, delta: "0" },
    { date: "2023-10-02", count: 45, delta: "+3" },
    { date: "2023-10-03", count: 39, delta: "-6" },
    { date: "2023-10-04", count: 51, delta: "+12" },
  ];
  const sqlHtml = `<span style="color:var(--primary);font-weight:600">SELECT</span>\n    DATE_TRUNC(<span style="color:var(--tertiary)">'day'</span>, admission_date) <span style="color:var(--primary);font-weight:600">AS</span> trend_date,\n    <span style="color:var(--primary);font-weight:600">COUNT</span>(*) <span style="color:var(--primary);font-weight:600">AS</span> high_risk_count\n<span style="color:var(--primary);font-weight:600">FROM</span> patients_core\n<span style="color:var(--primary);font-weight:600">WHERE</span> risk_score &gt;= <span style="color:var(--tertiary)">0.8</span>\n    <span style="color:var(--primary);font-weight:600">AND</span> admission_date &gt;= CURRENT_DATE - <span style="color:var(--primary);font-weight:600">INTERVAL</span> <span style="color:var(--tertiary)">'30 days'</span>\n<span style="color:var(--primary);font-weight:600">GROUP BY</span> <span style="color:var(--tertiary)">1</span>\n<span style="color:var(--primary);font-weight:600">ORDER BY</span> trend_date <span style="color:var(--primary);font-weight:600">ASC</span>;`;

  return (
    <div style={{ padding: "var(--space-md)", display: "flex", flexDirection: "column", gap: "var(--space-md)", height: "100%", boxSizing: "border-box" }}>
      <Panel bodyPadding="var(--space-md)">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
          <div style={{ width: 40, height: 40, borderRadius: "var(--radius-full)", background: "var(--primary-container)", color: "var(--on-primary)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <span className="material-symbols-outlined">smart_toy</span>
          </div>
          <div style={{ flex: 1 }}>
            <Input size="md" defaultValue="Show the trend of high risk patients over the last month" />
          </div>
          <Button variant="primary" icon="bolt">Run query</Button>
        </div>
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "240px 1fr 320px", gap: "var(--space-md)", flex: 1, minHeight: 0 }}>
        <Panel title="Schema explorer" icon="account_tree" iconColor="var(--primary)" bodyStyle={{ overflowY: "auto" }} style={{ minHeight: 0 }}>
          <SchemaTable name="patients_core" icon="table_chart" iconColor="var(--secondary)" open fields={[
            { name: "patient_id", type: "VARCHAR", key: true },
            { name: "risk_score", type: "FLOAT" },
            { name: "admission_date", type: "DATE" },
            { name: "status", type: "VARCHAR" },
          ]} />
          <SchemaTable name="clinical_notes_vec" icon="scatter_plot" iconColor="var(--tertiary)" />
          <SchemaTable name="lab_results" icon="table_chart" iconColor="var(--secondary)" />
        </Panel>

        <Panel title="Query workbench" icon="terminal" iconColor="var(--primary)" bodyPadding="0" style={{ minHeight: 0 }}
               actions={<div style={{ display: "flex", gap: 6 }}><StatusBadge>SQL generator</StatusBadge><StatusBadge>Validator</StatusBadge></div>}>
          <div style={{ overflowY: "auto", maxHeight: "100%" }}>
            <div style={{ padding: "var(--space-md)", borderBottom: "1px solid var(--outline-variant)", display: "flex", gap: "var(--space-sm)" }}>
              <span className="material-symbols-outlined" style={{ color: "var(--primary)", fontSize: 20, marginTop: 1 }}>auto_awesome</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Agent summary</div>
                <p style={{ margin: "2px 0 0", fontSize: 13, color: "var(--on-surface-variant)", lineHeight: "18px" }}>High risk classifications rose steadily over the past 30 days and peaked in the middle of the month. The agent processed 14,203 records across two schemas.</p>
              </div>
            </div>
            <div style={{ padding: "var(--space-md)", borderBottom: "1px solid var(--outline-variant)", background: "var(--surface-container-lowest)" }}>
              <SQLPreview html={sqlHtml} />
              <div style={{ marginTop: "var(--space-sm)" }}>
                <ConfidenceMeter value={98} label="Execution confidence" width={160} />
              </div>
            </div>
            <div style={{ padding: "var(--space-sm) var(--space-md)", background: "var(--surface-container-low)", borderBottom: "1px solid var(--outline-variant)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)" }}>Result set, 30 rows</span>
              <Button variant="ghost" size="sm" icon="download">Export CSV</Button>
            </div>
            <DataTable columns={resultCols} rows={rows} />
          </div>
        </Panel>

        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)", minHeight: 0 }}>
          <Panel title="Visualization" icon="show_chart" iconColor="var(--tertiary)" style={{ flex: 1, minHeight: 0 }}>
            <MiniChart />
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 9, color: "var(--outline)", marginTop: 4 }}><span>10/01</span><span>10/15</span><span>10/30</span></div>
          </Panel>
          <Panel title="Clinical insight" icon="insights" iconColor="var(--secondary)">
            <p style={{ margin: "0 0 var(--space-sm)", fontSize: 13, color: "var(--on-surface-variant)", lineHeight: "18px" }}>High risk admissions show a statistically significant variance around October 12 to 15.</p>
            <EvidenceCitation index={1} snippet="Correlates with the Facility C admitting protocol change implemented on October 10." sourceLabel="View source audit" />
          </Panel>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ children }) {
  return <span style={{ padding: "2px 8px", borderRadius: "var(--radius-sm)", background: "var(--primary-fixed)", color: "var(--on-primary-fixed-variant)", fontSize: 10, fontWeight: 700, border: "1px solid var(--primary-fixed-dim)" }}>{children}</span>;
}

Object.assign(window, { DbIntelligenceScreen });
