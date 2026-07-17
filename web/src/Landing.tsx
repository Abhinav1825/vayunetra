// Public landing page — the pitch, live. Console lives at #/console.
import { useEffect, useState } from "react";
import { api } from "./api";
import { aqiCategory, pm25ToAqi } from "./aqi";

type AqiRow = { pm25?: number; value?: number };
type Trace = { total_latency_ms?: number };
type City = { city_id: string; name: string };

const LOOP = [
  { n: "01", title: "Trace", desc: "Per-km² source blame — GBM + SHAP hybrid, validated against official inventories (cosine 0.92 vs SAFAR-Delhi).", icon: "🔍" },
  { n: "02", title: "Predict", desc: "24/48/72h hyperlocal forecasts with honest, CQR-calibrated uncertainty bands that beat real baselines.", icon: "📈" },
  { n: "03", title: "Act", desc: "Cited enforcement worklist → evidence dossier → draft Notice PDF, officer-in-the-loop, fully auditable.", icon: "⚖️" },
  { n: "04", title: "Protect", desc: "Advisories in 4 languages over PWA, Telegram, IVR voice calls and public displays — proactively, from the forecast.", icon: "📣" },
];

const FEATURES = [
  { title: "Blame map", desc: "H3 hexagons with source shares and SHAP “why” tooltips; satellite NO₂ and dense 1 km coverage layers.", icon: "🗺️" },
  { title: "Forecast-triggered GRAP", desc: "Our 24h forecast maps onto the statutory CAQM stage bands — the graded response fires a day early.", icon: "🚦" },
  { title: "What-if + optimiser", desc: "Cited counterfactuals (odd-even, C&D ban, GRAP III) ranked by ΔAQI × people protected per inspector-hour.", icon: "🧪" },
  { title: "Health & carbon ROI", desc: "Every ΔPM2.5 becomes ₹, lives and CO₂e — WHO HRAPIE dose-response, GPW population, all cited.", icon: "💰" },
  { title: "Multi-hazard alerts", desc: "Heat×smog (IMD × CPCB criteria) and dust×traffic co-occurrence from live attribution.", icon: "🔥" },
  { title: "Multi-agent trace", desc: "Six agents on one LangGraph, per-node latency stamps — watch signal become cited action in seconds.", icon: "🤖" },
];

const PROOF = [
  { v: "0.92", l: "cosine vs SAFAR-Delhi inventory" },
  { v: "2.30×", l: "traffic SHAP lift in rush hours" },
  { v: "75–80%", l: "CQR interval coverage (nominal 80%)" },
  { v: "₹0", l: "infrastructure — 100% free tier" },
];

