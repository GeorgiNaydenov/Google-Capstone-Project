import type { AgentRun } from "./types";

export type WorkflowTurn = { id: string; question: string; run: AgentRun };

// In-memory conversation store shared across route mounts. Keyed by tenant +
// workflow (+ patient scope for Q&A) so leaving a chat and returning restores
// the thread instantly, including client-side synthetic demo runs that never
// reach the backend. Backend GET /runs re-hydrates API-backed runs after a
// full page reload, so the two layers together cover both navigation styles.
const store = new Map<string, WorkflowTurn[]>();

export function historyKey(tenantId: string, workflow: string, scope = ""): string {
  // The demo session id participates in the key so entering a fresh demo
  // session never inherits a previous session's cached thread.
  const session = sessionStorage.getItem("demoSession") ?? "public-demo";
  return `${tenantId}:${session}:${workflow}${scope ? `:${scope}` : ""}`;
}

export function loadTurns(key: string): WorkflowTurn[] {
  return store.get(key) ?? [];
}

export function saveTurns(key: string, turns: WorkflowTurn[]): void {
  store.set(key, turns);
}

export function clearHistory(): void {
  store.clear();
}
