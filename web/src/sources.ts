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
