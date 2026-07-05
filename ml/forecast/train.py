"""Agent 2 Forecast — LightGBM quantile trainer + persistence backtest.  ARCHITECTURE.md §9.2.

  python -m ml.forecast.train --city delhi                 # backtest, print skill @24/48/72h
  python -m ml.forecast.train --city delhi --write         # also write forecasts to Supabase

The headline number is skill = 1 - RMSE_model/RMSE_persistence (target >= 0.25).
NOTE: on the synthetic seed the skill will be low/honest — re-run once the real CAAQMS
connector lands and the target is real PM2.5.
"""
from __future__ import annotations

import argparse
import statistics
from datetime import datetime, timezone

import pandas as pd

from core.supa import client, load_measurements

from .baselines import rmse, skill_score
from .features import build_feature_table, make_supervised

QUANTILES = {"pi_low": 0.1, "value": 0.5, "pi_high": 0.9}
MODEL_VERSION = "lgbm-q-v1"


def _fit_predict(X_train, y_train, X_pred, alpha: float):
    import lightgbm as lgb

    model = lgb.LGBMRegressor(
        objective="quantile", alpha=alpha, n_estimators=200, learning_rate=0.05,
        num_leaves=31, min_child_samples=5, verbosity=-1,
    )
    model.fit(X_train, y_train)
    return model, model.predict(X_pred)


def backtest(wide: pd.DataFrame, horizon_h: int, n_folds: int = 3) -> dict:
    """Walk-forward (expanding-window) backtest: median model vs persistence AND climatology.

    More robust than a single split — skill is averaged over `n_folds` time folds.
    """
    X, y, meta, _ = make_supervised(wide, horizon_h)
    n = len(X)
    if n < 60:
        return {"horizon_h": horizon_h, "n": n, "skill_vs_persistence": None, "note": "insufficient data"}
    order = meta.sort_values("ts").index
    X, y = X.loc[order].reset_index(drop=True), y.loc[order].reset_index(drop=True)

    chunk = n // (n_folds + 1)
    skills_p, skills_c, rmses = [], [], []
    for i in range(n_folds):
        te0 = chunk * (i + 1)
        te1 = chunk * (i + 2) if i < n_folds - 1 else n
        Xtr, ytr, Xte, yte = X.iloc[:te0], y.iloc[:te0], X.iloc[te0:te1], y.iloc[te0:te1]
        if len(Xte) == 0:
            continue
        _, pred = _fit_predict(Xtr, ytr, Xte, 0.5)
        rm = rmse(yte, pred)
        rp = rmse(yte, Xte["pm25"].to_numpy())                    # persistence: yhat(t+h)=pm25(t)
        clim = ytr.groupby(Xtr["hour"]).mean()                    # climatology by hour-of-day
        cpred = Xte["hour"].map(clim).fillna(ytr.mean()).to_numpy()
        rc = rmse(yte, cpred)
        rmses.append(rm)
        skills_p.append(skill_score(rm, rp))
        skills_c.append(skill_score(rm, rc))

    return {
        "horizon_h": horizon_h, "n": n, "folds": len(skills_p),
        "rmse_model": round(statistics.mean(rmses), 2),
        "skill_vs_persistence": round(statistics.mean(skills_p), 3),
        "skill_vs_climatology": round(statistics.mean(skills_c), 3),
    }


def _finite(x) -> float | None:
    """Coerce to a finite float, else None (Postgres NULL).

    NaN/inf break JSON serialization on insert (and sparse-city cells can
    produce them), so anything non-finite becomes NULL rather than crashing.
    """
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if (f == f and f not in (float("inf"), float("-inf"))) else None


def write_forecasts(wide: pd.DataFrame, horizon_h: int) -> int:
    """Train on all samples, predict the latest row per cell, write to `forecasts`."""
    X, y, _, feature_cols = make_supervised(wide, horizon_h)
    if len(X) < 60:
        return 0
    clim = y.groupby(X["hour"]).mean()   # climatology by hour-of-day (for side-by-side storage)
    latest = wide.sort_values("ts").groupby("h3_cell").tail(1)
    X_pred = latest[feature_cols]
    preds = {name: _fit_predict(X, y, X_pred, a)[1] for name, a in QUANTILES.items()}
    issued_at = datetime.now(timezone.utc).isoformat()
    y_mean = float(y.mean())
    rows = []
    for i, (_, r) in enumerate(latest.iterrows()):
        mid = _finite(preds["value"][i])
        if mid is None:
            continue  # no central estimate for this cell -> skip (keeps NaN out of the payload)
        # enforce pi_low <= value <= pi_high (independent quantile models can cross on small data)
        bounds = sorted(v for v in (_finite(preds["pi_low"][i]), mid, _finite(preds["pi_high"][i])) if v is not None)
        lo, hi = bounds[0], bounds[-1]
        hour = r.get("hour")
        clim_val = _finite(clim.get(int(hour), y_mean)) if pd.notna(hour) else y_mean
        rows.append({
            "city_id": r["city_id"], "h3_cell": r["h3_cell"], "issued_at": issued_at,
            "horizon_h": horizon_h, "target_var": "pm25",
            "value": mid, "pi_low": lo, "pi_high": hi,
            "persistence_value": _finite(r["pm25"]),
            "climatology_value": clim_val if clim_val is not None else y_mean,
            "model_version": MODEL_VERSION,
        })
    if not rows:
        return 0
    # idempotent: replace this city+horizon's forecasts instead of accumulating
    city_id = str(latest["city_id"].iloc[0])
    c = client()
    c.table("forecasts").delete().eq("city_id", city_id).eq("horizon_h", horizon_h).execute()
    try:
        c.table("forecasts").insert(rows).execute()
    except Exception:  # noqa: BLE001 — climatology_value column not migrated yet -> store without it
        for row in rows:
            row.pop("climatology_value", None)
        c.table("forecasts").insert(rows).execute()
    return len(rows)


def run(city_id: str, horizons=(24, 48, 72), write: bool = False) -> None:
    long_df = pd.DataFrame(load_measurements(city_id))
    print(f"loaded {len(long_df)} measurements for {city_id}")
    wide = build_feature_table(long_df)
    for h in horizons:
        r = backtest(wide, h)
        print(
            f"  h={h:>2}h  n={r.get('n')} folds={r.get('folds')}  "
            f"skill vs persistence={r.get('skill_vs_persistence')}  vs climatology={r.get('skill_vs_climatology')}"
        )
        if write:
            print(f"        wrote {write_forecasts(wide, h)} forecasts")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--write", action="store_true", help="write forecasts to Supabase")
    args = ap.parse_args()
    run(args.city, write=args.write)


if __name__ == "__main__":
    main()
