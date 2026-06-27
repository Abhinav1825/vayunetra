import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { api } from "./api";

type City = { city_id: string; name: string; center: [number, number] };

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [cities, setCities] = useState<City[]>([]);
  const [active, setActive] = useState("delhi");

  // init the base map once (centered on Delhi)
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://demotiles.maplibre.org/style.json", // free, no token
      center: [77.21, 28.61],
      zoom: 9,
    });
  }, []);

  // load onboarded cities for the switcher (falls back silently in DEMO_MODE)
  useEffect(() => {
    api<City[]>("/cities").then(setCities).catch(() => setCities([]));
  }, []);

  // fly to the active city
  useEffect(() => {
    const c = cities.find((x) => x.city_id === active);
    if (c && mapRef.current) mapRef.current.flyTo({ center: c.center, zoom: 9 });
  }, [active, cities]);

  return (
    <div className="relative h-full w-full">
      <div ref={mapContainer} className="h-full w-full" />
      <div className="absolute left-4 top-4 rounded-lg bg-white/90 p-3 shadow">
        <div className="text-sm font-semibold">VayuNetra — Authority Console</div>
        <select
          className="mt-2 rounded border px-2 py-1 text-sm"
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
        <div className="mt-1 max-w-xs text-xs text-gray-500">
          Base shell (F4 — Sejal owns the panels). Blame map (Omkar), forecast slider
          (Omkar), enforcement worklist (Abhinav) plug in here as Deck.gl layers / panels.
        </div>
      </div>
    </div>
  );
}
