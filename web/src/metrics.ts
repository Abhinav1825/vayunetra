// Honest model metrics, surfaced in the UI.
// Source: walk-forward backtests (3 folds) via `python -m ml.forecast.train --city <c>`
// run against the live Supabase data on 2026-07-06. Regenerate with eval/evaluate.ipynb.
// skill = 1 − RMSE_model / RMSE_baseline  (higher is better; 0 = no better than baseline)

export type CitySkill = {
  n: number; // backtest samples @24h
  vsPersistence: Record<number, number>; // horizon_h -> skill
  vsClimatology: Record<number, number>;
};

export const FORECAST_SKILL: Record<string, CitySkill> = {
  delhi: {
    n: 27154,
    vsPersistence: { 24: 0.036, 48: 0.039, 72: 0.078 },
    vsClimatology: { 24: 0.307, 48: 0.181, 72: 0.158 },
  },
  bengaluru: {
    n: 3539,
    vsPersistence: { 24: 0.146, 48: 0.169, 72: 0.091 },
    vsClimatology: { 24: 0.142, 48: 0.045, 72: -0.07 },
  },
  mumbai: {
    n: 3584,
    vsPersistence: { 24: 0.148, 48: 0.178, 72: 0.3 },
    vsClimatology: { 24: 0.029, 48: 0.031, 72: 0.043 },
  },
};

export const SKILL_ASOF = "2026-07-06";

export function pct(x: number | undefined): string {
  if (x === undefined) return "–";
  return `${x >= 0 ? "+" : ""}${Math.round(x * 100)}%`;
}
