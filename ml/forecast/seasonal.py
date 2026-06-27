"""Seasonal / event calendar features for the forecast.  ARCHITECTURE.md §9.2; PRD §12.2.

The calendar drivers of Delhi's worst air: post-monsoon **stubble burning**, **Diwali**
firecracker spikes, and the **winter inversion** (shallow boundary layer traps pollution).
Inactive on summer data (all zero) — decisive once the demo uses winter/event windows.
"""
from __future__ import annotations

import pandas as pd

# Approximate main Diwali (Lakshmi Puja) night per year — the big firecracker spike.
DIWALI = {2023: (11, 12), 2024: (11, 1), 2025: (10, 21), 2026: (11, 8), 2027: (10, 29)}
DIWALI_WINDOW_DAYS = 3


def _is_diwali_window(ts: pd.Timestamp) -> int:
    d = DIWALI.get(ts.year)
    if not d:
        return 0
    diwali = pd.Timestamp(year=ts.year, month=d[0], day=d[1], tz=ts.tz)
    return int(abs((ts.normalize() - diwali.normalize()).days) <= DIWALI_WINDOW_DAYS)


def calendar_features(ts) -> dict:
    """Seasonal/event flags for a single timestamp (scalar; used in tests)."""
    ts = pd.Timestamp(ts)
    month = ts.month
    return {
        "is_stubble_season": int(month in (10, 11)),       # paddy-residue burning upwind
        "is_winter_inversion": int(month in (11, 12, 1, 2)),
        "is_diwali_window": _is_diwali_window(ts),
    }


def add_calendar_features(df: pd.DataFrame, ts_col: str = "ts") -> pd.DataFrame:
    """Vectorised: add the seasonal/event flag columns to a feature frame."""
    month = df[ts_col].dt.month
    df["is_stubble_season"] = month.isin([10, 11]).astype(int)
    df["is_winter_inversion"] = month.isin([11, 12, 1, 2]).astype(int)
    df["is_diwali_window"] = df[ts_col].apply(_is_diwali_window).astype(int)
    return df
