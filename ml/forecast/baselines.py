"""Forecast baselines + skill metric.  ARCHITECTURE.md §9.2; PRD §13, §21.2.

The brief grades forecast skill against **persistence**. We store persistence (and
climatology) beside every forecast and report skill = 1 - RMSE_model/RMSE_persistence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rmse(y_true, y_pred) -> float:
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def skill_score(rmse_model: float, rmse_persistence: float) -> float:
    """1 - RMSE_model / RMSE_persistence.  > 0 means better than persistence."""
    if rmse_persistence == 0:
        return 0.0
    return 1.0 - rmse_model / rmse_persistence


def climatology_by_hour(timestamps, values) -> dict[int, float]:
    """Mean value per hour-of-day — the climatology baseline."""
    hours = pd.to_datetime(pd.Series(timestamps), utc=True).dt.hour
    return pd.Series(np.asarray(values, dtype=float)).groupby(hours.values).mean().to_dict()
