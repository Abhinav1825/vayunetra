"""Wind-field advection for transported pollution.  ARCHITECTURE.md §9.3.

Traces an air parcel upwind to estimate the *transported* share of pollution at a
receptor cell (e.g. advecting satellite NO2/AOD from upwind). Pure geometry + decay;
the attribution model samples the satellite field at the returned upwind origin.
"""
from __future__ import annotations

import math

M_PER_DEG_LAT = 111_320.0


def meters_to_degrees(dx_m: float, dy_m: float, lat: float) -> tuple[float, float]:
    """Eastward/northward metres -> (dlng, dlat) degrees at the given latitude."""
    dlat = dy_m / M_PER_DEG_LAT
    dlng = dx_m / (M_PER_DEG_LAT * math.cos(math.radians(lat)))
    return dlng, dlat


def upwind_origin(lat: float, lng: float, u: float, v: float, hours: float) -> tuple[float, float]:
    """Where the air now at (lat, lng) came from, given wind (u east, v north) m/s over `hours`.

    The parcel travelled WITH the wind, so its origin is receptor - velocity * dt.
    """
    dt = hours * 3600.0
    dlng, dlat = meters_to_degrees(u * dt, v * dt, lat)
    return lat - dlat, lng - dlng


def decay(value: float, half_life_h: float, hours: float) -> float:
    """Exponential decay of a transported pollutant over travel time.

    NO2 is short-lived (half-life ~ hours); PM is long-lived (use a large half-life).
    """
    return value * 0.5 ** (hours / half_life_h)
