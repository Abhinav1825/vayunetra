"""Agent 2 Forecast — LightGBM quantile trainer + persistence backtest.  ARCHITECTURE.md §9.2.

  python -m ml.forecast.train --city delhi                 # backtest, print skill @24/48/72h
  python -m ml.forecast.train --city delhi --write         # also write forecasts to Supabase

The headline number is skill = 1 - RMSE_model/RMSE_persistence (target >= 0.25).
NOTE: on the synthetic seed the skill will be low/honest — re-run once the real CAAQMS
connector lands and the target is real PM2.5.
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

import pandas as pd

import core.env  # noqa: F401  (loads .env)

from .baselines import rmse, skill_score
from .features import build_feature_table, make_supervised

QUANTILES = {"pi_low": 0.1, "value": 0.5, "pi_high": 0.9}
MODEL_VERSION = "lgbm-q-v1"


def _client():
    from supabase import create_client

    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


def load_measurements(city_id: str) -> pd.DataFrame:
    """Page through all measurements for a city (PostgREST caps at 1000/page)."""
    client = _client()
    rows: list[dict] = []
    start, page = 0, 1000
    while True:
        batch = (
            client.table("measurements")
            .select("city_id,h3_cell,ts,variable,value")
            .eq("city_id", city_id)
            .range(start, start + page - 1)
            .execute()
            .data
        )
        rows.extend(batch)
        if len(batch) < page:
            break
        start += page
    return pd.DataFrame(rows)


def _fit_predict(X_train, y_train, X_pred, alpha: float):
    import lightgbm as lgb

    model = lgb.LGBMRegressor(
        objective="quantile", alpha=alpha, n_estimators=200, learning_rate=0.05,
        num_leaves=31, min_child_samples=5, verbosity=-1,
    )
    model.fit(X_train, y_train)
    return model, model.predict(X_pred)


def backtest(wide: pd.DataFrame, horizon_h: int, test_frac: float = 0.3) -> dict:
    """Temporal-split backtest of the median model vs persistence."""
    X, y, meta, _ = make_supervised(wide, horizon_h)
    n = len(X)
    if n < 20:
        return {"horizon_h": horizon_h, "n": n, "skill": None, "note": "insufficient data"}
    idx = meta.sort_values("ts").index
    X, y = X.loc[idx], y.loc[idx]
    split = int(n * (1 - test_frac))
    _, pred = _fit_predict(X.iloc[:split], y.iloc[:split], X.iloc[split:], 0.5)
    y_test = y.iloc[split:]
    rmse_model = rmse(y_test, pred)
    rmse_pers = rmse(y_test, X.iloc[split:]["pm25"].values)   # persistence: yhat(t+h)=pm25(t)
    return {
        "horizon_h": horizon_h, "n": n,
        "rmse_model": round(rmse_model, 2),
        "rmse_persistence": round(rmse_pers, 2),
        "skill": round(skill_score(rmse_model, rmse_pers), 3),
    }


def write_forecasts(wide: pd.DataFrame, horizon_h: int) -> int:
    """Train on all samples, predict the latest row per cell, write to `forecasts`."""
    X, y, _, feature_cols = make_supervised(wide, horizon_h)
    if len(X) < 20:
        return 0
    latest = wide.sort_values("ts").groupby("h3_cell").tail(1)
    X_pred = latest[feature_cols]
    preds = {name: _fit_predict(X, y, X_pred, a)[1] for name, a in QUANTILES.items()}
    issued_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for i, (_, r) in enumerate(latest.iterrows()):
        rows.append({
            "city_id": r["city_id"], "h3_cell": r["h3_cell"], "issued_at": issued_at,
            "horizon_h": horizon_h, "target_var": "pm25",
            "value": float(preds["value"][i]),
            "pi_low": float(preds["pi_low"][i]), "pi_high": float(preds["pi_high"][i]),
            "persistence_value": float(r["pm25"]), "model_version": MODEL_VERSION,
        })
    _client().table("forecasts").insert(rows).execute()
    return len(rows)


def run(city_id: str, horizons=(24, 48, 72), write: bool = False) -> None:
    long_df = load_measurements(city_id)
    print(f"loaded {len(long_df)} measurements for {city_id}")
    wide = build_feature_table(long_df)
    for h in horizons:
        result = backtest(wide, h)
        print(f"  h={h:>2}h  {result}")
        if write:
            n = write_forecasts(wide, h)
            print(f"        wrote {n} forecasts")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    ap.add_argument("--write", action="store_true", help="write forecasts to Supabase")
    args = ap.parse_args()
    run(args.city, write=args.write)


if __name__ == "__main__":
    main()
