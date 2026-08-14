import { useEffect, useState } from "react";
<<<<<<< HEAD
import { Bar, BarChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "./api";
import { inr, intfmt } from "./format";
import { EmptyState, Panel } from "./ui";
=======
import { api } from "./api";
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729

type CityCard = {
  city_id: string;
  name: string;
  current_pm25: number;
  forecast_24h_pm25: number;
  trend: string;
  dominant_source: string;
  signature_match: string;
  playbook: string[];
<<<<<<< HEAD
  compliance?: { total: number; proposed: number; approved: number; dispatched: number; dismissed: number };
  health?: {
    annual_pm25: number;
    attributable_deaths_per_year: number;
    annual_health_burden_inr: number;
  };
};

type Comparison = {
  summary: {
    cities_compared: number;
    highest_risk_city: string;
    highest_burden_city?: string;
    shared_pattern: string;
  };
=======
};

type Comparison = {
  summary: { cities_compared: number; highest_risk_city: string; shared_pattern: string };
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
  cities: CityCard[];
};

export default function ComparativePanel({ onSelectCity }: { onSelectCity: (city: string) => void }) {
  const [data, setData] = useState<Comparison | null>(null);
<<<<<<< HEAD
  const [failed, setFailed] = useState(false);

  function load() {
    setFailed(false);
    api<Comparison>("/comparison").then(setData).catch(() => setFailed(true));
  }
  useEffect(load, []);

  const chart = (data?.cities ?? []).map((c) => ({
    name: c.name,
    "avg now": Math.round(c.current_pm25),
    "+24h": Math.round(c.forecast_24h_pm25),
  }));

  return (
    <Panel title="Multi-City Compare">
      {failed && !data ? (
        <EmptyState message="Couldn't load the multi-city comparison." tone="error" onRetry={load} />
      ) : (
        <>
      <div className="text-xs text-gray-600">
        {data?.summary.shared_pattern ?? "Loading city comparison…"}
        <span className="ml-1 text-slate-400">· city-average PM2.5</span>
      </div>

      {chart.length > 0 && (
        <div className="mt-2 h-32">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart} margin={{ top: 4, right: 4, left: -10, bottom: -6 }} barGap={2}>
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 9, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={34} />
              <Tooltip
                formatter={(v) => `${v ?? "–"} µg/m³`}
                labelStyle={{ fontSize: 11 }}
                contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }}
                cursor={{ fill: "#f1f5f9" }}
              />
              <Legend wrapperStyle={{ fontSize: 10 }} iconSize={8} />
              <Bar dataKey="avg now" fill="#64748b" radius={[3, 3, 0, 0]} maxBarSize={26} />
              <Bar dataKey="+24h" fill="#2563eb" radius={[3, 3, 0, 0]} maxBarSize={26} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="mt-2 space-y-2">
=======

  useEffect(() => {
    api<Comparison>("/comparison").then(setData).catch(() => setData(null));
  }, []);

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">Multi-City Compare</div>
      <div className="mt-1 text-xs text-gray-600">{data?.summary.shared_pattern ?? "Comparison unavailable"}</div>
      <div className="mt-3 space-y-2">
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
        {data?.cities.map((c) => (
          <button
            key={c.city_id}
            onClick={() => onSelectCity(c.city_id)}
<<<<<<< HEAD
            className="block w-full rounded-lg border border-slate-200 p-2.5 text-left transition-colors hover:border-blue-300 hover:bg-blue-50"
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800">{c.name}</span>
              <span
                className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${
                  c.trend === "deteriorating" ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"
                }`}
              >
                {c.trend}
              </span>
            </div>
            <div className="mt-1 grid grid-cols-2 gap-x-2 gap-y-0.5 text-xs text-gray-600">
              <span>
                avg <b className="text-slate-800">{Math.round(c.current_pm25)}</b> µg/m³
              </span>
              <span>
                +24h <b className="text-slate-800">{Math.round(c.forecast_24h_pm25)}</b> µg/m³
              </span>
              <span className="capitalize">{c.dominant_source.replace("_", " ")}</span>
              <span>{c.signature_match}</span>
            </div>
            {c.health && (
              <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-gray-500">
                <span>~{intfmt(c.health.attributable_deaths_per_year)} deaths/yr</span>
                <span>·</span>
                <span>{inr(c.health.annual_health_burden_inr)}/yr</span>
                {data?.summary.highest_burden_city === c.city_id && (
                  <span className="rounded bg-red-100 px-1 text-red-700">highest burden</span>
                )}
              </div>
            )}
            <div className="mt-1.5 text-xs text-gray-600">→ {c.playbook[0]}</div>
            {c.compliance && c.compliance.total > 0 && (
              <div className="mt-1.5 border-t border-slate-100 pt-1.5 text-[11px] text-gray-500">
                <span className="font-medium text-gray-600">Compliance:</span> {c.compliance.total} recommendations
                {c.compliance.approved > 0 && <> · {c.compliance.approved} approved</>}
                {c.compliance.dispatched > 0 && <> · {c.compliance.dispatched} dispatched</>}
                {c.compliance.dismissed > 0 && <> · {c.compliance.dismissed} dismissed</>}
                {c.compliance.proposed === c.compliance.total && <> — all awaiting officer review</>}
              </div>
            )}
          </button>
        ))}
      </div>
        </>
      )}
    </Panel>
=======
            className="block w-full rounded-md border border-gray-200 p-2 text-left hover:border-blue-300 hover:bg-blue-50"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{c.name}</span>
              <span className="text-xs text-gray-500">{c.trend}</span>
            </div>
            <div className="mt-1 grid grid-cols-2 gap-2 text-xs text-gray-700">
              <span>now {Math.round(c.current_pm25)} ug/m3</span>
              <span>+24h {Math.round(c.forecast_24h_pm25)} ug/m3</span>
              <span>{c.dominant_source.replace("_", " ")}</span>
              <span>{c.signature_match}</span>
            </div>
            <div className="mt-2 text-xs text-gray-600">{c.playbook[0]}</div>
          </button>
        ))}
      </div>
    </div>
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
  );
}
