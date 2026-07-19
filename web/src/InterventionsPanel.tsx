// Before/after effect tracking for dispatched recs — the PS's "intervention
// effectiveness", built as machinery that arms itself at the first real
// dispatch. Until then it says so, honestly, in one line.
import { useEffect, useState } from "react";
import { api } from "./api";
import { Panel } from "./ui";

type Tracked = {
  rec_id: number;
  h3_cell: string;
  dispatched_at: string;
  days_since_dispatch: number;
  status: "measuring" | "provisional" | "measured";
  effect_pm25?: number;
  cell_delta?: number;
  city_drift?: number;
  note?: string;
};

type Data = { tracked: Tracked[]; note?: string };

export default function InterventionsPanel({ city }: { city: string }) {
  const [d, setD] = useState<Data | null>(null);

  useEffect(() => {
    let alive = true;
    setD(null);
    api<Data>(`/interventions?city=${city}`)
      .then((r) => alive && setD(r))
      .catch(() => alive && setD({ tracked: [] }));
    return () => {
      alive = false;
    };
  }, [city]);

  if (!d) return null;

  return (
    <Panel title="Intervention tracking">
      {d.tracked.length === 0 ? (
        <div className="text-xs leading-5 text-gray-500">
          {d.note ??
            "No real-world intervention dispatched yet — tracking arms automatically at first dispatch."}{" "}
          <span className="text-gray-400">
            Marking a recommendation "dispatched" freezes the cell's 7-day PM2.5 baseline and opens a
            before/after measurement window, corrected for city-wide drift.
          </span>
        </div>
      ) : (
        <div className="space-y-2">
          {d.tracked.map((t) => (
            <div key={t.rec_id} className="rounded-md border border-gray-200 p-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-medium">rec #{t.rec_id} · cell {t.h3_cell.slice(-6)}</span>
                <span
                  className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${
                    t.status === "measured"
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-amber-100 text-amber-800"
                  }`}
                >
                  {t.status}
                </span>
              </div>
              <div className="mt-1 text-gray-600">
                {typeof t.effect_pm25 === "number" ? (
                  <>
                    effect <b>{t.effect_pm25 > 0 ? "+" : ""}{t.effect_pm25} µg/m³</b> vs city drift ·{" "}
                    {t.days_since_dispatch} days since dispatch
                  </>
                ) : (
                  <>measuring — {t.days_since_dispatch} days since dispatch</>
                )}
                {t.note && <span className="text-gray-400"> · {t.note}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
