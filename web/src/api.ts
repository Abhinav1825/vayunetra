// Envelope-aware API client. Matches docs/API_CONTRACT.md.
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
// Supabase anon key — safe to expose in the browser (publishable by design).
// Sent as a Bearer token so the live backend (DEMO_MODE=false) accepts reads.
// Harmless when the backend runs in DEMO_MODE (the header is ignored).
const TOKEN = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;

type Envelope<T> = {
  success: boolean;
  data: T | null;
  error: { code: string; message: string } | null;
};

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (TOKEN && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${TOKEN}`);
  }
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  const env = (await res.json()) as Envelope<T>;
  if (!env.success || env.data === null) {
    throw new Error(env.error?.message ?? `API error (${res.status})`);
  }
  return env.data;
}

/** Fetch a binary endpoint (e.g. a PDF) with auth and trigger a browser download. */
export async function downloadFile(path: string, filename: string): Promise<void> {
  const headers = new Headers();
  if (TOKEN) headers.set("Authorization", `Bearer ${TOKEN}`);
  const res = await fetch(`${BASE}${path}`, { headers });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
