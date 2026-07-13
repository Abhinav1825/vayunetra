import { useEffect, useState } from "react";
import BlameMap, { type AttrCell, type CoverageCell, type MapMode } from "./BlameMap";
import ForecastPanel from "./ForecastPanel";
import { SOURCE_COLORS, PM25_LEGEND } from "./sources";
import { api } from "./api";
import AqiHeader from "./AqiHeader";
import CellStoryPanel from "./CellStoryPanel";
import LatencyWidget from "./LatencyWidget";
import EnforcementPanel from "./EnforcementPanel";
import CitizenPanel from "./CitizenPanel";
import ComparativePanel from "./ComparativePanel";
import CityIntelPanel from "./CityIntelPanel";
import TraceViewer from "./TraceViewer";
import WhatIfPanel from "./WhatIfPanel";
import RoiPanel from "./RoiPanel";

type LngLat = [number, number];
type GeoPoint = { coordinates: [number, number] };
type City = { city_id: string; name: string; center?: LngLat | GeoPoint; languages?: string[] };
type Tab = "action" | "citizen" | "compare" | "whatif" | "impact";

const TABS: Tab[] = ["action", "citizen", "compare", "whatif", "impact"];
const TAB_LABEL: Record<Tab, string> = {
  action: "Action",
  citizen: "Citizen",
  compare: "Compare",
  whatif: "What-if",
  impact: "ROI",
};

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
  const [showSources, setShowSources] = useState(false);
  const [tab, setTab] = useState<Tab>("action");
  const [cell, setCell] = useState<AttrCell | null>(null);
  const [fallback, setFallback] = useState(false);
  const [coverageKind, setCoverageKind] = useState<"stations" | "dense">("dense");
  const [coverage, setCoverage] = useState<{
    cells: CoverageCell[];
    n_cells?: number;
    n_stations?: number;
    validation?: { skill_vs_bilinear?: number };
  } | null>(null);

  useEffect(() => {
    api<City[]>("/cities").then(setCities).catch(() => setCities([]));
  }, []);

  // Demo insurance: api.ts dispatches this when the backend is unreachable
  // and bundled fixtures were served instead.
  useEffect(() => {
    const on = () => setFallback(true);
    window.addEventListener("api-fallback", on);
    return () => window.removeEventListener("api-fallback", on);
  }, []);

  useEffect(() => setCell(null), [active]); // clear story on city switch

  useEffect(() => {
    api<typeof coverage>(`/coverage?city=${active}`)
      .then(setCoverage)
      .catch(() => setCoverage(null));
  }, [active]);

  const city = cities.find((c) => c.city_id === active);
  const center = toLngLat(city?.center);

  return (
    <div className="relative h-full w-full overflow-y-auto bg-slate-100 lg:overflow-hidden">
      {/* Map — in-flow on mobile, full-bleed on desktop */}
      <div className="relative z-0 h-[46vh] w-full lg:absolute lg:inset-0 lg:h-full">
        <BlameMap
          city={active}
          center={center}
          mode={mode}
          selected={cell?.h3_cell}
          onSelect={setCell}
          showSources={showSources}
          coverageCells={coverage?.cells ?? []}
          coverageKind={coverageKind}
        />

        {/* Header overlays the map on all breakpoints */}
        <div className="absolute left-2 right-2 top-2 z-10 flex flex-wrap items-start justify-between gap-2 lg:left-4 lg:right-4 lg:top-4">
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
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`rounded px-3 py-1 text-sm ${tab === t ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"}`}
              >
                {TAB_LABEL[t]}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap items-start gap-2">
            <AqiHeader city={active} />
            <LatencyWidget city={active} />
          </div>
        </div>

        {fallback && (
          <div className="absolute inset-x-2 top-20 z-10 mx-auto max-w-md rounded-md bg-amber-100 px-3 py-1.5 text-center text-xs text-amber-900 shadow lg:top-24">
            ⚠ backend waking up — showing bundled demo snapshot.{" "}
            <button className="underline" onClick={() => window.location.reload()}>
              retry
            </button>
            <button className="ml-2 text-amber-500" onClick={() => setFallback(false)}>
              ✕
            </button>
          </div>
        )}

        <div className="absolute bottom-1 right-2 z-10 text-[9px] text-gray-500 lg:hidden">scroll for panels ↓</div>
      </div>

      {/* Left rail (desktop) / first stack (mobile) */}
      <div className="relative z-10 space-y-3 p-3 lg:absolute lg:bottom-4 lg:left-4 lg:top-24 lg:w-72 lg:overflow-auto lg:p-0 lg:pr-1">
        {cell && (
          <CellStoryPanel
            city={active}
            cell={cell}
            onClose={() => setCell(null)}
            onAct={() => setTab("action")} // keep the cell focused — enforcement sorts by it
          />
        )}
        <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
          <div className="font-semibold">Map Layers</div>
          <div className="mt-2 flex gap-1">
            {(["blame", "satellite", "coverage"] as MapMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 rounded px-2 py-1 text-xs ${
                  mode === m ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"
                }`}
              >
                {m === "blame" ? "Sources" : m === "satellite" ? "Sat NO2" : "PM2.5"}
              </button>
            ))}
          </div>

          {/* Independent overlay (not part of the blame/satellite radio) */}
          <button
            onClick={() => setShowSources((v) => !v)}
            className={`mt-2 flex w-full items-center justify-between rounded px-2 py-1 text-xs ${
              showSources ? "bg-slate-800 text-white" : "bg-gray-200 text-gray-700"
            }`}
          >
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-full border border-white bg-slate-900" />
              Detected sources
            </span>
            <span>{showSources ? "on" : "off"}</span>
          </button>

          {mode === "blame" && (
            <div className="mt-3 space-y-1 text-xs">
              {Object.entries(SOURCE_COLORS).map(([k, [r, g, b]]) => (
                <div key={k} className="flex items-center gap-2">
                  <span className="inline-block h-3 w-3 rounded" style={{ background: `rgb(${r},${g},${b})` }} />
                  <span>{k.replace("_", " ")}</span>
                </div>
              ))}
              <div className="pt-1 text-[10px] text-gray-400">tip: click a hexagon for its full story</div>
            </div>
          )}
          {mode === "satellite" && (
            <div className="mt-3 text-xs text-gray-600">Sentinel-5P NO2 column. Blue is lower, red is higher.</div>
          )}
          {mode === "coverage" && (
            <div className="mt-3 text-xs">
              <div className="flex gap-1">
                {(["stations", "dense"] as const).map((k) => (
                  <button
                    key={k}
                    onClick={() => setCoverageKind(k)}
                    className={`flex-1 rounded px-2 py-1 ${coverageKind === k ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"}`}
                  >
                    {k === "stations" ? "Stations only" : "Dense 1km"}
                  </button>
                ))}
              </div>
              <div className="mt-2 space-y-1">
                {PM25_LEGEND.map(([label, color]) => (
                  <div key={label} className="flex items-center gap-2">
                    <span className="inline-block h-3 w-3 rounded" style={{ background: color }} />
                    <span>{label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-1 text-[10px] text-gray-400">
                {coverage
                  ? `${coverage.n_stations ?? "~"} stations → ${coverage.n_cells ?? coverage.cells.length} cells · ${
                      typeof coverage.validation?.skill_vs_bilinear === "number"
                        ? `+${Math.round(coverage.validation.skill_vs_bilinear * 100)}% skill vs interpolation (synthetic-field validation)`
                        : "experimental — covariate-guided interpolation"
                    }`
                  : "loading field…"}
              </div>
            </div>
          )}
        </div>

        <ForecastPanel city={active} />
        <CityIntelPanel city={active} />
        <TraceViewer city={active} />
      </div>

      {/* Right rail (desktop) / second stack (mobile) */}
      <div className="relative z-10 space-y-3 p-3 pt-0 lg:absolute lg:bottom-4 lg:right-4 lg:top-24 lg:w-96 lg:overflow-auto lg:p-0 lg:pr-1">
        {tab === "action" && <EnforcementPanel city={active} focusCell={cell?.h3_cell ?? null} />}
        {tab === "citizen" && <CitizenPanel city={active} languages={city?.languages} />}
        {tab === "compare" && <ComparativePanel onSelectCity={setActive} />}
        {tab === "whatif" && <WhatIfPanel city={active} />}
        {tab === "impact" && <RoiPanel city={active} />}
      </div>
    </div>
  );
}
