import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { ScatterplotLayer } from "@deck.gl/layers";
import { api } from "./api";
import { colorFor, dominantSource, pm25Color, satColor, type Shares } from "./sources";

export type ShapDriver = { feature: string; source: string; contribution: number };

// Emission sources plotted as an optional overlay (registry/OSM today; E1 CV
// detections drop in later via the same shape with source_origin="cv_detected").
export type EmissionSource = {
  id: string;
  name: string;
  type: string;
  source_origin?: string;
  detection_confidence?: number;
  coordinates: [number, number];
};

// The live API returns PostGIS GeoJSON (`geom.coordinates`); fixtures use a flat
// `coordinates`. Normalize both so the overlay renders on real data too.
type RawSource = Omit<EmissionSource, "coordinates"> & {
  coordinates?: [number, number];
  geom?: { coordinates?: [number, number] } | null;
};

function normalizeSources(rows: RawSource[]): EmissionSource[] {
  return rows
    .map((s) => ({ ...s, coordinates: s.coordinates ?? s.geom?.coordinates }))
    .filter((s): s is EmissionSource => Array.isArray(s.coordinates) && s.coordinates.length === 2);
}

// E2 dense-coverage cell: dense (downscaled ~1 km) + sparse (stations-only) PM2.5.
export type CoverageCell = {
  h3_cell: string;
  pm25: number;
  pm25_stations: number;
  uncertainty: number;
};

export type AttrCell = {
  h3_cell: string;
  shares: Shares;
  confidence: number;
  evidence?: {
    no2?: number;
    no2_sat?: number;
    pm10_pm25_ratio?: number;
    shap_drivers?: ShapDriver[];
    model_r2?: number;
    top_signals?: string[];
    shrunk_toward?: string;
    [k: string]: unknown;
  };
};

// readable labels for SHAP driver features
export const DRIVER_LABELS: Record<string, string> = {
  no2: "NO₂",
  co: "CO",
  so2: "SO₂",
  no2_sat: "satellite NO₂",
  pm10_pm25_ratio: "PM10/PM2.5 ratio",
  fire: "fire (FIRMS)",
  advected_pm25: "upwind PM2.5",
};

export type MapMode = "blame" | "satellite" | "coverage";

// Clean light raster basemap (CARTO, free, no API key) — colored hexagons pop on it.
const BASEMAP = {
  version: 8,
  sources: {
    carto: {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution: "© OpenStreetMap © CARTO",
    },
  },
  layers: [{ id: "carto", type: "raster", source: "carto" }],
} as unknown as maplibregl.StyleSpecification;

const ZOOM = 10.5;

function tooltip(c: AttrCell, mode: MapMode) {
  if (mode === "satellite") {
    const v = c.evidence?.no2_sat ?? 0;
    return { html: `satellite NO₂ column<br/><b>${v.toExponential(2)}</b> mol/m²`, style: { fontSize: "12px" } };
  }
  const top = Object.entries(c.shares)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([k, v]) => `${k.replace("_", " ")} ${Math.round(v * 100)}%`)
    .join("<br/>");
  const ev = c.evidence ?? {};
  const drivers = (ev.shap_drivers ?? [])
    .map((d) => `${DRIVER_LABELS[d.feature] ?? d.feature} +${d.contribution.toFixed(1)}`)
    .join(" · ");
  return {
    html:
      `<b>${dominantSource(c.shares).replace("_", " ")}</b> · conf ${c.confidence}<br/>${top}` +
      (drivers ? `<br/><span style="color:#4ade80">SHAP drivers: ${drivers} µg/m³</span>` : "") +
      `<br/><span style="color:#888">NO₂ ${ev.no2 ?? "–"} · sat ${(ev.no2_sat ?? 0).toExponential?.(1) ?? "–"} · PM10/PM2.5 ${ev.pm10_pm25_ratio ?? "–"}</span>`,
    style: { fontSize: "12px" },
  };
}

