import { useEffect, useState } from "react";
import { api } from "./api";

type StaticLayers = {
  emission_sources: { id: string; type: string; name: string; detection_confidence: number }[];
  vulnerability: { ward_id: string; population: number; vulnerability_index: number; schools: number; hospitals: number }[];
};

type Mobility = { station_id: string; value: number; ts: string }[];

export default function CityIntelPanel({ city }: { city: string }) {
  const [layers, setLayers] = useState<StaticLayers | null>(null);
  const [mobility, setMobility] = useState<Mobility>([]);

  useEffect(() => {
    api<StaticLayers>(`/static-layers?city=${city}`).then(setLayers).catch(() => setLayers(null));
    api<Mobility>(`/mobility?city=${city}`).then(setMobility).catch(() => setMobility([]));
  }, [city]);

  const traffic = mobility.length ? Math.round(mobility.reduce((s, r) => s + r.value, 0) / mobility.length) : null;

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">City Intel</div>
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
        <div className="rounded bg-gray-100 p-2">
          <div className="text-gray-500">sources</div>
          <div className="font-semibold">{layers?.emission_sources.length ?? 0}</div>
        </div>
        <div className="rounded bg-gray-100 p-2">
          <div className="text-gray-500">traffic</div>
          <div className="font-semibold">{traffic ?? "--"}</div>
        </div>
        <div className="rounded bg-gray-100 p-2">
          <div className="text-gray-500">wards</div>
          <div className="font-semibold">{layers?.vulnerability.length ?? 0}</div>
        </div>
      </div>
      <div className="mt-2 space-y-1 text-xs text-gray-700">
        {layers?.emission_sources.slice(0, 2).map((s) => (
          <div key={s.id} className="flex justify-between gap-2">
            <span>{s.name}</span>
            <span>{Math.round(s.detection_confidence * 100)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
