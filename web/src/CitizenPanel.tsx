import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { Panel, SegBtn } from "./ui";

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

type BroadcastResult = {
  telegram?: { status: string; detail?: string; message_id?: number };
  ivr?: { status: string; detail?: string; sid?: string };
};

export default function CitizenPanel({ city, languages }: { city: string; languages?: string[] }) {
  const choices = useMemo(() => Array.from(new Set([...(languages ?? []), ...ALL_LANGS])), [languages]);
  const [lang, setLang] = useState(choices[0] ?? "en");
  const [rows, setRows] = useState<Advisory[] | null>(null);
  const [channel, setChannel] = useState("pwa");
  const [bcast, setBcast] = useState<"idle" | "confirm" | "sending" | "done" | "error">("idle");
  const [bcastMsg, setBcastMsg] = useState("");

  useEffect(() => {
    if (!choices.includes(lang)) setLang(choices[0] ?? "en");
  }, [choices, lang]);

  useEffect(() => {
    setRows(null);
    api<Advisory[]>(`/advisory?city=${city}&lang=${lang}`).then(setRows).catch(() => setRows([]));
  }, [city, lang]);

  async function broadcast() {
    setBcast("sending");
    try {
      const r = await api<BroadcastResult>("/advisory/broadcast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city, ivr: true }),
      });
      const parts: string[] = [];
      if (r.telegram) parts.push(`Telegram: ${r.telegram.status}`);
      if (r.ivr) parts.push(`IVR: ${r.ivr.status}`);
      setBcastMsg(parts.join(" · ") || "sent");
      setBcast("done");
    } catch (e) {
      setBcastMsg(e instanceof Error ? e.message : "failed");
      setBcast("error");
    }
    setTimeout(() => setBcast("idle"), 8000);
  }

  const visible = (rows ?? []).filter((r) => r.channel === channel);
  const channels = Array.from(new Set((rows ?? []).map((r) => r.channel)));

  return (
    <Panel
      title="Citizen Advisory"
      tag="A4"
      right={
        <select
          className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-700"
          value={lang}
          onChange={(e) => setLang(e.target.value)}
        >
          {choices.map((l) => (
            <option key={l} value={l}>
              {LABELS[l] ?? l}
            </option>
          ))}
        </select>
      }
    >
      <div className="flex flex-wrap gap-1">
        {(channels.length ? channels : ["pwa", "telegram", "ivr", "display"]).map((c) => (
          <SegBtn key={c} active={channel === c} onClick={() => setChannel(c)}>
            {c}
          </SegBtn>
        ))}
      </div>

      {rows === null ? (
        <div className="mt-3 space-y-2">
          {[0, 1].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-md bg-gray-100" />
          ))}
        </div>
      ) : (
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
      )}

      {/* Live multi-channel broadcast — the demo "wow" button */}
      <div className="mt-3 border-t border-gray-100 pt-2">
        {bcast === "idle" && (
          <button
            onClick={() => setBcast("confirm")}
            className="w-full rounded bg-emerald-600 px-2 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700"
          >
            📣 Broadcast latest alert (Telegram + IVR)
          </button>
        )}
        {bcast === "confirm" && (
          <div className="rounded border border-amber-300 bg-amber-50 p-2 text-xs">
            <div className="text-amber-800">Send a real Telegram message and place a real phone call?</div>
            <div className="mt-1.5 flex gap-2">
              <button onClick={broadcast} className="rounded bg-emerald-600 px-2 py-1 text-white">
                Yes, broadcast
              </button>
              <button onClick={() => setBcast("idle")} className="rounded bg-gray-200 px-2 py-1 text-gray-700">
                Cancel
              </button>
            </div>
          </div>
        )}
        {bcast === "sending" && <div className="text-center text-xs text-gray-500">broadcasting…</div>}
        {(bcast === "done" || bcast === "error") && (
          <div
            className={`rounded p-1.5 text-center text-xs ${
              bcast === "done" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
            }`}
          >
            {bcastMsg}
          </div>
        )}
      </div>
    </Panel>
  );
}
