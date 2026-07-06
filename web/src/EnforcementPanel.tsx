import { useEffect, useState } from "react";
import { api, downloadFile } from "./api";

type Rec = {
  id: number;
  priority_score: number;
  contribution: number;
  pop_exposed: number;
  rationale: string;
  status: string;
  rubric_score?: { total?: number };
};

type Citation = { rule?: string; url?: string; excerpt?: string; similarity?: number };

type Dossier = {
  rec_id: number;
  rationale?: string;
  contribution_pct?: number;
  pop_exposed?: number;
  citations?: Citation[];
  suggested_notice_text?: string;
};

export default function EnforcementPanel({ city }: { city: string }) {
  const [rows, setRows] = useState<Rec[] | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  useEffect(() => {
    setRows(null);
    setOpen(null);
    api<Rec[]>(`/enforcement?city=${city}&limit=5`).then(setRows).catch(() => setRows([]));
  }, [city]);

  function toggleDossier(id: number) {
    if (open === id) {
      setOpen(null);
      return;
    }
    setOpen(id);
    setDossier(null);
    api<Dossier>(`/enforcement/${id}/dossier`).then(setDossier).catch(() => setDossier({ rec_id: id, citations: [] }));
  }

  async function getNotice(id: number) {
    setBusy(id);
    try {
      await downloadFile(`/enforcement/${id}/notice.pdf`, `notice_${id}.pdf`);
    } catch {
      /* swallow — the button just re-enables so the user can retry */
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="font-semibold">Enforcement Worklist</div>
      {rows === null ? (
        <div className="mt-2 space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-md bg-gray-100" />
          ))}
        </div>
      ) : (
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
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => toggleDossier(r.id)}
                  className={`rounded px-2 py-1 text-xs ${
                    open === r.id ? "bg-slate-700 text-white" : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                  }`}
                >
                  {open === r.id ? "Hide dossier" : "Evidence dossier"}
                </button>
                <button
                  onClick={() => getNotice(r.id)}
                  disabled={busy === r.id}
                  className="rounded bg-blue-600 px-2 py-1 text-xs text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {busy === r.id ? "Generating…" : "Notice PDF"}
                </button>
              </div>

              {open === r.id && (
                <div className="mt-2 rounded-md bg-slate-50 p-2 ring-1 ring-slate-200">
                  {dossier === null ? (
                    <div className="h-12 animate-pulse rounded bg-slate-100" />
                  ) : (
                    <>
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                        Regulatory citations (RAG)
                      </div>
                      {(dossier.citations ?? []).length ? (
                        <div className="mt-1 space-y-1.5">
                          {dossier.citations!.map((c, i) => (
                            <div key={i} className="rounded border border-slate-200 bg-white p-1.5">
                              <div className="flex items-center justify-between gap-2">
                                <span className="text-xs font-semibold text-slate-800">{c.rule ?? "Regulation"}</span>
                                {typeof c.similarity === "number" && (
                                  <span className="shrink-0 rounded bg-emerald-100 px-1 text-[9px] text-emerald-700">
                                    match {Math.round(c.similarity * 100)}%
                                  </span>
                                )}
                              </div>
                              {c.excerpt && <div className="mt-0.5 text-[10px] leading-4 text-slate-500">{c.excerpt}</div>}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="mt-1 text-xs text-slate-400">no citations returned</div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
          {rows.length === 0 && <div className="text-xs text-gray-500">No active recommendations</div>}
        </div>
      )}
    </div>
  );
}
