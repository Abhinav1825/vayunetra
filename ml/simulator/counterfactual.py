"""E3 counterfactual interface — forecast × attribution what-if.  Owner: Omkar.

PLAN §3A: "expose the counterfactual interface Abhinav's what-if consumes".
Given an intervention (source-share reductions), recompute each cell's
forecast PM2.5:

    new_pm25 = forecast × (1 − Σ_source share[cell][source] × reduction[source])

plus a one-hop dispersion term: a cell's *transported* component shrinks with
the average local reduction elsewhere in the city (pollution that would have
been advected in is no longer produced). Pure function core (`apply_reductions`)
so Abhinav's /simulate and /optimize can call it with injected data; the
`simulate_intervention` wrapper loads live attribution + forecasts from Supabase.

Honest limits: people_protected uses a fixed per-cell population heuristic
(res-8 metro cell ≈ 40k; WorldPop refinement is Stage-2 E2), and tonnes-avoided
needs an emission inventory we don't have — it is returned as None, not faked.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Named interventions -> source-share reductions (fractions of that source removed).
INTERVENTIONS: dict[str, dict[str, float]] = {
    "construction_halt": {"construction_dust": 0.8},
    "traffic_restriction": {"traffic": 0.3},          # odd-even style
    "industrial_shutdown": {"industrial": 0.6},
    "waste_burn_ban": {"biomass_burning": 0.7},
    "grap_stage3": {"construction_dust": 0.8, "traffic": 0.2, "industrial": 0.3},
}

POP_PER_CELL = 40_000          # metro res-8 cell heuristic (Stage-2 E2 refines with WorldPop)
MEANINGFUL_AQI_DROP = 10       # a cell counts as "protected" below this delta
DISPERSION_COUPLING = 0.5      # how strongly the transported share follows city-wide reduction

# CPCB PM2.5 sub-index breakpoints: (C_lo, C_hi, I_lo, I_hi)
_BANDS = [(0, 30, 0, 50), (31, 60, 51, 100), (61, 90, 101, 200),
          (91, 120, 201, 300), (121, 250, 301, 400), (251, 500, 401, 500)]


def pm25_to_aqi(pm25: float) -> int:
    c = max(0.0, min(500.0, pm25))
    for clo, chi, ilo, ihi in _BANDS:
        if c <= chi:
            return round(ilo + (ihi - ilo) * (c - clo) / (chi - clo))
    return 500


@dataclass(frozen=True)
class CellState:
    h3_cell: str
    pm25_forecast: float
    shares: dict[str, float]        # source_category -> share (sums ~1)
    confidence: float


def apply_reductions(
    cells: list[CellState],
    reductions: dict[str, float],
    target_cells: list[str] | None = None,
) -> dict[str, Any]:
    """Pure counterfactual: reduced source shares -> per-cell PM2.5/AQI deltas."""
    targets = set(target_cells) if target_cells else None
    affected = [c for c in cells if targets is None or c.h3_cell in targets]
    if not affected:
        return {"delta_aqi_by_cell": {}, "delta_pm25_by_cell": {}, "people_protected": 0,
                "exposure_hours_reduced": 0, "pm25_tonnes_avoided": None, "confidence": 0.0}

    local_frac = {
        c.h3_cell: sum(c.shares.get(src, 0.0) * min(max(r, 0.0), 1.0) for src, r in reductions.items())
        for c in affected
    }
    city_mean_reduction = sum(local_frac.values()) / len(local_frac)

    delta_pm25: dict[str, float] = {}
    delta_aqi: dict[str, int] = {}
    for c in affected:
        # one-hop dispersion: the transported component shrinks with city-wide action
        transported_gain = (
            c.shares.get("transported", 0.0) * city_mean_reduction * DISPERSION_COUPLING
            if "transported" not in reductions else 0.0
        )
        frac = min(0.95, local_frac[c.h3_cell] + transported_gain)
        new = c.pm25_forecast * (1.0 - frac)
        delta_pm25[c.h3_cell] = round(new - c.pm25_forecast, 2)
        delta_aqi[c.h3_cell] = pm25_to_aqi(new) - pm25_to_aqi(c.pm25_forecast)

    protected_cells = [h for h, d in delta_aqi.items() if d <= -MEANINGFUL_AQI_DROP]
    people = len(protected_cells) * POP_PER_CELL
    conf = round(sum(c.confidence for c in affected) / len(affected), 3)

    return {
        "delta_pm25_by_cell": delta_pm25,
        "delta_aqi_by_cell": delta_aqi,
        "people_protected": people,
        "exposure_hours_reduced": 0,   # filled by the wrapper (needs horizon)
        "pm25_tonnes_avoided": None,   # needs an emission inventory — not faked
        "confidence": conf,
    }


def _load_cells(city_id: str, horizon_h: int) -> list[CellState]:
    """Live attribution shares + forecasts -> CellState list (server-side only)."""
    from core.supa import client

    db = client()
    attr = (
        db.table("attribution")
        .select("h3_cell,source_category,share,confidence")
        .eq("city_id", city_id)
        .execute()
        .data
    )
    fc = (
        db.table("forecasts")
        .select("h3_cell,value")
        .eq("city_id", city_id)
        .eq("horizon_h", horizon_h)
        .execute()
        .data
    )
    fc_by_cell = {r["h3_cell"]: float(r["value"]) for r in fc if r.get("value") is not None}

    shares: dict[str, dict[str, float]] = {}
    conf: dict[str, float] = {}
    for r in attr:
        shares.setdefault(r["h3_cell"], {})[r["source_category"]] = float(r["share"])
        conf[r["h3_cell"]] = float(r.get("confidence") or 0.5)

    return [
        CellState(h3_cell=cell, pm25_forecast=fc_by_cell[cell], shares=s, confidence=conf.get(cell, 0.5))
        for cell, s in shares.items()
        if cell in fc_by_cell
    ]


def simulate_intervention(
    city_id: str,
    intervention_type: str = "construction_halt",
    target_cells: list[str] | None = None,
    horizon_h: int = 24,
    reductions: dict[str, float] | None = None,
) -> dict[str, Any]:
    """The interface /simulate (and later /optimize) consumes. Loads live data."""
    red = reductions or INTERVENTIONS.get(intervention_type)
    if not red:
        raise ValueError(
            f"unknown intervention '{intervention_type}' — known: {sorted(INTERVENTIONS)} "
            "(or pass explicit `reductions`)"
        )
    cells = _load_cells(city_id, horizon_h)
    result = apply_reductions(cells, red, target_cells)
    protected = result["people_protected"]
    return {
        **result,
        "exposure_hours_reduced": protected * horizon_h,
        "intervention": {"type": intervention_type, "reductions": red, "horizon_h": horizon_h},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
