// ImageExtractionScreen — multi-agent pipeline turning a scan into structured fields.
const NDS_ext = window.NexusClinicalAIDesignSystem_29a409;

function PipelineStep({ state, title, body, detail }) {
  const done = state === "done", active = state === "active";
  return (
    <div style={{ display: "flex", gap: "var(--space-sm)", padding: "var(--space-sm)", borderRadius: "var(--radius-md)", background: active ? "var(--primary-fixed)" : "transparent", border: active ? "1px solid var(--primary-fixed-dim)" : "1px solid transparent" }}>
      <span className="material-symbols-outlined" style={{ fontSize: 20, color: done ? "var(--success)" : active ? "var(--primary)" : "var(--outline-variant)", fontVariationSettings: (done || active) ? "'FILL' 1" : "'FILL' 0", marginTop: 1 }}>
        {done ? "check_circle" : active ? "radio_button_checked" : "radio_button_unchecked"}
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: state === "pending" ? "var(--on-surface-variant)" : "var(--on-surface)" }}>{title}</div>
        <div style={{ fontSize: 12, color: "var(--on-surface-variant)", marginTop: 1, lineHeight: "16px" }}>{body}</div>
        {detail ? <div style={{ marginTop: 6, fontFamily: "var(--font-mono)", fontSize: 11, background: "var(--surface-container-highest)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-sm)", padding: "4px 6px", color: "var(--on-surface)" }}>{detail}</div> : null}
      </div>
    </div>
  );
}

function ImageExtractionScreen() {
  const { Panel, Button, ConfidenceMeter, Checkbox, StatusChip } = NDS_ext;
  const [review, setReview] = React.useState({ a: false, b: false, c: false });
  const fields = [
    { f: "Modality", v: "CR, computed radiography", c: 99 },
    { f: "Laterality", v: "Unspecified", c: 95 },
    { f: "Primary finding", v: "Consolidation", c: 78 },
    { f: "Location", v: "Ambiguous, lower lobe", c: 42, flag: true },
    { f: "Secondary finding", v: "None observed", c: 91 },
    { f: "Hardware", v: "Endotracheal tube", c: 88 },
  ];
  const logs = [
    ["10:42:01.102", "Orchestrator", "Initialized multi-agent workflow id 8A-9F2-C1", "var(--primary)"],
    ["10:42:01.450", "QualityAgent", "Evaluating DICOM headers. Pass.", "var(--success)"],
    ["10:42:02.015", "VisionAgent", "Running segmentation model v4.2", "var(--secondary)"],
    ["10:42:03.882", "VisionAgent", "Found 3 regions. Confidence 0.98, 0.94, 0.82.", "var(--secondary)"],
    ["10:42:04.100", "OCRAgent", "Extracting text overlays. 4 strings found.", "var(--secondary)"],
    ["10:42:04.550", "StructAgent", "Low confidence mapping on finding 3 to standard ontology.", "var(--error)"],
  ];

  return (
    <div style={{ padding: "var(--space-md)", display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 600, letterSpacing: "-0.02em" }}>Image extraction</h1>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--on-surface-variant)" }}>Session 8A-9F2-C1. Nine specialist agents run in sequence to structure the scan.</p>
        </div>
        <div style={{ display: "flex", gap: "var(--space-sm)" }}>
          <Button variant="outline" size="md" icon="restart_alt">Reset</Button>
          <Button variant="primary" size="md" icon="done_all">Approve output</Button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 360px", gap: "var(--space-md)", alignItems: "start" }}>
        <Panel title="Session image" icon="imagesmode" bodyPadding="0">
          <div style={{ background: "#0b0d12", padding: "var(--space-lg)", display: "flex", alignItems: "center", justifyContent: "center", minHeight: 320, position: "relative" }}>
            <span className="material-symbols-outlined" style={{ fontSize: 64, color: "var(--outline)" }}>radiology</span>
            <div style={{ position: "absolute", top: 80, left: "50%", transform: "translateX(-30%)", border: "2px solid var(--primary-fixed-dim)", borderRadius: 2, width: 90, height: 70 }}>
              <span style={{ position: "absolute", top: -18, left: 0, background: "var(--primary)", color: "var(--on-primary)", fontSize: 9, fontWeight: 700, padding: "1px 4px", borderRadius: 2 }}>LOWER LOBE</span>
            </div>
          </div>
          <div style={{ padding: "var(--space-sm) var(--space-md)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--on-surface-variant)" }}>IMG-2231.dcm</span>
            <StatusChip tone="verified">Loaded</StatusChip>
          </div>
        </Panel>

        <Panel title="Agent pipeline" icon="lan" iconColor="var(--primary)" bodyStyle={{ display: "flex", flexDirection: "column", gap: 4 }}>
          <PipelineStep state="done" title="Quality assessor" body="Resolution 4K, contrast optimal, no artifacts detected." />
          <PipelineStep state="done" title="Vision analyzer" body="Radiograph, AP view. Three key regions identified." />
          <PipelineStep state="done" title="OCR engine" body="Extracted burned-in metadata and timestamp details." />
          <PipelineStep state="active" title="Semantic structuring" body="Mapping visual findings to the SNOMED CT ontology." detail={"MATCH (f:Finding {type:'opacity'})\nLINK TO (r:Region {name:'L-lobe'})"} />
          <PipelineStep state="pending" title="Validation gate" body="Waiting on structuring to finish before final confidence scoring." />
        </Panel>

        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
          <Panel title="Extracted variables" icon="data_object" bodyPadding="0"
                 actions={<span style={{ fontSize: 11, color: "var(--on-surface-variant)" }}>12 found</span>}>
            <div style={{ padding: "var(--space-xs) 0" }}>
              {fields.map((row, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)", padding: "6px var(--space-md)", borderBottom: i < fields.length - 1 ? "1px solid color-mix(in srgb, var(--outline-variant) 50%, transparent)" : "none" }}>
                  <span style={{ width: 110, fontSize: 12, color: "var(--on-surface-variant)", display: "flex", alignItems: "center", gap: 4 }}>{row.flag ? <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--error)" }} /> : null}{row.f}</span>
                  <span style={{ flex: 1, fontSize: 13, fontWeight: 500, color: row.flag ? "var(--error)" : "var(--on-surface)" }}>{row.v}</span>
                  <ConfidenceMeter value={row.c} width={56} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Required human review" icon="rule" iconColor="var(--error)">
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <Checkbox checked={review.a} onChange={() => setReview({ ...review, a: !review.a })} label="Verify the ambiguous location, lower lobe versus lingula" />
              <Checkbox checked={review.b} onChange={() => setReview({ ...review, b: !review.b })} label="Confirm the primary finding of consolidation, confidence below 80 percent" />
              <Checkbox checked={review.c} onChange={() => setReview({ ...review, c: !review.c })} label="Acknowledge the missing laterality specification" />
            </div>
          </Panel>
        </div>
      </div>

      <Panel title="Agent event stream" icon="terminal" bodyPadding="0"
             actions={<span style={{ fontSize: 11, color: "var(--on-surface-variant)" }}>Auto scroll on</span>}>
        <div style={{ background: "var(--inverse-surface)", padding: "var(--space-md)", fontFamily: "var(--font-mono)", fontSize: 12, lineHeight: "20px" }}>
          {logs.map((l, i) => (
            <div key={i} style={{ color: "var(--inverse-on-surface)" }}>
              <span style={{ color: "var(--outline)" }}>{l[0]}</span>{" "}
              <span style={{ color: l[3] }}>[{l[1]}]</span>{" "}
              <span>{l[2]}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

Object.assign(window, { ImageExtractionScreen });
