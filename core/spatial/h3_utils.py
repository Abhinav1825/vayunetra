"""H3 spatial helpers — the universal spatial key (ARCHITECTURE.md §6).

Primary resolution = res 8 (≈ 0.74 km², edge ≈ 0.46 km) → the brief's "~1 km grid".
Owner: Omkar (F5). This is a working starting point; extend with ward<->H3 mapping.
"""
from __future__ import annotations

from typing import Iterable

import h3  # pip install h3

DEFAULT_RES = 8


def latlng_to_cell(lat: float, lng: float, res: int = DEFAULT_RES) -> str:
    """Point -> H3 cell id at the given resolution."""
    return h3.latlng_to_cell(lat, lng, res)


def cell_to_latlng(cell: str) -> tuple[float, float]:
    """H3 cell id -> (lat, lng) of its center."""
    return h3.cell_to_latlng(cell)


def cells_in_bbox(bbox: tuple[float, float, float, float], res: int = DEFAULT_RES) -> list[str]:
    """All H3 cells covering a [min_lng, min_lat, max_lng, max_lat] bbox."""
    min_lng, min_lat, max_lng, max_lat = bbox
    poly = h3.LatLngPoly(
        [(min_lat, min_lng), (min_lat, max_lng), (max_lat, max_lng), (max_lat, min_lng)]
    )
    return list(h3.polygon_to_cells(poly, res))


def parent(cell: str, res: int) -> str:
    """Aggregate a cell up to a coarser resolution (e.g. res 8 -> res 6 zone)."""
    return h3.cell_to_parent(cell, res)


def k_ring(cell: str, k: int = 1) -> list[str]:
    """Neighbouring cells within distance k (spatial smoothing / neighbours feature)."""
    return list(h3.grid_disk(cell, k))


# TODO Omkar: ward_geojson -> covering H3 set; ward<->h3 mapping table loader.
def cells_for_iterable_points(points: Iterable[tuple[float, float]], res: int = DEFAULT_RES) -> set[str]:
    return {latlng_to_cell(lat, lng, res) for lat, lng in points}
