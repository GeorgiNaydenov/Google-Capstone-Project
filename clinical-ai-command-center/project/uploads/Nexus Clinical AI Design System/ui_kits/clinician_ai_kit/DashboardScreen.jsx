// DashboardScreen — clinician home: priority work, AI guidance, today's plan.
const NDS_dash = window.NexusClinicalAIDesignSystem_29a409;

function KpiCard({ label, value, sub, icon, iconColor, iconBg, critical }) {
  return (
    <div style={{
      background: "var(--surface-container-lowest)", border: "1px solid var(--outline-variant)",
      borderLeft: critical ? "3px solid var(--error)" : "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-lg)", padding: "var(--space-md)",
      display: "flex", alignItems: "center", justifyContent: "space-between",
    }}>
      <div>
        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)" }}>{label}</div>
        <div style={{ fontSize: 24, fontWeight: 600, marginTop: 4, color: critical ? "var(--error)" : "var(--on-surface)" }}>{value}</div>
        {sub ? <div style={{ fontSize: 11, color: "var(--on-surface-variant)", marginTop: 2 }}>{sub}</div> : null}
      </div>
      <span className="material-symbols-outlined" style={{ fontSize: 22, color: iconColor, background: iconBg, padding: 8, borderRadius: "var(--radius-md)" }}>{icon}</span>
    </div>
  );
}

function RecommendationCard({ icon, iconColor, title, body, action, onAct }) {
  return (
    <div style={{ border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-sm)", background: "var(--surface-container-lowest)" }}>
      <div style={{ display: "flex", gap: "var(--space-sm)", alignItems: "flex-start" }}>
        <span className="material-symbols-outlined" style={{ fontSize: 18, color: iconColor, marginTop: 1 }}>{icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--on-surface)" }}>{title}</div>
          <div style={{ fontSize: 12, color: "var(--on-surface-variant)", marginTop: 2, lineHeight: "16px" }}>{body}</div>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "var(--space-sm)" }}>
        <NDS_dash.Button variant="outline" size="sm" onClick={onAct}>{action}</NDS_dash.Button>
      </div>
    </div>
  );
}

function TimelineEvent({ color, title, meta, danger }) {
  return (
    <div style={{ position: "relative", paddingLeft: "var(--space-xl)" }}>
      <span style={{ position: "absolute", left: -5, top: 4, width: 10, height: 10, borderRadius: "var(--radius-full)", background: color, border: "2px solid var(--surface-container-lowest)" }} />
      <div style={{ fontSize: 13, fontWeight: 500, color: danger ? "var(--error)" : "var(--on-surface)" }}>{title}</div>
      <div style={{ fontSize: 11, color: "var(--on-surface-variant)", marginTop: 2 }}>{meta}</div>
    </div>
  );
}

