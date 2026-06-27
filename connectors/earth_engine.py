"""Earth Engine connector (satellite features).  Owner: Omkar.

Auth via the registered service account, then pull satellite variables and reduce them
onto the H3 grid -> canonical `measurements`. Spec: ARCHITECTURE.md §7.1, §9; PRD §11.

Smoke test (after EE registration is APPROVED + the EE API is enabled):
    python -m connectors.earth_engine
"""
from __future__ import annotations

import os

import ee

from core.spatial.h3_utils import latlng_to_cell

GEE_SERVICE_ACCOUNT = os.getenv("GEE_SERVICE_ACCOUNT", "")
GEE_KEY_JSON = os.getenv("GEE_KEY_JSON", "./gee-key.json")
GEE_PROJECT = os.getenv("GEE_PROJECT", "")

# Earth Engine product ids used by VayuNetra
S5P_NO2 = "COPERNICUS/S5P/OFFL/L3_NO2"   # also _SO2, _CO, _AER_AI variants
MODIS_AOD = "MODIS/061/MCD19A2_GRANULES"  # AOD; VIIRS active-fire is a separate product


def init() -> None:
    """Authenticate the service account and initialise Earth Engine."""
    if not (GEE_SERVICE_ACCOUNT and GEE_PROJECT):
        raise RuntimeError("Set GEE_SERVICE_ACCOUNT and GEE_PROJECT in .env")
    creds = ee.ServiceAccountCredentials(GEE_SERVICE_ACCOUNT, GEE_KEY_JSON)
    ee.Initialize(creds, project=GEE_PROJECT)


def fetch_s5p_no2(city_id: str, bbox: list[float], start: str, end: str, h3_res: int = 8) -> list[dict]:
    """Mean tropospheric NO2 over `bbox` for [start, end), sampled at H3 cell centres.

    Returns canonical measurement dicts ready for the `measurements` table.
    bbox = [min_lng, min_lat, max_lng, max_lat]; dates = 'YYYY-MM-DD'.
    """
    region = ee.Geometry.Rectangle(bbox)
    img = (
        ee.ImageCollection(S5P_NO2)
        .select("tropospheric_NO2_column_number_density")
        .filterDate(start, end)
        .filterBounds(region)
        .mean()
    )

    # H3 cell centres covering the bbox -> sample the image at each point.
    # TODO Omkar: replace this coarse grid with core.spatial.cells_in_bbox centres.
    step = 0.05
    points, cells = [], []
    lng = bbox[0]
    while lng <= bbox[2]:
        lat = bbox[1]
        while lat <= bbox[3]:
            points.append(ee.Feature(ee.Geometry.Point([lng, lat])))
            cells.append((lat, lng))
            lat += step
        lng += step

    fc = ee.FeatureCollection(points)
    sampled = img.reduceRegions(collection=fc, reducer=ee.Reducer.first(), scale=1000).getInfo()

    rows: list[dict] = []
    for feat, (lat, lng) in zip(sampled["features"], cells):
        val = feat["properties"].get("tropospheric_NO2_column_number_density")
        if val is None:
            continue
        rows.append({
            "city_id": city_id,
            "h3_cell": latlng_to_cell(lat, lng, h3_res),
            "ts": end,
            "variable": "no2",
            "value": float(val),
            "unit": "mol/m^2",
            "source": "s5p",
            "confidence": 1.0,
        })
    return rows


if __name__ == "__main__":
    # Minimal end-to-end check: auth + one real EE call over Delhi.
    init()
    delhi_bbox = [76.84, 28.40, 77.35, 28.88]
    n = (
        ee.ImageCollection(S5P_NO2)
        .filterDate("2026-06-20", "2026-06-27")
        .filterBounds(ee.Geometry.Rectangle(delhi_bbox))
        .size()
        .getInfo()
    )
    print(f"EE OK ✓ — {n} Sentinel-5P NO2 images over Delhi this week")
