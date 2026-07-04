// Envelope-aware API client. Matches docs/API_CONTRACT.md.
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type Envelope<T> = {
  success: boolean;
  data: T | null;
  error: { code: string; message: string } | null;
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  const env = (await res.json()) as Envelope<T>;
  if (!env.success || env.data === null) {
    throw new Error(env.error?.message ?? `API error (${res.status})`);
  }
  return env.data;
}
