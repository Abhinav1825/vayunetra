// E7 — City ROI dashboard: the annual PM2.5 health burden and the NCAP-target
// savings, i.e. "the funding case". Consumes GET /roi?city. Every figure cited.
import { useEffect, useState } from "react";
import { api } from "./api";
import { Citations, type Citation } from "./ImpactCards";
import { inr, intfmt } from "./format";

type Roi = {
  city_id: string;
  annual_pm25: number;
  who_guideline_pm25: number;
  population: number;
  attributable_deaths_per_year: number;
  annual_health_burden_inr: number;
  ncap_target_reduction_pct: number;
  deaths_avertable_per_year: number;
  annual_savings_inr: number;
  narrative: string;
  citations: Citation[];
};

function Big({ label, value, tone }: { label: string; value: string; tone: "bad" | "good" }) {
  const cls =
    tone === "bad"
      ? "border-red-100 bg-red-50 text-red-700"
      : "border-emerald-100 bg-emerald-50 text-emerald-700";
  return (
    <div className={`rounded-md border p-2 ${cls}`}>
      <div className="text-[10px] uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-lg font-semibold leading-tight">{value}</div>
    </div>
  );
}

export default function RoiPanel({ city }: { city: string }) {
  const [d, setD] = useState<Roi | null>(null);

  useEffect(() => {
    api<Roi>(`/roi?city=${city}`)
      .then(setD)
      .catch(() => setD(null));
  }, [city]);

  if (!d) return <div className="rounded-lg bg-white/95 p-3 text-sm shadow">City ROI unavailable</div>;

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">
        City ROI — the funding case <span className="text-[10px] font-normal text-gray-400">E7</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <Big label="Attributable deaths / yr" value={intfmt(d.attributable_deaths_per_year)} tone="bad" />
        <Big label="Annual health burden" value={inr(d.annual_health_burden_inr)} tone="bad" />
        <Big
          label={`Avertable (−${d.ncap_target_reduction_pct}% NCAP)`}
          value={intfmt(d.deaths_avertable_per_year)}
          tone="good"
        />
        <Big label="Avertable ₹ / yr" value={inr(d.annual_savings_inr)} tone="good" />
      </div>
      <div className="mt-2 text-[11px] text-gray-600">
        Annual mean {d.annual_pm25} µg/m³ vs WHO {d.who_guideline_pm25} µg/m³ · pop {intfmt(d.population)}
      </div>
      <div className="mt-2 rounded bg-slate-50 p-2 text-xs leading-snug text-gray-700">{d.narrative}</div>
      <Citations items={d.citations ?? []} />
    </div>
  );
}
