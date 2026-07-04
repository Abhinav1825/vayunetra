import { useEffect, useState } from "react";
import { api } from "./api";

type Rec = {
  id: number;
  priority_score: number;
  contribution: number;
  pop_exposed: number;
  rationale: string;
  status: string;
  rubric_score?: { total?: number };
};

export default function EnforcementPanel({ city }: { city: string }) {
  const [rows, setRows] = useState<Rec[]>([]);

  useEffect(() => {
    api<Rec[]>(`/enforcement?city=${city}&limit=5`).then(setRows).catch(() => setRows([]));
  }, [city]);

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">Enforcement Worklist</div>
      <div className="mt-2 space-y-2">
        {rows.map((r) => (
          <div key={r.id} className="rounded-md border border-gray-200 p-2">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">Priority {Math.round(r.priority_score * 100)}</span>
              <span className="text-xs text-gray-500">rubric {r.rubric_score?.total ?? "--"}/10</span>
            </div>
            <div className="mt-1 text-xs text-gray-700">{r.rationale}</div>
            <div className="mt-1 text-xs text-gray-500">
              {Math.round(r.contribution * 100)}% contribution · {r.pop_exposed.toLocaleString()} exposed
            </div>
          </div>
        ))}
        {rows.length === 0 && <div className="text-xs text-gray-500">No active recommendations</div>}
      </div>
    </div>
  );
}
