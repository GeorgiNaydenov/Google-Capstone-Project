export function normalizeBuildId(value: string | undefined): string {
  return (value ?? "local").replace(/[^a-zA-Z0-9_-]/g, "-");
}
