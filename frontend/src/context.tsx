import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { TENANTS, type Patient, type Role, type Tenant, type TenantId } from "./types";

interface ClinicalContextValue {
  role: Role;
  setRole: (role: Role) => void;
  patient: Patient | null;
  setPatient: (patient: Patient | null) => void;
  tenant: Tenant;
  setTenant: (id: TenantId) => void;
}

const ClinicalContext = createContext<ClinicalContextValue | null>(null);

// Older sessions stored pre-tenancy values; map them onto the registry.
const LEGACY_TENANTS: Record<string, TenantId> = { demo: "research-clinic", local: "research-clinic", live: "capstone" };

function storedTenant(): Tenant {
  const raw = sessionStorage.getItem("tenant") ?? "";
  const id = LEGACY_TENANTS[raw] ?? raw;
  return TENANTS.find(item => item.id === id) ?? TENANTS[0];
}

export function ClinicalProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>(() => localStorage.getItem("clinicalRole") === "admin" ? "admin" : "clinician");
  const [patient, setPatientState] = useState<Patient | null>(() => {
    try { return JSON.parse(sessionStorage.getItem("activePatient") ?? "null") as Patient | null; }
    catch { return null; }
  });
  const [tenant, setTenantState] = useState<Tenant>(storedTenant);
  const setRole = (next: Role) => { localStorage.setItem("clinicalRole", next); setRoleState(next); };
  const setPatient = (next: Patient | null) => {
    if (next) sessionStorage.setItem("activePatient", JSON.stringify(next)); else sessionStorage.removeItem("activePatient");
    setPatientState(next);
  };
  const setTenant = (id: TenantId) => {
    const next = TENANTS.find(item => item.id === id) ?? TENANTS[0];
    sessionStorage.setItem("tenant", next.id);
    // Patient ids differ across tenants, so the active patient cannot survive a switch.
    setPatient(null);
    setTenantState(next);
  };
  useEffect(() => { document.documentElement.dataset.role = role; }, [role]);
  const value = useMemo(() => ({ role, setRole, patient, setPatient, tenant, setTenant }), [role, patient, tenant]);
  return <ClinicalContext.Provider value={value}>{children}</ClinicalContext.Provider>;
}

export function useClinical() {
  const value = useContext(ClinicalContext);
  if (!value) throw new Error("useClinical must be used inside ClinicalProvider");
  return value;
}
