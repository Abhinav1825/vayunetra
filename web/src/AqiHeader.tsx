import { useEffect, useRef, useState } from "react";
import { api, API_BASE, API_TOKEN } from "./api";
import { agoLabel, aqiCategory, pm25ToAqi } from "./aqi";

type AqiRow = { h3_cell: string; pm25?: number; value?: number; aqi?: number; ts?: string };

/** Pulsing dot showing the /live WebSocket connection state. */
function LiveDot() {
  const [on, setOn] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout>;
    function connect() {
      const base = API_BASE.replace(/^http/, "ws");
      const q = API_TOKEN ? `?token=${encodeURIComponent(API_TOKEN)}` : "";
      try {
        const ws = new WebSocket(`${base}/live${q}`);
        wsRef.current = ws;
        ws.onopen = () => {
          if (closed) {
            ws.close(); // unmounted while connecting (StrictMode dev remount)
            return;
          }
          setOn(true);
        };
        ws.onclose = () => {
          if (closed) return; // no setState / retries after unmount
          setOn(false);
          retry = setTimeout(connect, 15_000);
        };
        ws.onerror = () => {
          if (ws.readyState === WebSocket.OPEN) ws.close();
        };
      } catch {
        setOn(false);
      }
    }
    connect();
    return () => {
      // Never close a CONNECTING socket (browsers log a warning); let onopen do it.
      closed = true;
      clearTimeout(retry);
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) ws.close();
    };
  }, []);

  return (
    <span className="flex items-center gap-1 text-[10px] font-medium" title={on ? "Live feed connected" : "Live feed offline"}>
      <span className={`inline-block h-2 w-2 rounded-full ${on ? "animate-pulse bg-emerald-500" : "bg-gray-300"}`} />
      <span className={on ? "text-emerald-600" : "text-gray-400"}>{on ? "LIVE" : "OFF"}</span>
    </span>
  );
}

type Compound = {
  level: "none" | "watch" | "alert";
  tmax_next24_c?: number | null;
  grap?: { stage: number; label: string; trigger_aqi?: number } | null;
  dust_traffic?: { count: number } | null;
};

const GRAP_ROMAN = ["", "I", "II", "III", "IV"];

/** Hero AQI badge: worst-cell CPCB AQI, category color, data freshness. */
export default function AqiHeader({ city }: { city: string }) {
  const [rows, setRows] = useState<AqiRow[] | null>(null);
  const [compound, setCompound] = useState<Compound | null>(null);

  useEffect(() => {
    setRows(null);
    api<AqiRow[]>(`/aqi/current?city=${city}`).then(setRows).catch(() => setRows([]));
    api<Compound>(`/alerts/compound?city=${city}`).then(setCompound).catch(() => setCompound(null));
  }, [city]);

  if (rows === null) {
    return <div className="h-14 w-44 animate-pulse rounded-lg bg-white/80 shadow" />;
  }

  const pm = rows
    .map((r) => (typeof r.pm25 === "number" ? r.pm25 : typeof r.value === "number" ? r.value : null))
    .filter((v): v is number => v !== null);
  const worst = pm.length ? Math.max(...pm) : null;
  const aqi = worst !== null ? pm25ToAqi(worst) : null;
  const cat = aqi !== null ? aqiCategory(aqi) : null;
  const latest = rows.map((r) => r.ts).filter(Boolean).sort().pop();

  return (
    <div className="flex items-center gap-3 rounded-lg bg-white/95 px-3 py-2 shadow">
      {aqi !== null && cat ? (
        <>
          <div
            className="flex h-12 min-w-16 flex-col items-center justify-center rounded-md px-2"
            style={{ background: cat.color, color: cat.text }}
          >
            <span className="text-xl font-extrabold leading-none">{aqi}</span>
            <span className="text-[9px] font-semibold uppercase tracking-wide">AQI</span>
          </div>
          <div className="text-xs">
            <div className="text-sm font-bold" style={{ color: cat.color }}>
              {cat.label}
            </div>
            <div className="text-gray-500">
              worst cell · PM2.5 {Math.round(worst!)} µg/m³
            </div>
            <div className="flex items-center gap-2 text-gray-400">
              <span>data {agoLabel(latest)}</span>
              <LiveDot />
            </div>
            {compound && compound.level !== "none" && (
              <div
                className={`mt-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                  compound.level === "alert" ? "bg-red-700 text-white" : "bg-orange-500 text-white"
                }`}
                title="Compound risk: heat amplifies PM mortality and drives ozone formation (IMD heatwave criteria x CPCB bands)"
              >
                🔥 HEAT×SMOG {compound.level.toUpperCase()}
                {typeof compound.tmax_next24_c === "number" && ` · ${Math.round(compound.tmax_next24_c)}°C`}
              </div>
            )}
            {compound?.grap && (
              <div
                className="mt-0.5 rounded bg-purple-700 px-1.5 py-0.5 text-[10px] font-bold text-white"
                title={`Forecast-triggered graded response: 24h forecast AQI ${compound.grap.trigger_aqi ?? "--"} enters the CAQM GRAP Stage ${GRAP_ROMAN[compound.grap.stage]} band (statutory in Delhi-NCR; advisory playbook elsewhere) — a day before observed AQI would trigger it`}
              >
                ⚖️ GRAP STAGE {GRAP_ROMAN[compound.grap.stage]} · forecast-triggered
              </div>
            )}
            {compound?.dust_traffic && compound.dust_traffic.count > 0 && (
              <div
                className="mt-0.5 rounded bg-amber-600 px-1.5 py-0.5 text-[10px] font-bold text-white"
                title="Cells where construction dust AND traffic are both major contributors (attribution shares ≥25% each) — traffic resuspends construction dust, so these corridors escalate fastest"
              >
                🚧 DUST×TRAFFIC · {compound.dust_traffic.count} cell{compound.dust_traffic.count > 1 ? "s" : ""}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="text-xs text-gray-500">no AQI data</div>
      )}
    </div>
  );
}
