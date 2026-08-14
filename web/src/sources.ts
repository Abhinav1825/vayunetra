// Source-category palette + helpers for the blame map.
export type Shares = Record<string, number>;

export const SOURCE_COLORS: Record<string, [number, number, number]> = {
  traffic: [220, 80, 60],
  construction_dust: [200, 160, 60],
  industrial: [150, 70, 160],
  biomass_burning: [230, 120, 40],
  transported: [80, 140, 200],
  other: [140, 140, 140],
};

export function dominantSource(shares: Shares): string {
  let best = "other";
  let bestVal = -1;
  for (const [k, v] of Object.entries(shares)) {
    if (v > bestVal) {
      bestVal = v;
      best = k;
    }
  }
  return best;
}

// Fill colour for a cell: dominant source's hue, opacity scaled by how dominant it is.
export function colorFor(shares: Shares): [number, number, number, number] {
  const d = dominantSource(shares);
  const [r, g, b] = SOURCE_COLORS[d] ?? SOURCE_COLORS.other;
  const top = shares[d] ?? 0.5;
  return [r, g, b, Math.round(110 + 130 * Math.min(1, top))];
}

// Satellite NO2 column (mol/m^2) -> sequential blue→red heat. Urban range ~4e-5..2e-4.
export function satColor(no2_sat: number): [number, number, number, number] {
  const t = Math.max(0, Math.min(1, ((no2_sat || 0) - 4e-5) / 1.6e-4));
  return [Math.round(50 + 190 * t), Math.round(120 * (1 - t)), Math.round(200 * (1 - t)), 175];
}
<<<<<<< HEAD

// CPCB PM2.5 AQI band colours (µg/m³) -> deck.gl RGBA, matching aqi.ts categories.
// Used by the E2 dense-coverage field layer.
const PM25_BANDS: [number, [number, number, number]][] = [
  [30, [22, 163, 74]], // good
  [60, [132, 204, 22]], // satisfactory
  [90, [234, 179, 8]], // moderate
  [120, [249, 115, 22]], // poor
  [250, [220, 38, 38]], // very poor
];
export function pm25Color(pm25: number): [number, number, number, number] {
  for (const [hi, [r, g, b]] of PM25_BANDS) if (pm25 <= hi) return [r, g, b, 205];
  return [127, 29, 29, 205]; // severe
}
export const PM25_LEGEND: [string, string][] = [
  ["≤30 Good", "#16a34a"],
  ["31–60 Satisfactory", "#84cc16"],
  ["61–90 Moderate", "#eab308"],
  ["91–120 Poor", "#f97316"],
  ["121–250 Very Poor", "#dc2626"],
  [">250 Severe", "#7f1d1d"],
];
=======
>>>>>>> 434ad3829631b833a9fa2a960fb5ce96ce106729
