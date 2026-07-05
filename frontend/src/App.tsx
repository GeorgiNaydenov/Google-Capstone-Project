import { type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { ClinicalProvider, useClinical } from "./context";
import { Shell } from "./Shell";
import { AdminDashboard, AgentConfiguration, DataStorage, UsersRoles } from "./screens/AdminScreens";
import { ClinicalInbox, ClinicianDashboard, PatientOverview, PatientProfile, PatientSearch, SessionDetail } from "./screens/ClinicalScreens";
import { Landing, RoleSelection } from "./screens/EntryScreens";
import { DatabaseIntelligence, Extraction, PatientQa } from "./screens/WorkflowScreens";
import { DeveloperConsole } from "./screens/DeveloperConsole";
import type { Role } from "./types";

export const primaryRoutes = [
  "/", "/roles", "/app/patients", "/app/overview", "/app/dashboard", "/app/queue",
  "/app/patient/:patientId", "/app/session/:sessionId", "/app/extraction", "/app/qa",
  "/app/database", "/app/inbox", "/app/admin", "/app/users", "/app/storage", "/app/configuration", "/app/console",
  "/docs-viewer",
] as const;

function RequireRole({ allow, fallback, children }: { allow: Role; fallback: string; children: ReactNode }) {
  const { role } = useClinical();
  if (role !== allow) return <Navigate to={fallback} replace />;
  return <>{children}</>;
}

export function App() {
  return <ClinicalProvider><Routes>
    <Route path="/" element={<Landing/>}/><Route path="/roles" element={<RoleSelection/>}/>
    <Route path="/docs-viewer" element={<DeveloperConsole/>}/>
    <Route path="/app" element={<Shell/>}>
      <Route index element={<Navigate to="dashboard" replace/>}/>
      <Route path="patients" element={<PatientSearch/>}/><Route path="overview" element={<PatientOverview/>}/>
      <Route path="dashboard" element={<ClinicianDashboard/>}/><Route path="queue" element={<PatientSearch queue/>}/>
      <Route path="patient/:patientId" element={<PatientProfile/>}/><Route path="session/:sessionId" element={<SessionDetail/>}/>
      <Route path="extraction" element={<Extraction/>}/><Route path="qa" element={<PatientQa/>}/>
      <Route path="database" element={<DatabaseIntelligence/>}/><Route path="inbox" element={<ClinicalInbox/>}/>
      <Route path="admin" element={<RequireRole allow="admin" fallback="/app/dashboard"><AdminDashboard/></RequireRole>}/>
      <Route path="users" element={<RequireRole allow="admin" fallback="/app/dashboard"><UsersRoles/></RequireRole>}/>
      <Route path="storage" element={<RequireRole allow="admin" fallback="/app/dashboard"><DataStorage/></RequireRole>}/>
      <Route path="configuration" element={<RequireRole allow="admin" fallback="/app/dashboard"><AgentConfiguration/></RequireRole>}/>
      <Route path="console" element={<Navigate to="/docs-viewer?tab=api_runner" replace/>}/>
    </Route><Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></ClinicalProvider>;
}
