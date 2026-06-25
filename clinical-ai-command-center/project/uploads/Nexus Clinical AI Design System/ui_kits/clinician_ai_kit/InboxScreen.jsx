// InboxScreen — triage of AI-raised items needing clinician action.
const NDS_inbox = window.NexusClinicalAIDesignSystem_29a409;

function InboxScreen() {
  const { Panel, Button, Tabs, StatusChip, ConfidenceMeter, SQLPreview } = NDS_inbox;
  const [tab, setTab] = React.useState("Action required");
  const [selected, setSelected] = React.useState(0);
  const items = [
    { tone: "critical", tag: "High risk", id: "PT-1145", time: "10 minutes ago", title: "Verify the AI-detected pulmonary anomalies", body: "Automated extraction flags a high probability of incidental nodules in the recent CT scan. Clinician verification is required before the report is finalized." },
    { tone: "info", tag: "Missing data", id: "SESS-2231", time: "1 hour ago", title: "Missing image evidence for extraction", body: "The multimodal analysis agent could not locate the referenced MRI sequence in the linked PACS study. Manual linking is requested." },
    { tone: "neutral", tag: "Review", id: "AUDIT-99", time: "4 hours ago", title: "Review batch extraction confidence anomalies", body: "The system detected a 15 percent drop in agent confidence across the last 50 oncology notes processed. Review the sample set for prompt tuning." },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-md)", padding: "var(--space-md)", height: "100%", boxSizing: "border-box" }}>
      <Panel title="Clinical inbox" icon="inbox" bodyPadding="0" style={{ minHeight: 0 }}
             actions={<Button variant="ghost" size="sm" icon="filter_list">Filter</Button>}>
        <div style={{ padding: "var(--space-sm) var(--space-md) 0" }}>
          <Tabs tabs={["Action required", "Pending reviews", "System messages"]} value={tab} onChange={setTab} />
        </div>
        <div style={{ padding: "var(--space-md)", display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
          {items.map((it, i) => (
            <div key={i} onClick={() => setSelected(i)} style={{
              border: `1px solid ${selected === i ? "var(--primary)" : "var(--outline-variant)"}`,
              borderRadius: "var(--radius-md)", padding: "var(--space-md)", cursor: "pointer",
              background: selected === i ? "var(--surface-container-low)" : "var(--surface-container-lowest)",
              transition: "border-color 150ms ease",
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
                  <StatusChip tone={it.tone}>{it.tag}</StatusChip>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--on-surface-variant)" }}>{it.id}</span>
                </div>
                <span style={{ fontSize: 11, color: "var(--on-surface-variant)" }}>{it.time}</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--on-surface)", marginBottom: 4 }}>{it.title}</div>
              <p style={{ margin: 0, fontSize: 13, color: "var(--on-surface-variant)", lineHeight: "18px" }}>{it.body}</p>
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="PT-1145 context" icon="description" bodyStyle={{ display: "flex", flexDirection: "column", gap: "var(--space-md)", overflowY: "auto", maxHeight: "100%" }} style={{ minHeight: 0 }}
             actions={<Button variant="outline" size="sm" icon="open_in_new">Open full session</Button>}>
        <div style={{ border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-md)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-sm)" }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>AI finding summary</span>
            <StatusChip tone="critical">Action required</StatusChip>
          </div>
          <p style={{ margin: "0 0 var(--space-md)", fontSize: 14, lineHeight: "20px", color: "var(--on-surface)" }}>The vision language model identified structural irregularities consistent with early stage pulmonary nodules in the right lower lobe. This finding was not explicitly mentioned in the original radiology dictation.</p>
          <div style={{ display: "flex", gap: "var(--space-sm)" }}>
            <Button variant="primary" size="sm" icon="check">Verify finding</Button>
            <Button variant="outline" size="sm" icon="close">Reject</Button>
          </div>
        </div>

        <div style={{ border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-md)" }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", marginBottom: 8 }}>Agent confidence</div>
          <ConfidenceMeter value={82} width={220} />
          <p style={{ margin: "var(--space-sm) 0 0", fontSize: 12, color: "var(--on-surface-variant)", lineHeight: "16px" }}>Model Vision v3. Confidence was reduced by poor image contrast in slices 44 to 48.</p>
        </div>

        <div style={{ border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-md)" }}>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", marginBottom: 8 }}>Source evidence</div>
          <div style={{ display: "flex", gap: "var(--space-md)" }}>
            <div style={{ width: 96, height: 72, borderRadius: "var(--radius-sm)", background: "#0b0d12", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <span className="material-symbols-outlined" style={{ fontSize: 28, color: "var(--outline)" }}>radiology</span>
            </div>
            <div>
              <p style={{ margin: 0, fontSize: 13, color: "var(--on-surface)", lineHeight: "18px" }}>Excerpt from sequence 3, slice 46. Hyperdensity noted at coordinates x 142, y 88.</p>
              <a href="#" onClick={(e) => e.preventDefault()} style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", textDecoration: "none", marginTop: 6, display: "inline-block" }}>View full study</a>
            </div>
          </div>
        </div>

        <div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)", marginBottom: 8 }}>Extraction query trace</div>
          <SQLPreview label="Query" html={`<span style="color:var(--primary);font-weight:600">SELECT</span> patient_id, scan_date, modality\n<span style="color:var(--primary);font-weight:600">FROM</span> pacs_metadata\n<span style="color:var(--primary);font-weight:600">WHERE</span> study_id = <span style="color:var(--tertiary)">'S-1145-CT'</span>\n    <span style="color:var(--primary);font-weight:600">AND</span> has_findings = <span style="color:var(--tertiary)">TRUE</span>;`} />
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, { InboxScreen });
