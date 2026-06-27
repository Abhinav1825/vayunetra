import { useEffect, useState } from "react";
import BlameMap from "./BlameMap";
import ForecastPanel from "./ForecastPanel";
import { SOURCE_COLORS } from "./sources";
import { api } from "./api";

type City = { city_id: string; name: string; center: [number, number] };

export default function App() {
  const [cities, setCities] = useState<City[]>([]);
  const [active, setActive] = useState("delhi");

  useEffect(() => {
    api<City[]>("/cities").then(setCities).catch(() => setCities([]));
  }, []);

  const city = cities.find((c) => c.city_id === active);
  const center: [number, number] = city?.center ?? [77.21, 28.61];

  return (
    <div className="relative h-full w-full">
      <BlameMap city={active} center={center} />

      <div className="absolute left-4 top-4 w-64 space-y-3">
        <div className="rounded-lg bg-white/95 p-3 shadow">
          <div className="text-sm font-semibold">VayuNetra — Blame Map</div>
          <select
            className="mt-2 w-full rounded border px-2 py-1 text-sm"
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
          <div className="mt-3 space-y-1 text-xs">
            {Object.entries(SOURCE_COLORS).map(([k, [r, g, b]]) => (
              <div key={k} className="flex items-center gap-2">
                <span
                  className="inline-block h-3 w-3 rounded"
                  style={{ background: `rgb(${r},${g},${b})` }}
                />
                <span>{k.replace("_", " ")}</span>
              </div>
            ))}
          </div>
        </div>

        <ForecastPanel city={active} />
      </div>
    </div>
  );
}