export default function BlameMap({
  city,
  center,
  mode,
  selected,
  onSelect,
  onCellsLoaded,
  showSources = false,
  coverageCells = [],
  coverageKind = "dense",
}: {
  city: string;
  center: [number, number];
  mode: MapMode;
  selected?: string | null;
  onSelect?: (cell: AttrCell | null) => void;
  onCellsLoaded?: (cells: AttrCell[]) => void;
  showSources?: boolean;
  coverageCells?: CoverageCell[];
  coverageKind?: "stations" | "dense";
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [cells, setCells] = useState<AttrCell[]>([]);
  const [sources, setSources] = useState<EmissionSource[]>([]);

  const [mapError, setMapError] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    try {
      const map = new maplibregl.Map({ container: containerRef.current, style: BASEMAP, center, zoom: ZOOM });
      const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
      map.addControl(overlay);
      map.on("error", () => {}); // tile fetch failures shouldn't spam the console
      mapRef.current = map;
      overlayRef.current = overlay;
    } catch {
      // WebGL unavailable (headless VM, blocked GPU) — panels still work.
      setMapError(true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const [lng, lat] = center;
    if (Number.isFinite(lng) && Number.isFinite(lat)) {
      mapRef.current?.flyTo({ center, zoom: ZOOM });
    }
  }, [center]);

  useEffect(() => {
    api<AttrCell[]>(`/attribution?city=${city}`)
      .then((c) => {
        setCells(c);
        onCellsLoaded?.(c);
      })
      .catch(() => setCells([]));
  }, [city]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    api<{ emission_sources?: RawSource[] }>(`/static-layers?city=${city}`)
      .then((d) => setSources(normalizeSources(d.emission_sources ?? [])))
      .catch(() => setSources([]));
  }, [city]);

  useEffect(() => {
    const blame = new H3HexagonLayer<AttrCell>({
      id: "blame",
      data: cells,
      getHexagon: (d) => d.h3_cell,
      getFillColor: (d) => (mode === "satellite" ? satColor(d.evidence?.no2_sat ?? 0) : colorFor(d.shares)),
      getLineColor: (d) => (d.h3_cell === selected ? [30, 64, 175, 255] : [255, 255, 255, 90]),
      getLineWidth: (d) => (d.h3_cell === selected ? 3 : 1),
      lineWidthMinPixels: 1,
      lineWidthUnits: "pixels",
      extruded: false,
      pickable: true,
      onClick: ({ object }: { object?: AttrCell }) => {
        onSelect?.(object && object.h3_cell !== selected ? object : null);
        return true;
      },
      updateTriggers: { getFillColor: mode, getLineColor: selected, getLineWidth: selected },
    });

    // E2 dense-coverage PM2.5 field — replaces the blame layer when active.
    const coverage = new H3HexagonLayer<CoverageCell>({
      id: "coverage",
      data: coverageCells,
      getHexagon: (d) => d.h3_cell,
      getFillColor: (d) => pm25Color(coverageKind === "stations" ? d.pm25_stations : d.pm25),
      stroked: false,
      extruded: false,
      pickable: true,
      updateTriggers: { getFillColor: coverageKind },
    });

    type AnyLayer =
      | H3HexagonLayer<AttrCell>
      | H3HexagonLayer<CoverageCell>
      | ScatterplotLayer<EmissionSource>;
    const layers: AnyLayer[] = [mode === "coverage" ? coverage : blame];
    if (showSources && sources.length) {
      layers.push(
        new ScatterplotLayer<EmissionSource>({
          id: "sources",
          data: sources,
          getPosition: (d) => d.coordinates,
          getRadius: (d) => 140 + 240 * (d.detection_confidence ?? 0.5),
          radiusUnits: "meters",
          radiusMinPixels: 5,
          radiusMaxPixels: 24,
          stroked: true,
          getFillColor: [17, 24, 39, 235],
          getLineColor: [255, 255, 255, 235],
          lineWidthMinPixels: 1.5,
          pickable: true,
        }),
      );
    }

    overlayRef.current?.setProps({
      layers,
      getTooltip: (info: { object?: AttrCell | CoverageCell | EmissionSource }) => {
        const o = info?.object;
        if (!o) return null;
        if ("shares" in o) return tooltip(o, mode);
        if ("pm25" in o) {
          const val = coverageKind === "stations" ? o.pm25_stations : o.pm25;
          return {
            html: `<b>${Math.round(val)} µg/m³</b> PM2.5 · ${coverageKind}<br/><span style="color:#888">±${o.uncertainty} µg/m³ uncertainty</span>`,
            style: { fontSize: "12px" },
          };
        }
        return {
          html: `<b>${o.name}</b><br/>${o.type.replace("_", " ")} · ${Math.round((o.detection_confidence ?? 0) * 100)}% · ${o.source_origin ?? "registry"}`,
          style: { fontSize: "12px" },
        };
      },
    });
  }, [cells, mode, selected, onSelect, showSources, sources, coverageCells, coverageKind]);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      {mapError && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-100 p-6 text-center text-sm text-slate-500">
          Map view unavailable on this device — the analysis panels still work.
        </div>
      )}
    </div>
  );
}
