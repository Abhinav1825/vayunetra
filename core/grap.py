"""GRAP graded-response mapping + multi-hazard co-occurrence screens.

CAQM's Graded Response Action Plan escalates statutory actions in Delhi-NCR by
CPCB AQI band; VayuNetra mirrors the same schedule as an advisory playbook for
non-NCR cities. VayuNetra's twist: the stage is triggered PROACTIVELY from our
own 24h PM2.5 forecast (q50 max), not yesterday's observed AQI — the same
published schedule, applied a day early.

Stage bands + representative actions: CAQM GRAP schedule (revised 2022, as
amended Dec 2024). AQI conversion: CPCB PM2.5 sub-index (National AQI, 2014).
"""
from __future__ import annotations

from ml.simulator.counterfactual import pm25_to_aqi

# (aqi_lo, aqi_hi, stage, label, representative statutory actions)
GRAP_STAGES: tuple[tuple[int, int, int, str, str], ...] = (
    (201, 300, 1, "Poor",
     "mechanised road sweeping + water sprinkling; strict dust control at C&D sites; PUC enforcement"),
    (301, 400, 2, "Very Poor",
     "ban coal/firewood eateries and diesel generators (non-emergency); intensify C&D inspections"),
    (401, 450, 3, "Severe",
     "ban non-essential construction & demolition; restrict BS-III petrol / BS-IV diesel LMVs"),
    (451, 10_000, 4, "Severe+",
     "halt non-essential truck entry; consider school closures and odd-even scheme"),
)

GRAP_CITATION = {
    "figure": "GRAP stage bands", "value": "I:201-300 II:301-400 III:401-450 IV:>450",
    "unit": "CPCB AQI",
    "source": "CAQM Graded Response Action Plan schedule (revised 2022, amended Dec 2024); "
              "statutory in Delhi-NCR, mirrored as advisory playbook elsewhere",
}

# Both majors at once ⇒ dust-corridor risk: traffic resuspends construction
# dust, so the same cell earns two escalating source signals. Threshold is a
# transparent heuristic screen, not a claim of measured interaction.
CO_OCCURRENCE_MIN_SHARE = 0.25

CO_OCCURRENCE_CITATION = {
    "figure": "co-occurrence screen", "value": CO_OCCURRENCE_MIN_SHARE, "unit": "attribution share (each)",
    "source": "heuristic: cells where construction_dust AND traffic each exceed the threshold; "
              "road/resuspended dust is a top PM contributor in SAFAR-Delhi 2018 inventory",
}


def grap_stage_from_aqi(aqi: float | None) -> dict | None:
    """Map a CPCB AQI to its GRAP stage block, or None below Stage I."""
    if aqi is None:
        return None
    for lo, hi, stage, label, actions in GRAP_STAGES:
        if lo <= aqi <= hi:
            return {"stage": stage, "label": label, "aqi_band": [lo, min(hi, 500)],
                    "actions": actions}
    return None


def forecast_grap(pm25_forecast_max: float | None) -> dict | None:
    """GRAP stage triggered by the 24h PM2.5 forecast (proactive, not reactive)."""
    if pm25_forecast_max is None:
        return None
    aqi = pm25_to_aqi(pm25_forecast_max)
    block = grap_stage_from_aqi(aqi)
    if block is None:
        return None
    return {**block, "trigger_aqi": aqi, "trigger_pm25": round(float(pm25_forecast_max), 1),
            "trigger": "24h forecast q50 max (proactive — applied a day before observed AQI would)"}


def dust_traffic_cells(cells: list[dict], min_share: float = CO_OCCURRENCE_MIN_SHARE) -> list[dict]:
    """Cells where construction_dust AND traffic are simultaneously major.

    `cells` is the /attribution reshape: [{h3_cell, shares: {category: share}}].
    Returns [{h3_cell, construction_dust, traffic, combined}] sorted worst-first.
    """
    hits = []
    for c in cells:
        shares = c.get("shares") or {}
        dust = float(shares.get("construction_dust") or 0.0)
        traffic = float(shares.get("traffic") or 0.0)
        if dust >= min_share and traffic >= min_share:
            hits.append({"h3_cell": c.get("h3_cell"),
                         "construction_dust": round(dust, 3), "traffic": round(traffic, 3),
                         "combined": round(dust + traffic, 3)})
    return sorted(hits, key=lambda h: -h["combined"])
