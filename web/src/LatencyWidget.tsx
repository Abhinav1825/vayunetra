import { useEffect, useState } from "react";
import { api } from "./api";

type Trace = {
  city_id: string;
  total_latency_ms: number;
  signal_ts: string;
  advisory_ts: string;
};

function fmt(ms?: number) {
  if (!ms || ms <= 0) return "--";
  if (ms < 10_000) return `${(ms / 1000).toFixed(1)}s`; // never show a fake-looking "0s"
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
    <div
      className="rounded-lg bg-emerald-600 px-4 py-2 text-white shadow"
      title="Multi-agent pipeline wall time: spike detected → attribution → forecast → enforcement + advisory issued. Target < 5 min."
    >
      <div className="text-[10px] font-semibold uppercase tracking-wider text-emerald-100">⚡ Signal → Action</div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-extrabold leading-tight">{fmt(ms)}</span>
        {under5 && <span className="rounded bg-white/20 px-1.5 py-0.5 text-[10px] font-semibold">&lt; 5 min target ✓</span>}
      </div>
      <div className="text-[9px] text-emerald-200">agent pipeline: detect → decide → issue</div>
    </div>
  );
}
