import { useEffect, useState } from "react";

export const TOUR_KEY = "vayunetra-tour-v1";

export function tourSeen(): boolean {
  try {
    return localStorage.getItem(TOUR_KEY) === "done";
  } catch {
    return true; // storage blocked — never nag
  }
}

function markSeen() {
  try {
    localStorage.setItem(TOUR_KEY, "done");
  } catch {
    /* storage blocked — the flag just won't persist */
  }
}

type Step = {
  title: string;
  body: string;
  // Desktop placement overrides; the base classes center the card (mobile +
  // step 2). Right-anchored steps must also cancel the base `left-1/2`.
  place: string;
  arrow?: "up-left" | "left" | "right";
};

const STEPS: Step[] = [
  {
    title: "One city at a time",
    body: "Pick Delhi, Bengaluru or Mumbai up here. Everything below — map, forecasts, actions — follows the city you choose.",
    place: "lg:translate-x-0 lg:translate-y-0 lg:left-56 lg:top-16",
    arrow: "up-left",
  },
  {
    title: "Every hexagon is ~1 km² of the city",
    body: "The map shows who is to blame for PM2.5, square kilometre by square kilometre. Click any hexagon to see its full story: sources, evidence and a 72-hour outlook.",
    place: "",
  },
  {
    title: "From blame to action",
    body: "The Enforcement panel turns the science into a ranked officer worklist — each item carries cited evidence, a satellite dossier and a ready-to-send notice PDF.",
    place: "lg:translate-x-0 lg:translate-y-0 lg:left-auto lg:right-[26.5rem] lg:top-24",
    arrow: "right",
  },
  {
    title: "Explore the rest",
    body: "Forecast, citizen Advisories in 4 languages, city comparison, a what-if Simulator, health & ₹ Impact, and the live agent Pipeline — all in the sidebar.",
    place: "lg:translate-x-0 lg:translate-y-0 lg:left-52 lg:top-1/3",
    arrow: "left",
  },
];

/** First-run guided tour: 4 fixed cards, no library, dismiss = never again. */
export default function Tour({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);
  const s = STEPS[step];
  const last = step === STEPS.length - 1;

  function finish() {
    markSeen();
    onDone();
  }

  // Standard dialog affordances: Escape and backdrop-click both dismiss.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") finish();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div
      className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-[2px]"
      role="dialog"
      aria-modal="true"
      aria-label="Quick tour"
      onClick={(e) => e.target === e.currentTarget && finish()}
    >
      {/* Positioning and animation live on separate elements — the vn-pop
          keyframe's `transform` would otherwise override the centering
          translate (animation fill-mode wins over utility classes). */}
      <div
        className={`absolute left-1/2 top-1/2 w-[19rem] max-w-[calc(100vw-2rem)] -translate-x-1/2 -translate-y-1/2 ${s.place}`}
      >
        <div key={step} className="vn-pop relative rounded-xl bg-white p-4 shadow-2xl">
          {s.arrow === "up-left" && (
            <div className="absolute -top-1.5 left-6 hidden h-3 w-3 rotate-45 bg-white lg:block" aria-hidden="true" />
          )}
          {s.arrow === "left" && (
            <div className="absolute -left-1.5 top-8 hidden h-3 w-3 rotate-45 bg-white lg:block" aria-hidden="true" />
          )}
          {s.arrow === "right" && (
            <div className="absolute -right-1.5 top-8 hidden h-3 w-3 rotate-45 bg-white lg:block" aria-hidden="true" />
          )}

          <div className="mb-1 flex items-center gap-2">
            <img src="/icon-192.png" alt="" className="h-5 w-5 rounded" width={20} height={20} />
            <span className="text-[13px] font-bold text-slate-900">{s.title}</span>
          </div>
          <p className="text-[12.5px] leading-relaxed text-slate-600">{s.body}</p>

          <div className="mt-3 flex items-center justify-between">
            <div className="flex gap-1.5" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
              {STEPS.map((_, i) => (
                <span
                  key={i}
                  className={`h-1.5 w-1.5 rounded-full transition-colors ${i === step ? "bg-blue-600" : "bg-slate-200"}`}
                />
              ))}
            </div>
            <div className="flex items-center gap-2">
              {!last && (
                <button onClick={finish} className="text-[12px] font-medium text-slate-400 transition-colors hover:text-slate-600">
                  Skip
                </button>
              )}
              <button
                onClick={() => (last ? finish() : setStep(step + 1))}
                className="rounded-md bg-blue-600 px-3 py-1.5 text-[12px] font-semibold text-white transition-colors hover:bg-blue-700"
              >
                {last ? "Start exploring" : "Next"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
