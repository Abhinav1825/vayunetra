"""Unit tests for forecast baselines + feature engineering (no DB / no training)."""
import pandas as pd

from ml.forecast.baselines import climatology_by_hour, rmse, skill_score
from ml.forecast.features import build_feature_table, make_supervised


def test_rmse():
    assert rmse([1, 2, 3], [1, 2, 3]) == 0.0
    assert round(rmse([0, 0], [3, 4]), 4) == round(12.5 ** 0.5, 4)


def test_skill_score():
    assert skill_score(5, 10) == 0.5      # half the error of persistence
    assert skill_score(10, 10) == 0.0     # no better than persistence
    assert skill_score(5, 0) == 0.0       # guard divide-by-zero


def test_climatology_by_hour():
    ts = ["2026-06-27T00:00:00+00:00", "2026-06-27T00:30:00+00:00", "2026-06-27T01:00:00+00:00"]
    clim = climatology_by_hour(ts, [10, 20, 30])
    assert clim[0] == 15.0 and clim[1] == 30.0


def _long():
    rows = []
    for i, v in enumerate([10, 20, 30, 40]):
        t = f"2026-06-27T0{i}:00:00+00:00"
        rows.append({"city_id": "delhi", "h3_cell": "A", "ts": t, "variable": "pm25", "value": v})
        rows.append({"city_id": "delhi", "h3_cell": "center", "ts": t, "variable": "temp", "value": 25 + i})
    return pd.DataFrame(rows)


def test_build_feature_table_broadcasts_met_and_adds_lags():
    wide = build_feature_table(_long())
    assert {"pm25", "temp", "pm25_lag1", "hour", "dow"} <= set(wide.columns)
    # met (regional) broadcast onto the pollutant cell rows
    a = wide[wide.h3_cell == "A"].sort_values("ts")
    assert list(a["temp"]) == [25, 26, 27, 28]


def test_physics_ventilation_feature():
    t = "2026-06-27T00:00:00+00:00"
    rows = [
        {"city_id": "delhi", "h3_cell": "A", "ts": t, "variable": "pm25", "value": 100},
        {"city_id": "delhi", "h3_cell": "met", "ts": t, "variable": "wind_u", "value": 3.0},
        {"city_id": "delhi", "h3_cell": "met", "ts": t, "variable": "wind_v", "value": 4.0},
        {"city_id": "delhi", "h3_cell": "met", "ts": t, "variable": "blh", "value": 500.0},
    ]
    wide = build_feature_table(pd.DataFrame(rows))
    r = wide[wide.h3_cell == "A"].iloc[0]
    assert r["wind_speed"] == 5.0        # sqrt(3^2 + 4^2)
    assert r["ventilation"] == 2500.0    # wind_speed * blh


def test_make_supervised_target_alignment():
    wide = build_feature_table(_long())
    X, y, meta, cols = make_supervised(wide, horizon_h=1)
    # pm25 [10,20,30,40] -> y(t) = pm25(t+1) = [20,30,40] (last row dropped: no future target)
    assert list(y) == [20.0, 30.0, 40.0]
    assert list(X["pm25"]) == [10.0, 20.0, 30.0]   # persistence anchor stays a feature
    assert {"temp", "pm25_lag1"} <= set(cols)
