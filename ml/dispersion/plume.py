"""Gaussian plume dispersion (physics prior).  ARCHITECTURE.md §9.3.

A steady-state Gaussian plume for local point/area sources (industry, construction).
Output feeds attribution (local source share) and forecast (a physics feature).
Dispersion coefficients use the Briggs (1973) *urban* parameterization.
"""
from __future__ import annotations

import numpy as np

# Pasquill stability groups -> sigma_y(x), sigma_z(x), x = downwind distance in metres.
# Briggs urban coefficients (valid ~100 m – 10 km).
_SIGMA_Y = {
    "A-B": lambda x: 0.32 * x * (1 + 0.0004 * x) ** -0.5,
    "C":   lambda x: 0.22 * x * (1 + 0.0004 * x) ** -0.5,
    "D":   lambda x: 0.16 * x * (1 + 0.0004 * x) ** -0.5,
    "E-F": lambda x: 0.11 * x * (1 + 0.0004 * x) ** -0.5,
}
_SIGMA_Z = {
    "A-B": lambda x: 0.24 * x * (1 + 0.001 * x) ** 0.5,
    "C":   lambda x: 0.20 * x,
    "D":   lambda x: 0.14 * x * (1 + 0.0003 * x) ** -0.5,
    "E-F": lambda x: 0.08 * x * (1 + 0.0015 * x) ** -0.5,
}
STABILITY_CLASSES = tuple(_SIGMA_Y)


def sigma_y(x, stability: str = "D"):
    return _SIGMA_Y[stability](np.asarray(x, dtype=float))


def sigma_z(x, stability: str = "D"):
    return _SIGMA_Z[stability](np.asarray(x, dtype=float))


def pasquill_stability(wind_ms: float, is_day: bool = True) -> str:
    """Coarse Pasquill-Gifford stability class from wind speed + day/night."""
    if is_day:
        if wind_ms < 2:
            return "A-B"      # light wind, strong convection -> unstable
        if wind_ms < 5:
            return "C"
        return "D"            # neutral
    if wind_ms < 3:
        return "E-F"          # calm night -> stable (inversion)
    return "D"


def gaussian_plume_concentration(
    Q: float, u: float, x, y=0.0, z=0.0, H: float = 0.0, stability: str = "D"
):
    """Concentration (g/m^3) at receptor (x downwind, y crosswind, z height), metres.

    Q  emission rate (g/s) · u wind speed (m/s) · H effective source height (m).
    Accepts scalars or numpy arrays for x/y/z (vectorised for field computation).
    Upwind / at-source (x <= 0) returns 0 — the Gaussian plume is undefined there.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    z = np.asarray(z, dtype=float)
    sy = sigma_y(x, stability)
    sz = sigma_z(x, stability)
    with np.errstate(divide="ignore", invalid="ignore"):
        coef = Q / (2.0 * np.pi * u * sy * sz)
        crosswind = np.exp(-(y**2) / (2.0 * sy**2))
        vertical = np.exp(-((z - H) ** 2) / (2.0 * sz**2)) + np.exp(-((z + H) ** 2) / (2.0 * sz**2))
        c = coef * crosswind * vertical
    return np.where(x > 0, c, 0.0)
