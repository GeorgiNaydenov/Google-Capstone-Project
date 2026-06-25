// MultimodalQAScreen — ask questions across a patient's records; cited answers.
const NDS_qa = window.NexusClinicalAIDesignSystem_29a409;

function CitationMark({ n }) {
  return <sup><button style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 16, height: 16, borderRadius: "var(--radius-sm)", background: "var(--secondary-container)", color: "var(--on-secondary-container)", border: "1px solid var(--outline-variant)", fontFamily: "var(--font-mono)", fontSize: 10, cursor: "pointer", verticalAlign: "super" }}>{n}</button></sup>;
}

function MultimodalQAScreen() {
  const { Panel, Button, Textarea, Select, Checkbox, ConfidenceMeter, DataTable } = NDS_qa;
  const [sources, setSources] = React.useState({ notes: true, imaging: true, labs: true });
  const ctxCols = [
    { key: "ref", header: "Ref", mono: true, render: (r) => <span style={{ color: "var(--primary)", fontWeight: 600 }}>[{r.ref}]</span> },
    { key: "type", header: "Type", render: (r) => <span style={{ display: "inline-block", padding: "1px 6px", borderRadius: "var(--radius-sm)", fontSize: 10, fontWeight: 600, background: r.type === "Image" ? "var(--tertiary-fixed)" : r.type === "Text" ? "var(--secondary-fixed)" : "var(--surface-variant)", color: "var(--on-surface-variant)" }}>{r.type}</span> },
    { key: "date", header: "Date", mono: true },
    { key: "rel", header: "Relevance", render: (r) => <div style={{ width: 120 }}><ConfidenceMeter value={r.rel} width={80} showValue={false} color="var(--primary)" /></div> },
    { key: "name", header: "Source document" },
  ];
  const ctx = [
    { ref: 1, type: "Image", date: "2024-01-05", rel: 89, name: "MRI Abdomen without contrast, Series 4" },
    { ref: 2, type: "Text", date: "2023-10-12", rel: 76, name: "Radiology report, previous MRI findings" },
    { ref: 3, type: "Text", date: "2024-01-08", rel: 62, name: "Oncology clinic note, Dr. Vance" },
    { ref: 4, type: "Struct", date: "2024-01-04", rel: 45, name: "Comprehensive metabolic panel" },
  ];

  return (
    <div style={{ padding: "var(--space-md)", display: "flex", flexDirection: "column", gap: "var(--space-md)", height: "100%", boxSizing: "border-box" }}>
      <Panel bodyPadding="var(--space-sm) var(--space-md)">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
            <div style={{ width: 32, height: 32, borderRadius: "var(--radius-full)", background: "var(--surface-container-highest)", border: "1px solid var(--outline-variant)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <span className="material-symbols-outlined" style={{ fontSize: 20, color: "var(--on-surface-variant)" }}>person</span>
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600 }}>Sarah Jenkins</div>
              <div style={{ fontSize: 12, color: "var(--on-surface-variant)" }}>MRN-99824-A. Date of birth 04/12/1965, age 58.</div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
            <NDS_qa.StatusChip tone="critical" icon="warning">High risk</NDS_qa.StatusChip>
            <span style={{ fontSize: 11, color: "var(--on-surface-variant)" }}>Agents active: Retrieval, Context, Citation</span>
          </div>
        </div>
      </Panel>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr 320px", gap: "var(--space-md)", flex: 1, minHeight: 0 }}>
        <Panel title="Intelligence query" icon="search" bodyStyle={{ display: "flex", flexDirection: "column", gap: "var(--space-md)", height: "100%", boxSizing: "border-box" }} style={{ minHeight: 0 }}>
          <div>
            <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", display: "block", marginBottom: 6 }}>Natural language question</label>
            <Textarea rows={4} defaultValue="Has there been any progression in the secondary hepatic lesions since the last scan in October?" />
          </div>
          <div style={{ borderTop: "1px solid var(--outline-variant)", paddingTop: "var(--space-md)" }}>
            <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", display: "block", marginBottom: 6 }}>Date range</label>
            <Select defaultValue="Last 6 months"><option>Last 6 months</option><option>Last 12 months</option><option>All time</option></Select>
          </div>
          <div>
            <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", display: "block", marginBottom: 8 }}>Source types</label>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <Checkbox checked={sources.notes} onChange={() => setSources({ ...sources, notes: !sources.notes })} label="Clinical notes (text)" />
              <Checkbox checked={sources.imaging} onChange={() => setSources({ ...sources, imaging: !sources.imaging })} label="Imaging reports (vector)" />
              <Checkbox checked={sources.labs} onChange={() => setSources({ ...sources, labs: !sources.labs })} label="Lab results (structured)" />
            </div>
          </div>
          <div style={{ marginTop: "auto" }}>
            <Button variant="primary" icon="auto_awesome" fullWidth>Synthesize answer</Button>
          </div>
        </Panel>

        <Panel title="Agent synthesis" icon="forum" bodyStyle={{ display: "flex", flexDirection: "column", gap: "var(--space-lg)", overflowY: "auto", maxHeight: "100%" }} style={{ minHeight: 0 }}
               actions={<ConfidenceMeter value={92} label="Synthesis confidence" width={90} />}>
          <div style={{ alignSelf: "flex-end", maxWidth: "85%" }}>
            <div style={{ background: "var(--surface-container)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-lg) var(--radius-lg) 0 var(--radius-lg)", padding: "var(--space-md)", fontSize: 14, color: "var(--on-surface)" }}>
              Has there been any progression in the secondary hepatic lesions since the last scan in October?
            </div>
            <div style={{ fontSize: 11, color: "var(--on-surface-variant)", textAlign: "right", marginTop: 4 }}>10:42 AM</div>
          </div>
          <div style={{ display: "flex", gap: "var(--space-md)", maxWidth: "92%" }}>
            <div style={{ width: 32, height: 32, borderRadius: "var(--radius-full)", background: "var(--primary-fixed)", border: "1px solid var(--primary-fixed-dim)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 4 }}>
              <span className="material-symbols-outlined" style={{ fontSize: 18, color: "var(--primary)" }}>neurology</span>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ background: "var(--surface-container-lowest)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-lg) var(--radius-lg) var(--radius-lg) 0", padding: "var(--space-md)" }}>
                <p style={{ margin: "0 0 var(--space-md)", fontSize: 14, lineHeight: "20px", color: "var(--on-surface)" }}>Comparing the abdominal MRI from October 12 with the recent scan on January 5, there is evidence of slight progression.</p>
                <p style={{ margin: "0 0 var(--space-md)", fontSize: 14, lineHeight: "20px", color: "var(--on-surface)" }}>The largest secondary lesion in segment VI increased from 1.2 cm to roughly 1.5 cm.<CitationMark n={1} /> Smaller adjacent satellite nodules appear stable, and no new definitive lesions were identified in the remaining hepatic segments.<CitationMark n={2} /></p>
                <div style={{ borderTop: "1px solid var(--outline-variant)", paddingTop: "var(--space-md)" }}>
                  <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", marginBottom: 6 }}>Primary evidence</div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--surface-container)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-sm)" }}>
                    <span style={{ fontSize: 13, color: "var(--on-surface)" }}><span style={{ fontFamily: "var(--font-mono)", fontSize: 11, background: "color-mix(in srgb, var(--outline-variant) 40%, transparent)", padding: "1px 5px", borderRadius: 3, marginRight: 6 }}>[1]</span>MRI Abdomen without contrast, January 5</span>
                    <a href="#" onClick={(e) => e.preventDefault()} style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", textDecoration: "none" }}>View source</a>
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 11, color: "var(--on-surface-variant)", marginTop: 4 }}>Context agent. 10:42 AM</div>
            </div>
          </div>
        </Panel>

        <Panel title="Source viewer" icon="image" bodyPadding="0" style={{ minHeight: 0 }}>
          <div style={{ background: "#0b0d12", padding: "var(--space-md)", display: "flex", alignItems: "center", justifyContent: "center", height: 150 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 40, color: "var(--outline)" }}>radiology</span>
          </div>
          <div style={{ padding: "var(--space-md)" }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", marginBottom: 6 }}>Extracted finding</div>
            <div style={{ background: "var(--surface-container)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-sm)", fontSize: 13, color: "var(--on-surface)", lineHeight: "18px" }}>
              Lesion in segment VI measuring 1.5 by 1.4 cm, increased from a prior 1.2 cm. Margins remain well defined.
            </div>
            <div style={{ marginTop: "var(--space-md)", display: "flex", flexDirection: "column", gap: 6 }}>
              {[["Study date", "2024-01-05"], ["Modality", "MRI without contrast"], ["Vector similarity", "0.8924"], ["Agent", "Vision Extractor v3"]].map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: "var(--on-surface-variant)" }}>{k}</span>
                  <span style={{ fontFamily: "var(--font-mono)", color: "var(--on-surface)" }}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Retrieved context sources" icon="library_books" bodyPadding="0"
             actions={<span style={{ fontSize: 11, color: "var(--on-surface-variant)" }}>Top 4 vectorized matches</span>}>
        <DataTable columns={ctxCols} rows={ctx} />
      </Panel>
    </div>
  );
}

Object.assign(window, { MultimodalQAScreen });