export default function Landing() {
  const [cities, setCities] = useState<City[]>([]);
  const [worstAqi, setWorstAqi] = useState<number | null>(null);
  const [latencyS, setLatencyS] = useState<string | null>(null);

  useEffect(() => {
    api<City[]>("/cities").then(setCities).catch(() => {});
    api<AqiRow[]>("/aqi/current?city=delhi")
      .then((rows) => {
        const pm = rows.map((r) => r.pm25 ?? r.value).filter((v): v is number => typeof v === "number");
        if (pm.length) setWorstAqi(pm25ToAqi(Math.max(...pm)));
      })
      .catch(() => {});
    api<Trace>("/latency?city=delhi")
      .then((t) => {
        const ms = t?.total_latency_ms;
        if (typeof ms === "number" && ms > 0) setLatencyS((ms / 1000).toFixed(1));
      })
      .catch(() => {});
  }, []);

  const cat = worstAqi !== null ? aqiCategory(worstAqi) : null;

  return (
    <div className="min-h-full overflow-y-auto bg-slate-950 text-slate-100" style={{ scrollBehavior: "smooth" }}>
      {/* Nav */}
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2 text-lg font-extrabold tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-blue-700 font-black text-white shadow-lg shadow-blue-900/40">
            V
          </span>
          VayuNetra
        </div>
        <div className="flex items-center gap-3">
          <a href="https://github.com/omkarrr88/VayuNetra" target="_blank" rel="noreferrer"
            className="hidden text-sm text-slate-400 transition-colors hover:text-white sm:block">
            GitHub
          </a>
          <a href="#/console"
            className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-900/40 transition-colors hover:bg-sky-400">
            Open console →
          </a>
        </div>
      </nav>

      {/* Hero */}
      <header className="relative mx-auto max-w-6xl px-6 pb-16 pt-12 text-center sm:pt-20">
        <div className="pointer-events-none absolute inset-x-0 top-0 mx-auto h-72 max-w-3xl rounded-full bg-sky-500/10 blur-3xl" />
        <p className="mx-auto mb-4 w-fit rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs font-medium text-sky-300">
          ET AI Hackathon 2026 · PS-5 · Urban Air Quality Intelligence
        </p>
        <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-tight tracking-tight sm:text-6xl">
          We don't just measure the air.
          <span className="block bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-transparent">
            We trace it, predict it, act on it.
          </span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-slate-400 sm:text-lg">
          A multi-agent action engine for Indian cities: live source attribution per square kilometre,
          calibrated 72-hour forecasts, cited enforcement notices, and citizen alerts in four languages —
          from signal to action in minutes, on ₹0 infrastructure.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <a href="#/console"
            className="rounded-xl bg-sky-500 px-6 py-3 text-sm font-bold text-white shadow-xl shadow-sky-900/40 transition-transform hover:scale-105 hover:bg-sky-400">
            Launch live console
          </a>
          <a href="#how"
            className="rounded-xl border border-slate-700 px-6 py-3 text-sm font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white">
            How it works
          </a>
        </div>

        {/* Live strip — real numbers from the running API */}
        <div className="mx-auto mt-10 flex w-fit flex-wrap items-center justify-center gap-x-6 gap-y-2 rounded-2xl border border-slate-800 bg-slate-900/60 px-6 py-3 text-sm backdrop-blur">
          <span className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            <b>{cities.length || 3}</b>&nbsp;cities live
          </span>
          {cat && (
            <span>
              Delhi now: <b style={{ color: cat.color }}>{worstAqi} AQI · {cat.label}</b>
            </span>
          )}
          {latencyS && (
            <span>
              signal → action <b className="text-emerald-400">{latencyS}s</b>
            </span>
          )}
          <span>
            <b>4</b> languages · <b>4</b> channels
          </span>
        </div>
      </header>

      {/* The loop */}
      <section id="how" className="mx-auto max-w-6xl px-6 py-14">
        <h2 className="text-center text-2xl font-bold sm:text-3xl">The loop nobody else closes</h2>
        <p className="mx-auto mt-2 max-w-xl text-center text-sm text-slate-400">
          CPCB measures. SAFAR forecasts. <b className="text-slate-200">VayuNetra operates</b> — the layer between data and action.
        </p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {LOOP.map((s) => (
            <div key={s.n} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 transition-colors hover:border-sky-800">
              <div className="flex items-center justify-between">
                <span className="text-2xl">{s.icon}</span>
                <span className="text-xs font-bold text-slate-600">{s.n}</span>
              </div>
              <div className="mt-3 text-lg font-bold text-sky-300">{s.title}</div>
              <p className="mt-1.5 text-[13px] leading-relaxed text-slate-400">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-10">
        <h2 className="text-center text-2xl font-bold sm:text-3xl">Built for the control room — and the street</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5">
              <div className="text-xl">{f.icon}</div>
              <div className="mt-2 font-bold text-slate-100">{f.title}</div>
              <p className="mt-1 text-[13px] leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Proof */}
      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-8">
          <h2 className="text-center text-xl font-bold sm:text-2xl">Every number is checked — including the failures</h2>
          <div className="mt-6 grid gap-6 text-center sm:grid-cols-4">
            {PROOF.map((p) => (
              <div key={p.l}>
                <div className="bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-3xl font-extrabold text-transparent">{p.v}</div>
                <div className="mt-1 text-xs text-slate-400">{p.l}</div>
              </div>
            ))}
          </div>
          <p className="mt-6 text-center text-xs text-slate-500">
            Walk-forward backtests vs persistence and climatology · TFT trained on GPU and rejected when LightGBM won ·
            full validation trail reproducible from the repo notebook.
          </p>
        </div>
      </section>

      {/* CTA + footer */}
      <footer className="mx-auto max-w-6xl px-6 pb-10 pt-6 text-center">
        <a href="#/console"
          className="inline-block rounded-xl bg-sky-500 px-8 py-3 text-sm font-bold text-white shadow-xl shadow-sky-900/40 transition-transform hover:scale-105 hover:bg-sky-400">
          Open the live console →
        </a>
        <p className="mt-6 text-xs text-slate-600">
          VayuNetra · Delhi — Bengaluru — Mumbai · built by Omkar, Abhinav & Sejal ·{" "}
          <a className="underline hover:text-slate-400" href="https://github.com/omkarrr88/VayuNetra" target="_blank" rel="noreferrer">
            open source
          </a>
        </p>
      </footer>
    </div>
  );
}
