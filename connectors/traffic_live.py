"""Live traffic congestion via the TomTom Traffic Flow API (free tier).

Optional upgrade of the OSM time-of-day traffic proxy to a REAL mobility feed —
the PS asks for "mobility feeds", and TomTom's free tier (2,500 req/day) covers
a per-city sample comfortably. Entirely env-gated:

    TOMTOM_API_KEY unset  -> everything falls back to the existing proxy,
                             and callers label the basis honestly.

Usage:
    from connectors.traffic_live import live_congestion
    ratio = live_congestion(lat, lon)   # None when no key / API down

    python -m connectors.traffic_live --city delhi   # probe sample points
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import requests

import core.env  # noqa: F401

FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"
CITIES_DIR = Path(__file__).resolve().parent.parent / "core" / "config" / "cities"


def api_key() -> str | None:
    return os.getenv("TOMTOM_API_KEY") or None


def live_congestion(lat: float, lon: float, timeout: int = 10) -> float | None:
    """Congestion ratio at a point: 0 = free-flow … 1 = standstill.

    Derived from currentSpeed / freeFlowSpeed on the nearest road segment.
    Returns None (caller falls back to the proxy) when no key, no coverage,
    or any API failure — a mobility hiccup must never break attribution.
    """
    key = api_key()
    if not key:
        return None
    try:
        resp = requests.get(
            FLOW_URL,
            params={"key": key, "point": f"{lat},{lon}"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return None
        seg = (resp.json() or {}).get("flowSegmentData") or {}
        cur = float(seg.get("currentSpeed") or 0)
        free = float(seg.get("freeFlowSpeed") or 0)
        if free <= 0:
            return None
        return round(max(0.0, min(1.0, 1.0 - cur / free)), 3)
    except (requests.RequestException, ValueError, TypeError):
        return None


def city_sample_points(city_id: str, n: int = 5) -> list[tuple[float, float]]:
    """A few points spread across the city bbox (center + quadrant midpoints)."""
    import yaml

    cfg = yaml.safe_load((CITIES_DIR / f"{city_id}.yml").read_text())
    w, s, e, nb = cfg["bbox"]
    cx, cy = (w + e) / 2, (s + nb) / 2
    pts = [
        (cy, cx),
        ((cy + nb) / 2, (cx + w) / 2),
        ((cy + nb) / 2, (cx + e) / 2),
        ((cy + s) / 2, (cx + w) / 2),
        ((cy + s) / 2, (cx + e) / 2),
    ]
    return pts[:n]


def city_congestion(city_id: str) -> dict | None:
    """Mean live congestion across the sample points, or None without a key."""
    if not api_key():
        return None
    vals = [v for pt in city_sample_points(city_id) if (v := live_congestion(*pt)) is not None]
    if not vals:
        return None
    return {
        "congestion_ratio": round(sum(vals) / len(vals), 3),
        "n_points": len(vals),
        "basis": "TomTom Traffic Flow (live)",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="delhi")
    args = ap.parse_args()
    if not api_key():
        print("TOMTOM_API_KEY not set — live mobility disabled, proxy in use.")
        return
    result = city_congestion(args.city)
    print(result if result else "no coverage / API unavailable at sample points")


if __name__ == "__main__":
    main()
