"""Intervention effect measurement — armed at dispatch, honest until proven.

The PS asks for "intervention effectiveness"; ground truth requires a real
intervention to have happened. This module is the machinery that measures it
the moment one does: baseline frozen at dispatch, post-window compared against
the same cell AND corrected for city-wide drift (weather affects everyone —
subtracting the city delta isolates the local effect, crudely but honestly).

Pure functions; DB access stays in the API layer.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

MIN_MEASURE_DAYS = 7.0  # verdicts before a full week are labeled provisional


def mean(values: list[float]) -> float | None:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def effect_summary(
    baseline_pm25: float | None,
    cell_after: float | None,
    city_before: float | None,
    city_after: float | None,
    dispatched_at: str,
    now: datetime | None = None,
) -> dict:
    """Provisional intervention effect for one tracked rec.

    effect = (cell_after - baseline) - (city_after - city_before)
    i.e. the cell's change minus the whole city's change over the same window.
    Negative = air improved more than the city did after the intervention.
    """
    now = now or datetime.now(timezone.utc)
    try:
        t0 = datetime.fromisoformat(str(dispatched_at).replace("Z", "+00:00"))
        if t0.tzinfo is None:
            t0 = t0.replace(tzinfo=timezone.utc)
    except ValueError:
        t0 = now
    days = round((now - t0) / timedelta(days=1), 1)

    out: dict = {"days_since_dispatch": max(0.0, days), "status": "measuring"}
    if baseline_pm25 is None or cell_after is None:
        out["note"] = "collecting post-dispatch measurements"
        return out

    cell_delta = round(cell_after - baseline_pm25, 2)
    drift = None
    if city_before is not None and city_after is not None:
        drift = round(city_after - city_before, 2)
    effect = round(cell_delta - (drift or 0.0), 2)

    out.update({
        "baseline_pm25": baseline_pm25,
        "cell_after_pm25": cell_after,
        "cell_delta": cell_delta,
        "city_drift": drift,
        "effect_pm25": effect,
        "status": "measured" if days >= MIN_MEASURE_DAYS else "provisional",
    })
    if days < MIN_MEASURE_DAYS:
        out["note"] = f"needs ≥{int(MIN_MEASURE_DAYS)} days for a stable read"
    return out
