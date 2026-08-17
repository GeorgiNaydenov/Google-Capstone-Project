import { useCallback, useEffect, useState } from "react";

export function useApi<T>(load: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(() => {
    setLoading(true); setError(null);
    return load().then(setData).catch(setError).finally(() => setLoading(false));
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { void refresh(); }, [refresh]);
  return { data, error, loading, refresh, setData };
}
