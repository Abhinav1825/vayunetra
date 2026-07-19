import { useEffect, useRef, useState } from "react";
import "maplibre-gl/dist/maplibre-gl.css";
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
import FairnessPanel from "./FairnessPanel";
import { Panel, SegBtn } from "./ui";

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

const CITY_STORE_KEY = "vayunetra-city";

function storedCity(): string {
  try {
    return localStorage.getItem(CITY_STORE_KEY) ?? "delhi";
  } catch {
    return "delhi"; // storage blocked (private mode) — default is fine
  }
}

export default function App() {
  const [cities, setCities] = useState<City[]>([]);
  const [active, setActive] = useState(storedCity);
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
    api<City[]>("/cities")
      .then((list) => {
        setCities(list);
        // Stored city might have been deleted (e.g. an onboarding demo city) —
        // fall back to Delhi rather than render an empty console.
        if (list.length && !list.some((c) => c.city_id === storedCity())) {
          setActive("delhi");
        }
      })
      .catch(() => setCities([]));
  }, []);

  // Refresh keeps you on the city you were on (Mumbai stays Mumbai).
  useEffect(() => {
    try {
      localStorage.setItem(CITY_STORE_KEY, active);
    } catch {
      /* storage blocked — refresh just defaults to delhi */
    }
  }, [active]);

  // Demo insurance: api.ts dispatches "api-fallback" when the backend is
  // unreachable and bundled fixtures were served instead — and "api-live" on
  // every successful response, so the banner clears itself the moment the
  // backend is actually awake (it used to stick forever after one slow call).
  useEffect(() => {
    const onFallback = () => setFallback(true);
    const onLive = () => setFallback(false);
    window.addEventListener("api-fallback", onFallback);
    window.addEventListener("api-live", onLive);
    return () => {
      window.removeEventListener("api-fallback", onFallback);
      window.removeEventListener("api-live", onLive);
    };
  }, []);

  // A ref (always current, unlike a captured `cell`/state closure) records
  // whether a story is already open for this city — so an async auto-open can
  // never overwrite a selection the user made while attribution was loading.
  const openedRef = useRef(false);

  useEffect(() => {
    setCell(null); // clear story on city switch
    openedRef.current = false; // allow one auto-open for the new city
  }, [active]);

  // Any explicit selection (map click / deselect) locks out auto-open.
  function handleSelect(c: AttrCell | null) {
    if (c) openedRef.current = true;
    setCell(c);
  }

  // Discoverability: the whole product is behind a hexagon click, so open one
  // for the judge on first load. Prefer a model-explained (SHAP) cell so the
  // first thing seen is the full "why", else the highest-confidence cell.
  function autoOpenBest(cells: AttrCell[]) {
    if (openedRef.current || !cells.length) return;
    const explained = cells.filter((c) => (c.evidence?.shap_drivers ?? []).length > 0);
    const pool = explained.length ? explained : cells;
    const best = [...pool].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))[0];
    if (best) {
      openedRef.current = true;
      setCell(best);
    }
  }

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
          onSelect={handleSelect}
          onCellsLoaded={autoOpenBest}
          showSources={showSources}
          coverageCells={coverage?.cells ?? []}
          coverageKind={coverageKind}
        />

        {/* Header overlays the map on all breakpoints */}
        <div className="absolute left-2 right-2 top-2 z-10 flex flex-wrap items-start justify-between gap-2 lg:left-4 lg:right-4 lg:top-4">
          <div className="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200/80 bg-white/95 p-2 shadow-lg shadow-slate-900/5 backdrop-blur">
            <a
              href="#/"
              title="Back to landing page"
              aria-label="Back to landing page"
              className="flex h-7 w-7 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
                <path d="M19 12H5m6-6l-6 6 6 6" />
              </svg>
            </a>
            <a href="#/" className="flex items-center gap-1.5 pr-1.5 text-sm font-extrabold tracking-tight text-slate-800">
              <span className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-sky-500 to-blue-700 text-[13px] font-black text-white shadow-sm">
                V
              </span>
              VayuNetra
            </a>
            <select
              className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
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
            <div className="flex rounded-lg bg-slate-100 p-0.5">
              {TABS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
                    tab === t ? "bg-blue-600 text-white shadow-sm" : "text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {TAB_LABEL[t]}
                </button>
              ))}
            </div>
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
            <button aria-label="Dismiss notice" className="ml-2 text-amber-500" onClick={() => setFallback(false)}>
              ✕
            </button>
          </div>
        )}

        <div className="absolute bottom-1 right-2 z-10 text-[11px] text-gray-500 lg:hidden">scroll for panels ↓</div>
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
        <Panel title="Map Layers">
          <div className="flex gap-1">
            {(["blame", "satellite", "coverage"] as MapMode[]).map((m) => (
              <SegBtn key={m} active={mode === m} onClick={() => setMode(m)} className="flex-1">
                {m === "blame" ? "Sources" : m === "satellite" ? "Sat NO2" : "PM2.5"}
              </SegBtn>
            ))}
          </div>

          {/* Independent overlay (not part of the blame/satellite radio) */}
          <button
            onClick={() => setShowSources((v) => !v)}
            className={`mt-2 flex w-full items-center justify-between rounded-md px-2 py-1 text-xs font-medium transition-colors ${
              showSources ? "bg-slate-800 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
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
              <div className="pt-1 text-[11px] text-gray-400">tip: click a hexagon for its full story</div>
            </div>
          )}
          {mode === "satellite" && (
            <div className="mt-3 text-xs text-gray-600">Sentinel-5P NO2 column. Blue is lower, red is higher.</div>
          )}
          {mode === "coverage" && (
            <div className="mt-3 text-xs">
              <div className="flex gap-1">
                {(["stations", "dense"] as const).map((k) => (
                  <SegBtn key={k} active={coverageKind === k} onClick={() => setCoverageKind(k)} className="flex-1">
                    {k === "stations" ? "Stations only" : "Dense 1km"}
                  </SegBtn>
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
              <div className="mt-1 text-[11px] text-gray-400">
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
        </Panel>

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
        {tab === "impact" && (
          <>
            <RoiPanel city={active} />
            <FairnessPanel />
          </>
        )}
      </div>
    </div>
  );
}
