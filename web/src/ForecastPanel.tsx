import { useEffect, useState } from "react";
import { api } from "./api";

type FC = {
  h3_cell: string;
  horizon_h: number;
  value: number;
  pi_low: number;
  pi_high: number;
  persistence_value: number;
};

const HORIZONS = [24, 48, 72];

// Forecast time-slider (Omkar's panel): pick a horizon, see model vs persistence.
// Reads GET /forecast?city&horizon.
export default function ForecastPanel({ city }: { city: string }) {
  const [horizon, setHorizon] = useState(24);
  const [rows, setRows] = useState<FC[]>([]);

  useEffect(() => {
    api<FC[]>(`/forecast?city=${city}&horizon=${horizon}`).then(setRows).catch(() => setRows([]));
  }, [city, horizon]);

  const avg = rows.length ? Math.round(rows.reduce((s, r) => s + r.value, 0) / rows.length) : null;
  const avgPers = rows.length
    ? Math.round(rows.reduce((s, r) => s + r.persistence_value, 0) / rows.length)
    : null;

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
      {avg !== null ? (
        <div className="mt-2 text-xs text-gray-700">
          <div>
            city avg <b>{avg}</b> µg/m³{" "}
            <span className="text-gray-400">(persistence {avgPers})</span>
          </div>
          <div className="mt-1 max-h-40 space-y-0.5 overflow-auto">
            {rows.map((r) => (
              <div key={r.h3_cell} className="flex justify-between font-mono">
                <span>{r.h3_cell.slice(0, 8)}</span>
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
