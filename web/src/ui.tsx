// Shared UI primitives — one card/button language across every panel.
import type { ReactNode } from "react";

export function Panel({
  title,
  tag,
  right,
  children,
  className = "",
}: {
  title?: ReactNode;
  tag?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-slate-200/80 bg-white/95 p-3 text-sm shadow-lg shadow-slate-900/5 backdrop-blur ${className}`}
    >
      {title !== undefined && (
        <div className="mb-2 flex items-center justify-between gap-2">
          <div className="flex items-baseline gap-1.5">
            <span className="whitespace-nowrap text-[13px] font-bold tracking-tight text-slate-800">{title}</span>
            {tag && (
              <span className="whitespace-nowrap rounded bg-slate-100 px-1 py-px text-[9px] font-semibold uppercase tracking-wider text-slate-400">
                {tag}
              </span>
            )}
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

/** Small option button used in every segmented control (horizons, layers, channels…). */
export function SegBtn({
  active,
  onClick,
  children,
  className = "",
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-2 py-1 text-xs font-medium transition-colors ${
        active ? "bg-blue-600 text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
      } ${className}`}
    >
      {children}
    </button>
  );
}
