"""Forecast feature engineering.  ARCHITECTURE.md §9.2.

Turns long-format `measurements` into a supervised table: per (cell, t) features
(pollutant levels, broadcast met, calendar, lags) -> target pm25 at t+horizon.
Met is regional (joined by city+ts); pollutants are per H3 cell.
"""
from __future__ import annotations

import pandas as pd

POLLUTANTS = ["pm25", "pm10", "no2", "so2", "co", "o3"]
MET = ["temp", "rh", "precip", "wind_u", "wind_v", "blh"]
LAGS = (1, 24)


def build_feature_table(long_df: pd.DataFrame) -> pd.DataFrame:
    """Long measurements -> wide per (city_id, h3_cell, ts) + met broadcast + calendar + lags."""
    df = long_df.copy()
    # floor to the hour so sources on different sub-hour offsets align
    # (OpenAQ hourly lands at :30, Open-Meteo at :00) — otherwise the met join misses entirely.
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.floor("h")

    poll = df[df["variable"].isin(POLLUTANTS)]
    poll_wide = poll.pivot_table(
        index=["city_id", "h3_cell", "ts"], columns="variable", values="value"
    ).reset_index()

    met = df[df["variable"].isin(MET)]
    met_wide = met.pivot_table(
        index=["city_id", "ts"], columns="variable", values="value"
    ).reset_index()

    wide = poll_wide.merge(met_wide, on=["city_id", "ts"], how="left")
    wide = wide.sort_values(["h3_cell", "ts"]).reset_index(drop=True)

    # physics-informed feature: ventilation coefficient = transport wind speed x mixing height.
    # Low ventilation (calm + shallow boundary layer) => pollution accumulates. (ARCH §9.2)
    if {"wind_u", "wind_v", "blh"} <= set(wide.columns):
        wide["wind_speed"] = (wide["wind_u"] ** 2 + wide["wind_v"] ** 2) ** 0.5
        wide["ventilation"] = wide["wind_speed"] * wide["blh"]

    wide["hour"] = wide["ts"].dt.hour
    wide["dow"] = wide["ts"].dt.dayofweek
    for lag in LAGS:
        wide[f"pm25_lag{lag}"] = wide.groupby("h3_cell")["pm25"].shift(lag)
    return wide


def make_supervised(wide: pd.DataFrame, horizon_h: int, target: str = "pm25"):
    """Return (X, y, meta, feature_cols); y = target at t+horizon within each cell.

    Assumes hourly-contiguous rows per cell (true for our connectors).
    """
    wide = wide.sort_values(["h3_cell", "ts"]).reset_index(drop=True).copy()
    wide["y"] = wide.groupby("h3_cell")[target].shift(-horizon_h)
    drop = {"city_id", "h3_cell", "ts", "y"}
    feature_cols = [c for c in wide.columns if c not in drop]
    # reset index on the whole sample frame so X / y / meta stay aligned (used by .loc in backtest)
    samples = wide.dropna(subset=["y", target]).reset_index(drop=True)
    return (
        samples[feature_cols],
        samples["y"],
        samples[["city_id", "h3_cell", "ts"]],
        feature_cols,
    )
