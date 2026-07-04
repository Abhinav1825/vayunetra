import { useEffect, useState } from "react";
import { api } from "./api";

type Trace = {
  city_id: string;
  total_latency_ms: number;
  signal_ts: string;
  advisory_ts: string;
};

function fmt(ms?: number) {
  if (!ms) return "--";
  const total = Math.round(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}m ${String(s).padStart(2, "0")}s`;
}

export default function LatencyWidget({ city }: { city: string }) {
  const [trace, setTrace] = useState<Trace | null>(null);

  useEffect(() => {
    api<Trace>(`/latency?city=${city}`).then(setTrace).catch(() => setTrace(null));
  }, [city]);

  return (
    <div className="min-w-40 rounded-md bg-emerald-50 px-3 py-2 text-xs text-emerald-900 ring-1 ring-emerald-200">
      <div className="font-semibold">Signal to action</div>
      <div className="text-lg font-bold leading-tight">{fmt(trace?.total_latency_ms)}</div>
    </div>
  );
}
