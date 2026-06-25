// AppShell — chrome for Clinician AI KIT: grouped sidebar nav + top bar.
const NDS_shell = window.NexusClinicalAIDesignSystem_29a409;

// Grouped navigation keeps the dense product calm: three short sections
// instead of one long flat list.
const NAV_GROUPS = [
  {
    label: "Workspace",
    items: [
      { id: "dashboard", icon: "dashboard", label: "Dashboard" },
      { id: "inbox", icon: "inbox", label: "Clinical Inbox", badge: 6 },
      { id: "patient", icon: "groups", label: "Patients" },
    ],
  },
  {
    label: "AI Agents",
    items: [
      { id: "extraction", icon: "biotech", label: "Image Extraction" },
      { id: "qa", icon: "neurology", label: "Multimodal Q and A" },
      { id: "db", icon: "database", label: "Database Intelligence" },
    ],
  },
  {
    label: "Governance",
    items: [
      { id: "audit", icon: "policy", label: "Audit Trail" },
    ],
  },
];

function NavItem({ item, active, onNavigate }) {
  return (
    <a href="#" onClick={(e) => { e.preventDefault(); onNavigate(item.id); }}
      style={{
        display: "flex", alignItems: "center", gap: "var(--space-md)", height: 36, padding: "0 var(--space-md)",
        borderRadius: active ? "0 var(--radius-md) var(--radius-md) 0" : "var(--radius-md)",
        background: active ? "var(--secondary-container)" : "transparent",
        color: active ? "var(--on-secondary-container)" : "var(--on-surface-variant)",
        borderLeft: active ? "3px solid var(--primary)" : "3px solid transparent",
        fontSize: 13, fontWeight: active ? 600 : 500,
        textDecoration: "none", transition: "background-color 150ms ease",
      }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = "var(--surface-container-high)"; }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = "transparent"; }}>
      <span className="material-symbols-outlined" style={{ fontSize: 20, fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0" }}>{item.icon}</span>
      <span style={{ flex: 1 }}>{item.label}</span>
      {item.badge ? (
        <span style={{ minWidth: 18, height: 18, padding: "0 5px", borderRadius: "var(--radius-full)", background: "var(--error)", color: "var(--on-error)", fontSize: 10, fontWeight: 700, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>{item.badge}</span>
      ) : null}
    </a>
  );
}

function SideNav({ current, onNavigate }) {
  return (
    <nav style={{
      width: "var(--sidebar-width)", flexShrink: 0, height: "100%",
      background: "var(--surface-container-low)", borderRight: "1px solid var(--outline-variant)",
      display: "flex", flexDirection: "column", padding: "var(--space-md) 0",
    }}>
      <div style={{ padding: "0 var(--space-lg)", marginBottom: "var(--space-lg)", display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
        <img src="../../assets/clinician-ai-kit-mark.png" alt="Clinician AI KIT" style={{ height: 26, width: "auto" }} />
        <div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "var(--on-surface)", letterSpacing: "-0.01em" }}>Clinician AI KIT</div>
          <div style={{ fontSize: 10, color: "var(--on-surface-variant)" }}>Clinical Command v2.4</div>
        </div>
      </div>
      <div style={{ padding: "0 var(--space-sm)", marginBottom: "var(--space-lg)" }}>
        <NDS_shell.Button variant="primary" icon="add" fullWidth size="sm">New session</NDS_shell.Button>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "0 var(--space-sm)", display: "flex", flexDirection: "column", gap: "var(--space-lg)" }}>
        {NAV_GROUPS.map((group) => (
          <div key={group.label} style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <div style={{ padding: "0 var(--space-md)", marginBottom: 4, fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--outline)" }}>{group.label}</div>
            {group.items.map((item) => (
              <NavItem key={item.id} item={item} active={current === item.id} onNavigate={onNavigate} />
            ))}
          </div>
        ))}
      </div>
      <div style={{ marginTop: "auto", padding: "var(--space-md) var(--space-lg) 0", borderTop: "1px solid var(--outline-variant)", display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
        <div style={{ width: 32, height: 32, borderRadius: "var(--radius-full)", background: "var(--primary-container)", color: "var(--on-primary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700 }}>SM</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: "var(--on-surface)" }}>Dr. Sarah Miller</div>
          <div style={{ fontSize: 10, color: "var(--on-surface-variant)" }}>Oncologist</div>
        </div>
        <NDS_shell.IconButton icon="more_vert" label="Account menu" size="sm" />
      </div>
    </nav>
  );
}

function TopBar({ role, onRole, title }) {
  return (
    <header style={{
      height: "var(--row-height-md)", flexShrink: 0, background: "var(--surface)",
      borderBottom: "1px solid var(--outline-variant)", display: "flex", alignItems: "center",
      justifyContent: "space-between", padding: "0 var(--space-lg)", zIndex: 10,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-lg)" }}>
        <span style={{ fontSize: 15, fontWeight: 600, color: "var(--on-surface)" }}>{title}</span>
        <span style={{ width: 1, height: 20, background: "var(--outline-variant)" }} />
        <NDS_shell.RoleSwitcher options={["Clinician", "Admin"]} value={role} onChange={onRole} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
        <div style={{ width: 260 }}><NDS_shell.Input size="sm" icon="search" placeholder="Search patients, sessions, or IDs" /></div>
        <NDS_shell.IconButton icon="sync" label="Sync data" />
        <NDS_shell.IconButton icon="notifications" label="Notifications" />
        <NDS_shell.IconButton icon="settings" label="Settings" />
      </div>
    </header>
  );
}

function AppShell({ current, onNavigate, title, children }) {
  const [role, setRole] = React.useState("Clinician");
  return (
    <div style={{ display: "flex", height: "100%", background: "var(--background)", color: "var(--on-surface)", fontFamily: "var(--font-sans)" }}>
      <SideNav current={current} onNavigate={onNavigate} />
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "var(--surface-container-low)" }}>
        <TopBar role={role} onRole={setRole} title={title} />
        <div style={{ flex: 1, overflow: "auto" }}>{children}</div>
      </main>
    </div>
  );
}

Object.assign(window, { AppShell });
