// Public landing page. Console lives at #/console.
import { useEffect, useState } from "react";
import { api } from "./api";
import { aqiCategory, pm25ToAqi } from "./aqi";

type AqiRow = { pm25?: number; value?: number };
type Trace = { total_latency_ms?: number };

/* Minimal 20px stroke icons — no emoji, no icon fonts. */
function Icon({ d, className = "h-5 w-5" }: { d: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <path d={d} />
    </svg>
  );
}
const IC = {
  hex: "M12 2l8 4.5v9L12 20l-8-4.5v-9L12 2zM12 8v4m0 0l3.5 2M12 12l-3.5 2",
  chart: "M3 20h18M5 16l4-5 3 3 6-8M17 6h2v2",
  scale: "M12 3v18m-7-3h14M7 7l-3 6h6l-3-6zm10 0l-3 6h6l-3-6zM5 7h14",
  megaphone: "M3 11v2a1 1 0 001 1h2l4 4V7L6 11H4a1 1 0 00-1 0zM14 8a4 4 0 010 8M17 5a8 8 0 010 14",
  flame: "M12 3s5 4.5 5 9a5 5 0 01-10 0c0-1.5.5-3 1.5-4.5 0 0 .5 2 2 2.5C10 8 10.5 5 12 3z",
  chip: "M9 9h6v6H9zM5 5h14v14H5zM9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3",
  arrow: "M5 12h14m-6-6l6 6-6 6",
  github:
    "M12 2a10 10 0 00-3.2 19.5c.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.2-3.4-1.2-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.4 1.1 3 .8.1-.6.4-1.1.6-1.3-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.2-.4-1.2.1-2.6 0 0 .8-.3 2.7 1a9.4 9.4 0 015 0c1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.6.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.9v2.8c0 .3.2.6.7.5A10 10 0 0012 2z",
};

const STEPS = [
  {
    icon: IC.hex,
    title: "Trace",
    body: "A gradient-boosted model with SHAP explanations assigns PM2.5 blame to traffic, construction, industry and burning — per square-kilometre H3 cell, cross-checked against published emission inventories.",
  },
  {
    icon: IC.chart,
    title: "Predict",
    body: "Quantile forecasts at 24, 48 and 72 hours for every cell, with conformal-calibrated intervals. Backtested walk-forward against persistence and climatology; both baselines shown in the product.",
  },
  {
    icon: IC.scale,
    title: "Act",
    body: "A ranked enforcement worklist scores each registered source by contribution, exposure and actionability. One click produces an evidence dossier with regulatory citations and a draft notice PDF.",
  },
  {
    icon: IC.megaphone,
    title: "Protect",
    body: "Health advisories generated from the forecast — not yesterday's reading — delivered in English, Hindi, Kannada and Marathi over the web app, Telegram, IVR phone calls and public displays.",
  },
];

const FEATURES = [
  {
    icon: IC.hex,
    title: "Source blame map",
    body: "Interactive hexagon map with per-source shares, SHAP drivers in µg/m³, satellite NO₂ overlay and a dense 1 km coverage layer where no station exists.",
  },
  {
    icon: IC.flame,
    title: "Forecast-triggered GRAP",
    body: "The 24-hour forecast is mapped onto the statutory CAQM GRAP stage bands, flagging the graded response a day before observed AQI would trigger it.",
  },
  {
    icon: IC.chart,
    title: "What-if simulator",
    body: "Counterfactuals for odd-even, construction bans and full GRAP packages — intervention magnitudes cited from Delhi trials, impact priced in ₹, lives and CO₂e.",
  },
  {
    icon: IC.scale,
    title: "Inspector-hour optimiser",
    body: "Ranks whole intervention packages by AQI improvement × people protected per inspector-hour, under a configurable enforcement budget.",
  },
  {
    icon: IC.megaphone,
    title: "Multi-hazard alerts",
    body: "Compound heat–smog risk from IMD and CPCB criteria, plus dust–traffic co-occurrence corridors detected from live attribution shares.",
  },
  {
    icon: IC.chip,
    title: "Auditable agent pipeline",
    body: "Six agents on one LangGraph with per-node latency stamps. Every recommendation carries its trace — from signal to cited action in seconds.",
  },
];

