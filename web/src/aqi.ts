// CPCB National AQI — PM2.5 sub-index (24h) breakpoints.
// https://cpcb.nic.in — [C_lo, C_hi, I_lo, I_hi]
const BANDS: [number, number, number, number][] = [
  [0, 30, 0, 50],
  [31, 60, 51, 100],
  [61, 90, 101, 200],
  [91, 120, 201, 300],
  [121, 250, 301, 400],
  [251, 500, 401, 500],
];

export type AqiCategory = {
  label: string;
  color: string; // hex for backgrounds
  text: string; // readable text color on that background
};

const CATEGORIES: [number, AqiCategory][] = [
  [50, { label: "Good", color: "#16a34a", text: "#ffffff" }],
  [100, { label: "Satisfactory", color: "#84cc16", text: "#1a2e05" }],
  [200, { label: "Moderate", color: "#eab308", text: "#422006" }],
  [300, { label: "Poor", color: "#f97316", text: "#ffffff" }],
  [400, { label: "Very Poor", color: "#dc2626", text: "#ffffff" }],
  [500, { label: "Severe", color: "#7f1d1d", text: "#ffffff" }],
];

/** PM2.5 (µg/m³) -> CPCB AQI sub-index. */
export function pm25ToAqi(pm25: number): number {
  const c = Math.max(0, Math.min(500, pm25));
  for (const [clo, chi, ilo, ihi] of BANDS) {
    if (c <= chi) return Math.round(ilo + ((ihi - ilo) * (c - clo)) / (chi - clo));
  }
  return 500;
}

export function aqiCategory(aqi: number): AqiCategory {
  for (const [max, cat] of CATEGORIES) {
    if (aqi <= max) return cat;
  }
  return CATEGORIES[CATEGORIES.length - 1][1];
}

/** Human "x min/h ago" from an ISO timestamp. */
export function agoLabel(iso?: string): string {
  if (!iso) return "–";
  const ms = Date.now() - new Date(iso).getTime();
  if (!Number.isFinite(ms) || ms < 0) return "now";
  const min = Math.round(ms / 60_000);
  if (min < 1) return "just now";
  if (min < 60) return `${min} min ago`;
  const h = Math.round(min / 60);
  if (h < 48) return `${h}h ago`;
  return `${Math.round(h / 24)}d ago`;
}
