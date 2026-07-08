import { useEffect, useState } from "react";
import { api } from "./api";
import { aqiCategory, pm25ToAqi } from "./aqi";
import { SOURCE_COLORS, dominantSource, type Shares } from "./sources";
import { DRIVER_LABELS, type AttrCell } from "./BlameMap";

type FC = { h3_cell: string; horizon_h: number; value: number; pi_low: number; pi_high: number };

const HORIZONS = [24, 48, 72];

/** The full story for one clicked hexagon: blame → forecast → act. */
export default function CellStoryPanel({
  city,
  cell,
  onClose,
  onAct,
}: {
  city: string;
  cell: AttrCell;
  onClose: () => void;
  onAct: () => void;
}) {
  const [fc, setFc] = useState<FC[] | null>(null);

  useEffect(() => {
    setFc(null);
    Promise.all(HORIZONS.map((h) => api<FC[]>(`/forecast?city=${city}&horizon=${h}`).catch(() => [] as FC[])))
      .then((all) => setFc(all.flat().filter((r) => r.h3_cell === cell.h3_cell)))
      .catch(() => setFc([]));
  }, [city, cell.h3_cell]);

  const shares = Object.entries(cell.shares as Shares).sort((a, b) => b[1] - a[1]);
  const dom = dominantSource(cell.shares);
  const ev = cell.evidence ?? {};

  return (
    <div className="rounded-lg border-2 border-blue-500 bg-white/95 p-3 text-sm shadow-lg">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wide text-blue-600">Cell story</div>
          <div className="font-mono text-xs text-gray-500">{cell.h3_cell}</div>
        </div>
        <button onClick={onClose} className="rounded px-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700">
          ✕
        </button>
      </div>

      {/* 1 — Blame */}
      <div className="mt-2">
        <div className="text-xs font-semibold text-gray-700">
          1 · Who's to blame — <span className="capitalize">{dom.replace("_", " ")}</span>
          <span className="ml-1 font-normal text-gray-400">conf {Math.round(cell.confidence * 100)}%</span>
        </div>
        <div className="mt-1 space-y-1">
          {shares.map(([k, v]) => {
            const [r, g, b] = SOURCE_COLORS[k as keyof typeof SOURCE_COLORS] ?? [120, 120, 120];
            return (
              <div key={k} className="flex items-center gap-2 text-xs">
                <span className="w-24 shrink-0 capitalize text-gray-600">{k.replace("_", " ")}</span>
                <div className="h-2 flex-1 rounded bg-gray-100">
                  <div
                    className="h-2 rounded"
                    style={{ width: `${Math.round(v * 100)}%`, background: `rgb(${r},${g},${b})` }}
                  />
                </div>
                <span className="w-8 text-right font-mono text-gray-500">{Math.round(v * 100)}%</span>
              </div>
            );
          })}
        </div>
        {(ev.shap_drivers ?? []).length > 0 && (
          <div className="mt-1.5 rounded bg-emerald-50 px-1.5 py-1 text-[10px] text-emerald-800">
            <span className="font-semibold">SHAP drivers (µg/m³):</span>{" "}
            {ev.shap_drivers!.map((d) => `${DRIVER_LABELS[d.feature] ?? d.feature} +${d.contribution.toFixed(1)}`).join(" · ")}
            {typeof ev.model_r2 === "number" && <span className="text-emerald-500"> · model R² {ev.model_r2}</span>}
          </div>
        )}
        {(ev.no2 !== undefined || ev.no2_sat !== undefined) && (
          <div className="mt-1 text-[10px] text-gray-400">
            evidence: NO₂ {ev.no2 ?? "–"} · sat {typeof ev.no2_sat === "number" ? ev.no2_sat.toExponential(1) : "–"} ·
            PM10/PM2.5 {ev.pm10_pm25_ratio ?? "–"}
          </div>
        )}
      </div>

      {/* 2 — Forecast */}
      <div className="mt-3">
        <div className="text-xs font-semibold text-gray-700">2 · Where it's heading</div>
        {fc === null ? (
          <div className="mt-1 h-8 animate-pulse rounded bg-gray-100" />
        ) : fc.length ? (
          <div className="mt-1 flex gap-2">
            {HORIZONS.map((h) => {
              const r = fc.find((x) => x.horizon_h === h);
              if (!r) return null;
              const cat = aqiCategory(pm25ToAqi(r.value));
              return (
                <div key={h} className="flex-1 rounded-md border border-gray-200 p-1.5 text-center">
                  <div className="text-[10px] text-gray-400">+{h}h</div>
                  <div className="text-sm font-bold" style={{ color: cat.color }}>
                    {Math.round(r.value)}
                  </div>
                  <div className="text-[9px] text-gray-400">
                    [{Math.round(r.pi_low)}–{Math.round(r.pi_high)}]
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="mt-1 text-xs text-gray-400">no per-cell forecast (see city panel)</div>
        )}
      </div>

      {/* 3 — Act */}
      <button
        onClick={onAct}
        className="mt-3 w-full rounded bg-blue-600 px-2 py-1.5 text-xs font-semibold text-white hover:bg-blue-700"
      >
        3 · Act — view enforcement actions →
      </button>
    </div>
  );
}
