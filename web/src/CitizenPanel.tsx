import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

type Advisory = {
  ward_id: string;
  risk_tier: string;
  audience_segment: string;
  language: string;
  channel: string;
  message: string;
};

const ALL_LANGS = ["en", "hi", "kn", "mr"];
const LABELS: Record<string, string> = { en: "English", hi: "Hindi", kn: "Kannada", mr: "Marathi" };

export default function CitizenPanel({ city, languages }: { city: string; languages?: string[] }) {
  const choices = useMemo(() => Array.from(new Set([...(languages ?? []), ...ALL_LANGS])), [languages]);
  const [lang, setLang] = useState(choices[0] ?? "en");
  const [rows, setRows] = useState<Advisory[]>([]);
  const [channel, setChannel] = useState("pwa");

  useEffect(() => {
    if (!choices.includes(lang)) setLang(choices[0] ?? "en");
  }, [choices, lang]);

  useEffect(() => {
    api<Advisory[]>(`/advisory?city=${city}&lang=${lang}`).then(setRows).catch(() => setRows([]));
  }, [city, lang]);

  const visible = rows.filter((r) => r.channel === channel);
  const channels = Array.from(new Set(rows.map((r) => r.channel)));

  return (
    <div className="rounded-lg bg-white/95 p-3 text-sm shadow">
      <div className="flex items-center justify-between gap-2">
        <div className="font-semibold">Citizen Advisory</div>
        <select className="rounded border px-2 py-1 text-xs" value={lang} onChange={(e) => setLang(e.target.value)}>
          {choices.map((l) => (
            <option key={l} value={l}>
              {LABELS[l] ?? l}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        {(channels.length ? channels : ["pwa", "telegram", "ivr", "display"]).map((c) => (
          <button
            key={c}
            onClick={() => setChannel(c)}
            className={`rounded px-2 py-1 text-xs ${channel === c ? "bg-emerald-600 text-white" : "bg-gray-200 text-gray-700"}`}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="mt-3 space-y-2">
        {visible.map((a, idx) => (
          <div key={`${a.ward_id}-${a.channel}-${idx}`} className="rounded-md border border-gray-200 p-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium">{a.ward_id}</span>
              <span className="rounded bg-amber-100 px-1.5 py-0.5 text-amber-800">{a.risk_tier.replace("_", " ")}</span>
            </div>
            <div className="mt-1 text-xs leading-5 text-gray-700">{a.message}</div>
          </div>
        ))}
        {visible.length === 0 && <div className="text-xs text-gray-500">No advisory in this language/channel yet</div>}
      </div>
    </div>
  );
}
