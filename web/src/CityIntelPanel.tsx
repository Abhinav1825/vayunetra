import { useEffect, useState } from "react";
import { api } from "./api";
import { Panel } from "./ui";

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
  const stats: Array<[string, string]> = [];
  if (layers?.emission_sources.length) stats.push(["registry sources", String(layers.emission_sources.length)]);
  if (traffic !== null) stats.push(["traffic index", String(traffic)]);
  if (layers?.vulnerability.length) stats.push(["wards mapped", String(layers.vulnerability.length)]);

  return (
    <Panel title="City Intel">
      {stats.length > 0 ? (
        <div className={`grid gap-2 text-xs ${stats.length === 3 ? "grid-cols-3" : "grid-cols-2"}`}>
          {stats.map(([label, value]) => (
            <div key={label} className="rounded-md bg-slate-50 p-2 ring-1 ring-slate-100">
              <div className="text-[10px] text-slate-500">{label}</div>
              <div className="text-sm font-bold text-slate-800">{value}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-xs text-gray-500">loading city profile…</div>
      )}
      {(layers?.emission_sources.length ?? 0) > 0 && (
        <div className="mt-2 space-y-1 text-xs text-gray-600">
          <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">top registered sources</div>
          {layers!.emission_sources.slice(0, 2).map((s) => (
            <div key={s.id} className="flex justify-between gap-2">
              <span className="truncate">{s.name}</span>
              <span className="shrink-0 text-slate-400">{Math.round(s.detection_confidence * 100)}%</span>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
