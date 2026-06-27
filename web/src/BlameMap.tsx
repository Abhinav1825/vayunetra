import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { api } from "./api";
import { colorFor, dominantSource, type Shares } from "./sources";

type AttrCell = { h3_cell: string; shares: Shares; confidence: number; evidence?: unknown };

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

// Blame Map (Omkar's panel): Deck.gl H3 hexagons coloured by dominant attributed source,
// over a MapLibre basemap. Reads GET /attribution. SHAP-style tooltip on hover.
export default function BlameMap({ city, center }: { city: string; center: [number, number] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [cells, setCells] = useState<AttrCell[]>([]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASEMAP,
      center,
      zoom: ZOOM,
    });
    const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
    map.addControl(overlay);
    mapRef.current = map;
    overlayRef.current = overlay;
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mapRef.current?.flyTo({ center, zoom: ZOOM });
  }, [center]);

  useEffect(() => {
    api<AttrCell[]>(`/attribution?city=${city}`).then(setCells).catch(() => setCells([]));
  }, [city]);

  useEffect(() => {
    const layer = new H3HexagonLayer<AttrCell>({
      id: "blame",
      data: cells,
      getHexagon: (d) => d.h3_cell,
      getFillColor: (d) => colorFor(d.shares),
      getLineColor: [255, 255, 255, 90],
      lineWidthMinPixels: 1,
      extruded: false,
      pickable: true,
    });
    overlayRef.current?.setProps({
      layers: [layer],
      getTooltip: ({ object }: { object?: AttrCell }) => {
        if (!object) return null;
        const d = dominantSource(object.shares);
        const pct = Math.round((object.shares[d] ?? 0) * 100);
        return {
          html: `<b>${d.replace("_", " ")}</b> — ${pct}%<br/>confidence ${object.confidence}`,
          style: { fontSize: "12px" },
        };
      },
    });
  }, [cells]);

  return <div ref={containerRef} className="h-full w-full" />;
}
