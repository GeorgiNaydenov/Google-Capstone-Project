import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api";
import { Icon, RoleSwitcher, StatusBadge } from "./components";
import { useClinical } from "./context";
import { ONBOARDING_KEY, OnboardingTour } from "./Onboarding";
import { OrchestrationPanel } from "./OrchestrationPanel";
import { TENANTS, type ClinicalNotification, type Patient, type TenantId, type WorkspaceSummary } from "./types";

const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.userAgent);

type NavItem = { to: string; icon: string; label: string; countKey?: "queue" | "inbox"; external?: boolean };
type NavGroup = { label: string; items: NavItem[] };

const documentationGroup: NavGroup = { label: "Developer & Documentation", items: [
  { to: "/documentation/", icon: "report", label: "Documentation Hub", external: true },
  { to: "/documentation/llm-wiki/index.html", icon: "brain", label: "Karpathy LLM Wiki", external: true },
  { to: "/documentation/project-wiki/Home.html", icon: "activity", label: "Obsidian Wiki", external: true },
  { to: "/docs", icon: "report", label: "Interactive API Docs", external: true },
  { to: "/docs-viewer?tab=api_runner", icon: "sliders", label: "API Console" },
]};

const clinicianGroups: NavGroup[] = [
  { label: "Workspace", items: [
    { to: "/app/dashboard", icon: "dashboard", label: "Dashboard" },
    { to: "/app/queue", icon: "list", label: "Patient Queue", countKey: "queue" },
    { to: "/app/patients", icon: "patients", label: "Patients" },
    { to: "/app/patients?view=sessions", icon: "calendar", label: "Sessions" },
    { to: "/app/overview", icon: "chart", label: "Population Overview" },
    { to: "/app/inbox", icon: "inbox", label: "Clinical Inbox", countKey: "inbox" },
    { to: "/app/extraction", icon: "microscope", label: "Image Extraction" },
    { to: "/app/qa", icon: "brain", label: "Multimodal Q&A" },
    { to: "/app/database", icon: "database", label: "Database Intelligence" },
  ]},
  { label: "Reports & Compliance", items: [
    { to: "/app/overview?view=reports", icon: "report", label: "Reports" },
    { to: "/app/inbox?view=audit", icon: "shield", label: "Audit Trail" },
  ]},
  documentationGroup,
];

const adminGroups: NavGroup[] = [
  { label: "Administration", items: [
    { to: "/app/admin", icon: "dashboard", label: "Admin Dashboard" },
    { to: "/app/users", icon: "patients", label: "Users & Roles" },
    { to: "/app/overview", icon: "chart", label: "Patients Overview" },
    { to: "/app/configuration", icon: "sliders", label: "Agent Configuration" },
  ]},
  { label: "Data Platform", items: [
    { to: "/app/storage?view=pipelines", icon: "activity", label: "Data Pipelines" },
    { to: "/app/storage", icon: "cloud", label: "Storage & Integrations" },
    { to: "/app/storage?view=vector", icon: "vector", label: "Vector Indexes" },
    { to: "/app/storage?view=relational", icon: "database", label: "Relational Database" },
  ]},
  { label: "Governance & Audit", items: [
    { to: "/app/inbox?view=audit", icon: "shield", label: "Audit Logs" },
    { to: "/app/admin?view=health", icon: "pulse", label: "System Health" },
    { to: "/app/configuration?view=settings", icon: "settings", label: "Settings" },
  ]},
  documentationGroup,
];

function routeTitle(pathname: string, search: string) {
  const fullPath = search ? `${pathname}${search}` : pathname;
  const match = [...clinicianGroups, ...adminGroups].flatMap(group => group.items).find(item => item.to === fullPath || item.to === pathname);
  return match?.label ?? "Clinical workspace";
}