const VALIDATION: Array<[string, string, string]> = [
  ["Attribution matches official inventories", "cosine 0.92 / 0.88 / 0.79", "vs SAFAR-Delhi 2018, CSTEP-Bengaluru 2022, Urban-Emissions Mumbai"],
  ["Attribution behaves physically", "2.30× traffic signal in rush hours", "IST rush vs off-peak SHAP, weather controlled"],
  ["Forecast beats real baselines", "+4–8% Delhi · +9–30% Bengaluru, Mumbai", "walk-forward RMSE vs persistence and climatology"],
  ["Uncertainty intervals are honest", "48–63% raw → 75–80% after CQR", "conformal recalibration audit, nominal 80%"],
  ["Model choice was earned", "TFT trained on GPU — and rejected", "LightGBM won all three cities on held-out skill"],
  ["The loop is fast", "0.8–9.7 s signal → cited action", "live per-node agent traces, target under 5 minutes"],
];

const DATA_SOURCES = ["CPCB / CAAQMS", "Sentinel-5P", "Sentinel-2", "Open-Meteo · ERA5", "NASA FIRMS", "OpenStreetMap", "GPW v4.11"];

export default function Landing() {
  const [aqi, setAqi] = useState<number | null>(null);
  const [latencyS, setLatencyS] = useState<string | null>(null);

  useEffect(() => {
    api<AqiRow[]>("/aqi/current?city=delhi")
      .then((rows) => {
        const pm = rows.map((r) => r.pm25 ?? r.value).filter((v): v is number => typeof v === "number");
        if (pm.length) setAqi(pm25ToAqi(Math.max(...pm)));
      })
      .catch(() => {});
    api<Trace>("/latency?city=delhi")
      .then((t) => {
        const ms = t?.total_latency_ms;
        if (typeof ms === "number" && ms > 0) setLatencyS((ms / 1000).toFixed(1));
      })
      .catch(() => {});
  }, []);

  const cat = aqi !== null ? aqiCategory(aqi) : null;

  return (
    <div className="min-h-full overflow-y-auto bg-slate-950 text-slate-300 antialiased" style={{ scrollBehavior: "smooth" }}>
      {/* Nav */}
      <nav className="sticky top-0 z-20 border-b border-slate-800/60 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-8">
            <a href="#/" className="flex items-center gap-2 text-[15px] font-bold tracking-tight text-white">
              <span className="flex h-6 w-6 items-center justify-center rounded bg-sky-500 text-[12px] font-black text-white">V</span>
              VayuNetra
            </a>
            <div className="hidden items-center gap-6 text-[13px] text-slate-400 md:flex">
              <a href="#how" className="transition-colors hover:text-white">How it works</a>
              <a href="#product" className="transition-colors hover:text-white">Product</a>
              <a href="#validation" className="transition-colors hover:text-white">Validation</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://github.com/omkarrr88/VayuNetra" target="_blank" rel="noreferrer"
              className="text-slate-400 transition-colors hover:text-white" title="Source on GitHub">
              <svg viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5" aria-hidden="true"><path d={IC.github} /></svg>
            </a>
            <a href="#/console"
              className="rounded-md bg-white px-3.5 py-1.5 text-[13px] font-semibold text-slate-900 transition-colors hover:bg-slate-200">
              Open console
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="mx-auto max-w-6xl px-6 pb-12 pt-16 sm:pt-24">
        <p className="font-mono text-[11px] font-medium uppercase tracking-[0.2em] text-sky-400">
          ET AI Hackathon 2026 · Problem Statement 5
        </p>
        <h1 className="mt-4 max-w-3xl text-4xl font-bold leading-[1.1] tracking-tight text-white sm:text-[3.4rem]">
          The operations layer for urban air quality.
        </h1>
        <p className="mt-5 max-w-2xl text-[17px] leading-relaxed text-slate-400">
          VayuNetra traces PM2.5 back to its sources square-kilometre by square-kilometre, forecasts
          72 hours ahead with calibrated uncertainty, and turns both into cited enforcement notices
          and citizen alerts in four languages. Live today for Delhi, Bengaluru and Mumbai — built
          entirely on free public infrastructure.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <a href="#/console"
            className="flex items-center gap-2 rounded-md bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 transition-colors hover:bg-slate-200">
            Open the console
            <Icon d={IC.arrow} className="h-4 w-4" />
          </a>
          <a href="https://github.com/omkarrr88/VayuNetra" target="_blank" rel="noreferrer"
            className="rounded-md border border-slate-700 px-5 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:border-slate-500 hover:text-white">
            View source
          </a>
        </div>
        {(cat || latencyS) && (
          <p className="mt-6 flex items-center gap-2 font-mono text-xs text-slate-500">
            <span className="relative flex h-2 w-2">
              <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-500 opacity-60" />
              <span className="relative h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            live
            {cat && (
              <>
                <span className="text-slate-700">·</span>
                Delhi AQI <span style={{ color: cat.color }}>{aqi} {cat.label}</span>
              </>
            )}
            {latencyS && (
              <>
                <span className="text-slate-700">·</span>
                signal to action {latencyS}s
              </>
            )}
          </p>
        )}
      </header>

      {/* Product screenshot in a browser frame */}
      <div className="mx-auto max-w-6xl px-6">
        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl shadow-black/50">
          <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-2.5">
            <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
            <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
            <span className="h-2.5 w-2.5 rounded-full bg-slate-700" />
            <span className="ml-3 rounded bg-slate-800 px-3 py-0.5 font-mono text-[11px] text-slate-500">
              vayunetra-aqi.vercel.app/#/console
            </span>
          </div>
          <img src="/console.jpg" alt="VayuNetra operations console: source blame map, forecast, enforcement worklist"
            className="block w-full" width={2400} height={1500} />
        </div>
        <p className="mt-3 text-center font-mono text-[11px] text-slate-600">
          The live console — Delhi blame map with a cell opened: attribution shares, 72 h forecast, and the enforcement worklist it feeds.
        </p>
      </div>

      {/* Data sources strip */}
      <div className="mx-auto max-w-6xl px-6 py-14">
        <p className="text-center font-mono text-[11px] uppercase tracking-[0.2em] text-slate-600">
          Built on public data infrastructure
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 font-mono text-[13px] text-slate-500">
          {DATA_SOURCES.map((s) => <span key={s}>{s}</span>)}
        </div>
      </div>

      {/* How it works */}
      <section id="how" className="border-t border-slate-800/60">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-sky-400">How it works</p>
          <h2 className="mt-3 max-w-xl text-2xl font-bold tracking-tight text-white sm:text-3xl">
            From raw signal to a signed notice, in one pipeline.
          </h2>
          <p className="mt-3 max-w-2xl text-[15px] text-slate-400">
            India's monitoring network measures and SAFAR forecasts. The missing layer is operational:
            who is responsible in this square kilometre, and what should be done before tomorrow.
          </p>
          <div className="mt-10 grid gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s, i) => (
              <div key={s.title}>
                <div className="flex items-center gap-3">
                  <span className="text-sky-400"><Icon d={s.icon} /></span>
                  <span className="font-mono text-[11px] text-slate-600">0{i + 1}</span>
                </div>
                <h3 className="mt-3 text-[15px] font-semibold text-white">{s.title}</h3>
                <p className="mt-1.5 text-[13px] leading-relaxed text-slate-400">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Product */}
      <section id="product" className="border-t border-slate-800/60">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-sky-400">Product</p>
          <h2 className="mt-3 max-w-xl text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Built for the control room and the street.
          </h2>
          <div className="mt-10 grid gap-px overflow-hidden rounded-xl border border-slate-800 bg-slate-800 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-slate-950 p-6">
                <span className="text-slate-500"><Icon d={f.icon} /></span>
                <h3 className="mt-3 text-[15px] font-semibold text-white">{f.title}</h3>
                <p className="mt-1.5 text-[13px] leading-relaxed text-slate-400">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Validation */}
      <section id="validation" className="border-t border-slate-800/60">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-sky-400">Validation</p>
          <h2 className="mt-3 max-w-2xl text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Every number is checked — including the failures.
          </h2>
          <p className="mt-3 max-w-2xl text-[15px] text-slate-400">
            Each claim below is reproducible from the evaluation notebook in the repository. Where a
            method underperformed, that result ships too.
          </p>
          <div className="mt-8 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse text-left">
              <thead>
                <tr className="border-b border-slate-800 font-mono text-[11px] uppercase tracking-wider text-slate-600">
                  <th className="py-3 pr-4 font-medium">Claim</th>
                  <th className="py-3 pr-4 font-medium">Result</th>
                  <th className="py-3 font-medium">Method</th>
                </tr>
              </thead>
              <tbody>
                {VALIDATION.map(([claim, result, method]) => (
                  <tr key={claim} className="border-b border-slate-800/60">
                    <td className="py-3.5 pr-4 text-[13px] text-slate-300">{claim}</td>
                    <td className="py-3.5 pr-4 font-mono text-[13px] font-medium text-sky-300">{result}</td>
                    <td className="py-3.5 text-[13px] text-slate-500">{method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-800/60">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-6 py-14 sm:flex-row sm:items-center">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white sm:text-2xl">See it running on live data.</h2>
            <p className="mt-1 text-[14px] text-slate-400">Three cities, real measurements, no sign-up.</p>
          </div>
          <a href="#/console"
            className="flex items-center gap-2 rounded-md bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 transition-colors hover:bg-slate-200">
            Open the console
            <Icon d={IC.arrow} className="h-4 w-4" />
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/60">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-10 sm:flex-row sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-[14px] font-bold text-white">
              <span className="flex h-5 w-5 items-center justify-center rounded bg-sky-500 text-[11px] font-black">V</span>
              VayuNetra
            </div>
            <p className="mt-2 max-w-xs text-[12px] leading-relaxed text-slate-500">
              Air-quality intelligence for smart-city intervention. Delhi · Bengaluru · Mumbai.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-10 text-[13px] sm:grid-cols-3">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-slate-600">Product</p>
              <div className="mt-2 space-y-1.5 text-slate-400">
                <a href="#/console" className="block transition-colors hover:text-white">Console</a>
                <a href="#how" className="block transition-colors hover:text-white">How it works</a>
                <a href="#validation" className="block transition-colors hover:text-white">Validation</a>
              </div>
            </div>
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-slate-600">Resources</p>
              <div className="mt-2 space-y-1.5 text-slate-400">
                <a href="https://github.com/omkarrr88/VayuNetra" target="_blank" rel="noreferrer" className="block transition-colors hover:text-white">GitHub</a>
                <a href="https://vayunetra-c8i8.onrender.com/health" target="_blank" rel="noreferrer" className="block transition-colors hover:text-white">API status</a>
              </div>
            </div>
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-slate-600">Team</p>
              <div className="mt-2 space-y-1.5 text-slate-400">
                <span className="block">Omkar Kadam</span>
                <span className="block">Abhinav Prasad</span>
                <span className="block">Sejal Kumbhar</span>
              </div>
            </div>
          </div>
        </div>
        <div className="border-t border-slate-800/60 py-4 text-center font-mono text-[11px] text-slate-600">
          © 2026 VayuNetra · open source · built for ET AI Hackathon 2026
        </div>
      </footer>
    </div>
  );
}
