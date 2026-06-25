// PatientProfileScreen — unified patient record with timeline and AI copilot.
const NDS_pt = window.NexusClinicalAIDesignSystem_29a409;

function ProfileSection({ title, action, children }) {
  return (
    <section style={{ marginBottom: "var(--space-xl)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--space-sm)" }}>
        <h3 style={{ margin: 0, fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)" }}>{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function PatientProfileScreen({ onBack }) {
  const { Panel, Button, Tabs, StatusChip, ConfidenceMeter, Input } = NDS_pt;
  const [tab, setTab] = React.useState("Timeline");
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ background: "var(--surface)", borderBottom: "1px solid var(--outline-variant)", padding: "var(--space-md) var(--space-lg)", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-xl)" }}>
          {onBack ? <NDS_pt.Button variant="ghost" size="sm" icon="list" onClick={onBack}>Back to queue</NDS_pt.Button> : null}
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em" }}>Jonathan Doe</h1>
            <div style={{ fontSize: 13, color: "var(--on-surface-variant)", marginTop: 2 }}>PT-8829. Male, 62 years.</div>
          </div>
          <div style={{ display: "flex", gap: "var(--space-sm)" }}>
            <StatusChip tone="critical" icon="warning">High risk</StatusChip>
            <StatusChip tone="info">Oncology</StatusChip>
            <StatusChip tone="info">NSCLC</StatusChip>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-xl)" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)" }}>Data completeness</div>
            <div style={{ marginTop: 4 }}><ConfidenceMeter value={88} width={96} color="var(--primary)" /></div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr 340px", flex: 1, minHeight: 0 }}>
        <div style={{ background: "var(--surface)", borderRight: "1px solid var(--outline-variant)", padding: "var(--space-lg)", overflowY: "auto" }}>
          <ProfileSection title="Demographics">
            {[["Date of birth", "05/12/1961"], ["Weight", "82 kg"], ["Height", "178 cm"], ["Blood type", "O positive"]].map(([k, v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "3px 0" }}><span style={{ color: "var(--on-surface-variant)" }}>{k}</span><span style={{ color: "var(--on-surface)" }}>{v}</span></div>
            ))}
          </ProfileSection>

          <ProfileSection title="Active diagnoses" action={<NDS_pt.IconButton icon="edit" label="Edit diagnoses" size="sm" />}>
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
              <div style={{ background: "var(--surface-container-low)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-sm)" }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Non-small cell lung cancer</div>
                <div style={{ fontSize: 11, color: "var(--on-surface-variant)", marginTop: 2 }}>Stage IIIa. Diagnosed 2022.</div>
              </div>
              <div style={{ background: "var(--surface-container-low)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-sm)" }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Hypertension</div>
                <div style={{ fontSize: 11, color: "var(--on-surface-variant)", marginTop: 2 }}>Primary. Managed.</div>
              </div>
            </div>
          </ProfileSection>

          <ProfileSection title="Current medications">
            {[["Pembrolizumab", "200 mg IV every 3 weeks"], ["Lisinopril", "10 mg by mouth daily"]].map(([m, d]) => (
              <div key={m} style={{ display: "flex", gap: "var(--space-sm)", padding: "4px 0" }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16, color: "var(--secondary)", marginTop: 1 }}>medication</span>
                <div><div style={{ fontSize: 13, color: "var(--on-surface)" }}>{m}</div><div style={{ fontSize: 11, color: "var(--on-surface-variant)" }}>{d}</div></div>
              </div>
            ))}
          </ProfileSection>

          <ProfileSection title="Allergies">
            <div style={{ background: "var(--error-container)", border: "1px solid color-mix(in srgb, var(--error) 30%, transparent)", borderRadius: "var(--radius-md)", padding: "var(--space-sm)" }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--on-error-container)" }}>Penicillin</div>
              <div style={{ fontSize: 11, color: "var(--on-error-container)", marginTop: 2 }}>Reaction: hives, anaphylaxis risk.</div>
            </div>
          </ProfileSection>
        </div>

        <div style={{ background: "var(--surface-container-low)", display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div style={{ background: "var(--surface)", borderBottom: "1px solid var(--outline-variant)", padding: "var(--space-sm) var(--space-lg) 0" }}>
            <Tabs tabs={["Timeline", "Sessions", "Notes", "Images", "Metrics"]} value={tab} onChange={setTab} />
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-xl)" }}>
            <div style={{ position: "relative", borderLeft: "1px solid var(--outline-variant)", marginLeft: 12, display: "flex", flexDirection: "column", gap: "var(--space-xl)", paddingLeft: "var(--space-xl)" }}>
              <TimelineCard icon="description" title="Oncology review note extracted" meta="Dr. Sarah Chen. Today, 09:42 AM" verified
                body="Patient reports mild fatigue after infusion. No new respiratory symptoms. Tumor markers remain stable. Continue the current immunotherapy regimen." />
              <TimelineCard icon="imagesmode" title="CT thorax with contrast uploaded" meta="System auto ingest. Oct 24, 2023, 2:15 PM"
                findings={["Primary lesion in the right upper lobe measures 3.2 cm, down from 3.4 cm.", "No new lymphadenopathy.", "Mild pleural effusion noted at the right base."]} conf={94} />
            </div>
          </div>
        </div>

        <div style={{ background: "var(--surface)", borderLeft: "1px solid var(--outline-variant)", display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div style={{ padding: "var(--space-md) var(--space-lg)", borderBottom: "1px solid var(--outline-variant)", display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
            <span className="material-symbols-outlined" style={{ fontSize: 20, color: "var(--primary)", fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
            <span style={{ fontSize: 15, fontWeight: 600 }}>AI copilot</span>
          </div>
          <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-lg)", display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            <div style={{ background: "var(--primary-fixed)", border: "1px solid var(--primary-fixed-dim)", borderRadius: "var(--radius-md)", padding: "var(--space-md)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16, color: "var(--primary)" }}>lightbulb</span>
                <span style={{ fontSize: 12, fontWeight: 700, color: "var(--on-primary-fixed-variant)" }}>Clinical insight</span>
              </div>
              <p style={{ margin: 0, fontSize: 13, lineHeight: "18px", color: "var(--on-surface)" }}>Recent CT volumetrics and clinical notes suggest a partial response to pembrolizumab. Pneumonitis risk stays elevated given the prior radiation history.</p>
              <a href="#" onClick={(e) => e.preventDefault()} style={{ fontSize: 12, fontWeight: 600, color: "var(--primary)", textDecoration: "none", marginTop: 8, display: "inline-block" }}>View source guideline</a>
            </div>
            <div style={{ alignSelf: "flex-end", maxWidth: "85%", background: "var(--surface-container)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-sm) var(--space-md)", fontSize: 13 }}>Summarize the last three creatinine results.</div>
            <div style={{ background: "var(--surface-container-lowest)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-md)", padding: "var(--space-md)", fontSize: 13 }}>
              <div style={{ marginBottom: 8 }}>Recent creatinine trend:</div>
              <ul style={{ margin: 0, paddingLeft: 18, color: "var(--on-surface)" }}>
                <li>Oct 24: 1.1 mg/dL</li>
                <li>Sep 12: 1.0 mg/dL</li>
                <li>Aug 05: 1.2 mg/dL</li>
              </ul>
              <p style={{ margin: "8px 0 0", fontSize: 12, color: "var(--on-surface-variant)" }}>Values stay within the normal range of 0.7 to 1.3 mg/dL.</p>
            </div>
          </div>
          <div style={{ padding: "var(--space-md) var(--space-lg)", borderTop: "1px solid var(--outline-variant)" }}>
            <Input size="md" icon="chat" placeholder="Ask the copilot about this patient" />
          </div>
        </div>
      </div>
    </div>
  );
}

function TimelineCard({ icon, title, meta, body, findings, verified, conf }) {
  return (
    <div style={{ position: "relative" }}>
      <div style={{ position: "absolute", left: "calc(-1 * var(--space-xl) - 12px)", top: 0, width: 24, height: 24, borderRadius: "var(--radius-full)", background: "var(--surface)", border: "1px solid var(--outline-variant)", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="material-symbols-outlined" style={{ fontSize: 14, color: "var(--secondary)" }}>{icon}</span>
      </div>
      <div style={{ background: "var(--surface-container-lowest)", border: "1px solid var(--outline-variant)", borderRadius: "var(--radius-lg)", padding: "var(--space-md)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>{title}</div>
            <div style={{ fontSize: 11, color: "var(--on-surface-variant)", marginTop: 2 }}>{meta}</div>
          </div>
          {verified ? <NDS_pt.StatusChip tone="verified" icon="verified">Verified</NDS_pt.StatusChip> : null}
        </div>
        {body ? <p style={{ margin: "var(--space-sm) 0 0", fontSize: 13, lineHeight: "18px", color: "var(--on-surface)" }}>{body}</p> : null}
        {findings ? (
          <div style={{ marginTop: "var(--space-sm)" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--on-surface-variant)", marginBottom: 4 }}>AI findings</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--on-surface)", lineHeight: "20px" }}>
              {findings.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
            <div style={{ marginTop: "var(--space-sm)" }}><NDS_pt.ConfidenceMeter value={conf} label="AI confidence" width={120} /></div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

Object.assign(window, { PatientProfileScreen });
