// Agent Trace Viewer — makes the multi-agent architecture visible: the latest
// orchestrator→attribution→forecast→enforcement→advisory run as a timeline,
// plus a button that runs the whole pipeline live on stage.
import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { Panel } from "./ui";

type TraceStep = { node: string; ts: string; meta?: Record<string, unknown> };
type TraceRow = { city_id: string; total_latency_ms?: number; trace?: TraceStep[]; signal_ts?: string };
type AgentRun = { latency_ms?: number; trace?: TraceStep[] };

const NODE_LABELS: Record<string, string> = {
  orchestrator: "🧭 Orchestrator",
  attribution: "🔍 Attribution",
  forecast: "📈 Forecast",
  spike_gate: "🚦 Spike gate",
  enforcement: "⚖️ Enforcement",
  advisory: "📣 Advisory",
};

function Timeline({ steps }: { steps: TraceStep[] }) {
  if (!steps.length) return <div className="text-xs text-gray-400">no trace yet</div>;
  const t0 = new Date(steps[0].ts).getTime();
  return (
    <div className="mt-1 space-y-1">
      {steps.map((s, i) => {
        const dt = new Date(s.ts).getTime() - t0;
        const prev = i > 0 ? new Date(s.ts).getTime() - new Date(steps[i - 1].ts).getTime() : 0;
        return (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className="w-4 text-center text-gray-300">{i === steps.length - 1 ? "└" : "├"}</span>
            <span className="w-32 shrink-0">{NODE_LABELS[s.node] ?? s.node}</span>
            <span className="font-mono text-gray-500">+{(dt / 1000).toFixed(1)}s</span>
            {i > 0 && <span className="font-mono text-[10px] text-gray-400">({(prev / 1000).toFixed(1)}s step)</span>}
          </div>
        );
      })}
    </div>
  );
}

export default function TraceViewer({ city }: { city: string }) {
  const [steps, setSteps] = useState<TraceStep[]>([]);
  const [latency, setLatency] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    api<TraceRow[] | TraceRow>(`/traces?city=${city}&limit=1`)
      .then((d) => {
        const row = Array.isArray(d) ? d[0] : d;
        setSteps(row?.trace ?? []);
        setLatency(row?.total_latency_ms ?? null);
      })
      .catch(() => setSteps([]));
  }, [city]);

  useEffect(load, [load]);

  async function runLive() {
    setRunning(true);
    setErr(null);
    try {
      const r = await api<AgentRun>("/agent/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, query: "live judging demo run" }),
      });
      if (r.trace?.length) setSteps(r.trace);
      if (typeof r.latency_ms === "number") setLatency(r.latency_ms);
      else load();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <Panel
      title="Agent Pipeline"
      tag="A0"
      right={
        latency != null && latency > 0 ? (
          <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700">
            {(latency / 1000).toFixed(1)}s end-to-end
          </span>
        ) : undefined
      }
    >
      <div className="text-[10px] text-gray-400">last multi-agent run · detect → decide → issue</div>
      <Timeline steps={steps} />
      <button
        onClick={runLive}
        disabled={running}
        className="mt-2 w-full rounded-md bg-slate-800 px-2 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-slate-900 disabled:opacity-50"
      >
        {running ? "Agents running…" : "▶ Run agents live"}
      </button>
      {err && <div className="mt-1 text-[10px] text-red-600">{err}</div>}
    </Panel>
  );
}
