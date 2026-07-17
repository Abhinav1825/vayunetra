import { useEffect, useMemo, useState } from "react";
import { cellToLatLng } from "h3-js";
import { api, downloadFile } from "./api";

type Rec = {
  id: number;
  h3_cell?: string;
  priority_score: number;
  contribution: number;
  pop_exposed: number;
  rationale: string;
  status: string;
  rubric_score?: { total?: number };
};

/** Rough km between two H3 cells (equirectangular — fine at city scale). */
function cellKm(a: string, b: string): number | null {
  try {
    const [la1, ln1] = cellToLatLng(a);
    const [la2, ln2] = cellToLatLng(b);
    const x = (ln2 - ln1) * Math.cos(((la1 + la2) / 2) * (Math.PI / 180));
    const y = la2 - la1;
    return Math.sqrt(x * x + y * y) * 111.32;
  } catch {
    return null;
  }
}

type Citation = { rule?: string; url?: string; excerpt?: string; similarity?: number };

type SatellitePatch = {
  title?: string;
  image_ref?: string;
  source_url?: string;
  excerpt?: string;
  similarity?: number;
  metadata?: {
    detection_confidence?: number;
    source_type?: string;
  };
};

type Dossier = {
  rec_id: number;
  rationale?: string;
  contribution_pct?: number;
  pop_exposed?: number;
  citations?: Citation[];
  satellite_patch?: string | SatellitePatch | null;
  suggested_notice_text?: string;
};

function normalizePatch(patch: Dossier["satellite_patch"]): SatellitePatch | null {
  if (!patch) return null;
  if (typeof patch === "string") return { title: "Sentinel-2 patch", image_ref: patch };
  return patch;
}

export default function EnforcementPanel({ city, focusCell }: { city: string; focusCell?: string | null }) {
  const [rows, setRows] = useState<Rec[] | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  useEffect(() => {
    setRows(null);
    setOpen(null);
    api<Rec[]>(`/enforcement?city=${city}&limit=8`).then(setRows).catch(() => setRows([]));
  }, [city]);

  // With a focused hexagon, closest actions come first — the story's step 3.
  const ordered = useMemo(() => {
    if (!rows) return null;
    if (!focusCell) return rows;
    return rows
      .map((r) => ({ ...r, km: r.h3_cell ? cellKm(focusCell, r.h3_cell) : null }))
      .sort((a, b) => (a.km ?? 1e9) - (b.km ?? 1e9));
  }, [rows, focusCell]);

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
      <div className="flex items-center justify-between">
        <div className="font-semibold">Enforcement Worklist</div>
        {focusCell && (
          <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700">
            nearest to selected cell first
          </span>
        )}
      </div>
      {ordered === null ? (
        <div className="mt-2 space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-md bg-gray-100" />
          ))}
        </div>
      ) : (
        <div className="mt-2 space-y-2">
          {ordered.map((r: Rec & { km?: number | null }) => (
            <div
              key={r.id}
              className={`rounded-md border p-2 ${
                focusCell && r.h3_cell === focusCell ? "border-blue-400 bg-blue-50/50" : "border-gray-200"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium">Priority {Math.round(r.priority_score * 100)}</span>
                <span className="flex items-center gap-1.5 text-xs text-gray-500">
                  {focusCell && r.h3_cell === focusCell && (
                    <span className="rounded bg-blue-600 px-1 py-0.5 text-[9px] font-semibold text-white">📍 this cell</span>
                  )}
                  {focusCell && r.h3_cell !== focusCell && typeof r.km === "number" && (
                    <span className="text-[10px] text-gray-400">~{r.km < 1 ? "<1" : Math.round(r.km)} km</span>
                  )}
                  rubric {r.rubric_score?.total ?? "--"}/10
                </span>
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
                      {(() => {
                        const patch = normalizePatch(dossier.satellite_patch);
                        return patch ? (
                          <div className="mb-2 rounded border border-sky-100 bg-white p-1.5">
                            <div className="text-[10px] font-semibold uppercase tracking-wide text-sky-700">
                              Satellite evidence
                            </div>
                            {patch.image_ref && (
                              <img
                                src={patch.image_ref}
                                alt={patch.title ?? "Sentinel-2 satellite patch"}
                                className="mt-1 aspect-[3/2] w-full rounded object-cover ring-1 ring-slate-200"
                              />
                            )}
                            <div className="mt-1 text-xs font-semibold text-slate-800">{patch.title ?? "Sentinel-2 patch"}</div>
                            <div className="text-[10px] leading-4 text-slate-500">
                              {patch.metadata?.source_type?.replace(/_/g, " ") ?? "detected source"}
                              {typeof patch.metadata?.detection_confidence === "number" &&
                                ` · ${Math.round(patch.metadata.detection_confidence * 100)}% detection confidence`}
                            </div>
                          </div>
                        ) : null;
                      })()}
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
          {ordered.length === 0 && <div className="text-xs text-gray-500">No active recommendations</div>}
        </div>
      )}
    </div>
  );
}
