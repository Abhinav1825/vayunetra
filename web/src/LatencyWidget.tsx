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
  if (total < 60) return `${total}s`;
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}m ${String(s).padStart(2, "0")}s`;
}

/** North-Star banner: end-to-end signal → action latency (target < 5 min). */
export default function LatencyWidget({ city }: { city: string }) {
  const [trace, setTrace] = useState<Trace | null>(null);

  useEffect(() => {
    api<Trace>(`/latency?city=${city}`).then(setTrace).catch(() => setTrace(null));
  }, [city]);

  const ms = trace?.total_latency_ms;
  const under5 = typeof ms === "number" && ms > 0 && ms < 5 * 60_000;

  return (
    <div className="rounded-lg bg-emerald-600 px-4 py-2 text-white shadow" title="End-to-end pipeline latency: first signal → last agent action">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-100">⚡ Signal → Action</div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-extrabold leading-tight">{fmt(ms)}</span>
        {under5 && <span className="rounded bg-white/20 px-1.5 py-0.5 text-[10px] font-semibold">&lt; 5 min target ✓</span>}
      </div>
    </div>
  );
}
