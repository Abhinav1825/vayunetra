"""Chemical-signature source attribution (priors).  ARCHITECTURE.md §9.1; PRD §12.1.

MVP attributor: maps a cell's pollutant signature to a normalised source-share vector
+ confidence + evidence. These are transparent **physics/chemistry priors** — the
supervised gradient-boosting model (calibrated to held-out SAFAR/TERI, with SHAP) is the
Stage-2 upgrade that replaces the fixed weights here. Output shape is identical, so the
blame map / API don't change when the model lands.
"""
from __future__ import annotations

CATEGORIES = (
    "traffic", "construction_dust", "industrial",
    "biomass_burning", "transported", "other",
)

# fallback reference concentrations (~urban winter high) used when data-driven
# calibration isn't available. Prefer calibrate_references() so blame tracks the
# *current* distribution rather than a fixed season.
_REF = {"no2": 80.0, "co": 2.0, "so2": 30.0, "pm25": 150.0, "pm10": 300.0, "fire": 50.0}


def _norm(value: float, ref: float) -> float:
    return max(0.0, min(value / ref, 1.5))


def calibrate_references(values_by_pollutant: dict[str, list]) -> dict:
    """Data-driven reference scales = the 90th percentile of each pollutant.

    A cell near the city's p90 normalises to ~1.0 (strong marker); below-median
    cells stay small. Falls back to the fixed _REF where data is sparse.
    """
    import numpy as np

    refs = dict(_REF)
    for pollutant, values in values_by_pollutant.items():
        clean = [v for v in values if v is not None]
        if pollutant in refs and len(clean) >= 10:
            p90 = float(np.percentile(clean, 90))
            if p90 > 0:
                refs[pollutant] = p90
    return refs


def signature_shares(values: dict, refs: dict | None = None) -> tuple[dict, float, dict]:
    """Pollutant values for a cell -> (shares summing to 1, confidence, evidence).

    `refs` overrides the marker reference scales (use calibrate_references()).
    """
    _REF_USE = refs or _REF
    no2 = values.get("no2") or 0.0
    co = values.get("co") or 0.0
    so2 = values.get("so2") or 0.0
    pm25 = values.get("pm25") or 0.0
    pm10 = values.get("pm10") or 0.0
    fire = values.get("fire") or 0.0
    ratio = (pm10 / pm25) if pm25 > 0 else 0.0   # coarse-dust dominance

    scores = {
        "traffic": 0.6 * _norm(no2, _REF_USE["no2"]) + 0.4 * _norm(co, _REF_USE["co"]),
        "industrial": _norm(so2, _REF_USE["so2"]),
        "construction_dust": max(0.0, ratio - 1.8) * 0.6,
        "biomass_burning": _norm(fire, _REF_USE["fire"]),
        "transported": 0.15,   # regional background baseline (refined by advection later)
        "other": 0.10,
    }
    total = sum(scores.values()) or 1.0
    shares = {k: round(v / total, 4) for k, v in scores.items()}
    confidence = round(min(0.95, max(0.30, max(shares.values()))), 3)
    evidence = {
        "no2": no2, "co": co, "so2": so2, "pm10_pm25_ratio": round(ratio, 2), "fire": fire,
        "top_signals": sorted(shares, key=shares.get, reverse=True)[:2],
    }
    return shares, confidence, evidence
