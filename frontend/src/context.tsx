import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Patient, Role } from "./types";

interface ClinicalContextValue {
  role: Role;
  setRole: (role: Role) => void;
  patient: Patient | null;
  setPatient: (patient: Patient | null) => void;
}

const ClinicalContext = createContext<ClinicalContextValue | null>(null);

export function ClinicalProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>(() => localStorage.getItem("clinicalRole") === "admin" ? "admin" : "clinician");
  const [patient, setPatientState] = useState<Patient | null>(() => {
    try { return JSON.parse(sessionStorage.getItem("activePatient") ?? "null") as Patient | null; }
    catch { return null; }
  });
  const setRole = (next: Role) => { localStorage.setItem("clinicalRole", next); setRoleState(next); };
  const setPatient = (next: Patient | null) => {
    if (next) sessionStorage.setItem("activePatient", JSON.stringify(next)); else sessionStorage.removeItem("activePatient");
    setPatientState(next);
  };
  useEffect(() => { document.documentElement.dataset.role = role; }, [role]);
  const value = useMemo(() => ({ role, setRole, patient, setPatient }), [role, patient]);
  return <ClinicalContext.Provider value={value}>{children}</ClinicalContext.Provider>;
}

export function useClinical() {
  const value = useContext(ClinicalContext);
  if (!value) throw new Error("useClinical must be used inside ClinicalProvider");
  return value;
}