export function Shell() {
  const { role, setRole, patient, setPatient, tenant, setTenant } = useClinical();
  const navigate = useNavigate();
  const location = useLocation();
  const searchRef = useRef<HTMLInputElement>(null);
  const [commandOpen, setCommandOpen] = useState(false);
  const [initialCommand, setInitialCommand] = useState("");
  const [noticeOpen, setNoticeOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(() => localStorage.getItem(ONBOARDING_KEY) !== "done" && location.pathname !== "/app/console");
  const [searchOpen, setSearchOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [matches, setMatches] = useState<Patient[]>([]);
  const [notifications, setNotifications] = useState<ClinicalNotification[]>([]);
  const [summary, setSummary] = useState<WorkspaceSummary | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const groups = role === "clinician" ? clinicianGroups : adminGroups;
  const unread = notifications.filter(item => !item.read).length;
  const title = routeTitle(location.pathname, location.search);

  useEffect(() => {
    if (location.pathname === "/app/console") {
      setTourOpen(false);
      localStorage.setItem(ONBOARDING_KEY, "done");
    }
  }, [location.pathname]);

  useEffect(() => { void api.notifications().then(setNotifications).catch(() => setNotifications([])); }, [tenant.id]);
  useEffect(() => { void api.summary().then(setSummary).catch(() => setSummary(null)); }, [tenant.id, location.pathname]);
  useEffect(() => {
    if (search.trim().length < 2) { setMatches([]); return; }
    const timer = window.setTimeout(() => { void api.patients(search).then(setMatches).catch(() => setMatches([])); }, 180);
    return () => window.clearTimeout(timer);
  }, [search]);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openOrchestrator(); }
    };
    document.addEventListener("keydown", shortcut);
    return () => document.removeEventListener("keydown", shortcut);
  }, []);
  useEffect(() => { setNoticeOpen(false); setSearchOpen(false); setProfileOpen(false); }, [location.pathname, location.search]);

  const switchRole = (next: typeof role) => {
    setRole(next);
    if (patient) {
      navigate(next === "admin" ? `/app/storage?patient=${patient.id}&view=lineage` : `/app/patient/${patient.id}`);
      return;
    }
    navigate(next === "admin" ? "/app/admin" : "/app/dashboard");
  };
  const submitSearch = (event: FormEvent) => {
    event.preventDefault();
    const query = search.trim();
    if (!query) return;
    if (matches.length === 1) { openPatient(matches[0]); return; }
    navigate(`/app/patients?q=${encodeURIComponent(query)}`);
  };
  const openPatient = (item: Patient) => {
    setPatient(item); setSearch(""); setSearchOpen(false); navigate(`/app/patient/${item.id}`);
  };
  const openOrchestrator = () => {
    setInitialCommand(search.trim());
    setCommandOpen(true);
    setSearchOpen(false);
  };
  const readNotice = async (item: ClinicalNotification) => {
    const updated = await api.readNotification(item.id);
    setNotifications(current => current.map(entry => entry.id === updated.id ? updated : entry));
    navigate(item.route);
  };
  const currentPath = `${location.pathname}${location.search}`;
  const nav = useMemo(() => groups, [groups]);

  return <div className="clinical-shell">
    <aside className="clinical-sidebar">
      <NavLink to="/" className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></NavLink>
      <button className="new-session" onClick={() => navigate("/app/extraction")}><Icon name="plus" size={16}/>New session</button>
      <nav className="grouped-nav" aria-label={`${role} navigation`}>{nav.map(group => <section key={group.label}><h2>{group.label}</h2>{group.items.map(item => {
        const target = item.to.split("?")[0];
        const active = currentPath === item.to || (!item.to.includes("?") && location.pathname === target);
        const count = item.countKey === "queue" ? summary?.queueCount : item.countKey === "inbox" ? summary?.inboxCount : undefined;
        if (item.external) return <a key={item.to} href={item.to} target="_blank" rel="noreferrer"><Icon name={item.icon} size={17}/><span>{item.label}</span></a>;
        return <NavLink key={item.to} to={item.to} className={active ? "active" : ""}><Icon name={item.icon} size={17}/><span>{item.label}</span>{count ? <b>{count}</b> : null}</NavLink>;
      })}</section>)}</nav>
      <div className="sidebar-profile-wrap">
        <button className="sidebar-profile" aria-expanded={profileOpen} aria-haspopup="menu" onClick={() => setProfileOpen(value => !value)}><span>{role === "admin" ? "AD" : "CL"}</span><span><strong>{role === "admin" ? "Administrator" : "Clinician"} workspace</strong><small>{tenant.name} · {tenant.kind === "real" ? "Live" : "Demo"}</small></span><Icon name="chevron" size={14}/></button>
        {profileOpen && <div className="profile-popover" role="menu">
          <button role="menuitem" onClick={() => { setProfileOpen(false); switchRole(role === "admin" ? "clinician" : "admin"); }}>Switch to {role === "admin" ? "clinician" : "admin"} view</button>
          <button role="menuitem" onClick={() => { setProfileOpen(false); setTourOpen(true); }}>Replay product tour</button>
          <button role="menuitem" onClick={() => { setProfileOpen(false); window.location.assign("/documentation/"); }}>Documentation hub</button>
          <button role="menuitem" onClick={() => { setProfileOpen(false); navigate("/"); }}>Back to landing page</button>
        </div>}
      </div>
    </aside>

    <header className="clinical-topbar">
      <div className="workspace-title"><strong>{title}</strong><RoleSwitcher role={role} onChange={switchRole}/></div>
      <form className="unified-search" onSubmit={submitSearch}><Icon name="search" size={16}/><input ref={searchRef} aria-label="Global patient search and orchestrator" value={search} onFocus={() => setSearchOpen(true)} onChange={event => { setSearch(event.target.value); setSearchOpen(true); }} placeholder="Search patients, IDs, or ask orchestrator"/><kbd>{isMac ? "Cmd K" : "Ctrl K"}</kbd></form>
      <div className="topbar-tools">
        <select className="organization-select" aria-label="Organization" value={tenant.id} onChange={event => setTenant(event.target.value as TenantId)}>{TENANTS.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <StatusBadge tone={tenant.kind === "real" ? "risk-high" : "risk-low"}>{tenant.kind === "real" ? "Live" : "Demo"}</StatusBadge>
        <button className="utility-button" aria-label="Replay product tour" onClick={() => setTourOpen(true)}><Icon name="agent" size={18}/></button>
        <button className="utility-button" aria-label="Notifications" onClick={() => setNoticeOpen(value => !value)}><Icon name="bell" size={18}/>{unread > 0 && <b>{unread}</b>}</button>
        <button className="utility-button" aria-label="Settings" onClick={() => navigate("/app/configuration?view=settings")}><Icon name="settings" size={18}/></button>
      </div>
      {searchOpen && search.trim().length >= 2 && <section className="search-popover"><header><span>Unified search</span><small>{matches.length} patient result{matches.length === 1 ? "" : "s"}; route unmatched work to agents</small></header>{matches.slice(0, 6).map(item => <button key={item.id} onClick={() => openPatient(item)}><span className="mini-avatar">{item.name.split(" ").map(part => part[0]).join("")}</span><span><strong>{item.name}</strong><small>{item.id} - {item.condition}</small></span><StatusBadge tone={`risk-${item.risk}`}>{item.risk}</StatusBadge></button>)}{!matches.length && <p>No matching patients. Send this to the orchestrator.</p>}<footer><button type="button" onClick={openOrchestrator}>Ask orchestrator with this text</button><button type="button" onClick={submitSearch}>View patient search results</button></footer></section>}
      {noticeOpen && <section className="notification-drawer"><header><div><strong>Clinical notifications</strong><small>{unread} unread - agent generated</small></div><button aria-label="Close notifications" onClick={() => setNoticeOpen(false)}>x</button></header>{notifications.map(item => <button key={item.id} className={item.read ? "read" : ""} onClick={() => void readNotice(item)}><i className={item.severity}/><span><strong>{item.title}</strong><small>{item.detail}</small><em>{item.agent}</em></span></button>)}</section>}
    </header>

    {patient && <div className="patient-context-strip"><span>Active patient</span><button onClick={() => navigate(`/app/patient/${patient.id}`)}><strong>{patient.name}</strong><small>{patient.id} - {patient.condition}</small></button><StatusBadge tone={`risk-${patient.risk}`}>{patient.risk} risk</StatusBadge><button aria-label="Clear active patient" onClick={() => setPatient(null)}>x</button></div>}
    <main key={tenant.id} className={patient ? "clinical-main has-context" : "clinical-main"}><Outlet/></main>
    <OrchestrationPanel open={commandOpen} initialQuery={initialCommand} onClose={() => setCommandOpen(false)}/>
    <OnboardingTour open={tourOpen} onClose={() => setTourOpen(false)}/>
  </div>;
}
