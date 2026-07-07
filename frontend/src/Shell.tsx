import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "./api";
import { Icon, RoleSwitcher, StatusBadge } from "./components";
import { useClinical } from "./context";
import { ONBOARDING_KEY, OnboardingTour } from "./Onboarding";
import { OrchestrationPanel } from "./OrchestrationPanel";
import { TENANTS, type ClinicalNotification, type Patient, type TenantId, type WorkspaceSummary } from "./types";

type NavItem = { to: string; icon: string; label: string; countKey?: "queue" | "inbox"; external?: boolean };
type NavGroup = { label: string; items: NavItem[] };

const clinicianGroups: NavGroup[] = [
  { label: "Workspace", items: [
    { to: "/app/dashboard", icon: "dashboard", label: "Dashboard" },
    { to: "/app/queue", icon: "list", label: "Patient Queue", countKey: "queue" },
    { to: "/app/patients", icon: "patients", label: "Patients" },
    { to: "/app/patients?view=sessions", icon: "calendar", label: "Sessions" },
    { to: "/app/overview", icon: "chart", label: "Population Overview" },
    { to: "/app/inbox", icon: "inbox", label: "Clinical Inbox", countKey: "inbox" },
  ]},
  { label: "AI Workflows", items: [
    { to: "/app/extraction", icon: "microscope", label: "Evidence Extraction" },
    { to: "/app/qa", icon: "brain", label: "Patient Q&A" },
    { to: "/app/database", icon: "database", label: "Population Insights" },
  ]},
  { label: "Reports & Compliance", items: [
    { to: "/app/overview?view=reports", icon: "report", label: "Reports" },
    { to: "/app/inbox?view=audit", icon: "shield", label: "Audit Trail" },
  ]},
];

