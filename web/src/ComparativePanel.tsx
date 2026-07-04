import { useEffect, useState } from "react";
import { api } from "./api";

type CityCard = {
  city_id: string;
  name: string;
  current_pm25: number;
  forecast_24h_pm25: number;
  trend: string;
  dominant_source: string;
  signature_match: string;
  playbook: string[];
};

type Comparison = {
  summary: { cities_compared: number; highest_risk_city: string; shared_pattern: string };
  cities: CityCard[];
};

export default function ComparativePanel({ onSelectCity }: { onSelectCity: (city: string) => void }) {
  const [data, setData] = useState<Comparison | null>(null);

  useEffect(() => {
    api<Comparison>("/comparison").then(setData).catch(() => setData(null));
  }, []);

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">Multi-City Compare</div>
      <div className="mt-1 text-xs text-gray-600">{data?.summary.shared_pattern ?? "Comparison unavailable"}</div>
      <div className="mt-3 space-y-2">
        {data?.cities.map((c) => (
          <button
            key={c.city_id}
            onClick={() => onSelectCity(c.city_id)}
            className="block w-full rounded-md border border-gray-200 p-2 text-left hover:border-blue-300 hover:bg-blue-50"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{c.name}</span>
              <span className="text-xs text-gray-500">{c.trend}</span>
            </div>
            <div className="mt-1 grid grid-cols-2 gap-2 text-xs text-gray-700">
              <span>now {Math.round(c.current_pm25)} ug/m3</span>
              <span>+24h {Math.round(c.forecast_24h_pm25)} ug/m3</span>
              <span>{c.dominant_source.replace("_", " ")}</span>
              <span>{c.signature_match}</span>
            </div>
            <div className="mt-2 text-xs text-gray-600">{c.playbook[0]}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
