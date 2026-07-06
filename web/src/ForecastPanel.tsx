import { useEffect, useState } from "react";
import { api } from "./api";
import { FORECAST_SKILL, SKILL_ASOF, pct } from "./metrics";

type FC = {
  h3_cell: string;
  horizon_h: number;
  value: number;
  pi_low: number;
  pi_high: number;
  persistence_value: number;
};

const HORIZONS = [24, 48, 72];
const SPIKE = 90; // µg/m³ PM2.5 — "very poor" threshold for a spike alert

// Forecast time-slider (Omkar's panel): horizon picker, model vs persistence, spike alerts.
export default function ForecastPanel({ city }: { city: string }) {
  const [horizon, setHorizon] = useState(24);
  const [rows, setRows] = useState<FC[]>([]);

  useEffect(() => {
    api<FC[]>(`/forecast?city=${city}&horizon=${horizon}`).then(setRows).catch(() => setRows([]));
  }, [city, horizon]);

  const skill = FORECAST_SKILL[city];

  const avg = rows.length ? Math.round(rows.reduce((s, r) => s + r.value, 0) / rows.length) : null;
  const avgPers = rows.length
    ? Math.round(rows.reduce((s, r) => s + r.persistence_value, 0) / rows.length)
    : null;
  const spikes = rows.filter((r) => r.value >= SPIKE);

  return (
    <div className="rounded-lg bg-white/95 p-3 shadow text-sm">
      <div className="font-semibold">Forecast — PM2.5</div>
      <div className="mt-2 flex gap-1">
        {HORIZONS.map((h) => (
          <button
            key={h}
            onClick={() => setHorizon(h)}
            className={`rounded px-2 py-1 text-xs ${
              horizon === h ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"
            }`}
          >
            +{h}h
          </button>
        ))}
      </div>

      {skill && (
        <div
          className="mt-2 rounded bg-indigo-50 px-2 py-1 text-[10px] leading-4 text-indigo-800"
          title={`Walk-forward backtest (3 folds, n=${skill.n}) on live data, ${SKILL_ASOF}. skill = 1 − RMSE_model/RMSE_baseline`}
        >
          backtested skill @{horizon}h: <b>{pct(skill.vsPersistence[horizon])}</b> vs persistence ·{" "}
          <b>{pct(skill.vsClimatology[horizon])}</b> vs climatology
        </div>
      )}

      {avg !== null ? (
        <div className="mt-2 text-xs text-gray-700">
          <div>
            city avg <b>{avg}</b> µg/m³ <span className="text-gray-400">(persistence {avgPers})</span>
          </div>
          {spikes.length > 0 && (
            <div className="mt-1 rounded bg-red-50 px-2 py-1 text-red-700">
              ⚠ spike alert: {spikes.length} cell{spikes.length > 1 ? "s" : ""} forecast ≥ {SPIKE} µg/m³
            </div>
          )}
          <div className="mt-1 max-h-40 space-y-0.5 overflow-auto">
            {rows.map((r) => (
              <div
                key={r.h3_cell}
                className={`flex justify-between font-mono ${r.value >= SPIKE ? "text-red-600" : ""}`}
              >
                <span>
                  {r.value >= SPIKE ? "⚠ " : ""}
                  {r.h3_cell.slice(0, 8)}
                </span>
                <span>
                  {Math.round(r.value)} [{Math.round(r.pi_low)}–{Math.round(r.pi_high)}]
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-2 text-xs text-gray-500">no forecast data</div>
      )}
    </div>
  );
}