const adminGroups: NavGroup[] = [
  { label: "Administration", items: [
    { to: "/app/admin", icon: "dashboard", label: "Admin Dashboard" },
    { to: "/app/users", icon: "patients", label: "Users & Roles" },
    { to: "/app/overview", icon: "chart", label: "Patients Overview" },
  ]},
  { label: "AI Workflows", items: [
    { to: "/app/configuration", icon: "sliders", label: "Agent Configuration & Settings" },
  ]},
  { label: "Data Platform", items: [
    { to: "/app/storage", icon: "dashboard", label: "Storage Overview" },
    { to: "/app/storage?view=objects", icon: "cloud", label: "Object Storage" },
    { to: "/app/storage?view=pipelines", icon: "activity", label: "Data Pipelines" },
    { to: "/app/storage?view=json", icon: "report", label: "JSON Document Store" },
    { to: "/app/storage?view=relational", icon: "database", label: "Relational Database" },
    { to: "/app/storage?view=vector", icon: "vector", label: "Vector Search Index" },
  ]},
  { label: "Governance & Audit", items: [
    { to: "/app/inbox?view=audit", icon: "shield", label: "Audit Logs" },
    { to: "/app/admin?view=health", icon: "pulse", label: "System Health" },
  ]},
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
  const [tourOpen, setTourOpen] = useState(() => localStorage.getItem(ONBOARDING_KEY) !== "done" && ["/app", "/app/dashboard"].includes(location.pathname));
  const [searchOpen, setSearchOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [matches, setMatches] = useState<Patient[]>([]);
  const [notifications, setNotifications] = useState<ClinicalNotification[]>([]);
  const [summary, setSummary] = useState<WorkspaceSummary | null>(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const groups = role === "clinician" ? clinicianGroups : adminGroups;
  const visibleNotifications = notifications.filter(item => role === "admin" || (!item.title.toLowerCase().includes("api") && !item.route.includes("admin")));
  const unread = visibleNotifications.filter(item => !item.read).length;
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
  useEffect(() => { setNoticeOpen(false); setSearchOpen(false); setProfileOpen(false); setMenuOpen(false); }, [location.pathname, location.search]);
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [menuOpen]);

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

  return <div className={menuOpen ? "clinical-shell menu-open" : "clinical-shell"}>
    {menuOpen && <div className="sidebar-backdrop" onClick={() => setMenuOpen(false)}/>}
    <aside className={menuOpen ? "clinical-sidebar open" : "clinical-sidebar"}>
      <Link to="/" className="product-lockup"><span className="product-symbol"><img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/></span><span><strong>Clinician AI KIT</strong><small>Clinical Command v2.4</small></span></Link>
      <button className="new-session" onClick={() => navigate("/app/extraction")}><Icon name="plus" size={16}/>New session</button>
      <nav className="grouped-nav" aria-label={`${role} navigation`}>{nav.map(group => <section key={group.label}><h2>{group.label}</h2>{group.items.map(item => {
        const target = item.to.split("?")[0];
        const active = (() => {
          if (location.pathname !== target) return false;
          const itemParams = new URLSearchParams(item.to.split("?")[1] || "");
          const currentParams = new URLSearchParams(location.search);
          const itemView = itemParams.get("view");
          const currentView = currentParams.get("view");
          if (itemView) {
            return currentView === itemView;
          } else {
            if (!currentView) return true;
            if (target === "/app/storage") {
              return !["objects", "pipelines", "json", "relational", "vector"].includes(currentView);
            }
            if (target === "/app/patients") {
              return currentView !== "sessions";
            }
            if (target === "/app/overview") {
              return currentView !== "reports";
            }
            if (target === "/app/inbox") {
              return currentView !== "audit";
            }
            if (target === "/app/admin") {
              return currentView !== "health";
            }
            return true;
          }
        })();
        const count = item.countKey === "queue" ? summary?.queueCount : item.countKey === "inbox" ? summary?.inboxCount : undefined;
        if (item.external) return <a key={item.to} href={item.to} target="_blank" rel="noreferrer"><Icon name={item.icon} size={17}/><span>{item.label}</span></a>;
        return <Link key={item.to} to={item.to} className={active ? "active" : ""}><Icon name={item.icon} size={17}/><span>{item.label}</span>{count ? <b>{count}</b> : null}</Link>;
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
      <button className="menu-toggle" aria-label="Toggle navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(value => !value)}><Icon name="list" size={20}/></button>
      <div className="workspace-title"><strong>{title}</strong><RoleSwitcher role={role} onChange={switchRole}/></div>
      <form className="unified-search" onSubmit={submitSearch}><Icon name="search" size={16}/><input ref={searchRef} aria-label="Global patient search" value={search} onFocus={() => setSearchOpen(true)} onChange={event => { setSearch(event.target.value); setSearchOpen(true); }} placeholder="Search patients, record numbers, or ask a question"/></form>
      <div className="topbar-tools">
        <select className="organization-select" aria-label="Organization" value={tenant.id} onChange={event => setTenant(event.target.value as TenantId)}>{TENANTS.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
        <StatusBadge tone={tenant.kind === "real" ? "risk-high" : "risk-low"}>{tenant.kind === "real" ? "Live" : "Demo"}</StatusBadge>
        <button className="utility-button" aria-label="Replay product tour" onClick={() => setTourOpen(true)}><Icon name="agent" size={18}/></button>
        <button className="utility-button" aria-label="Notifications" onClick={() => setNoticeOpen(value => !value)}><Icon name="bell" size={18}/>{unread > 0 && <b>{unread}</b>}</button>
        <button className="utility-button" aria-label="Settings" onClick={() => navigate("/app/configuration?view=settings")}><Icon name="settings" size={18}/></button>
      </div>
      {searchOpen && search.trim().length >= 2 && <><div className="click-outside-backdrop" onClick={() => setSearchOpen(false)}/><section className="search-popover"><header><span>Unified search</span><small>{matches.length} patient result{matches.length === 1 ? "" : "s"}; route unmatched work to agents</small></header>{matches.slice(0, 6).map(item => <button key={item.id} onClick={() => openPatient(item)}><span className="mini-avatar">{item.name.split(" ").map(part => part[0]).join("")}</span><span><strong>{item.name}</strong><small>{item.id} - {item.condition}</small></span><StatusBadge tone={`risk-${item.risk}`}>{item.risk}</StatusBadge></button>)}{!matches.length && <p>No matching patients. Ask this as a question instead.</p>}<footer><button type="button" onClick={openOrchestrator}>Ask this as a question</button><button type="button" onClick={submitSearch}>View patient search results</button></footer></section></>}
      {noticeOpen && <><div className="click-outside-backdrop" onClick={() => setNoticeOpen(false)}/><section className="notification-drawer"><header><div><strong>Clinical notifications</strong><small>{unread} unread - agent generated</small></div><button aria-label="Close notifications" onClick={() => setNoticeOpen(false)}>x</button></header>{visibleNotifications.map(item => <button key={item.id} className={item.read ? "read" : ""} onClick={() => void readNotice(item)}><i className={item.severity}/><span><strong>{item.title}</strong><small>{item.detail}</small><em>{item.agent}</em></span></button>)}</section></>}
    </header>

    {patient && <div className="patient-context-strip"><span>Active patient</span><button onClick={() => navigate(`/app/patient/${patient.id}`)}><strong>{patient.name}</strong><small>{patient.id} - {patient.condition}</small></button><StatusBadge tone={`risk-${patient.risk}`}>{patient.risk} risk</StatusBadge><button aria-label="Clear active patient" onClick={() => setPatient(null)}>x</button></div>}
    <main key={tenant.id} className={patient ? "clinical-main has-context" : "clinical-main"}><Outlet/></main>
    <OrchestrationPanel open={commandOpen} initialQuery={initialCommand} onClose={() => setCommandOpen(false)}/>
    <OnboardingTour open={tourOpen} onClose={() => setTourOpen(false)}/>
  </div>;
}
