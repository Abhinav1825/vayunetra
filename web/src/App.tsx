import { useEffect, useState } from "react";
import BlameMap, { type MapMode } from "./BlameMap";
import ForecastPanel from "./ForecastPanel";
import { SOURCE_COLORS } from "./sources";
import { api } from "./api";
import LatencyWidget from "./LatencyWidget";
import EnforcementPanel from "./EnforcementPanel";
import CitizenPanel from "./CitizenPanel";
import ComparativePanel from "./ComparativePanel";
import CityIntelPanel from "./CityIntelPanel";

type LngLat = [number, number];
type GeoPoint = { coordinates: [number, number] };
type City = { city_id: string; name: string; center?: LngLat | GeoPoint; languages?: string[] };
type Tab = "action" | "citizen" | "compare";

const DELHI: LngLat = [77.21, 28.61];

// /cities returns `center` as a plain [lng,lat] (demo fixtures) OR a GeoJSON
// Point (live PostGIS). Normalize both to a finite [lng,lat] for MapLibre.
function toLngLat(center: City["center"]): LngLat {
  const co = Array.isArray(center) ? center : center?.coordinates;
  if (Array.isArray(co) && Number.isFinite(co[0]) && Number.isFinite(co[1])) {
    return [co[0], co[1]];
  }
  return DELHI;
}

export default function App() {
  const [cities, setCities] = useState<City[]>([]);
  const [active, setActive] = useState("delhi");
  const [mode, setMode] = useState<MapMode>("blame");
  const [tab, setTab] = useState<Tab>("action");

  useEffect(() => {
    api<City[]>("/cities").then(setCities).catch(() => setCities([]));
  }, []);

  const city = cities.find((c) => c.city_id === active);
  const center = toLngLat(city?.center);

  return (
    <div className="relative h-full w-full overflow-hidden bg-slate-100">
      <BlameMap city={active} center={center} mode={mode} />

      <div className="absolute left-4 right-4 top-4 flex flex-wrap items-start justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2 rounded-lg bg-white/95 p-2 shadow">
          <div className="px-2 text-sm font-semibold">VayuNetra</div>
          <select
            className="rounded border px-2 py-1 text-sm"
            value={active}
            onChange={(e) => setActive(e.target.value)}
          >
            {cities.length === 0 && <option value="delhi">Delhi</option>}
            {cities.map((c) => (
              <option key={c.city_id} value={c.city_id}>
                {c.name}
              </option>
            ))}
          </select>
          {(["action", "citizen", "compare"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded px-3 py-1 text-sm ${tab === t ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"}`}
            >
              {t}
            </button>
          ))}
        </div>
        <LatencyWidget city={active} />
      </div>

      <div className="absolute bottom-4 left-4 top-24 w-72 space-y-3 overflow-auto pr-1">
        <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
          <div className="font-semibold">Map Layers</div>
          <div className="mt-2 flex gap-1">
            {(["blame", "satellite"] as MapMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 rounded px-2 py-1 text-xs ${
                  mode === m ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"
                }`}
              >
                {m === "blame" ? "Sources" : "Satellite NO2"}
              </button>
            ))}
          </div>

          {mode === "blame" ? (
            <div className="mt-3 space-y-1 text-xs">
              {Object.entries(SOURCE_COLORS).map(([k, [r, g, b]]) => (
                <div key={k} className="flex items-center gap-2">
                  <span className="inline-block h-3 w-3 rounded" style={{ background: `rgb(${r},${g},${b})` }} />
                  <span>{k.replace("_", " ")}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-3 text-xs text-gray-600">
              Sentinel-5P NO2 column. Blue is lower, red is higher.
            </div>
          )}
        </div>

        <ForecastPanel city={active} />
        <CityIntelPanel city={active} />
      </div>

      <div className="absolute bottom-4 right-4 top-24 w-96 space-y-3 overflow-auto pr-1">
        {tab === "action" && <EnforcementPanel city={active} />}
        {tab === "citizen" && <CitizenPanel city={active} languages={city?.languages} />}
        {tab === "compare" && <ComparativePanel onSelectCity={setActive} />}
      </div>
    </div>
  );
}
