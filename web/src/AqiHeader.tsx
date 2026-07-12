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
        ws.onopen = () => setOn(true);
        ws.onclose = () => {
          setOn(false);
          if (!closed) retry = setTimeout(connect, 15_000);
        };
        ws.onerror = () => ws.close();
      } catch {
        setOn(false);
      }
    }
    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      wsRef.current?.close();
    };
  }, []);

  return (
    <span className="flex items-center gap-1 text-[10px] font-medium" title={on ? "Live feed connected" : "Live feed offline"}>
      <span className={`inline-block h-2 w-2 rounded-full ${on ? "animate-pulse bg-emerald-500" : "bg-gray-300"}`} />
      <span className={on ? "text-emerald-600" : "text-gray-400"}>{on ? "LIVE" : "OFF"}</span>
    </span>
  );
}

type Compound = { level: "none" | "watch" | "alert"; tmax_next24_c?: number | null };

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
          </div>
        </>
      ) : (
        <div className="text-xs text-gray-500">no AQI data</div>
      )}
    </div>
  );
}