function DashboardScreen({ onOpenPatient }) {
  const { Panel, Button, DataTable, StatusChip } = NDS_dash;
  const queue = [
    { id: "PT-8829", name: "Jonathan Doe", risk: "High risk", tone: "critical", reason: "Elevated troponin found in the most recent lab extraction." },
    { id: "PT-1044", name: "Sarah Smith", risk: "Needs review", tone: "warning", reason: "Medication history conflicts across three clinical notes." },
    { id: "PT-5510", name: "Wei Chen", risk: "Stable", tone: "stable", reason: "Routine AI summary generated with no acute flags." },
    { id: "PT-9921", name: "Maria Garcia", risk: "Needs review", tone: "warning", reason: "Imaging report missing for the recent MRI study." },
  ];
  const cols = [
    { key: "id", header: "Patient ID", mono: true },
    { key: "name", header: "Name", render: (r) => <span style={{ fontWeight: 500 }}>{r.name}</span> },
    { key: "risk", header: "Risk status", render: (r) => <StatusChip tone={r.tone}>{r.risk}</StatusChip> },
    { key: "reason", header: "Reason flagged", render: (r) => <span style={{ color: "var(--on-surface-variant)", display: "inline-block", maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis" }}>{r.reason}</span> },
    { key: "action", header: "Action", align: "right", render: (r) => <a href="#" onClick={(e) => { e.preventDefault(); onOpenPatient && onOpenPatient(); }} style={{ color: "var(--primary)", fontWeight: 500, textDecoration: "none" }}>{r.tone === "stable" ? "View" : "Review"}</a> },
  ];

  return (
    <div style={{ padding: "var(--space-md)", display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
      <div>
        <h1 style={{ margin: 0, fontSize: 26, fontWeight: 600, letterSpacing: "-0.02em" }}>Good morning, Dr. Miller</h1>
        <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--on-surface-variant)" }}>You have 7 high risk patients and 12 items waiting in your clinical inbox.</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "var(--space-md)" }}>
        <KpiCard label="Total patients" value="1,248" sub="Assigned to your panel" icon="groups" iconColor="var(--primary)" iconBg="var(--primary-fixed)" />
        <KpiCard label="Pending extractions" value="34" sub="Awaiting AI processing" icon="pending_actions" iconColor="var(--tertiary)" iconBg="var(--tertiary-fixed)" />
        <KpiCard label="High risk alerts" value="7" sub="Need clinical attention" icon="warning" iconColor="var(--error)" iconBg="var(--error-container)" critical />
        <KpiCard label="Clinical inbox" value="12" sub="Items to review" icon="inbox" iconColor="var(--secondary)" iconBg="var(--secondary-fixed)" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "var(--space-md)" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
          <Panel title="Priority patient queue" icon="priority_high" bodyPadding="0"
                 actions={<Button variant="ghost" size="sm">View all</Button>}>
            <DataTable columns={cols} rows={queue} onRowClick={() => onOpenPatient && onOpenPatient()} />
          </Panel>

          <Panel title="Recent agent activity" icon="history">
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)", borderLeft: "1px solid var(--outline-variant)", marginLeft: "var(--space-sm)", paddingTop: 4 }}>
              <TimelineEvent color="var(--primary)" title="Extraction complete for MRI Brain, PT-8829" meta="2 minutes ago. Confidence 94 percent." />
              <TimelineEvent color="var(--outline)" title="EHR database sync finished" meta="15 minutes ago. Processed 42 new records." />
              <TimelineEvent color="var(--error)" danger title="Alert generated for troponin elevation" meta="1 hour ago. Raised by the monitoring agent." />
            </div>
          </Panel>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
          <Panel title="AI recommendations" icon="lightbulb" iconColor="var(--primary)"
                 actions={<Button variant="ghost" size="sm">View all</Button>}>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
              <RecommendationCard icon="refresh" iconColor="var(--tertiary)" title="Re-run extraction for PT-8829"
                body="The previous text extraction scored 72 percent confidence. Re-processing with high resolution OCR is recommended." action="Run extraction" />
              <RecommendationCard icon="assignment" iconColor="var(--primary)" title="Review the updated treatment plan"
                body="New lab results for PT-1044 conflict with the current medication. The agent suggests an alternative dose." action="Open draft" />
            </div>
          </Panel>

          <Panel title="Today's sessions" icon="event" bodyPadding="var(--space-sm)">
            {[
              { time: "10:00 AM", label: "Tumor board preparation", status: "In progress", live: true },
              { time: "01:30 PM", label: "PT-8829 consult", status: "Scheduled" },
              { time: "03:00 PM", label: "Data sync review", status: "Scheduled" },
            ].map((s, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 36, padding: "0 var(--space-sm)", borderBottom: i < 2 ? "1px solid color-mix(in srgb, var(--outline-variant) 50%, transparent)" : "none" }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: s.live ? "var(--on-surface)" : "var(--on-surface-variant)", width: 72 }}>{s.time}</span>
                <span style={{ flex: 1, fontSize: 13, color: "var(--on-surface)" }}>{s.label}</span>
                <span style={{ fontSize: 11, fontWeight: 600, color: s.live ? "var(--primary)" : "var(--on-surface-variant)" }}>{s.status}</span>
              </div>
            ))}
          </Panel>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { DashboardScreen });
