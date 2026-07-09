// E3 what-if simulator + E7 impact — pick an intervention, run the counterfactual,
// see ΔAQI and the cited health/carbon payoff. Consumes POST /simulate.
import { useState } from "react";
import { api } from "./api";
import ImpactCards, { type ImpactData } from "./ImpactCards";

type SimResult = ImpactData & {
  delta_aqi_by_cell?: Record<string, number>;
  confidence?: number;
  intervention?: { type: string; description?: string; ward?: string; horizon_h?: number };
};

const INTERVENTIONS = [
  { id: "waste_burn_ban", label: "Crop-residue / waste burn ban" },
  { id: "construction_halt", label: "Halt construction dust" },
  { id: "traffic_restriction", label: "Traffic restriction (odd-even)" },
  { id: "industrial_shutdown", label: "Industrial shutdown" },
  { id: "grap_stage3", label: "GRAP Stage III (combined)" },
];

export default function WhatIfPanel({ city }: { city: string }) {
  const [type, setType] = useState("waste_burn_ban");
  const [horizon, setHorizon] = useState(24);
  const [res, setRes] = useState<SimResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setErr(null);
    try {
      const data = await api<SimResult>("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, intervention_type: type, horizon_h: horizon }),
      });
      setRes(data);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const deltas = res ? Object.values(res.delta_aqi_by_cell ?? {}) : [];
  const avgDelta = deltas.length ? Math.round(deltas.reduce((a, b) => a + b, 0) / deltas.length) : 0;
  const bestDelta = deltas.length ? Math.min(...deltas) : 0;

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">
        What-if Simulator <span className="text-[10px] font-normal text-gray-400">E3 + E7</span>
      </div>
      <div className="mt-1 text-xs text-gray-600">
        Counterfactual over attribution × forecast, with cited health &amp; carbon impact.
      </div>

      <div className="mt-3 space-y-2">
        <label className="block text-xs">
          <span className="text-gray-500">Intervention</span>
          <select
            className="mt-1 w-full rounded border px-2 py-1 text-sm"
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            {INTERVENTIONS.map((i) => (
              <option key={i.id} value={i.id}>
                {i.label}
              </option>
            ))}
          </select>
        </label>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-500">Horizon</span>
          {[24, 48, 72].map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={`rounded px-2 py-1 ${horizon === h ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"}`}
            >
              +{h}h
            </button>
          ))}
        </div>
        <button
          onClick={run}
          disabled={loading}
          className="w-full rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {loading ? "Simulating…" : "Run simulation"}
        </button>
      </div>

      {err && <div className="mt-2 text-xs text-red-600">{err}</div>}

      {res && (
        <div className="mt-3 border-t border-gray-100 pt-2">
          {res.intervention?.description && (
            <div className="text-xs font-medium text-gray-800">{res.intervention.description}</div>
          )}
          {res.intervention?.ward && <div className="text-[11px] text-gray-500">{res.intervention.ward}</div>}
          <div className="mt-2 grid grid-cols-2 gap-x-2 gap-y-1 text-xs text-gray-700">
            <span>
              avg ΔAQI <b>{avgDelta}</b>
            </span>
            <span>
              best cell ΔAQI <b>{bestDelta}</b>
            </span>
            <span>
              cells affected <b>{deltas.length}</b>
            </span>
            <span>
              confidence <b>{res.confidence != null ? `${Math.round(res.confidence * 100)}%` : "—"}</b>
            </span>
          </div>
          <ImpactCards data={res} />
        </div>
      )}
    </div>
  );
}
