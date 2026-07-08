import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { api } from "./api";
import { colorFor, dominantSource, satColor, type Shares } from "./sources";

export type ShapDriver = { feature: string; source: string; contribution: number };

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

export type MapMode = "blame" | "satellite";

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
}: {
  city: string;
  center: [number, number];
  mode: MapMode;
  selected?: string | null;
  onSelect?: (cell: AttrCell | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [cells, setCells] = useState<AttrCell[]>([]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({ container: containerRef.current, style: BASEMAP, center, zoom: ZOOM });
    const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
    map.addControl(overlay);
    mapRef.current = map;
    overlayRef.current = overlay;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const [lng, lat] = center;
    if (Number.isFinite(lng) && Number.isFinite(lat)) {
      mapRef.current?.flyTo({ center, zoom: ZOOM });
    }
  }, [center]);

  useEffect(() => {
    api<AttrCell[]>(`/attribution?city=${city}`).then(setCells).catch(() => setCells([]));
  }, [city]);

  useEffect(() => {
    const layer = new H3HexagonLayer<AttrCell>({
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
    overlayRef.current?.setProps({
      layers: [layer],
      getTooltip: ({ object }: { object?: AttrCell }) => (object ? tooltip(object, mode) : null),
    });
  }, [cells, mode, selected, onSelect]);

  return <div ref={containerRef} className="h-full w-full" />;
}
